import datetime
import math
import os.path
import queue
import socket

from mncam.backlight import find_backlight, get_backlight_int, set_backlight
from mncam.toolkit import StateNumber, Layout, GuidesButton, HandleInputs, TapEvent, DoubleTapEvent, VBox, Slider, \
    ToggleRow, Guides, RadioRow, MoveEvent, ReleaseEvent, TextRow


class UI:
    def __init__(self, width, height, camera, config, limits, hdmi=False):
        self.width = width
        self.height = height
        self.cam = camera
        self.config = config
        self.hdmi = hdmi

        self.screens = {}
        self.create_screen("main", (0, 0, 0, 0))
        self.create_screen("settings", (34, 43, 55, 255))
        self.active_screen = "main"
        self.paint_hook = None
        self.state = None
        self.overlay_state = {}
        self.settings_tab = StateNumber("system")

        # Fixed info
        self.min_shutter = StateNumber(self.config.sensor.framerate)
        self.max_shutter = StateNumber(self.config.sensor.framerate * 10)

        ctrl_min, ctrl_max, ctrl_default = limits["AnalogueGain"]
        self.max_gain = StateNumber(ctrl_max)
        ctrl_min, ctrl_max, ctrl_default = limits["ExposureValue"]
        self.min_ec = StateNumber(ctrl_min)
        self.max_ec = StateNumber(ctrl_max)
        self.has_af = StateNumber("LensPosition" in limits)
        if self.has_af.value:
            ctrl_min, ctrl_max, ctrl_default = limits["LensPosition"]
            self.min_focus = StateNumber(ctrl_min)
            self.max_focus = StateNumber(ctrl_max)
        ctrl_min, ctrl_max, ctrl_default = limits["ColourTemperature"]
        self.min_temp = StateNumber(ctrl_min)
        self.max_temp = StateNumber(ctrl_max)

        # Camera state
        self.fps = StateNumber(self.config.sensor.framerate)
        self.shutter = StateNumber()
        self.gain = StateNumber()
        self.temperature = StateNumber()
        self.tc = StateNumber()
        self.camera_id = StateNumber()
        self.ae = StateNumber(True)
        self.awb = StateNumber(True)
        self.awbmode = StateNumber("auto")
        self.ec = StateNumber(0.0)
        self.af = StateNumber("C")
        self.af_pos = StateNumber((0.5, 0.5))
        self.focus = StateNumber(0.0)
        self.tally = StateNumber(0)
        self.ip = StateNumber("N/A")

        # Preview state
        self.zebra = StateNumber(False)
        self.histogram = StateNumber(False)
        self.focus_assist = StateNumber(False)
        self.false_color = StateNumber(False)
        self.guides = StateNumber("thirds")
        self.zoom = StateNumber(1.0)

        # Audio state
        self.audio_gain_left = StateNumber(self.config.audio.left_gain)
        self.audio_gain_right = StateNumber(self.config.audio.right_gain)
        self.audio_gain_min = StateNumber(self.cam.audio.get_min_gain())
        self.audio_gain_max = StateNumber(self.cam.audio.get_max_gain())
        self.audio_mux_left = StateNumber("XLR1 [DIFF]")
        self.audio_mux_right = StateNumber("XLR2 [DIFF]")

        # HDMI overlay state
        self.hdmi_overlay = StateNumber(False)

        # Recording mode controls
        self.recording = StateNumber(False)
        self.recording_time = StateNumber(0)

        # UI state
        self.tab_state = StateNumber("")

        # Settings
        bl = find_backlight(config)
        if bl is not None:
            self.backlight = StateNumber(get_backlight_int(bl, "brightness"))
            self.min_backlight = StateNumber(1)
            self.max_backlight = StateNumber(get_backlight_int(bl, "max_brightness"))
            if self.backlight.value == 0:
                # Make sure the backlight is never fully off
                set_backlight(bl, 1)
                self.backlight.set(1)
            if config.monitor.backlight <= self.max_backlight.value:
                set_backlight(bl, config.monitor.backlight)
                self.backlight.set(config.monitor.backlight)
            self.bl = bl
        else:
            self.bl = None
            self.backlight = StateNumber(0)
            self.min_backlight = StateNumber(0)
            self.max_backlight = StateNumber(0)

        self.input_queue = queue.Queue()
        if self.hdmi:
            self._create_hdmi_layout()
        else:
            self._create_main_layout()
            self._create_settings_layout()

    def start(self):
        if self.hdmi:
            return
        HandleInputs(self.input_queue, self.config)
        self.ip.set(self.get_ip())

    def _create_hdmi_layout(self):
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

        l.compute()

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

        l.add_label(Layout.TOPMIDDLE, 130, "Timecode", "{}", self.tc, None, "middle", name="tc")

        if self.has_af.value:
            l.add_label(Layout.TOPRIGHT, 80, "Focus", "{}", self.af, align="left",
                        handler=lambda v: self.tab_state.toggle("focus"),
                        button_state=self.tab_state, state_cmp=lambda s: s == "focus")

        l.add_label(Layout.TOPRIGHT, 100, "Balance", "{}k", self.temperature, align="left", name="wb",
                    handler=lambda v: self.tab_state.toggle("wb"),
                    button_state=self.tab_state, state_cmp=lambda s: s == "wb")

        l.add_label(Layout.TOPRIGHT, 100, "Camera ID", "{}", self.camera_id, None, "left")
        l.add_button(Layout.TOPRIGHT, 64, "\uf013", StateNumber(False),
                     lambda v: self.open_settings(True))

        l.add_button(Layout.BOTTOMLEFT, 130, "Zebra", self.zebra, lambda v: self.cam.enable_zebra(v))
        l.add_button(Layout.BOTTOMLEFT, 130, "Hist.", self.histogram, lambda v: self.cam.enable_histogram(v))
        l.add_button(Layout.BOTTOMLEFT, 130, "Focus", self.focus_assist, lambda v: self.cam.enable_focus_assist(v))
        l.add_button(Layout.BOTTOMLEFT, 130, "Exp.", self.false_color, lambda v: self.cam.enable_false_color(v))
        l.add_widget(Layout.BOTTOMLEFT, GuidesButton(130, "Guides", self.guides, lambda v: self.cycle_guides()))

        if self.config.monitor.controls == "live":
            l.add_button(Layout.BOTTOMRIGHT, 180, "HDMI overlay", self.hdmi_overlay,
                         lambda v: self.cam.enable_hdmi_overlay(v))
        else:
            l.add_button(Layout.BOTTOMRIGHT, 180, "Record", self.recording,
                         lambda v: self.cam.enable_recording(v))

        l.page_state = self.tab_state
        # Empty panel which shows the guides when needed
        empty = VBox(name="")
        empty.add(Guides(self.guides, self.af, self.af_pos, handler=lambda x, y: self.cam.set_focus_area(x, y)))
        l.add_widget(Layout.MIDDLE, empty)
        empty.compute()

        # Shutter control panel
        shutter_panel = VBox(name="shutter")
        shutter_panel.add(
            Slider("Shutter", self.shutter, handler=lambda v: self.cam.set_shutter(v), min=self.min_shutter,
                   max=self.max_shutter, background=(0, 0, 0, 80)))
        shutter_panel.compute()
        l.add_widget(Layout.MIDDLE, shutter_panel)

        # Gain control panel
        gain_panel = VBox(name="gain")
        gain_panel.add(
            Slider("Gain", self.gain, min=StateNumber(1.0), max=self.max_gain, handler=lambda v: self.cam.set_gain(v),
                   background=(0, 0, 0, 80)))
        gain_panel.compute()
        l.add_widget(Layout.MIDDLE, gain_panel)

        # FPS control panel
        fps_panel = VBox(name="fps")
        fps_panel.add(RadioRow("Framerate", self.fps, options={
            24: "24",
            25: "25",
            30: "30",
            60: "60",
        }, handler=lambda v: self.cam.set_fps(v),
                               background=(0, 0, 0, 80)))
        fps_panel.compute()
        l.add_widget(Layout.MIDDLE, fps_panel)

        # Auto exposure controls panel
        ae_panel = VBox(name="ae")
        ae_panel.add(
            Slider("AE Comp", self.ec, min=self.min_ec, max=self.max_ec, handler=lambda v: self.cam.set_ev(v),
                   background=(0, 0, 0, 80)))
        ae_panel.add(ToggleRow("Auto Exposure", self.ae, handler=lambda v: self.cam.enable_auto_exposure(v),
                               background=(0, 0, 0, 80)))
        ae_panel.compute()
        l.add_widget(Layout.MIDDLE, ae_panel)

        # Whitebalance control panel
        wb_panel = VBox(name="wb")
        wb_panel.add(
            Slider("Temperature", self.temperature, min=self.min_temp, max=self.max_temp,
                   handler=lambda v: self.cam.set_whitebalance(v),
                   background=(0, 0, 0, 80)))
        wb_panel.add(ToggleRow("Auto Whitebalance", self.awb, handler=lambda v: self.cam.enable_auto_whitebalance(v),
                               background=(0, 0, 0, 80)))
        wb_panel.add(RadioRow("Mode", self.awbmode, options={
            "auto": "Auto",
            "tungsten": "Tungsten",
            "fluorescent": "Fluorescent",
            "indoor": "Indoor",
            "daylight": "Daylight",
            "cloudy": "Cloudy",
        }, handler=lambda v: self.cam.set_awb_mode(v),
                              background=(0, 0, 0, 80)))

        wb_panel.compute()
        l.add_widget(Layout.MIDDLE, wb_panel)

        # Focus control panel
        if self.has_af.value:
            focus_panel = VBox(name="focus")
            focus_panel.add(
                Slider("Distance", self.focus, min=self.min_focus, max=self.max_focus,
                       handler=lambda v: self.cam.set_focus(v),
                       background=(0, 0, 0, 80)))
            focus_panel.add(RadioRow("Mode", self.af, options={
                "M": "Manual",
                "S": "Single",
                "C": "Continuous",
            }, handler=lambda v: self.cam.set_autofocus(v),
                                     background=(0, 0, 0, 80)))

            focus_panel.compute()
            l.add_widget(Layout.MIDDLE, focus_panel)

        l.on_double_tap_empty = lambda: self.cam.enable_focus_zoom(self.zoom.value == 1.0)

        l.compute()

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except:
            print("Could not get default IP")
            return "0.0.0.0"
        return str(ip)

    def get_sensor(self):
        props = self.cam.cam.camera_properties
        sensor = props["Model"]
        if sensor.startswith("imx"):
            sensor = sensor.upper()
        return sensor

    def _set_audio_gain(self, chan, val):
        self.cam.audio.set_gain(chan, val)
        if chan == 'L':
            self.audio_gain_left.set(val)
        else:
            self.audio_gain_right.set(val)

    def _set_audio_mux(self, chan, src):
        self.cam.audio.set_route(chan, src)
        if chan == 'L':
            self.audio_mux_left.set(src)
            self.config.audio.left_source = src
        else:
            self.audio_mux_right.set(src)
            self.config.audio.right_source = src
        self.config.save_config()

    def _create_settings_layout(self):
        l: Layout = self.screens["settings"]

        l.add_button(Layout.TOPLEFT, 100, "System", self.settings_tab, lambda v: self.settings_tab.set("system"),
                     state_cmp=lambda s: s == "system")
        l.add_button(Layout.TOPLEFT, 100, "Audio", self.settings_tab, lambda v: self.settings_tab.set("audio"),
                     state_cmp=lambda s: s == "audio")
        l.add_button(Layout.TOPLEFT, 100, "Info", self.settings_tab, lambda v: self.settings_tab.set("info"),
                     state_cmp=lambda s: s == "info")

        l.add_button(Layout.TOPRIGHT, 64, "\uf013", StateNumber(False),
                     lambda v: self.open_settings(False))

        page1 = VBox(name="system")
        page1.add(
            Slider("Backlight", self.backlight, handler=lambda v: self.set_backlight(v),
                   min=self.min_backlight, max=self.max_backlight))
        l.add_widget(Layout.MIDDLE, page1)
        page1.compute()

        page3 = VBox(name="audio")
        page3.add(
            Slider("Left gain", self.audio_gain_left, handler=lambda v: self._set_audio_gain('L', v),
                   min=self.audio_gain_min, max=self.audio_gain_max, text_width=130))
        page3.add(
            Slider("Right gain", self.audio_gain_right, handler=lambda v: self._set_audio_gain('R', v),
                   min=self.audio_gain_min, max=self.audio_gain_max, text_width=130))

        left_opts = {}
        for item in self.cam.audio.get_routes('L'):
            left_opts[item] = item
        right_opts = {}
        for item in self.cam.audio.get_routes('R'):
            right_opts[item] = item

        page3.add(RadioRow("Left src", self.audio_mux_left, options=left_opts,
                           handler=lambda v: self._set_audio_mux('L', v),
                           text_width=130))
        page3.add(RadioRow("Right src", self.audio_mux_right, options=right_opts,
                           handler=lambda v: self._set_audio_mux('R', v),
                           text_width=130))

        l.add_widget(Layout.MIDDLE, page3)
        page3.compute()

        page2 = VBox(name="info")
        page2.add(TextRow("Sensor", StateNumber(self.get_sensor()), None, text_width=130))
        page2.add(TextRow("IP Address", self.ip, None, text_width=130))
        l.add_widget(Layout.MIDDLE, page2)
        page2.compute()

        l.page_state = self.settings_tab
        l.compute()

    def cycle_guides(self):
        if self.guides.value == "thirds":
            self.guides.set("cross")
        elif self.guides.value == "cross":
            self.guides.set("safe")
        elif self.guides.value == "safe":
            self.guides.set(False)
        elif not self.guides.value:
            self.guides.set("thirds")

    def create_screen(self, name, bg):
        self.screens[name] = Layout(self.width, self.height, bg)

    def update_state(self, state):
        self.state = state

        if self.tally.once(self):
            color = (255, 255, 255, 255)
            if self.tally.value & 2:
                color = (0, 255, 0, 255)
            if self.tally.value & 1:
                color = (255, 0, 0, 255)
            tc = self.screens["main"]["tc"]
            if tc is not None:
                tc.color_text = color

        if not self.hdmi:
            while not self.input_queue.empty():
                event = self.input_queue.get()
                if isinstance(event, TapEvent):
                    self.screens[self.active_screen].tap(event.x, event.y)
                elif isinstance(event, MoveEvent):
                    self.screens[self.active_screen].move(event.x, event.y)
                elif isinstance(event, ReleaseEvent):
                    self.screens[self.active_screen].release(event.x, event.y)
                elif isinstance(event, DoubleTapEvent):
                    self.screens[self.active_screen].doubletap(event.x, event.y)

        tc = datetime.datetime.fromtimestamp(self.state["SensorTimestamp"] / 1000000000, tz=datetime.timezone.utc)
        self.tc.set(tc.strftime("%H:%M:%S"))
        self.shutter.set(int(1000000 / state["ExposureTime"]))
        self.gain.set(int(round(10 * math.log10(state["AnalogueGain"]))))
        self.temperature.set(state["ColourTemperature"])
        if "LensPosition" in state:
            self.focus.set(state["LensPosition"])
        if "AfState" in state:
            if state["AfState"] == 0:
                self.af.set("M")
            elif state["AfState"] == 1:
                self.af.set("S")
            elif state["AfState"] == 2:
                self.af.set("C")
        else:
            self.af.set("")

        if self.ae.once("update_state"):
            self.screens["main"]["gain"].color_text = (128, 128, 128, 255) if self.ae.value else (255, 255, 255, 255)
            self.screens["main"]["shutter"].color_text = (128, 128, 128, 255) if self.ae.value else (255, 255, 255, 255)
            self.screens["main"]["ae"].color_text = (128, 128, 128, 255) if not self.ae.value else (255, 255, 255, 255)

        buf = self.screens[self.active_screen].render()
        if buf is not None:
            self.paint_hook(buf)

    def switch_screen(self, name):
        if self.active_screen == "main" and name != "main":
            # Save overlay state
            self.overlay_state = {
                'histogram': self.histogram.value,
            }
        self.active_screen = name
        self.screens[self.active_screen].dirty = True

        if name == "main":
            self.cam.enable_histogram(self.overlay_state["histogram"])
            self.cam.move_vu(False)
        else:
            self.cam.enable_histogram(False)
            self.cam.move_vu(True)
            self.ip.set(self.get_ip())

    def open_settings(self, state):
        if state:
            self.switch_screen("settings")
        else:
            self.switch_screen("main")

    def set_backlight(self, value):
        if self.bl is not None:
            set_backlight(self.bl, value)
            self.backlight.set(value)
            self.config.monitor.backlight = int(value)
            self.config.save_config()
