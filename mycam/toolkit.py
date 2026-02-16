import threading
import time

import evdev
from PIL import ImageFont, Image, ImageDraw


class StateNumber:
    def __init__(self, initial=None):
        self.value = None
        self.last_value = None
        self._changed = {None: False}

        if initial is not None:
            self.value = initial
            self._changed[None] = True

    def set(self, value):
        self.value = value
        if self.value != self.last_value:
            self.last_value = self.value
            self.force_state(True)

    def force_state(self, state):
        for k in self._changed:
            self._changed[k] = state

    def toggle(self, strval=None):
        if strval is not None:
            if self.value != strval:
                self.set(strval)
            else:
                self.set("")
            return
        self.set(not self.value)

    def once(self, selector=None):
        if selector not in self._changed:
            self._changed[selector] = False
            return True
        changed = self._changed[selector]
        self._changed[selector] = False
        return changed

    def __str__(self):
        return str(self.value)


class TapEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class DoubleTapEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Widget:
    def __init__(self):
        self.name = None
        self.x = 0
        self.y = 0
        self.x2 = 0
        self.y2 = 0
        self.width = 0
        self.height = 0
        self.layout_width = 0
        self.layout_height = 0
        self.hexpand = False
        self.visible = StateNumber(True)
        self.color_active = (0, 128, 255, 200)
        self.color_inactive = (128, 128, 128, 200)
        self.color_clear = (0, 0, 0, 0)
        self._dirty = StateNumber(False)

    def render(self, ctx):
        pass

    def tap(self, x, y):
        pass

    def doubletap(self, x, y):
        pass

    def mark_dirty(self):
        self._dirty.force_state(True)


class Button(Widget):
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)

    def __init__(self, width, text, state, handler, state_cmp=None):
        super().__init__()
        self.width = width
        self.text = text
        self.state = state
        self.state_cmp = state_cmp
        self.handler = handler

    def render(self, ctx):
        if not self.state.once(self):
            return False
        ctx.has_changed = True

        if self.state_cmp is not None:
            active = self.state_cmp(self.state.value)
        else:
            active = self.state.value
        fill = self.color_active if active else self.color_clear
        ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=fill)

        _, _, w, h = ctx.textbbox((0, 0), str(self.text), font=self.FONT)
        ctx.text((self.x + ((self.width - w) / 2), self.y2 - 46), str(self.text), font=self.FONT,
                 fill=(255, 255, 255, 255),
                 stroke_fill=(0, 0, 0, 255), stroke_width=1)
        return True

    def tap(self, x, y):
        if self.handler is not None:
            new_val = None
            if self.state is not None and isinstance(self.state.value, bool):
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
        super().render(ctx)


class Guides(Widget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.hexpand = True

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once():
            return
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

    def __init__(self, width, text, format, state, handler, align="left", button_state=None, state_cmp=None):
        super().__init__(width, text, button_state, handler, state_cmp=state_cmp)
        self.align = align
        self.format = format
        self.label_state = state
        self.color = (255, 255, 255, 255)

    @property
    def color_text(self):
        return self.color

    @color_text.setter
    def color_text(self, value):
        self.color = value
        self.label_state.force_state(True)

    def render(self, ctx):
        if self.state is not None and self.state.once(self):
            self.label_state.force_state(True)

        if not self.label_state.once(self):
            return
        ctx.has_changed = True

        fill = (0, 0, 0, 0)

        if self.state is None:
            active = False
        elif self.state_cmp is not None:
            active = self.state_cmp(self.state.value)
        else:
            active = self.state.value

        if active:
            fill = self.color_active

        ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=fill)
        ctx.text((self.x + 10, self.y + 10), str(self.text), font=self.HEADER, fill=self.color_text,
                 stroke_fill=(0, 0, 0, 255), stroke_width=1)
        ctx.text((self.x + 10, self.y + 24), self.format.format(self.label_state.value), font=self.FONT,
                 fill=self.color_text, stroke_fill=(0, 0, 0, 255), stroke_width=1)


