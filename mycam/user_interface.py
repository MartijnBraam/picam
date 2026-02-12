import datetime
import math

from PIL import ImageFont, ImageDraw, Image


class StateNumber:
    def __init__(self, initial=None):
        self.value = None
        self.last_value = None
        self.changed = False

        if initial is not None:
            self.value = initial
            self.changed = True

    def set(self, value):
        self.value = value
        if self.value != self.last_value:
            self.last_value = self.value
            self.changed = True

    def once(self):
        changed = self.changed
        self.changed = False
        return changed

    def __str__(self):
        return str(self.value)


class UI:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/DejaVuSans.ttf", 15)
        self.font_heading = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 15)
        self.font_value = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)

        self.screens = {}
        self.create_screen("main")
        self.paint_hook = None
        self.state = None
        self.debug = False

        self.fps = 60
        self.shutter = StateNumber()
        self.gain = StateNumber()
        self.tc = StateNumber()
        self.camera_id = StateNumber()

        self.zebra = StateNumber(False)
        self.focus_assist = StateNumber(False)
        self.false_color = StateNumber(False)
        self.guides = StateNumber("thirds")

        self.color_active = (0, 128, 255, 200)

        self.value_rect = Image.new("RGBA", (100, 32), (255, 255, 255, 255))

    def start(self):
        self.render_main_screen()

    def _paint(self, name):
        self.paint_hook(self.screens[name])

    def draw_value(self, ctx: ImageDraw.ImageDraw, x, width, name, value):
        ctx.has_changed = True
        tox = x + width
        if self.debug:
            ctx.rectangle((x - 1, 0, tox, 64), fill=(255, 0, 0, 255))
        ctx.rectangle((x, 1, tox - 1, 63), fill=(0, 0, 0, 0))
        ctx.text((x + 1, 10), name, font=self.font_heading, fill=(255, 255, 255, 255), stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)
        ctx.text((x + 1, 24), str(value), font=self.font_value, fill=(255, 255, 255, 255), stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)

    def draw_button(self, ctx: ImageDraw.ImageDraw, x, width, name, active):
        ctx.has_changed = True
        fill = (0, 0, 0, 0)
        stroke = 1
        if active:
            fill = self.color_active
        ctx.rectangle((x, self.height - 64, x + width, self.height), fill=fill)

        _, _, w, h = ctx.textbbox((0, 0), str(name), font=self.font_value)
        ctx.text((x + ((width - w) / 2), self.height - 46), str(name), font=self.font_value, fill=(255, 255, 255, 255),
                 stroke_fill=(0, 0, 0, 255), stroke_width=stroke)

    def draw_text(self):
        pass

    def create_screen(self, name):
        self.screens[name] = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

    def _draw(self, name) -> ImageDraw.ImageDraw:
        return ImageDraw.Draw(self.screens[name])

    def render_main_screen(self):
        ctx = self._draw("main")
        ctx.has_changed = False
        self.draw_value(ctx, 10, 100, "FPS", self.fps)
        if self.shutter.once():
            self.draw_value(ctx, 120, 100, "Shutter", f"1/{self.shutter}")
        if self.gain.once():
            self.draw_value(ctx, 240, 100, "Gain", f"{self.gain} dB")

        if self.tc.once():
            self.draw_value(ctx, 400, 200, "TC", self.tc)

        if self.camera_id.once():
            self.draw_value(ctx, 650, 100, "Camera ID", self.camera_id)

        if self.zebra.once():
            self.draw_button(ctx, 10, 120, "Zebra", self.zebra.value)
        if self.focus_assist.once():
            self.draw_button(ctx, 140, 120, "Focus", self.focus_assist.value)
        if self.false_color.once():
            self.draw_button(ctx, 270, 120, "Exposure", self.false_color.value)

        if self.guides.once():
            self.draw_button(ctx, 400, 120, self.guides.value.title(), self.guides.value != "none")
            if self.guides.value == "thirds":
                ctx.line((self.width / 3, 64, self.width / 3, self.height - 65), (128, 128, 128, 128))
                ctx.line((self.width / 3 * 2, 64, self.width / 3 * 2, self.height - 65), (128, 128, 128, 128))
                ctx.line((0, self.height / 3, self.width, self.height / 3), (128, 128, 128, 128))
                ctx.line((0, self.height / 3 * 2, self.width, self.height / 3 * 2), (128, 128, 128, 128))

        if ctx.has_changed:
            self._paint("main")

    def update_state(self, state):
        self.state = state
        tc = datetime.datetime.fromtimestamp(self.state["SensorTimestamp"] / 1000000000, tz=datetime.timezone.utc)
        self.tc.set(tc.strftime("%H:%M:%S"))
        self.shutter.set(int(1000000 / state["ExposureTime"]))
        self.gain.set(int(round(10 * math.log10(state["AnalogueGain"]))))
        self.render_main_screen()
