import os.path
import configparser

import humanfriendly


class MonitorConfig:
    def __init__(self):
        self.output = "HDMI-A-2"
        self.mode = (1280, 720)
        self.touchscreen_rotate = 0
        self.touchscreen_flip_x = False
        self.touchscreen_flip_y = False
        self.touchscreen_res = (1280, 720)
        self.exposure_helper_min = 61
        self.exposure_helper_max = 70


class OutputConfig:
    def __init__(self):
        self.output = "HDMI-A-1"
        self.mode = (1920, 1080)
        self.framerate = 60


class EncoderConfig:
    def __init__(self):
        self.bitrate = "10M"
        self.enabled = True

    @property
    def bitrate_int(self):
        return humanfriendly.parse_size(self.bitrate)


class SensorConfig:
    def __init__(self):
        self.framerate = 30


class Config:
    def __init__(self, path):
        self._path = path

        self.monitor = MonitorConfig()
        self.output = OutputConfig()
        self.encoder = EncoderConfig()
        self.sensor = SensorConfig()

        self.load_defaults()
        if os.path.isfile(path):
            self.load_config()
        self.save_config()

    def load_defaults(self):
        if self._has_dsi():
            self.monitor.output = "DSI-1"
        else:
            self.monitor.output = "HDMI-A-2"

    def load_config(self):
        parser = configparser.ConfigParser()
        parser.read(self._path)

        for section in parser.sections():
            if hasattr(self, section):
                ob = getattr(self, section)
                for key in parser[section]:
                    attr = key.replace("-", "_")
                    if hasattr(ob, attr):
                        cur = getattr(ob, attr)
                        new = parser[section][key]
                        if isinstance(cur, str):
                            pass
                        elif isinstance(cur, bool):
                            new = new == "True" or new == "true" or new == "yes"
                        elif isinstance(cur, int):
                            new = int(new)
                        elif isinstance(cur, float):
                            new = float(new)
                        elif isinstance(cur, tuple):
                            if len(cur) == 2:
                                res = new.split("x")
                                new = (int(res[0]), int(res[1]))
                            else:
                                new = tuple(int(new[i:i + 2], 16) for i in (0, 2, 4))
                        setattr(ob, attr, new)

        if self.encoder.enabled:
            # The framerate cannot be above 30 when the hardware video encoder is used
            self.sensor.framerate = min(30, self.sensor.framerate)

    def save_config(self):
        sections = ["sensor", "output", "monitor", "encoder"]
        parser = configparser.ConfigParser()
        for section in sections:
            parser.add_section(section)
            ob = getattr(self, section)
            data = ob.__dict__
            for key in data:
                attr = key.replace("_", "-")
                val = data[key]
                if isinstance(val, tuple):
                    if len(val) == 2:
                        val = f"{val[0]}x{val[1]}"
                    elif len(val) == 3:
                        val = "#{0:02x}{1:02x}{2:02x}".format(*val)
                parser.set(section, attr, str(val))
        with open(self._path, "w") as handle:
            parser.write(handle)

    def _has_dsi(self):
        if not os.path.isdir("/sys/class/drm/card1-DSI-1"):
            return False

        with open("/sys/class/drm/card1-DSI-1/status", "r") as handle:
            raw = handle.read()

        return "connected" in raw
