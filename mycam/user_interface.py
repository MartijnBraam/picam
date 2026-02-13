import datetime
import math
import queue

from mycam.toolkit import StateNumber, Layout, GuidesButton, HandleInputs


class UI:
    def __init__(self, width, height, camera, config):
        self.width = width
        self.height = height
        self.cam = camera
        self.config = config

        self.screens = {}
        self.create_screen("main")
        self.active_screen = "main"
        self.paint_hook = None
        self.state = None

        self.fps = StateNumber(30)
        self.shutter = StateNumber()
        self.gain = StateNumber()
        self.tc = StateNumber()
        self.camera_id = StateNumber()

        self.zebra = StateNumber(False)
        self.focus_assist = StateNumber(False)
        self.false_color = StateNumber(False)
        self.guides = StateNumber("thirds")

        self.input_queue = queue.Queue()
        self._create_main_layout()

    def start(self):
        HandleInputs(self.input_queue, self.config)

    def _create_main_layout(self):
        l: Layout = self.screens["main"]

        l.add_label(Layout.TOPLEFT, 80, "FPS", "{}", self.fps, None, "left")
        l.add_label(Layout.TOPLEFT, 100, "Shutter", "1/{}", self.shutter, None, "left")
        l.add_label(Layout.TOPLEFT, 100, "Gain", "{} dB", self.gain, None, "left")
        l.add_label(Layout.TOPMIDDLE, 200, "Timecode", "{}", self.tc, None, "middle")
        l.add_label(Layout.TOPRIGHT, 100, "Camera ID", "{}", self.camera_id, None, "left")

        l.add_button(Layout.BOTTOMLEFT, 130, "Zebra", self.zebra, lambda v: self.cam.enable_zebra(v))
        l.add_button(Layout.BOTTOMLEFT, 130, "Focus", self.focus_assist, lambda v: self.cam.enable_focus_assist(v))
        l.add_button(Layout.BOTTOMLEFT, 130, "Exp.", self.false_color, lambda v: self.cam.enable_false_color(v))
        l.add_widget(Layout.BOTTOMLEFT, GuidesButton(130, "Guides", self.guides, lambda v: self.cycle_guides()))

        l.compute()

    def cycle_guides(self):
        if self.guides.value == "thirds":
            self.guides.set(False)
        elif not self.guides.value:
            self.guides.set("thirds")

    def create_screen(self, name):
        self.screens[name] = Layout(self.width, self.height)

    def update_state(self, state):
        self.state = state

        while not self.input_queue.empty():
            event = self.input_queue.get()
            self.screens[self.active_screen].tap(event.x, event.y)

        tc = datetime.datetime.fromtimestamp(self.state["SensorTimestamp"] / 1000000000, tz=datetime.timezone.utc)
        self.tc.set(tc.strftime("%H:%M:%S"))
        self.shutter.set(int(1000000 / state["ExposureTime"]))
        self.gain.set(int(round(10 * math.log10(state["AnalogueGain"]))))

        buf = self.screens[self.active_screen].render()
        if buf is not None:
            self.paint_hook(buf)
