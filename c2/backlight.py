import glob
import os


def find_backlight(config):
    for path in glob.glob("/sys/class/backlight/*"):
        np = os.path.join(path, "display_name")
        if not os.path.isfile(np):
            continue
        with open(np, "r") as h:
            name = h.read().strip()

        if name == config.monitor.output:
            return path


def get_backlight_int(backlight, key):
    with open(os.path.join(backlight, key), "r") as h:
        return int(h.read().strip())


def set_backlight(backlight, value):
    with open(os.path.join(backlight, "brightness"), "w") as h:
        h.write(str(int(value)) + "\n")