class ToggleRow(Widget):
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)

    def __init__(self, text, state, handler, background=None, text_width=None, state_cmp=None):
        super().__init__()
        self.hexpand = True
        self.text = text
        self.state = state
        self.state_cmp = state_cmp
        self.handler = handler
        self.height = 64
        self.color_clear = background
        self.text_width = text_width

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once():
            return
        ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=self.color_clear)
        ctx.text((self.x + 10, self.y + 16), str(self.text), font=self.FONT, stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)
        if self.text_width is None:
            _, _, w, _ = ctx.textbbox((0, 0), str(self.text), font=self.FONT)
            self.text_width = w + 10

        if self.state_cmp is not None:
            active = self.state_cmp(self.state.value)
        else:
            active = self.state.value
        fill = self.color_active if active else (0, 0, 0, 200)

        btn_start = self.x + self.text_width + 10
        pad = 12
        ctx.rounded_rectangle((btn_start, self.y + pad, btn_start + 96, self.y2 - pad), 32, fill=fill)
        r = 12
        offset = 64 if active else 5
        ctx.ellipse((btn_start + offset, self.y + (self.height / 2) - r, btn_start + offset + r + r,
                     self.y + (self.height / 2) + r), fill=(255, 255, 255, 255))

    def tap(self, x, y):
        if self.handler is not None:
            new_val = None
            if self.state is not None and isinstance(self.state.value, bool):
                new_val = not self.state.value
            self.handler(new_val)
        else:
            print("Button pressed, but no handler")


class RadioRow(Widget):
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)

    def __init__(self, text, state, handler, options, background=None, text_width=None, state_cmp=None):
        super().__init__()
        self.hexpand = True
        self.text = text
        self.state = state
        self.options = options
        self.state_cmp = state_cmp
        self.handler = handler
        self.height = 64
        self.color_clear = background
        self.text_width = text_width
        self._regions = []

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once():
            return
        ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=self.color_clear)
        ctx.text((self.x + 10, self.y + 16), str(self.text), font=self.FONT, stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)
        if self.text_width is None:
            _, _, w, _ = ctx.textbbox((0, 0), str(self.text), font=self.FONT)
            self.text_width = w + 10

        if self.state_cmp is not None:
            active = self.state_cmp(self.state.value)
        else:
            active = self.state.value
        fill = self.color_active if active else (0, 0, 0, 200)

        pad = 6
        hpad = 24
        offset = self.x + self.text_width + 10
        self._regions = []
        for key in self.options:
            label = self.options[key]
            _, _, w, _ = ctx.textbbox((0, 0), str(label), font=self.FONT)
            width = w + hpad + hpad
            if key == self.state.value:
                ctx.rounded_rectangle((offset, self.y + pad, offset + width, self.y2 - pad), 32, fill=fill)
            ctx.text((offset + hpad, self.y + 16), str(label), font=self.FONT, stroke_fill=(0, 0, 0, 255),
                     stroke_width=1)
            self._regions.append((offset, offset + width, key))
            offset += width

    def tap(self, x, y):
        for start, end, key in self._regions:
            if start <= x < end:
                val = key
                break
        else:
            return
        if self.handler is not None:
            self.handler(val)
        else:
            print("Button pressed, but no handler")


