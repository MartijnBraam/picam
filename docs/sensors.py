"""
This file generates the HTML for the sensor comparison table in my blog post
"""
import math


class Sensor:
    def __init__(self, name, sensor, size, hactive, vactive, pixelsize, binning):
        self.name = name
        self.sensor = sensor
        self.size = size
        self.hactive = hactive
        self.vactive = vactive
        self.pixelsize = pixelsize
        self.binning = binning


sensors = [
    Sensor("HQ Camera", "imx477", '1/2.3"', 4072, 3064, 1.55, 2),
    Sensor("Pi Camera 3", "imx708", '1/2.43"', 4608, 2592, 1.4, 2),
    Sensor("Pi Camera 2", "imx219", '1/4"', 3280, 2464, 1.12, 1),
    None,
    Sensor("OneInchEye", "imx283", '1"', 5496, 3672, 2.4, 2),
    Sensor("StarlightEye", "imx585", '1/1.2"', 3840, 2160, 2.9, 2),
    Sensor("FourThirdsEye", "imx294", '4/3"', 4168, 2824, 4.63, 2),
]


def diag(w, h):
    return math.sqrt(w ** 2 + h ** 2)


print("<table>")
print("\t<tr>")
print("\t\t<th>Sensor</th>")
print("\t\t<th>Size</th>")
print("\t\t<th>Diagonal (at 16:9 crop)</th>")
print("\t\t<th>Active size</th>")
print("\t\t<th>Crop (at 1080p)</th>")
print("\t</tr>")

ffdiag = diag(36, 36 / 16 * 9)
for sensor in sensors:
    if sensor is None:
        print("\t<tr><td colspan=5></td></tr>")
        continue

    width = sensor.hactive * sensor.pixelsize / 1000
    hcrop = sensor.hactive / 16 * 9 * sensor.pixelsize / 1000
    height = sensor.vactive * sensor.pixelsize / 1000

    d = diag(width, height)
    dcrop = diag(width, hcrop)

    cropres = 1920 * sensor.binning
    cropwidth = cropres * sensor.pixelsize / 1000
    cropheight = cropwidth / 16 * 9
    # Calculating the crop factor based on 16:9 sensor use (to get a consistent horizontal fov)
    crop = ffdiag / dcrop
    crop1080 = ffdiag / diag(cropwidth, cropheight)

    print("\t<tr>")
    print(f"\t\t<td>{sensor.name} ({sensor.sensor})</td>")
    print(f"\t\t<td>{sensor.size}</td>")
    # Diagonal (at 16:9 crop)
    print(f"\t\t<td>{d:.2f}mm ({dcrop:.2f}mm)</td>")
    # Active size
    print(f"\t\t<td>{width:.1f} x {hcrop:.1f}</td>")
    # Crop (at 1080p)
    print(f"\t\t<td>{crop:.1f}x ({crop1080:.1f}x)</td>")
    print("\t</tr>")

print("</table>")
