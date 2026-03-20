import time
import threading
import queue
import cv2
import libcamera
from PIL import Image, ImageDraw

from libcamera import ColorSpace
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder
from picamera2.outputs import PyavOutput
import numpy as np

from mncam.api import ControlAPI
from mncam.audio import audiothread
from mncam.config import Config
from mncam.drmoutput import DRMOutput
from mncam.edid import check_edid

from mncam.user_interface import UI


class Camera:
    OVERLAY_ZEBRA = 0
    OVERLAY_FALSE = 1
    OVERLAY_FOCUS = 2
    OVERLAY_UI = 3
    OVERLAY_HISTOGRAM = 4
    OVERLAY_AUDIO = 5

    def __init__(self):
        self.cam = Picamera2()
        self.state = {}
        self.edid = None
        self.preview_w = 1
        self.preview_h = 1
        self.audio_levels = queue.Queue()

        self.config = Config("/boot/camera.ini")

        self.output_hdmi = self.config.output.output
        self.output_ui = self.config.monitor.output
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

        # Configure the hardware H.264 encoder
        if self.config.encoder.enabled:
            self.encoder = H264Encoder(self.config.encoder.bitrate_int)
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

        self.ui = UI(self.ui_size[0], self.ui_size[1], self, self.config, self.cam.camera_controls)
        self.ui_hdmi = UI(1920, 64, self, self.config, self.cam.camera_controls, hdmi=True)

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
        self.out_dsi.overlay_position(self.OVERLAY_AUDIO, 64, self.config.monitor.mode[1] - 232, 256, 32)
        self.out_hdmi.overlay_opacity(0, 0.0)

        # Set initial state to keep consistency with the API
        self.cam.set_controls({"AeEnable": True, "AwbEnable": True})
        self.preview_w, self.preview_h = self.cam.stream_configuration("lores")["size"]
        self.create_mask_images()
        self.ui.start()

        self.levels = Image.new("RGBA", (256, 32), "black")


        at = threading.Thread(target=audiothread, args=(self.audio_levels,))
        at.daemon = True
        at.start()

    def create_mask_images(self):
        self.mat_black = np.zeros((self.preview_h, self.preview_w), np.uint8)
        self.mat_white = np.zeros((self.preview_h, self.preview_w), np.uint8)
        self.mat_white[:] = (255,)
        self.mat_zebra = np.zeros((self.preview_h, self.preview_w), np.uint8)
        self.mat_zebra[:] = (255,)

        for offset in range(0, self.preview_w, 10):
            cv2.line(self.mat_zebra, (offset, 0), (offset, self.preview_h), (0, 0, 0), 3)

    def loop(self):
        self.state = self.cam.capture_metadata()
        self.api.update_state(self.cam.capture_metadata())
        self.api.do_work()
        self.ui.update_state(self.cam.capture_metadata())
        self.ui_hdmi.update_state(self.cam.capture_metadata())

        self.update_levels()

        if self.debounce > 10:
            self.debounce = 0
            self.edid = check_edid()
            self.ui.camera_id.set(self.edid.camera_id)
            self.ui_hdmi.camera_id.set(self.edid.camera_id)
        self.debounce += 1
        time.sleep(0.1)

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

    def enable_focus_zoom(self, enable):
        # The default 1280x800 monitor is at 0.66x scale, with 1.5x zoom it would archieve 1:1 pixel mapping
        # so this zooms to 3x to have 2:1 pixel mapping on the default zoom level
        one_to_one = 1920 / self.out_dsi.width
        self.out_dsi.zoom = one_to_one * 2 if enable else 1.0
        self.ui.zoom.set(self.out_dsi.zoom)

    def enable_auto_exposure(self, enabled):
        self.ui.ae.set(enabled)
        self.cam.set_controls({"AeEnable": enabled})

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

    def set_autofocus(self, mode):
        self.ui.af.set(mode)
        if mode == "M":
            self.cam.set_controls({"AfMode": libcamera.controls.AfModeEnum.Manual})
        elif mode == "C":
            self.cam.set_controls({"AfMode": libcamera.controls.AfModeEnum.Continuous})
        elif mode == "S":
            self.cam.set_controls({"AfMode": libcamera.controls.AfModeEnum.Auto})

    def set_focus_area(self, x, y, width=64, height=64):
        self.ui.af_pos.set((x, y))
        sw = self.state["ScalerCrop"][2]
        sh = self.state["ScalerCrop"][3]
        x *= sw
        x += self.state["ScalerCrop"][0]
        y *= sh
        y += self.state["ScalerCrop"][1]
        width = width / 1920 * sw
        height = height / 1080 * sh
        win = [(int(x-(width/2)), int(y-(height/2)), int(width), int(height))]
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
        self.out_hdmi.set_fps(fps)
        self.ui.min_shutter.set(fps)

    def set_tally(self, mask):
        self.ui.tally.set(mask)

    def update_levels(self):
        if self.audio_levels.empty():
            return
        data = self.audio_levels.get()
        width = 256
        height = 32

        ctx = ImageDraw.Draw(self.levels)
        ctx.rectangle((0, 0, width, height), fill=(0,0,0,255))
        for i, chan in enumerate(data):
            l = chan if chan > float('-inf') else -100
            offset = int((l+100) * 2.54)
            ctx.rectangle((0, 16*i, offset, 16+16*i), fill=(255,255,255,255))
        self.drm.set_overlay(self.levels, output=self.output_ui, num=self.OVERLAY_AUDIO)

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
                h = np.full((100, 256, 4), dtype=np.uint8, fill_value=(0,0,0,160))
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