class Slider(Widget):
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)

    def __init__(self, text, state, handler, background=None, text_width=None, min=None, max=None):
        super().__init__()
        self.hexpand = True
        self.text = text
        self.height = 64
        self.state = state
        self.handler = handler
        self.color_clear = background
        self.text_width = text_width
        self.thickness = 2
        self.radius = 10
        if min is None:
            min = StateNumber(0)
        if max is None:
            max = StateNumber(100)
        self.min = min
        self.max = max
        self.active = True
        self.color_bar = (0, 0, 0, 200)
        self.color_knob = (255, 255, 255, 255)

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once():
            return

        ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=self.color_clear)
        ctx.text((self.x + 10, self.y + 16), str(self.text), font=self.FONT, stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)
        if self.text_width is None:
            _, _, w, _ = ctx.textbbox((0, 0), str(self.text), font=self.FONT)
            self.text_width = w + 10

        slide_start = self.x + self.text_width + 10
        slide_len = self.x2 - 10 - slide_start
        pos = ((self.state.value - self.min.value) / (self.max.value - self.min.value)) * slide_len
        vcenter = self.y + (self.height / 2)

        bc = self.color_active if self.active else self.color_inactive

        ctx.rectangle((slide_start,
                       vcenter - self.thickness,
                       slide_start + pos,
                       vcenter + self.thickness,
                       ), fill=bc)
        ctx.rectangle((slide_start + pos,
                       vcenter - self.thickness,
                       self.x2 - 10,
                       vcenter + self.thickness,
                       ), fill=self.color_bar)

        ctx.ellipse((slide_start + pos - self.radius,
                     vcenter - self.radius,
                     slide_start + pos + self.radius,
                     vcenter + self.radius,
                     ), fill=self.color_knob)

    def tap(self, x, y):
        slide_start = self.text_width + 10
        slide_len = self.x2 - 10 - (self.x + slide_start)
        pos = ((self.state.value - self.min.value) / (self.max.value - self.min.value)) * slide_len

        if x < slide_start:
            return
        x -= slide_start
        x /= slide_len
        x *= self.max.value - self.min.value
        x += self.min.value
        if self.handler is not None:
            self.handler(x)


class VBox(Widget):
    def __init__(self, name=None, vpadding=0, hpadding=0, background=False, border=10):
        super().__init__()
        self.name = name
        self.widgets = []
        self.vpadding = vpadding
        self.hpadding = hpadding
        self.background = background
        self.border = border
        if self.background:
            self.color_background = (0, 0, 0, 128)
        else:
            self.color_background = (0, 0, 0, 0)

    def add(self, widget):
        self.widgets.append(widget)

    def compute(self):
        offset = 0
        for w in self.widgets:
            w.x = self.x + self.hpadding
            w.x2 = w.x + self.width
            if w.hexpand:
                w.x2 = self.x2 - self.hpadding
            w.y = self.y + self.vpadding + offset
            offset += w.height
            w.y2 = w.y + w.height
            w.layout_width = self.layout_width
            w.layout_height = self.layout_height
            if w.color_clear is None:
                w.color_clear = self.color_background

    def render(self, ctx):
        if self.visible.once(self):
            ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=(0, 0, 0, 0))
            if self.background:
                ctx.rectangle((
                    self.x + self.hpadding - self.border,
                    self.y + self.vpadding - self.border,
                    self.x2 - self.hpadding + self.border,
                    self.y2 - self.vpadding + self.border),
                    fill=self.color_background)
            for widget in self.widgets:
                widget.mark_dirty()

        for widget in self.widgets:
            widget.render(ctx)

    def tap(self, x, y):
        x += self.x
        y += self.y
        for w in self.widgets:
            if w.visible.value and w.x <= x <= w.x2 and w.y <= y <= w.y2:
                w.tap(x - w.x, y - w.y)
                break

    def doubletap(self, x, y):
        x += self.x
        y += self.y
        for w in self.widgets:
            if w.visible.value and w.x <= x <= w.x2 and w.y <= y <= w.y2:
                w.doubletap(x - w.x, y - w.y)
                break


