import subprocess
import time
from math import atan2

from picamera2 import Picamera2, MappedArray, Preview
import libcamera
import cv2
import numpy as np

from colour_checker_detection import detect_colour_checkers_segmentation

_checker = None
_lux = 0


def get_reference():
    global _lux
    p = subprocess.run(["spotread", "-a", "-O"], capture_output=True)
    raw = p.stdout.decode()
    for line in raw.splitlines():
        line = line.strip()

        print(repr(line))

        if line.startswith("Ambient "):
            part = line.split(" Lux")[0]
            part = part.split("=")[1]
            _lux = float(part.strip())

        if line.startswith("Closest Daylight temperature"):
            part = line.split("=")
            part = part[1].split()
            temp = part[0].replace("K", "")

            print(f"Reference light: {temp}K {_lux} Lux")

            return int(temp)
    raise RuntimeError("Could not get colorimeter reading")


def rotational_sort(list_of_xy_coords):
    cx, cy = list_of_xy_coords.mean(0)
    angles = [atan2(x - cx, y - cy) for x, y in list_of_xy_coords]
    indices = sorted(range(len(angles)), key=angles.__getitem__)
    return [list_of_xy_coords[i] for i in indices]


def middle(a, b):
    x = mean(a[0], b[0])
    y = mean(a[1], b[1])
    return int(x), int(y)


def mean(*nums):
    return sum(list(nums)) / len(list(nums))


def pax(a, b, pos):
    lowest = min(a, b)
    highest = max(a, b)
    distance = highest - lowest
    return lowest + (distance * pos)


def pal(a, b, pos):
    return int(pax(a[0], b[0], pos)), int(pax(a[1], b[1], pos))


def point_in_rect(rect, point):
    tl = rect[0]
    bl = rect[1]
    br = rect[2]
    tr = rect[3]

    x1, y1 = pal(tl, tr, point[0])
    x2, y2 = pal(bl, br, point[0])
    x3, y3 = pal(tl, bl, point[1])
    x4, y4 = pal(tr, br, point[1])

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / (
            (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / (
            (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    return int(px), int(py)


def get_mean_color(frame, point, size):
    hs = int(size / 2)
    m = np.mean(frame[point[1] - hs:point[1] + hs, point[0] - hs:point[0] + hs], axis=(0, 1))
    return m


def draw_overlay(request):
    if _checker is None:
        return

    with MappedArray(request, "main") as m:
        transformed = np.int32(_checker)
        cv2.polylines(m.array, [transformed], True, (255, 255, 255), 2)

        cv2.circle(m.array, point_in_rect(transformed, (1 / 12, 1 / 8)), 50, (0, 0, 255), 5)
        cv2.circle(m.array, point_in_rect(transformed, (1 - 1 / 12, 1 / 8)), 50, (0, 0, 255), 5)
        cv2.circle(m.array, point_in_rect(transformed, (1 / 12, 1 - 1 / 8)), 50, (0, 0, 255), 5)
        cv2.circle(m.array, point_in_rect(transformed, (1 - 1 / 12, 1 - 1 / 8)), 50, (0, 0, 255), 5)

        cv2.rectangle(m.array, (10, 10), (50, 100), (0, 255 if _gain_ok else 0, 0 if _gain_ok else 255), 4)


def find_color_checker(frame):
    result = detect_colour_checkers_segmentation(frame,
                                                 additional_data=True,
                                                 swatches_count_minimum=24,
                                                 swatches_count_maximum=24,
                                                 swatches_horizontal=6,
                                                 swatches_vertical=4,
                                                 swatches_chromatic_slice=slice(0 + 1, 0 + 6 - 1, 1),
                                                 swatches_achromatic_slice=slice(18 + 1, 18 + 6 - 1, 1),
                                                 )
    if len(result) == 0:
        return None
    corners = rotational_sort(result[0].quadrilateral)
    transformed = []
    for point in corners:
        transformed.append([int(point[0] / 1440 * 1920), int(point[1] / 1440 * 1920)])

    return transformed


cam = Picamera2()
preview_config = cam.create_preview_configuration(main={
    "size": (1920, 1080),
    "format": "RGB888",
},
    controls={
        'FrameRate': 30,
        "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Off,
    })
cam.configure(preview_config)
cam.post_callback = draw_overlay

cam.start_preview(Preview.DRM, x=0, y=0, width=1024, height=600)
cam.start()

# Let AE and AWB run for a bit
time.sleep(2)

# Get ambient light measurement
_ref = get_reference()

# Switch to manual
meta = cam.capture_metadata()
_gain = meta["AnalogueGain"]
_wb = list(meta["ColourGains"])
cam.set_controls({"AeEnable": False, "AwbEnable": False, "AnalogueGain": _gain, "ColourGains": _wb})

_visible = False
_gain_ok = False
_wb_ok = False

# First find the color checker in frame
while True:
    with cam.captured_request() as request:
        frame = request.make_array('main')
        _checker = find_color_checker(frame)
        if _checker is not None:
            break

# Find the white swatch for orientation
with cam.captured_request() as request:
    frame = request.make_array('main')

    bottom_left = point_in_rect(_checker, (1 / 12, 1 - 1 / 8))
    top_right = point_in_rect(_checker, (1 - 1 / 12, 1 / 8))

    col_bl = get_mean_color(frame, bottom_left, 30)
    col_tr = get_mean_color(frame, top_right, 30)

    if mean(*col_bl) > mean(*col_tr):
        white_patch = bottom_left
        neutral_patch = point_in_rect(_checker, (1 / 12 * 5, 1 - 1 / 8))
    else:
        white_patch = top_right
        neutral_patch = point_in_rect(_checker, (1 - 1 / 12 * 5, 1 / 8))

# Expose for the white patch
while True:
    with cam.captured_request() as request:
        frame = request.make_array('main')
        white = get_mean_color(frame, white_patch, 30)
        if white[0] > 254 or white[1] > 254 or white[2] > 254:
            _gain -= 0.1
            cam.set_controls({"AeEnable": False, "AwbEnable": False, "AnalogueGain": _gain, "ColourGains": tuple(_wb)})
            time.sleep(0.4)
        else:
            break

# Tune white balance on neutral patch
while True:
    with cam.captured_request() as request:
        frame = request.make_array('main')
        neutral = get_mean_color(frame, neutral_patch, 30)
        print(neutral)
        target = neutral[1]
        red_offset = neutral[2] - target
        blue_offset = neutral[0] - target
        change = False
        if abs(red_offset) > 1:
            _wb[0] -= red_offset / 1000
            change = True
        if abs(blue_offset) > 1:
            _wb[1] -= blue_offset / 1000
            change = True
        if change:
            cam.set_controls({"AeEnable": False, "AwbEnable": False, "AnalogueGain": _gain, "ColourGains": _wb})
            time.sleep(0.4)
        else:
            break

print("Calibration complete")
sensor_model = cam.camera_properties["Model"]
print(f"Sensor: {sensor_model}")
print(f"Temperature: {_ref}K")
print(f"Light level: {_lux} Lux")
print(f"Gains: {_wb}")

print("Result:")
print(f"{_ref:0.1f}, {1/_wb[0]:0.4f}, {1/_wb[1]:0.4f}")

cap = cam.switch_mode_capture_request_and_stop(preview_config)
fname = f"{sensor_model}_{_ref}k.dng"
cap.save_dng(fname)
print(f"Saved frame to {fname}")
