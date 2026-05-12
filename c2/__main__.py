import math
import os.path
import queue
import threading
import time
import cv2
import libcamera
import requests
from PIL import Image, ImageDraw

from libcamera import ColorSpace
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder
from picamera2.outputs import PyavOutput
import numpy as np

from c2.api import ControlAPI
from c2.audio import AudioManager
from c2.config import Config
from c2.drmoutput import DRMOutput
from c2.edid import check_edid
from c2.gamma import open_isp, generate_curve, set_isp_gamma

from c2.user_interface import UI


class Camera:
    OVERLAY_ZEBRA = 0
    OVERLAY_FALSE = 1
    OVERLAY_FOCUS = 2
    OVERLAY_UI = 3
    OVERLAY_HISTOGRAM = 4
    OVERLAY_AUDIO = 5

    def __init__(self):
        self.cam = Picamera2()
        self.isp = open_isp()
        self.state = {}
        self.edid = None
        self.preview_w = 1
        self.preview_h = 1
        self.cal = {}

        self.load_tuning()

        self.config = Config("/boot/camera.ini")

        self.output_hdmi = self.config.output.output
        self.output_ui = self.config.monitor.output
        self.output_aux = self.config.aux.output
        self.ui_size = self.config.monitor.mode

        # Set initial camera mode and controls
        preview_config = self.cam.create_preview_configuration(main={
            "size": (1920, 1080),
            "format": "YUV420"
        },
            lores={
                "size": self.ui_size,
                "format": "YUV420"
            },
            controls={
                'FrameRate': self.config.sensor.framerate,
                "NoiseReductionMode": self.config.sensor.noise_reduction_constant,
                "Sharpness": self.config.sensor.sharpness,
                "Saturation": self.config.sensor.saturation,
                "Contrast": self.config.sensor.contrast,
                "ExposureValue": self.config.sensor.exposure_compensation,
            }, colour_space=ColorSpace.Rec709())
        self.cam.configure(preview_config)

        # Enable DRM output of the camera stream to the HDMI output and the DSI display
        self.drm = DRMOutput(self.config.output.mode[0], self.config.output.mode[1])
        self.out_hdmi = self.drm.use_output(self.output_hdmi, self.config.output.mode[0], self.config.output.mode[1],
                                            self.config.output.framerate, 1)
        self.out_dsi = self.drm.use_output(self.output_ui, self.ui_size[0], self.ui_size[1], None, 6)
        if self.config.aux.output != "disabled":
            self.out_aux = self.drm.use_output(self.config.aux.output, self.config.aux.mode[0], self.config.aux.mode[1],
                                               self.config.aux.framerate, 1)
        # Configure the hardware H.264 encoder
        if self.config.encoder.enabled:
            self.encoder = H264Encoder(self.config.encoder.bitrate_int, framerate=self.config.sensor.framerate,
                                       profile='high')
            self.stream = PyavOutput("rtsp://127.0.0.1:8554/cam", format="rtsp")
            self.encoder.output = self.stream

        def preview(request):
            self.update_preview(request)

        self.cam.pre_callback = preview
        self.api = ControlAPI(self)

        self.mat_black = None
        self.mat_white = None
        self.mat_zebra = None
        self.update_idx = 0

        self.thresh_zebra = 230
        self.thresh_under = 18

        self.audio = AudioManager(self.config)
        self.levels = queue.Queue()
        self.vu = Image.new("RGBA", (512, 32), "black")

        self.ui = UI(self.ui_size[0], self.ui_size[1], self, self.config, self.cam.camera_controls)
        self.ui_hdmi = UI(1920, 64, self, self.config, self.cam.camera_controls, hdmi=True)

        def on_aux_paint(buf):
            self.drm.set_overlay(buf, output=self.output_aux, num=0)

        if self.config.aux.purpose != 'clean':
            self.ui_aux = UI(1920, 64, self, self.config, self.cam.camera_controls, hdmi=True)
            self.ui_aux.paint_hook = on_aux_paint

        def on_paint(buf):
            self.drm.set_overlay(buf, output=self.output_ui, num=self.OVERLAY_UI)

        self.ui.paint_hook = on_paint

        def on_hdmi_paint(buf):
            self.drm.set_overlay(buf, output=self.output_hdmi, num=0)

        self.ui_hdmi.paint_hook = on_hdmi_paint

        self.debounce = 0
        self.last_update = {
            "zebra": 0,
            "false": 0,
            "focus": 0,
            "histogram": 0,
        }

    def load_tuning(self):
        sensor_model = self.cam.camera_properties["Model"]
        cal_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "calibration")
        self.cam.close()
        self.cal = self.cam.load_tuning_file(f"{sensor_model}.json", dir=cal_dir)
        self.cam = Picamera2(tuning=self.cal)

    def start(self):
        self.cam.start_preview(self.drm)
        self.cam.start()
        if self.config.encoder.enabled:
            self.cam.start_encoder(self.encoder)

        for i in range(100):
            time.sleep(0.1)
            if self.out_hdmi.overlay_exists(0) and self.out_dsi.overlay_exists(0):
                break

        self.out_hdmi.overlay_position(0, 0, 0, self.config.output.mode[0], 64)
        self.out_dsi.overlay_position(self.OVERLAY_HISTOGRAM, 64, self.config.monitor.mode[1] - 200, 256, 100)
        if self.output_aux != 'disabled' and self.config.aux.purpose != 'clean':
            self.out_aux.overlay_position(0, 0, 0, self.config.aux.mode[0], 64)

        self.move_vu(False)
        self.out_hdmi.overlay_opacity(0, 0.0)

        # Set initial state to keep consistency with the API
        self.cam.set_controls({"AeEnable": True, "AwbEnable": True})
        self.preview_w, self.preview_h = self.cam.stream_configuration("lores")["size"]
        self.create_mask_images()
        self.ui.start()

        audio_thread = threading.Thread(target=self.audio.start_loop, args=(self.levels,))
        audio_thread.daemon = True
        audio_thread.start()

        # Change the temperature range to the one in the calibration file
        awb = Picamera2.find_tuning_algo(self.cal, "rpi.awb")
        if "ct_curve" in awb:
            self.ui.min_temp.set(awb["ct_curve"][0])
            self.ui.max_temp.set(awb["ct_curve"][-3])
        else:
            print("No CT curve defined in sensor calibration file")
            self.ui.min_temp.set(2500)
            self.ui.max_temp.set(9000)

        self.update_gamma_curve()

    def move_vu(self, in_settings):
        if not in_settings:
            self.out_dsi.overlay_position(self.OVERLAY_AUDIO, self.config.monitor.mode[0] - 256 - 64,
                                          self.config.monitor.mode[1] - 128, 256, 32)
        else:
            self.out_dsi.overlay_position(self.OVERLAY_AUDIO, int(self.config.monitor.mode[0] / 2) - 256,
                                          self.config.monitor.mode[1] - 48, 512, 32)

    def create_mask_images(self):
        self.mat_black = np.zeros((self.preview_h, self.preview_w), np.uint8)
        self.mat_white = np.zeros((self.preview_h, self.preview_w), np.uint8)
        self.mat_white[:] = (255,)
        self.mat_zebra = np.zeros((self.preview_h, self.preview_w), np.uint8)
        self.mat_zebra[:] = (255,)

        for offset in range(0, self.preview_w, 10):
            cv2.line(self.mat_zebra, (offset, 0), (offset, self.preview_h), (0, 0, 0), 3)

    def draw_audio(self):
        if self.levels.empty():
            return

        data = None
        while not self.levels.empty():
            frame = self.levels.get()
            if data is None:
                data = list(frame)
            for i, v in enumerate(frame):
                data[i] = max(data[i], v)

        width, height = self.vu.size

        thresh_yellow = 0.5
        off_yellow = int(width * thresh_yellow) + 1
        thresh_red = 0.8
        off_red = int(width * thresh_red) + 1

        ctx = ImageDraw.Draw(self.vu)
        ctx.rectangle((0, 0, width, height), fill=(10, 10, 10, 128))
        bh = (height - 2) / len(data)
        for i, chan in enumerate(data):
            norm = chan / 16446
            dB = 10 * math.log(norm + 0.00001)
            # TODO: Better curve fitting
            y = max(0.0, 1 + 0.03 * dB)
            val = int(y * (width - 2))
            ctx.rectangle((1, 1 + bh * i, min(val + 1, off_yellow), 1 + bh * (i + 1)), fill=(128, 255, 0, 255))
            if val > off_yellow:
                ctx.rectangle((off_yellow, 1 + bh * i, min(val + 1, off_red), 1 + bh * (i + 1)),
                              fill=(255, 255, 0, 255))
            if val > off_red:
                ctx.rectangle((off_red, 1 + bh * i, min(val + 1, width), 1 + bh * (i + 1)), fill=(255, 0, 0, 255))
        self.drm.set_overlay(self.vu, output=self.output_ui, num=self.OVERLAY_AUDIO)

    def loop(self):
        start = time.time()
        self.state = self.cam.capture_metadata()
        self.api.update_state(self.cam.capture_metadata())
        self.api.do_work()
        self.ui.update_state(self.cam.capture_metadata())
        self.ui_hdmi.update_state(self.cam.capture_metadata())
        if self.config.aux.output != 'disabled' and self.config.aux.purpose != 'clean':
            self.ui_aux.update_state(self.cam.capture_metadata())
        self.draw_audio()

        if self.debounce > 60:
            self.debounce = 0
            self.edid = check_edid()
            self.ui.camera_id.set(self.edid.camera_id)
            self.ui_hdmi.camera_id.set(self.edid.camera_id)
        self.debounce += 1
        time.sleep(max(1.0 / 30 - (time.time() - start), 0))

    def set_controls(self, **kwargs):
        self.cam.set_controls(kwargs)

    def enable_zebra(self, enable):
        self.ui.zebra.set(enable)
        self.out_dsi.overlay_opacity(self.OVERLAY_ZEBRA, 1.0 if enable else 0.0)

    def enable_histogram(self, enable):
        self.ui.histogram.set(enable)
        self.out_dsi.overlay_opacity(self.OVERLAY_HISTOGRAM, 1.0 if enable else 0.0)

    def enable_false_color(self, enable):
        self.ui.false_color.set(enable)
        self.out_dsi.overlay_opacity(self.OVERLAY_FALSE, 1.0 if enable else 0.0)

    def enable_focus_assist(self, enable):
        self.ui.focus_assist.set(enable)
        self.out_dsi.overlay_opacity(self.OVERLAY_FOCUS, 1.0 if enable else 0.0)

    def enable_hdmi_overlay(self, enable):
        self.ui.hdmi_overlay.set(enable)
        self.out_hdmi.overlay_opacity(0, 1.0 if enable else 0.0)

    def enable_recording(self, enable):
        self.ui.recording.set(enable)
        self.ui.tally.set(enable)

        requests.patch("http://127.0.0.1:9997/v3/config/paths/patch/cam", json={
            "record": enable
        })

    def enable_focus_zoom(self, enable):
        # The default 1280x800 monitor is at 0.66x scale, with 1.5x zoom it would archieve 1:1 pixel mapping
        # so this zooms to 3x to have 2:1 pixel mapping on the default zoom level
        one_to_one = 1920 / self.out_dsi.width
        self.out_dsi.zoom = one_to_one * 2 if enable else 1.0
        self.ui.zoom.set(self.out_dsi.zoom)

    def enable_auto_exposure(self, enabled):
        self.ui.ae.set(enabled)
        self.cam.set_controls({"AeEnable": enabled})

    def enable_auto_whitebalance(self, enabled):
        self.ui.awb.set(enabled)
        self.cam.set_controls({"AwbEnable": enabled})

    def update_gamma_curve(self):
        curve = generate_curve(self.ui.cc_lift.value, self.ui.cc_gamma.value, self.ui.cc_gain.value,
                               self.ui.cc_offset.value)
        set_isp_gamma(self.isp, curve)

    def set_gamma(self, gamma):
        """ Set gamma in the scale of the bmd primary color corrector (0 = linear) """
        self.ui.cc_gamma.set(gamma)
        self.update_gamma_curve()

    def set_lift(self, lift):
        self.ui.cc_lift.set(lift)
        self.update_gamma_curve()

    def set_cc_gain(self, gain):
        self.ui.cc_gain.set(gain)
        self.update_gamma_curve()

    def set_cc_offset(self, offset):
        self.ui.cc_offset.set(offset)
        self.update_gamma_curve()

    def set_ev(self, compensation):
        self.ui.ec.set(compensation)
        self.cam.set_controls({"ExposureValue": compensation})

    def set_gain(self, gain):
        self.enable_auto_exposure(False)
        self.ui.gain.set(gain)
        self.cam.set_controls({"AnalogueGain": gain})

    def set_focus(self, distance):
        self.ui.focus.set(distance)
        self.cam.set_controls({"LensPosition": distance})

    def set_awb_mode(self, mode):
        self.ui.awbmode.set(mode)
        if mode == "auto":
            self.cam.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Auto})
        elif mode == "tungsten":
            self.cam.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Tungsten})
        elif mode == "fluorescent":
            self.cam.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Fluorescent})
        elif mode == "indoor":
            self.cam.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Indoor})
        elif mode == "daylight":
            self.cam.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Daylight})
        elif mode == "cloudy":
            self.cam.set_controls({"AwbMode": libcamera.controls.AwbModeEnum.Cloudy})

    def set_whitebalance(self, temperature):
        awb = Picamera2.find_tuning_algo(self.cal, "rpi.awb")
        curve = {}
        lower = None
        upper = None
        for i in range(0, len(awb["ct_curve"]), 3):
            temp = awb["ct_curve"][i]
            r = awb["ct_curve"][i + 1]
            b = awb["ct_curve"][i + 2]
            if temp < temperature:
                lower = temp
            if temp > temperature and upper is None:
                upper = temp
            curve[temp] = (r, b)
        if upper is None:
            upper = temp
        if lower is None:
            lower = awb["ct_curve"][0]

        if upper == lower:
            r, b = curve[upper]
        else:
            offset = (temperature - lower) / (upper - lower)
            r = curve[lower][0] * (1.0 - offset) + curve[upper][0] * offset
            b = curve[lower][1] * (1.0 - offset) + curve[upper][1] * offset
        self.enable_auto_whitebalance(False)
        self.cam.set_controls({"ColourGains": (1.0 / r, 1.0 / b)})

    def set_autofocus(self, mode):
        if 'AfState' not in self.state:
            return

        self.ui.af.set(mode)
        if mode == "M":
            self.cam.set_controls({"AfMode": libcamera.controls.AfModeEnum.Manual})
        elif mode == "C":
            self.cam.set_controls({"AfMode": libcamera.controls.AfModeEnum.Continuous})
        elif mode == "S":
            self.cam.set_controls({"AfMode": libcamera.controls.AfModeEnum.Auto})

    def set_focus_area(self, x, y, width=64, height=64):
        if 'AfState' not in self.state:
            return
        self.ui.af_pos.set((x, y))
        sw = self.state["ScalerCrop"][2]
        sh = self.state["ScalerCrop"][3]
        x *= sw
        x += self.state["ScalerCrop"][0]
        y *= sh
        y += self.state["ScalerCrop"][1]
        width = width / 1920 * sw
        height = height / 1080 * sh
        win = [(int(x - (width / 2)), int(y - (height / 2)), int(width), int(height))]
        self.cam.set_controls({"AfWindows": win, "AfMetering": libcamera.controls.AfMeteringEnum.Windows})
        if self.ui.af.value == "S":
            self.trigger_autofocus()

    def trigger_autofocus(self):
        self.cam.autofocus_cycle(wait=False)

    def set_shutter(self, shutter):
        self.enable_auto_exposure(False)
        self.ui.shutter.set(shutter)
        et = int(1 / shutter * 1000000)
        self.cam.set_controls({"ExposureTime": et})

    def set_fps(self, fps):
        self.ui.fps.set(fps)
        self.cam.set_controls({"FrameRate": fps})
        self.out_dsi.set_fps(fps)
        self.out_hdmi.set_fps(fps)
        self.ui.min_shutter.set(fps)

    def set_tally(self, mask):
        self.ui.tally.set(mask)

    def update_preview(self, request):
        ordering = []
        toggles = {
            "zebra": self.ui.zebra.value,
            "false": self.ui.false_color.value,
            "focus": self.ui.focus_assist.value,
            "histogram": self.ui.histogram.value,
        }
        for k in self.last_update:
            self.last_update[k] += 1
            if toggles[k]:
                ordering.append((self.last_update[k], k))
        task = list(sorted(ordering, reverse=True))
        if len(task) == 0:
            return
        task = task[0][1]

        with MappedArray(request, "lores") as mapped:
            if task == 'zebra':
                grey = mapped.array[0:self.preview_h]
                _, clipping = cv2.threshold(grey, self.thresh_zebra, 255, cv2.THRESH_BINARY)
                clip_mat = cv2.merge((self.mat_zebra, self.mat_zebra, self.mat_zebra, clipping))
                self.drm.set_overlay(clip_mat, output=self.output_ui, num=self.OVERLAY_ZEBRA)
                self.last_update[task] = 0
            elif task == 'false':
                grey = mapped.array[0:self.preview_h]
                middle_grey = cv2.inRange(grey, self.config.monitor.exposure_helper_min,
                                          self.config.monitor.exposure_helper_max)
                middle_mat = cv2.merge((self.mat_black, self.mat_white, self.mat_black, middle_grey))
                self.drm.set_overlay(middle_mat, output=self.output_ui, num=self.OVERLAY_FALSE)
                self.last_update[task] = 0
            elif task == 'focus':
                if self.update_idx == 0:
                    grey = mapped.array[0:self.preview_h]
                    self.gradient = cv2.Sobel(grey, cv2.CV_32F, 1, 1, ksize=3)
                    self.update_idx = 1
                else:
                    gradient_8bit = np.uint8(self.gradient)
                    _, edges = cv2.threshold(gradient_8bit, 20, 255, cv2.THRESH_BINARY)
                    mat = cv2.merge((self.mat_white, self.mat_black, self.mat_black, edges))
                    self.drm.set_overlay(mat, output=self.output_ui, num=self.OVERLAY_FOCUS)
                    self.update_idx = 0
                    self.last_update[task] = 0
            elif task == 'histogram':
                grey = mapped.array[0:self.preview_h]
                hist = cv2.calcHist([grey], [0], None, [256], [0, 255])
                cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
                hist = np.int32(np.around(hist))
                h = np.full((100, 256, 4), dtype=np.uint8, fill_value=(0, 0, 0, 160))
                for x, y in enumerate(hist):
                    cv2.line(h, (x, 0), (x, y[0]), (255, 255, 255, 255), 1)
                y = np.flipud(h)
                self.drm.set_overlay(y, output=self.output_ui, num=self.OVERLAY_HISTOGRAM)
                self.last_update[task] = 0


if __name__ == '__main__':
    camera = Camera()
    camera.start()

    while True:
        camera.loop()
