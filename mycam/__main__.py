import math
import time

from picamera2 import Picamera2
import numpy as np

from mycam.edid import check_edid
from mycam.multipreview import MultiPreview
from PIL import Image, ImageDraw, ImageFont

cam = Picamera2()

for mode in cam.sensor_modes:
    if mode["size"][1] == 1080:
        cam_mode = mode
        break
else:
    print("No suitable mode found")
    exit(1)

cam.video_configuration = cam.create_video_configuration(raw={
    "size": cam_mode["size"],
    "format": cam_mode["format"].format,
})

preview_config = cam.create_preview_configuration({"size": (1920, 1080)}, controls={'FrameRate': 60})

cam.configure(preview_config)

drm = MultiPreview(rate=60)

cam.start_preview(drm)
cam.start()

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
font_heading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
font_value = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

state = cam.capture_metadata()
controls = {"ExposureTime": state["ExposureTime"], "AnalogueGain": state["AnalogueGain"],
            "ColourGains": state["ColourGains"]}


def draw_value(ctx, x, name, value):
    ctx.text((x, 10), name, font=font_heading, fill=(255, 255, 255, 255), stroke_fill=(0, 0, 0, 255),
             stroke_width=1)
    ctx.text((x, 24), str(value), font=font_value, fill=(255, 255, 255, 255), stroke_fill=(0, 0, 0, 255),
             stroke_width=1)

edid = check_edid()

ui = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
draw = ImageDraw.Draw(ui)
draw.rectangle((0, 0, 720, 28), fill=(0, 0, 0, 128))
draw.text((13, 10), f"Camera {edid.camera_id}", font=font, fill=(255, 255, 255, 255))
cam.set_overlay(np.array(ui))

hdmi_overlay = Image.new("RGBA", (1920, 64), (0, 0, 0, 0))

while True:
    time.sleep(0.5)

    edid = check_edid()

    time.sleep(0.5)
    draw = ImageDraw.Draw(hdmi_overlay)
    draw.rectangle((0, 0, 1920, 64), fill=(0, 0, 0, 128))

    draw_value(draw, 32, "Camera", edid.camera_id)
    state = cam.capture_metadata()
    gdb = int(10 * math.log10(state["AnalogueGain"]))
    draw_value(draw, 150, "Gain", f"{gdb} dB")

    draw_value(draw, 300, "Shutter", int(state["ExposureTime"] / float(state["FrameDuration"]) * 360))
    draw_value(draw, 450, "Whitebalance", state["ColourTemperature"])
    draw_value(draw, 600, "Focus", state["FocusFoM"])

    drm.set_overlay(np.array(hdmi_overlay), output="HDMI-A-1")

    print(state)