import re
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


class MoveEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class ReleaseEvent:
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
        self.vexpand = False
        self.visible = StateNumber(True)
        self.color_active = (0, 128, 255, 200)
        self.color_inactive = (128, 128, 128, 200)
        self.color_clear = (0, 0, 0, 0)
        self.color_background = None
        self._dirty = StateNumber(False)

    def render(self, ctx):
        pass

    def tap(self, x, y):
        pass

    def doubletap(self, x, y):
        pass

    def move(self, x, y):
        pass

    def release(self, x, y):
        pass

    def mark_dirty(self):
        self._dirty.force_state(True)

    def _clear(self, ctx):
        color = self.color_clear
        if self.color_background:
            color = self.color_background
        ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=color)
        ctx.has_changed = True


class Button(Widget):
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)
    FA = ImageFont.truetype("/usr/share/fonts-font-awesome/fonts/fontawesome-webfont.ttf", 30)
    RE_FA = re.compile(u'[\ue000-\uf8ff]', flags=re.UNICODE)

    def __init__(self, width, text, state, handler, state_cmp=None):
        super().__init__()
        self.width = width
        self.text = text
        self.state = state
        self.state_cmp = state_cmp
        self.handler = handler
        self.font = Button.FONT
        if self.RE_FA.match(self.text):
            self.font = Button.FA

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

        _, _, w, h = ctx.textbbox((0, 0), str(self.text), font=self.font)
        ctx.text((self.x + ((self.width - w) / 2), self.y2 - 46), str(self.text), font=self.font,
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
    def __init__(self, state, af_state, af_pos, handler=None):
        super().__init__()
        self.state = state
        self.af_state = af_state
        self.af_pos = af_pos
        self.handler = handler
        self.hexpand = True
        self.vexpand = True
        self.visible.value = True

    def _rect(self, ctx, size, w):
        width = self.layout_width
        height = self.layout_height
        x1 = width * (1 - size)
        x2 = width * size
        y1 = height * (1 - size)
        y2 = height * size

        ctx.line((x1, max(64, y1), x1, min(height - 65, y2)), (128, 128, 128, 128), width=w)
        ctx.line((x2, max(64, y1), x2, min(height - 65, y2)), (128, 128, 128, 128), width=w)

        if y1 > 64:
            ctx.line((x1, y1, x2, y1), (128, 128, 128, 128), width=w)
        if y2 < height - 65:
            ctx.line((x1, y2, x2, y2), (128, 128, 128, 128), width=w)

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once() and not self.af_state.once(
                self) and not self.af_pos.once(self):
            return
        width = self.layout_width
        height = self.layout_height
        ctx.rectangle((0, 64, width, height - 65), (0, 0, 0, 0))
        ctx.has_changed = True
        w = 2

        if self.state.value == "thirds":
            ctx.line((width / 3, 64, width / 3, height - 65), (128, 128, 128, 128), width=w)
            ctx.line((width / 3 * 2, 64, width / 3 * 2, height - 65), (128, 128, 128, 128), width=w)
            ctx.line((0, height / 3, width, height / 3), (128, 128, 128, 128), width=w)
            ctx.line((0, height / 3 * 2, width, height / 3 * 2), (128, 128, 128, 128), width=w)
        elif self.state.value == "cross":
            ctx.line((width / 2, 64, width / 2, height - 65), (128, 128, 128, 128), width=w)
            ctx.line((0, height / 2, width, height / 2), (128, 128, 128, 128), width=w)
        elif self.state.value == "safe":
            self._rect(ctx, 0.93, w)
            self._rect(ctx, 0.89, w)
            # 4/3 safe guide
            old = height / 3 * 4
            ctx.line((old, 64, old, height - 65), (128, 128, 128, 128), width=w)
            ctx.line((width - old, 64, width - old, height - 65), (128, 128, 128, 128), width=w)

        if self.af_state.value != "M" and self.af_state.value != "":
            afx = width * self.af_pos.value[0]
            afy = height * self.af_pos.value[1]
            ctx.rectangle((afx - 32, afy - 32, afx + 32, afy + 32), fill=None, outline=(255, 255, 255, 255), width=w)

    def tap(self, x, y):
        if self.handler is not None:
            self.handler(x / self.layout_width, (y + self.y) / self.layout_height)


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
        self.color_background = background
        self.text_width = text_width

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once():
            return
        self._clear(ctx)
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
        self.color_background = background
        self.text_width = text_width
        self._regions = []

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once():
            return
        self._clear(ctx)
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


class TextRow(Widget):
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
        self._regions = []

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once():
            return
        self._clear(ctx)
        ctx.text((self.x + 10, self.y + 16), str(self.text), font=self.FONT, stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)
        if self.text_width is None:
            _, _, w, _ = ctx.textbbox((0, 0), str(self.text), font=self.FONT)
            self.text_width = w + 10

        if self.state_cmp is not None:
            active = self.state_cmp(self.state.value)
        else:
            active = self.state.value

        hpad = 24
        offset = self.x + self.text_width + 10
        ctx.text((offset + hpad, self.y + 16), str(self.state.value), font=self.FONT, fill=(128, 128, 128, 255),
                 stroke_fill=(0, 0, 0, 255), stroke_width=1)

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
        self.color_background = background
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
        self.color_bar = (0, 0, 0, 255)
        self.color_knob = (255, 255, 255, 255)

    def render(self, ctx):
        if not self.state.once(self) and not self._dirty.once():
            return

        self._clear(ctx)

        ctx.text((self.x + 10, self.y + 16), str(self.text), font=self.FONT, stroke_fill=(0, 0, 0, 255),
                 stroke_width=1)
        if self.text_width is None:
            _, _, w, _ = ctx.textbbox((0, 0), str(self.text), font=self.FONT)
            self.text_width = w + 10

        slide_start = self.x + self.text_width + 10
        slide_len = self.x2 - 10 - slide_start
        pos = ((self.state.value - self.min.value) / (self.max.value - self.min.value)) * slide_len
        if pos < 0:
            pos = 0
        vcenter = self.y + (self.height / 2)

        bc = self.color_active if self.active else self.color_inactive

        ctx.rectangle((slide_start,
                       vcenter - self.thickness,
                       slide_start + pos,
                       vcenter + self.thickness,
                       ), fill=bc)
        if slide_start+pos < self.x2 - 10:
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

    def move(self, x, y):
        slide_start = self.text_width + 10
        slide_len = self.x2 - 10 - (self.x + slide_start)

        if x < slide_start:
            return
        x -= slide_start
        x /= slide_len
        x *= self.max.value - self.min.value
        x += self.min.value
        if self.handler is not None:
            self.handler(x)


class VBox(Widget):
    def __init__(self, name=None, vpadding=0, hpadding=0, border=10):
        super().__init__()
        self.name = name
        self.widgets = []
        self.vpadding = vpadding
        self.hpadding = hpadding
        self.border = border
        self.drag_widget = None

    def add(self, widget):
        self.widgets.append(widget)

    def compute(self):
        offset = 0
        for w in self.widgets:
            w.x = self.x + self.hpadding
            w.x2 = w.x + self.width
            if w.hexpand:
                w.x2 = self.x2 - self.hpadding
            if w.vexpand:
                w.y2 = self.y2 - self.vpadding
                w.height = w.y2 - w.y
            w.y = self.y + self.vpadding + offset
            offset += w.height
            w.y2 = w.y + w.height
            w.layout_width = self.layout_width
            w.layout_height = self.layout_height
            w.color_clear = self.color_clear

    def render(self, ctx):
        if self.visible.once(self):
            ctx.rectangle((self.x, self.y, self.x2, self.y2), fill=self.color_clear)
            if self.color_background:
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
            if isinstance(w, Guides) or w.visible.value and w.x <= x <= w.x2 and w.y <= y <= w.y2:
                w.tap(x - w.x, y - w.y)
                self.drag_widget = w
                break

    def doubletap(self, x, y):
        x += self.x
        y += self.y
        for w in self.widgets:
            if w.visible.value and w.x <= x <= w.x2 and w.y <= y <= w.y2:
                w.doubletap(x - w.x, y - w.y)
                break

    def release(self, x, y):
        if self.drag_widget is not None:
            self.drag_widget.release(x, y)
            self.drag_widget = None

    def move(self, x, y):
        if self.drag_widget is not None:
            self.drag_widget.move(x, y)


class Layout:
    TOPLEFT = 0
    TOPMIDDLE = 1
    TOPRIGHT = 2
    BOTTOMLEFT = 3
    BOTTOMMIDDLE = 4
    BOTTOMRIGHT = 5
    MIDDLE = 6

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.background = background
        self.buf = Image.new("RGBA", (self.width, self.height), self.background)
        self.on_double_tap_empty = None
        self.page_state = None
        self.dirty = True
        self.drag_widget = None

        self.widgets = {}
        for i in range(7):
            self.widgets[i] = []

    def add_button(self, attach, width, text, state, handler, state_cmp=None):
        self.widgets[attach].append(Button(width, text, state, handler, state_cmp=state_cmp))

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
                w.color_clear = self.background
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
        if self.dirty:
            ctx.has_changed = True
            self.dirty = False
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
                    self.drag_widget = w
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

    def release(self, x, y):
        if self.drag_widget is not None:
            self.drag_widget.release(x, y)
            self.drag_widget = None

    def move(self, x, y):
        if self.drag_widget is not None:
            self.drag_widget.move(x, y)


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
        x = config.monitor.touchscreen_res[0] - x
    if flip_y:
        y = config.monitor.touchscreen_res[1] - y
    x = x / config.monitor.touchscreen_res[0] * config.monitor.mode[0]
    y = y / config.monitor.touchscreen_res[1] * config.monitor.mode[1]
    return x, y


def _input_thread(path, queue, config):
    device = evdev.InputDevice(path)
    last_x = 0
    last_y = 0
    last_tap_x = 0
    last_tap_y = 0
    last_t = time.monotonic()
    for event in device.read_loop():
        # print(evdev.categorize(event))
        if event.type == evdev.ecodes.EV_ABS:
            if event.code == evdev.ecodes.ABS_MT_POSITION_X:
                last_x = event.value
                pos = _touch_transform(config, last_x, last_y)
                queue.put(MoveEvent(pos[0], pos[1]))
            elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                last_y = event.value
        if event.type == evdev.ecodes.EV_KEY and evdev.ecodes.BTN_TOUCH:
            pos = _touch_transform(config, last_x, last_y)
            if event.value == 1:
                # Touch down
                time_since_last = time.monotonic() - last_t
                dist = abs(pos[0] - last_tap_x) + abs(pos[1] - last_tap_y)
                if time_since_last < 0.3 and dist < 40:
                    queue.put(DoubleTapEvent(pos[0], pos[1]))
                else:
                    queue.put(TapEvent(pos[0], pos[1]))
                    last_t = time.monotonic()
                last_tap_x = pos[0]
                last_tap_y = pos[1]
            else:
                # Touch up
                queue.put(ReleaseEvent(pos[0], pos[1]))


def HandleInputs(input_queue, config):
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        print(device.path, device.name, device.phys)
        t = threading.Thread(target=_input_thread, args=(device.path, input_queue, config))
        t.daemon = True
        t.start()
