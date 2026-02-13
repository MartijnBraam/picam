import math
import time
import cv2

import libcamera
from libcamera import ColorSpace
from picamera2 import Picamera2, Preview, MappedArray
from picamera2.encoders import H264Encoder
from picamera2.outputs import PyavOutput
import numpy as np

from mycam.api import ControlAPI
from mycam.config import Config
from mycam.drmoutput import DRMOutput
from mycam.edid import check_edid
from PIL import Image, ImageDraw, ImageFont

from mycam.user_interface import UI


class Camera:
    OVERLAY_ZEBRA = 0
    OVERLAY_FALSE = 1
    OVERLAY_FOCUS = 2
    OVERLAY_UI = 3

    def __init__(self):
        self.cam = Picamera2()
        self.state = {}
        self.edid = None
        self.preview_w = 1
        self.preview_h = 1

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
                'FrameRate': 30,
                "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Fast,
                "Sharpness": 0,
                "Saturation": 1,
                "HdrMode": 3,
            }, colour_space=ColorSpace.Rec709())
        self.cam.configure(preview_config)

        # Enable DRM output of the camera stream to the HDMI output and the DSI display
        self.drm = DRMOutput(self.config.output.mode[0], self.config.output.mode[1])
        self.out_hdmi = self.drm.use_output(self.output_hdmi, self.config.output.mode[0], self.config.output.mode[1],
                                            60, 1)
        self.out_dsi = self.drm.use_output(self.output_ui, self.ui_size[0], self.ui_size[1], None, 4)

        # Configure the hardware H.264 encoder
        self.encoder = H264Encoder(self.config.encoder.bitrate_int)
        self.stream = PyavOutput("rtsp://127.0.0.1:8554/cam", format="rtsp")
        self.encoder.output = self.stream

        def preview(request):
            self.update_preview(request)

        self.cam.pre_callback = preview

        # Load fonts for overlays
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
        self.font_heading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        self.font_value = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

        # Image buffers for overlay drawing
        self.hdmi_overlay = Image.new("RGBA", (self.config.output.mode[0], 64), (0, 0, 0, 0))

        self.api = ControlAPI(self)

        self.mat_black = None
        self.mat_white = None
        self.mat_zebra = None
        self.update_idx = 0

        self.thresh_zebra = 230
        self.thresh_under = 18

        self.ui = UI(self.ui_size[0], self.ui_size[1], self, self.config)

        def on_paint(buf):
            self.drm.set_overlay(buf, output=self.output_ui, num=self.OVERLAY_UI)

        self.ui.paint_hook = on_paint
        self.debounce = 0
        self.last_update = {
            "zebra": 0,
            "false": 0,
            "focus": 0,
        }

    def start(self):
        self.cam.start_preview(self.drm)
        self.cam.start()
        self.cam.start_encoder(self.encoder)

        self.out_hdmi.overlay_position(0, 0, 0, self.config.output.mode[0], 64)

        # Set initial state to keep consistency with the API
        self.cam.set_controls({"AeEnable": True, "AwbEnable": True})
        self.preview_w, self.preview_h = self.cam.stream_configuration("lores")["size"]
        self.create_mask_images()
        self.ui.start()

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
        if self.debounce > 10:
            self.debounce = 0
            self.edid = check_edid()
            self.ui.camera_id.set(self.edid.camera_id)
        self.debounce += 1
        time.sleep(0.1)

    def set_controls(self, **kwargs):
        self.cam.set_controls(kwargs)

    def draw_hdmi_overlay(self):
        draw = ImageDraw.Draw(self.hdmi_overlay)
        draw.rectangle((0, 0, 1920, 64), fill=(0, 0, 0, 128))

        self.draw_value(draw, 32, "Camera", self.edid.camera_id)
        gdb = int(10 * math.log10(self.state["AnalogueGain"]))
        self.draw_value(draw, 150, "Gain", f"{gdb} dB")

        self.draw_value(draw, 300, "Shutter",
                        int(self.state["ExposureTime"] / float(self.state["FrameDuration"]) * 360))
        self.draw_value(draw, 450, "Whitebalance", f'{self.state["ColourTemperature"]}k')
        self.draw_value(draw, 600, "Focus", self.state["FocusFoM"])

        self.drm.set_overlay(np.array(self.hdmi_overlay), output=self.output_hdmi)

    def draw_value(self, ctx, x, name, value):
        ctx.text((x, 10), name, font=self.font_heading, fill=(255, 255, 255, 255), stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)
        ctx.text((x, 24), str(value), font=self.font_value, fill=(255, 255, 255, 255), stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)

    def enable_zebra(self, enable):
        self.ui.zebra.set(enable)
        self.out_dsi.overlay_opacity(self.OVERLAY_ZEBRA, 1.0 if enable else 0.0)

    def update_preview(self, request):
        ordering = []
        toggles = {
            "zebra": self.ui.zebra.value,
            "false": self.ui.false_color.value,
            "focus": self.ui.focus_assist.value,
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


if __name__ == '__main__':
    camera = Camera()
    camera.start()

    while True:
        camera.loop()
