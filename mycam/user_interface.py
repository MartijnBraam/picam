import datetime
import math
import queue

from mycam.toolkit import StateNumber, Layout, GuidesButton, HandleInputs, TapEvent, DoubleTapEvent, VBox, Slider, \
    ToggleRow


class UI:
    def __init__(self, width, height, camera, config, limits):
        self.width = width
        self.height = height
        self.cam = camera
        self.config = config

        self.screens = {}
        self.create_screen("main")
        self.active_screen = "main"
        self.paint_hook = None
        self.state = None

        # Fixed info
        ctrl_min, ctrl_max, ctrl_default = limits["AnalogueGain"]
        self.max_gain = ctrl_max
        ctrl_min, ctrl_max, ctrl_default = limits["ExposureTime"]
        self.min_shutter = ctrl_min
        self.max_shutter = ctrl_max
        ctrl_min, ctrl_max, ctrl_default = limits["ExposureValue"]
        self.min_ec = ctrl_min
        self.max_ec = ctrl_max

        # Camera state
        self.fps = StateNumber(self.config.sensor.framerate)
        self.shutter = StateNumber()
        self.gain = StateNumber()
        self.tc = StateNumber()
        self.camera_id = StateNumber()
        self.ae = StateNumber(True)
        self.ec = StateNumber(0.0)

        # Preview state
        self.zebra = StateNumber(False)
        self.focus_assist = StateNumber(False)
        self.false_color = StateNumber(False)
        self.guides = StateNumber("thirds")
        self.zoom = StateNumber(1.0)

        # UI state
        self.tab_state = StateNumber("")

        self.input_queue = queue.Queue()
        self._create_main_layout()

    def start(self):
        HandleInputs(self.input_queue, self.config)

    def _create_main_layout(self):
        l: Layout = self.screens["main"]

        l.add_label(Layout.TOPLEFT, 120, "Auto Exposure", "{0:.1f} EV", self.ec, align="left", name="ae",
                    handler=lambda v: self.tab_state.toggle("ae"),
                    button_state=self.tab_state, state_cmp=lambda s: s == "ae")

        l.add_label(Layout.TOPLEFT, 80, "FPS", "{}", self.fps, align="left",
                    handler=lambda v: self.tab_state.toggle("fps"),
                    button_state=self.tab_state, state_cmp=lambda s: s == "fps")
        l.add_label(Layout.TOPLEFT, 100, "Shutter", "1/{}", self.shutter, align="left", name="shutter",
                    handler=lambda v: self.tab_state.toggle("shutter"),
                    button_state=self.tab_state, state_cmp=lambda s: s == "shutter")
        l.add_label(Layout.TOPLEFT, 100, "Gain", "{} dB", self.gain, align="left", name="gain",
                    handler=lambda v: self.tab_state.toggle("gain"),
                    button_state=self.tab_state, state_cmp=lambda s: s == "gain")
        l.add_label(Layout.TOPMIDDLE, 200, "Timecode", "{}", self.tc, None, "middle")
        l.add_label(Layout.TOPRIGHT, 100, "Camera ID", "{}", self.camera_id, None, "left")

        l.add_button(Layout.BOTTOMLEFT, 130, "Zebra", self.zebra, lambda v: self.cam.enable_zebra(v))
        l.add_button(Layout.BOTTOMLEFT, 130, "Focus", self.focus_assist, lambda v: self.cam.enable_focus_assist(v))
        l.add_button(Layout.BOTTOMLEFT, 130, "Exp.", self.false_color, lambda v: self.cam.enable_false_color(v))
        l.add_widget(Layout.BOTTOMLEFT, GuidesButton(130, "Guides", self.guides, lambda v: self.cycle_guides()))

        l.page_state = self.tab_state
        # Empty panel which shows the guides when needed
        l.add_widget(Layout.MIDDLE, VBox(name=""))

        # Shutter control panel
        shutter_panel = VBox(name="shutter")
        shutter_panel.add(Slider("Shutter", self.shutter, None, background=(0, 0, 0, 80)))
        shutter_panel.compute()
        l.add_widget(Layout.MIDDLE, shutter_panel)

        # Gain control panel
        gain_panel = VBox(name="gain")
        gain_panel.add(Slider("Gain", self.gain, min=1.0, max=self.max_gain, handler=lambda v: self.cam.set_gain(v),
                              background=(0, 0, 0, 80)))
        gain_panel.compute()
        l.add_widget(Layout.MIDDLE, gain_panel)

        # Auto exposure controls panel
        ae_panel = VBox(name="ae")
        ae_panel.add(
            Slider("AE Comp", self.ec, min=self.min_ec, max=self.max_ec, handler=lambda v: self.cam.set_ev(v),
                   background=(0, 0, 0, 80)))
        ae_panel.add(ToggleRow("Auto Exposure", self.ae, handler=lambda v: self.cam.enable_auto_exposure(v),
                               background=(0, 0, 0, 80)))
        ae_panel.compute()
        l.add_widget(Layout.MIDDLE, ae_panel)

        l.on_double_tap_empty = lambda: self.cam.enable_focus_zoom(self.zoom.value == 1.0)

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
            if isinstance(event, TapEvent):
                self.screens[self.active_screen].tap(event.x, event.y)
            elif isinstance(event, DoubleTapEvent):
                self.screens[self.active_screen].doubletap(event.x, event.y)

        tc = datetime.datetime.fromtimestamp(self.state["SensorTimestamp"] / 1000000000, tz=datetime.timezone.utc)
        self.tc.set(tc.strftime("%H:%M:%S"))
        self.shutter.set(int(1000000 / state["ExposureTime"]))
        self.gain.set(int(round(10 * math.log10(state["AnalogueGain"]))))

        if self.ae.once("update_state"):
            self.screens["main"]["gain"].color_text = (128, 128, 128, 255) if self.ae.value else (255, 255, 255, 255)
            self.screens["main"]["shutter"].color_text = (128, 128, 128, 255) if self.ae.value else (255, 255, 255, 255)
            self.screens["main"]["ae"].color_text = (128, 128, 128, 255) if not self.ae.value else (255, 255, 255, 255)

        buf = self.screens[self.active_screen].render()
        if buf is not None:
            self.paint_hook(buf)