class Layout:
    TOPLEFT = 0
    TOPMIDDLE = 1
    TOPRIGHT = 2
    BOTTOMLEFT = 3
    BOTTOMMIDDLE = 4
    BOTTOMRIGHT = 5
    MIDDLE = 6

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.buf = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        self.on_double_tap_empty = None
        self.page_state = None

        self.widgets = {}
        for i in range(7):
            self.widgets[i] = []

    def add_button(self, attach, width, text, state, handler):
        self.widgets[attach].append(Button(width, text, state, handler))

    def add_label(self, attach, width, text, format, state, handler, align=None, button_state=None, state_cmp=None,
                  name=None):
        w = Label(width, text, format, state, handler, align=align, button_state=button_state, state_cmp=state_cmp)
        w.name = name
        self.widgets[attach].append(w)

    def add_widget(self, attach, widget):
        self.widgets[attach].append(widget)

    def _offset(self, widgets, x, y):
        for w in widgets:
            w.x += x
            w.y += y
            w.x2 += x
            w.y2 += y

    def switch_middle(self, name):
        print("Switching to", name, "tab")
        for w in self.widgets[Layout.MIDDLE]:
            w.visible.set(w.name == name)

    def __getitem__(self, item):
        for attachment in range(7):
            for w in self.widgets[attachment]:
                if w.name == item:
                    return w

    def compute(self):
        padding = 10
        height = 64
        for attachment in range(7):
            offset = 0
            for w in self.widgets[attachment]:
                if attachment == Layout.MIDDLE:
                    # The middle attachment widgets are all stacked on top of eachother in the same spot
                    # filling the entire center area
                    w.x = 0
                    w.x2 = self.width
                    w.y = height
                    w.y2 = self.height - height
                    w.layout_width = self.width
                    w.layout_height = self.height
                else:
                    w.x = offset
                    w.y = 0
                    w.x2 = offset + w.width
                    w.y2 = w.y + height
                    w.layout_width = self.width
                    w.layout_height = self.height
                offset += w.width + padding
                if hasattr(w, "compute"):
                    w.compute()

            total = offset - padding

            if attachment == Layout.TOPLEFT:
                self._offset(self.widgets[attachment], 0, 0)
            elif attachment == Layout.TOPMIDDLE:
                self._offset(self.widgets[attachment], (self.width / 2) - (total / 2), 0)
            elif attachment == Layout.TOPRIGHT:
                self._offset(self.widgets[attachment], self.width - total, 0)
            elif attachment == Layout.BOTTOMLEFT:
                self._offset(self.widgets[attachment], 0, self.height - height)
            elif attachment == Layout.BOTTOMMIDDLE:
                self._offset(self.widgets[attachment], (self.width / 2) - (total / 2), self.height - height)
            elif attachment == Layout.BOTTOMRIGHT:
                self._offset(self.widgets[attachment], self.width - total, self.height - height)
            elif attachment == Layout.MIDDLE:
                pass

    def render(self):
        if self.page_state is not None:
            if self.page_state.once(self):
                self.switch_middle(self.page_state.value)

        ctx = ImageDraw.Draw(self.buf)
        ctx.has_changed = False
        for attachment in range(7):
            for w in self.widgets[attachment]:
                if w.visible.value:
                    w.render(ctx)
        if ctx.has_changed:
            return self.buf
        return None

    def tap(self, x, y):
        for attachment in range(7):
            for w in self.widgets[attachment]:
                if w.visible.value and w.x <= x <= w.x2 and w.y <= y <= w.y2:
                    w.tap(x - w.x, y - w.y)
                    break

    def doubletap(self, x, y):
        for attachment in range(7):
            for w in self.widgets[attachment]:
                if w.visible.value and w.x <= x <= w.x2 and w.y <= y <= w.y2:
                    w.doubletap(x - w.x, y - w.y)
                    break
        else:
            # Double tap outside a widget, used for zooming
            if self.on_double_tap_empty is not None:
                self.on_double_tap_empty()


def _touch_transform(config, x, y):
    flip_x = False
    flip_y = False
    if config.monitor.touchscreen_rotate == 90:
        x, y = y, x
    elif config.monitor.touchscreen_rotate == 180:
        flip_x = True
    elif config.monitor.touchscreen_rotate == 270:
        x, y = y, x
        flip_x = True
    flip_x ^= config.monitor.touchscreen_flip_x
    flip_y ^= config.monitor.touchscreen_flip_y
    if flip_x:
        x = config.touchscreen_res[0] - x
    if flip_y:
        y = config.touchscreen_res[1] - y
    return x, y


def _input_thread(path, queue, config):
    device = evdev.InputDevice(path)
    last_x = 0
    last_y = 0
    last_t = time.monotonic()
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
                pos = _touch_transform(config, last_x, last_y)
                time_since_last = time.monotonic() - last_t
                if time_since_last < 0.5:
                    queue.put(DoubleTapEvent(pos[0], pos[1]))
                else:
                    queue.put(TapEvent(pos[0], pos[1]))
                last_t = time.monotonic()
            else:
                # Touch up
                pass


def HandleInputs(input_queue, config):
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        print(device.path, device.name, device.phys)
        t = threading.Thread(target=_input_thread, args=(device.path, input_queue, config))
        t.daemon = True
        t.start()
