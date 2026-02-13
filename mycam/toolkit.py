import threading

import evdev
from PIL import ImageFont, Image, ImageDraw


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


class TapEvent:
    def __init__(self, x, y):
        self.x = y
        self.y = x


class Widget:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.x2 = 0
        self.y2 = 0
        self.width = 0
        self.height = 0
        self.layout_width = 0
        self.layout_height = 0
        self.color_active = (0, 128, 255, 200)

    def render(self, ctx):
        pass

    def tap(self):
        pass


class Button(Widget):
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)

    def __init__(self, width, text, state, handler):
        super().__init__()
        self.width = width
        self.text = text
        self.state = state
        self.handler = handler

    def render(self, ctx):
        if not self.state.once():
            return False
        ctx.has_changed = True
        fill = (0, 0, 0, 0)
        stroke = 1
        if self.state.value:
            fill = self.color_active
        ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=fill)

        _, _, w, h = ctx.textbbox((0, 0), str(self.text), font=self.FONT)
        ctx.text((self.x + ((self.width - w) / 2), self.y2 - 46), str(self.text), font=self.FONT,
                 fill=(255, 255, 255, 255),
                 stroke_fill=(0, 0, 0, 255), stroke_width=stroke)
        return True

    def tap(self):
        if self.handler is not None:
            new_val = None
            if isinstance(self.state.value, bool):
                new_val = not self.state.value
            self.handler(new_val)
        else:
            print("Button pressed, but no handler")


class GuidesButton(Button):
    def render(self, ctx):
        if self.state.value:
            self.text = self.state.value.title()
        else:
            self.text = "Guides"
        once = super().render(ctx)

        if once:
            width = self.layout_width
            height = self.layout_height
            if self.state.value == "thirds":
                ctx.line((width / 3, 64, width / 3, height - 65), (128, 128, 128, 128))
                ctx.line((width / 3 * 2, 64, width / 3 * 2, height - 65), (128, 128, 128, 128))
                ctx.line((0, height / 3, width, height / 3), (128, 128, 128, 128))
                ctx.line((0, height / 3 * 2, width, height / 3 * 2), (128, 128, 128, 128))
            else:
                ctx.rectangle((0, 64, width, height - 65), (0, 0, 0, 0))


class Label(Button):
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)
    HEADER = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 15)

    def __init__(self, width, text, format, state, handler, align="left"):
        super().__init__(width, text, state, handler)
        self.align = align
        self.format = format

    def render(self, ctx):
        if not self.state.once():
            return
        ctx.has_changed = True
        ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=(0, 0, 0, 0))
        ctx.text((self.x, self.y + 10), str(self.text), font=self.HEADER, fill=(255, 255, 255, 255),
                 stroke_fill=(0, 0, 0, 255), stroke_width=1)
        ctx.text((self.x, self.y + 24), self.format.format(self.state), font=self.FONT, fill=(255, 255, 255, 255),
                 stroke_fill=(0, 0, 0, 255), stroke_width=1)


class Layout:
    TOPLEFT = 0
    TOPMIDDLE = 1
    TOPRIGHT = 2
    BOTTOMLEFT = 3
    BOTTOMMIDDLE = 4
    BOTTOMRIGHT = 5

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.buf = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

        self.widgets = {}
        for i in range(6):
            self.widgets[i] = []

    def add_button(self, attach, width, text, state, handler):
        self.widgets[attach].append(Button(width, text, state, handler))

    def add_label(self, attach, width, text, format, state, handler, align=None):
        self.widgets[attach].append(Label(width, text, format, state, handler, align=align))

    def add_widget(self, attach, widget):
        self.widgets[attach].append(widget)

    def _offset(self, widgets, x, y):
        for w in widgets:
            w.x += x
            w.y += y
            w.x2 += x
            w.y2 += y

    def compute(self):
        padding = 10
        height = 64
        for attachment in range(6):
            offset = 0
            for w in self.widgets[attachment]:
                w.x = offset
                w.y = 0
                w.x2 = offset + w.width
                w.y2 = w.y + height
                w.layout_width = self.width
                w.layout_height = self.height
                offset += w.width + padding
            total = offset - padding

            if attachment == Layout.TOPLEFT:
                self._offset(self.widgets[attachment], padding, 0)
            elif attachment == Layout.TOPMIDDLE:
                self._offset(self.widgets[attachment], (self.width / 2) - (total / 2), 0)
            elif attachment == Layout.TOPRIGHT:
                self._offset(self.widgets[attachment], self.width - total - padding, 0)
            elif attachment == Layout.BOTTOMLEFT:
                self._offset(self.widgets[attachment], padding, self.height - height)
            elif attachment == Layout.BOTTOMMIDDLE:
                self._offset(self.widgets[attachment], (self.width / 2) - (total / 2), self.height - height)
            elif attachment == Layout.BOTTOMRIGHT:
                self._offset(self.widgets[attachment], self.width - total - padding, self.height - height)

    def render(self):
        ctx = ImageDraw.Draw(self.buf)
        ctx.has_changed = False
        for attachment in range(6):
            for w in self.widgets[attachment]:
                w.render(ctx)
        if ctx.has_changed:
            return self.buf
        return None

    def tap(self, x, y):
        for attachment in range(6):
            for w in self.widgets[attachment]:
                if w.x <= x <= w.x2 and w.y <= y <= w.y2:
                    w.tap()
                    break


def _input_thread(path, queue):
    device = evdev.InputDevice(path)
    last_x = 0
    last_y = 0
    for event in device.read_loop():
        # print(evdev.categorize(event))
        if event.type == evdev.ecodes.EV_ABS:
            if event.code == evdev.ecodes.ABS_MT_POSITION_X:
                last_x = event.value
            elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                last_y = event.value
        if event.type == evdev.ecodes.EV_KEY and evdev.ecodes.BTN_TOUCH:
            if event.value == 1:
                # Touch down
                queue.put(TapEvent(last_x, last_y))
            else:
                # Touch up
                pass


def HandleInputs(input_queue):
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        print(device.path, device.name, device.phys)
        t = threading.Thread(target=_input_thread, args=(device.path, input_queue))
        t.daemon = True
        t.start()
