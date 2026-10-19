from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
try:
    from kivy.uix.codeinput import CodeInput
    from pygments.lexers import PythonLexer
    CODE_HIGHLIGHTING = True
except Exception:
    CodeInput = None
    PythonLexer = None
    CODE_HIGHLIGHTING = False
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle, Ellipse
from PIL import Image
from PIL import ImageOps
from PIL import ImageEnhance
from PIL import ImageFilter
from PIL import ImageChops
from PIL import ImageStat
import subprocess
import os
import threading
import re
import json
import time
import urllib.request
import urllib.error
import http.server
import socketserver
from functools import partial
import ast
import sys
import io
import base64
import math
import glob
import shutil
from contextlib import redirect_stdout, redirect_stderr
if platform not in ('android', 'ios'):
    Window.size = (1180, 780)
    Window.minimum_width = 620
    Window.minimum_height = 460
LLAMA_SERVER = 'C:\\Users\\rutup\\AppData\\Local\\Microsoft\\WinGet\\Packages\\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\\llama-server.exe'
LLAMA_CLI = LLAMA_SERVER.replace('llama-server.exe', 'llama-cli.exe')
MODEL = 'Qwen/Qwen3-VL-2B-Instruct-GGUF:Q4_K_M'
APP_DIR = os.path.dirname(os.path.abspath(__file__))

def writable_dir():
    app = App.get_running_app()
    if platform in ('android', 'ios') and app is not None:
        path = app.user_data_dir
        os.makedirs(path, exist_ok=True)
        return path
    return APP_DIR

def find_llama_cli():
    """Find llama-cli on Windows even if WinGet's package path changed."""
    candidates = [LLAMA_CLI, shutil.which("llama-cli"), shutil.which("llama-cli.exe")]
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates.extend(glob.glob(os.path.join(
            local_app_data, "Microsoft", "WinGet", "Packages",
            "ggml.llamacpp*", "llama-cli.exe"
        )))
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None
QWEN_URL = 'http://127.0.0.1:8080'
IMAGE_URL = 'http://127.0.0.1:8765/selected_code_processed.png'

class ImageHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

class Panel(BoxLayout):

    def __init__(self, bg_color=(1, 1, 1, 1), radius=18, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self.update_background, size=self.update_background)

    def update_background(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

class StatusChip(Label):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = (0.7, 1, 0.8, 1)
        self.font_size = '12sp'
        with self.canvas.before:
            Color(0.07, 0.25, 0.19, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self.update_background, size=self.update_background)

    def update_background(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

class HamburgerButton(Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0.34, 0.31, 0.88, 1)
        with self.canvas.after:
            Color(1, 1, 1, 1)
            self.line1 = Line(points=[], width=2)
            self.line2 = Line(points=[], width=2)
            self.line3 = Line(points=[], width=2)
        self.bind(pos=self.update_lines, size=self.update_lines)

    def update_lines(self, *args):
        x1 = self.x + self.width * 0.3
        x2 = self.x + self.width * 0.7
        y1 = self.y + self.height * 0.68
        y2 = self.y + self.height * 0.5
        y3 = self.y + self.height * 0.32
        self.line1.points = [x1, y1, x2, y1]
        self.line2.points = [x1, y2, x2, y2]
        self.line3.points = [x1, y3, x2, y3]

class CloseButton(Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0.12, 0.16, 0.25, 1)
        with self.canvas.after:
            Color(1, 1, 1, 1)
            self.line1 = Line(points=[], width=2)
            self.line2 = Line(points=[], width=2)
        self.bind(pos=self.update_lines, size=self.update_lines)

    def update_lines(self, *args):
        self.line1.points = [self.x + self.width * 0.3, self.y + self.height * 0.3, self.x + self.width * 0.7, self.y + self.height * 0.7]
        self.line2.points = [self.x + self.width * 0.7, self.y + self.height * 0.3, self.x + self.width * 0.3, self.y + self.height * 0.7]

class MobileButton(Button):
    def __init__(self, bg_color=(0.12, 0.16, 0.24, 1), fg_color=(1, 1, 1, 1), radius=10, hint="", **kwargs):
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.radius = radius
        self.hint = hint
        self._is_hovered = False
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_down', '')
        kwargs.setdefault('background_color', (0, 0, 0, 0))
        kwargs.setdefault('color', fg_color)
        super().__init__(**kwargs)
        with self.canvas.before:
            self.shape_color = Color(*self.bg_color)
            self.shape = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius)])
        with self.canvas.after:
            self.active_color = Color(0.62, 0.79, 1, 0)
            self.active_border = Line(points=[], dash_length=dp(4), dash_offset=dp(2), width=dp(1.2))
        self.bind(pos=self._update_shape, size=self._update_shape, state=self._update_state)
        Window.bind(mouse_pos=self._on_mouse_pos)

    def _update_shape(self, *args):
        self.shape.pos = self.pos
        self.shape.size = self.size
        x1, y1 = self.x + dp(3), self.y + dp(3)
        x2, y2 = self.right - dp(3), self.top - dp(3)
        self.active_border.points = [x1, y1, x2, y1, x2, y2, x1, y2, x1, y1]

    def _update_state(self, *args):
        if self.state == 'down':
            self.shape_color.rgba = tuple(min(1, c * 1.16) for c in self.bg_color[:3]) + (self.bg_color[3],)
        else:
            self.shape_color.rgba = self.bg_color

    def set_active(self, value):
        self.active_color.a = 1 if value else 0

    def _on_mouse_pos(self, window, pos):
        if not self.hint or not self.get_root_window():
            return
        if self.opacity <= 0.05 or self.disabled:
            if self._is_hovered:
                self._is_hovered = False
                app = App.get_running_app()
                if app is not None and hasattr(app, 'hide_ribbon_for'):
                    app.hide_ribbon_for(self)
            return
        local_x, local_y = self.to_widget(pos[0], pos[1])
        inside = 0 <= local_x <= self.width and 0 <= local_y <= self.height
        if inside and not self._is_hovered:
            self._is_hovered = True
            app = App.get_running_app()
            if app is not None and hasattr(app, 'show_ribbon'):
                app.show_ribbon(self.hint, self, transient=False)
        elif not inside and self._is_hovered:
            self._is_hovered = False
            app = App.get_running_app()
            if app is not None and hasattr(app, 'hide_ribbon_for'):
                app.hide_ribbon_for(self)

    def on_touch_down(self, touch):
        if self.opacity > 0.05 and not self.disabled and self.collide_point(*touch.pos) and self.hint:
            app = App.get_running_app()
            if app is not None and hasattr(app, 'show_ribbon'):
                app.show_ribbon(self.hint, self, transient=True)
        return super().on_touch_down(touch)

    def on_parent(self, widget, parent):
        try:
            if parent is None:
                Window.unbind(mouse_pos=self._on_mouse_pos)
            else:
                Window.unbind(mouse_pos=self._on_mouse_pos)
                Window.bind(mouse_pos=self._on_mouse_pos)
        except Exception:
            pass

class IconToolButton(MobileButton):
    """Crisp, simple neon-accent line icons drawn with Kivy primitives."""

    ICON_COLORS = {
        "pen": (0.22, 0.88, 1.0, 1),
        "select": (0.30, 0.63, 1.0, 1),
        "erase": (1.0, 0.34, 0.62, 1),
        "capture": (0.22, 0.91, 0.78, 1),
        "read": (0.72, 0.52, 1.0, 1),
        "run": (0.27, 0.94, 0.57, 1),
        "clear": (1.0, 0.49, 0.40, 1),
        "undo": (0.43, 0.75, 1.0, 1),
        "redo": (0.43, 0.75, 1.0, 1),
    }

    def __init__(self, icon_name, **kwargs):
        self.icon_name = icon_name
        kwargs["text"] = ""
        kwargs.setdefault("size_hint", (1, None))
        kwargs.setdefault("height", dp(38))
        kwargs.setdefault("radius", 10)
        super().__init__(**kwargs)
        accent = self.ICON_COLORS.get(icon_name, (0.36, 0.78, 1, 1))
        # Subtle neon halo behind a clean, single-weight outline.
        with self.canvas.after:
            self.glow_color = Color(accent[0], accent[1], accent[2], 0.13)
            self.glow_lines = [Line(points=[], width=dp(4.1)) for _ in range(10)]
            self.icon_color = Color(*accent)
            self.icon_lines = [Line(points=[], width=dp(2.15)) for _ in range(10)]
            self.icon_circle = Line(circle=(0, 0, dp(0.1)), width=dp(2.15))
        self.bind(pos=self.update_icon, size=self.update_icon)
        self.update_icon()

    def update_icon(self, *args):
        cx, cy = self.center
        s = max(dp(6), min(self.width, self.height, dp(44)) * 0.29)
        lines = self.icon_lines
        for line in lines:
            line.points = []
            line.dash_length = 0
            line.dash_offset = 0
            line.width = dp(2.15)
        self.icon_circle.circle = (cx, cy, dp(0.1))

        if self.icon_name == "pen":
            # Pencil body, end cap, and nib.
            lines[0].points = [cx-s*0.58, cy-s*0.42, cx+s*0.35, cy+s*0.52, cx+s*0.60, cy+s*0.28, cx-s*0.33, cy-s*0.65, cx-s*0.58, cy-s*0.42]
            lines[1].points = [cx-s*0.58, cy-s*0.42, cx-s*0.76, cy-s*0.82, cx-s*0.33, cy-s*0.65]
            lines[2].points = [cx-s*0.28, cy-s*0.60, cx+s*0.43, cy+s*0.11]
        elif self.icon_name == "select":
            # Four crop brackets; selection region itself is dotted on canvas.
            lines[0].points = [cx-s, cy+s*0.42, cx-s, cy+s, cx-s*0.42, cy+s]
            lines[1].points = [cx+s*0.42, cy+s, cx+s, cy+s, cx+s, cy+s*0.42]
            lines[2].points = [cx-s, cy-s*0.42, cx-s, cy-s, cx-s*0.42, cy-s]
            lines[3].points = [cx+s*0.42, cy-s, cx+s, cy-s, cx+s, cy-s*0.42]
        elif self.icon_name == "erase":
            # Tilted eraser with a clear split line.
            lines[0].points = [cx-s*0.78, cy-s*0.12, cx-s*0.05, cy+s*0.67, cx+s*0.77, cy-s*0.20, cx+s*0.09, cy-s*0.77, cx-s*0.78, cy-s*0.12]
            lines[1].points = [cx-s*0.31, cy+s*0.16, cx+s*0.34, cy-s*0.40]
            lines[2].points = [cx-s*0.12, cy-s*0.54, cx+s*0.56, cy+s*0.03]
        elif self.icon_name == "capture":
            # Capture frame / crop corners.
            lines[0].points = [cx-s, cy+s*0.48, cx-s, cy+s, cx-s*0.48, cy+s]
            lines[1].points = [cx+s*0.48, cy+s, cx+s, cy+s, cx+s, cy+s*0.48]
            lines[2].points = [cx-s, cy-s*0.48, cx-s, cy-s, cx-s*0.48, cy-s]
            lines[3].points = [cx+s*0.48, cy-s, cx+s, cy-s, cx+s, cy-s*0.48]
            lines[4].points = [cx-s*0.38, cy, cx-s*0.12, cy, cx-s*0.12, cy+s*0.24]
        elif self.icon_name == "read":
            # Page with folded corner and text lines: clearer than a magnifier.
            lines[0].points = [cx-s*0.62, cy-s*0.78, cx+s*0.22, cy-s*0.78, cx+s*0.62, cy-s*0.38, cx+s*0.62, cy+s*0.78, cx-s*0.62, cy+s*0.78, cx-s*0.62, cy-s*0.78]
            lines[1].points = [cx+s*0.20, cy-s*0.76, cx+s*0.20, cy-s*0.35, cx+s*0.60, cy-s*0.35]
            lines[2].points = [cx-s*0.36, cy+s*0.25, cx+s*0.34, cy+s*0.25]
            lines[3].points = [cx-s*0.36, cy-s*0.02, cx+s*0.24, cy-s*0.02]
            lines[4].points = [cx-s*0.36, cy-s*0.29, cx+s*0.06, cy-s*0.29]
        elif self.icon_name == "run":
            lines[0].points = [cx-s*0.48, cy-s*0.70, cx+s*0.65, cy, cx-s*0.48, cy+s*0.70, cx-s*0.48, cy-s*0.70]
        elif self.icon_name == "clear":
            # Familiar trash bin silhouette.
            lines[0].points = [cx-s*0.58, cy+s*0.53, cx+s*0.58, cy+s*0.53]
            lines[1].points = [cx-s*0.25, cy+s*0.74, cx+s*0.25, cy+s*0.74]
            lines[2].points = [cx-s*0.47, cy+s*0.45, cx-s*0.36, cy-s*0.72, cx+s*0.36, cy-s*0.72, cx+s*0.47, cy+s*0.45]
            lines[3].points = [cx-s*0.15, cy+s*0.20, cx-s*0.15, cy-s*0.47]
            lines[4].points = [cx+s*0.15, cy+s*0.20, cx+s*0.15, cy-s*0.47]
        elif self.icon_name in ("undo", "redo"):
            # Smooth-looking arc plus two arrow-head strokes.
            direction = -1 if self.icon_name == "undo" else 1
            points = []
            for i in range(9):
                angle = math.radians(45 + i * (235 / 8))
                points.extend([
                    cx + direction * s * 0.60 * math.cos(angle),
                    cy + s * 0.60 * math.sin(angle)
                ])
            lines[0].points = points
            ex, ey = points[-2], points[-1]
            lines[1].points = [ex, ey, ex - direction*s*0.34, ey+s*0.12]
            lines[2].points = [ex, ey, ex - direction*s*0.10, ey+s*0.35]

        for glow, core in zip(self.glow_lines, lines):
            glow.points = list(core.points)
            glow.dash_length = core.dash_length
            glow.dash_offset = core.dash_offset
        # Circle is currently unused by these icons; keep it valid for Kivy.
        self.glow_color.a = 0.13


class ColorDot(Widget):

    def __init__(self, color_value, callback, **kwargs):
        super().__init__(**kwargs)
        self.color_value = color_value
        self.callback = callback
        with self.canvas:
            self.dot_color = Color(*self.color_value)
            self.dot = Ellipse(pos=self.pos, size=self.size)
            self.ring_color = Color(0.34, 0.31, 0.88, 0)
            self.ring = Line(circle=(self.center_x, self.center_y, dp(13)), width=3)
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        diameter = max(dp(12), min(self.width, self.height) - dp(10))
        self.dot.size = (diameter, diameter)
        self.dot.pos = (self.center_x - diameter / 2, self.center_y - diameter / 2)
        self.ring.circle = (self.center_x, self.center_y, diameter / 2 + dp(3))

    def set_selected(self, value):
        if value:
            self.ring_color.a = 1
        else:
            self.ring_color.a = 0

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.callback(self.color_value)
            return True
        return super().on_touch_down(touch)


class RibbonHint(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault('color', (0.94, 0.97, 1, 1))
        kwargs.setdefault('font_size', '10sp')
        kwargs.setdefault('bold', True)
        kwargs.setdefault('halign', 'center')
        kwargs.setdefault('valign', 'middle')
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.12, 0.17, 0.27, 0.98)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(9)])
            Color(0.35, 0.52, 0.92, 0.95)
            self.edge = Line(points=[], width=dp(1))
        self.bind(pos=self.update_bg, size=self.update_bg)
        self.update_bg()

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.edge.points = [self.x + dp(5), self.y + dp(2), self.right - dp(5), self.y + dp(2)]
        self.text_size = (max(0, self.width - dp(12)), self.height)

class CanvasArea(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0.045, 0.055, 0.075, 1)
        self.mode = 'pen'
        self.pen_color = (0.94, 0.96, 1, 1)
        self.start_x = 0
        self.start_y = 0
        self.selection = None
        self.selected_box = None
        self.lines = []
        self.redo_lines = []
        self.active_touch_ids = set()
        self.cancelled_touch_ids = set()
        self.active_strokes = {}
        self.multitouch_active = False
        with self.canvas.before:
            self.bg_instruction = Color(*self.background_color)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_background, size=self.update_background)

    def update_background(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def set_pen_color(self, color):
        self.pen_color = color
        self.mode = 'pen'

    def set_select_mode(self):
        self.mode = 'select'

    def set_eraser_mode(self):
        self.mode = 'eraser'

    def _remove_instruction(self, instruction):
        if instruction is not None:
            try:
                self.canvas.remove(instruction)
            except Exception:
                pass

    def _cancel_for_multitouch(self):
        self.multitouch_active = True
        self.cancelled_touch_ids.update(self.active_touch_ids)
        for color_instruction, line_instruction in list(self.active_strokes.values()):
            self._remove_instruction(color_instruction)
            self._remove_instruction(line_instruction)
        self.active_strokes.clear()
        if self.selection is not None:
            self._remove_instruction(self.selection)
            self.selection = None
        self.selected_box = None
        self.mode = 'pen'

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        touch_id = touch.uid
        self.active_touch_ids.add(touch_id)
        if len(self.active_touch_ids) > 1 or self.multitouch_active:
            self._cancel_for_multitouch()
            self.cancelled_touch_ids.add(touch_id)
            touch.grab(self)
            return True

        local_x, local_y = self.to_widget(touch.x, touch.y)
        if self.mode == 'select':
            if self.selection is not None:
                self._remove_instruction(self.selection)
                self.selection = None
            self.selected_box = None
            self.start_x = local_x
            self.start_y = local_y
            touch.grab(self)
            with self.canvas:
                Color(0.25, 0.83, 1.0, 1)
                self.selection = Line(
                    points=[local_x, local_y, local_x, local_y],
                    dash_length=dp(5),
                    dash_offset=dp(2.5),
                    width=dp(1.7)
                )
            return True

        draw_color = self.background_color if self.mode == 'eraser' else self.pen_color
        touch.grab(self)
        with self.canvas:
            color_instruction = Color(*draw_color)
            line_instruction = Line(points=[local_x, local_y], width=dp(3.0))
        pair = (color_instruction, line_instruction)
        touch.ud['line'] = pair
        self.active_strokes[touch_id] = pair
        self.redo_lines.clear()
        return True

    def on_touch_move(self, touch):
        touch_id = touch.uid
        if touch_id in self.cancelled_touch_ids or self.multitouch_active:
            return True
        if touch.grab_current is self:
            local_x, local_y = self.to_widget(touch.x, touch.y)
            if self.mode == 'select' and self.selection:
                x1, y1 = self.start_x, self.start_y
                x2, y2 = local_x, local_y
                self.selection.points = [x1, y1, x2, y1, x2, y2, x1, y2, x1, y1]
                self.selected_box = (
                    min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1)
                )
                return True
            if 'line' in touch.ud:
                color_instruction, line_instruction = touch.ud['line']
                line_instruction.points += [local_x, local_y]
                return True
        return False

    def on_touch_up(self, touch):
        touch_id = touch.uid
        was_grabbed = touch.grab_current is self
        if was_grabbed:
            touch.ungrab(self)

        if touch_id in self.cancelled_touch_ids or self.multitouch_active:
            self.active_touch_ids.discard(touch_id)
            self.cancelled_touch_ids.discard(touch_id)
            self.active_strokes.pop(touch_id, None)
            if not self.active_touch_ids:
                self.multitouch_active = False
                self.cancelled_touch_ids.clear()
            return True

        if not was_grabbed:
            self.active_touch_ids.discard(touch_id)
            return False

        self.active_touch_ids.discard(touch_id)
        if self.mode == 'select':
            local_x, local_y = self.to_widget(touch.x, touch.y)
            box = (
                min(self.start_x, local_x), min(self.start_y, local_y),
                abs(local_x - self.start_x), abs(local_y - self.start_y)
            )
            if box[2] >= dp(4) and box[3] >= dp(4):
                self.selected_box = box
            else:
                self.selected_box = None
                self._remove_instruction(self.selection)
                self.selection = None
            self.mode = 'pen'
            app = App.get_running_app()
            if app is not None and hasattr(app, 'selection_finished'):
                app.selection_finished(self.selected_box)
            return True

        if 'line' in touch.ud:
            self.lines.append(touch.ud['line'])
            self.active_strokes.pop(touch_id, None)
        return True

    def undo(self):
        if not self.lines:
            return
        item = self.lines.pop()
        color_instruction, line_instruction = item
        self.canvas.remove(color_instruction)
        self.canvas.remove(line_instruction)
        self.redo_lines.append(item)

    def redo(self):
        if not self.redo_lines:
            return
        item = self.redo_lines.pop()
        color_instruction, line_instruction = item
        self.canvas.add(color_instruction)
        self.canvas.add(line_instruction)
        self.lines.append(item)

    def capture_selected(self):
        self.last_capture_error = ''
        # Prefer the stored bounds; recover from the visible rectangle if a
        # touch-up event did not persist them (common with touch/trackpad input).
        if self.selected_box is None and self.selection is not None:
            try:
                points = list(self.selection.points)
                xs = points[0::2]
                ys = points[1::2]
                if len(xs) >= 4 and len(ys) >= 4:
                    box = (min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys))
                    if box[2] >= dp(4) and box[3] >= dp(4):
                        self.selected_box = box
            except Exception:
                pass
        if self.selected_box is None:
            return False

        x0, y0, w0, h0 = self.selected_box
        if w0 < dp(4) or h0 < dp(4):
            return False

        directory = writable_dir()
        os.makedirs(directory, exist_ok=True)
        temp_path = os.path.join(directory, 'canvas_temp.png')
        selected_path = os.path.join(directory, 'selected_code.png')
        selection_instruction = self.selection
        try:
            # Omit the dotted outline from the recognition image, but restore it
            # afterwards so users can see which region was captured.
            if selection_instruction is not None:
                try:
                    self.canvas.remove(selection_instruction)
                except Exception:
                    selection_instruction = None
            self.export_to_png(temp_path)
            with Image.open(temp_path) as original:
                image = original.convert('RGB')
            sx = image.width / max(1, self.width)
            sy = image.height / max(1, self.height)
            x = int(x0 * sx)
            y = int(y0 * sy)
            width = int(w0 * sx)
            height = int(h0 * sy)
            pad_x = max(8, int(dp(8) * sx))
            pad_y = max(8, int(dp(8) * sy))
            left = max(0, x - pad_x)
            right = min(image.width, x + width + pad_x)
            top = max(0, image.height - (y + height) - pad_y)
            bottom = min(image.height, image.height - y + pad_y)
            if right <= left or bottom <= top:
                image.close()
                return False
            cropped = image.crop((left, top, right, bottom))
            cropped.save(selected_path)
            cropped.close()
            image.close()
            return os.path.exists(selected_path) and os.path.getsize(selected_path) > 100
        except Exception as error:
            app = App.get_running_app()
            if app is not None:
                app.last_capture_error = str(error)
            return False
        finally:
            # Do not clear selected_box here: it remains valid until the user
            # starts another selection or clears the canvas.
            if selection_instruction is not None and self.selection is not None:
                try:
                    self.canvas.add(selection_instruction)
                except Exception:
                    pass

    def clear_canvas(self):
        for color_instruction, line_instruction in list(self.lines):
            self._remove_instruction(color_instruction)
            self._remove_instruction(line_instruction)
        self.lines.clear()
        self.redo_lines.clear()
        self.active_strokes.clear()
        self.active_touch_ids.clear()
        self.cancelled_touch_ids.clear()
        self.multitouch_active = False
        self._remove_instruction(self.selection)
        self.selection = None
        self.selected_box = None
        self.mode = 'pen'
        # Preserve the background instruction so Clear never turns the canvas transparent.
        self.bg.pos = self.pos
        self.bg.size = self.size

class CodeCanvasApp(App):

    def build(self):
        self.server_process = None
        self.image_server = None
        self.server_lock = threading.Lock()
        self.server_starting = False
        self.recognition_in_progress = False
        self.run_after_recognition = False
        self.drawer_open = False
        self.actions_open = False
        self.ribbon_source = None
        self.ribbon_event = None
        self.history = []
        self.current_file_path = os.path.join(writable_dir(), "untitled.py")
        self.qwen_url = QWEN_URL if platform not in ("android", "ios") else ""
        self.connection_message_text = (
            "Connect this device to the laptop's Qwen server to enable handwriting recognition."
        )
        try:
            with open(os.path.join(writable_dir(), "codecanvas_settings.json"), "r", encoding="utf-8") as stream:
                saved = json.load(stream)
            saved_url = str(saved.get("qwen_url", "")).strip().rstrip("/")
            if saved_url:
                self.qwen_url = saved_url
        except Exception:
            pass

        self.status = Label(
            text="READY", color=(0.37, 0.91, 0.70, 1),
            font_size="10sp", size_hint_x=None, width=dp(66),
            halign="right", valign="middle", bold=True
        )
        self.status.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        root = FloatLayout()
        self.root_layout = root
        with root.canvas.before:
            Color(0.018, 0.024, 0.038, 1)
            self.root_background = Rectangle(pos=root.pos, size=root.size)

        def update_root_background(widget, *args):
            self.root_background.pos = widget.pos
            self.root_background.size = widget.size
        root.bind(pos=update_root_background, size=update_root_background)

        self.main_layout = BoxLayout(
            orientation="vertical", padding=[dp(6), dp(5), dp(6), dp(5)],
            spacing=dp(5), size_hint=(1, 1), pos=(0, 0)
        )

        self.header = Panel(
            orientation="horizontal", size_hint_y=None, height=dp(44),
            padding=[dp(5), dp(3)], spacing=dp(7),
            bg_color=(0.045, 0.058, 0.087, 1), radius=13
        )
        menu_button = HamburgerButton(size_hint=(None, None), size=(dp(36), dp(36)))
        menu_button.background_color = (0.12, 0.16, 0.24, 1)
        menu_button.bind(on_release=lambda *_: self.toggle_drawer())

        logo = Label(
            text="<>", color=(0.36, 0.68, 1, 1), bold=True,
            font_size="18sp", size_hint_x=None, width=dp(27),
            valign="middle", halign="center"
        )
        title = Label(
            text="Code Canvas", color=(0.94, 0.96, 1, 1),
            font_size="16sp", bold=True, halign="left", valign="middle"
        )
        title.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.connect_button = MobileButton(
            text="LINK", bg_color=(0.10, 0.14, 0.21, 1),
            fg_color=(0.55, 0.86, 1, 1), radius=9,
            size_hint=(None, None), size=(dp(48), dp(34)),
            font_size="9sp", bold=True,
            hint="Connect to the laptop recognition engine; optional on desktop"
        )
        self.connect_button.bind(on_release=lambda *_: self.open_drawer("connect"))
        self.header.add_widget(menu_button)
        self.header.add_widget(logo)
        self.header.add_widget(title)
        self.header.add_widget(self.status)
        self.header.add_widget(self.connect_button)

        # A single left-side icon rail is used on phones, tablets and desktops.
        # No large action bar sits below the canvas, leaving writing space free.
        self.workspace = BoxLayout(orientation="horizontal", spacing=dp(5))
        self.canvas_area = CanvasArea()
        self.canvas_panel = Panel(
            orientation="vertical", padding=dp(2),
            bg_color=(0.075, 0.09, 0.125, 1), radius=14
        )
        self.canvas_panel.add_widget(self.canvas_area)

        self.tool_bar = Panel(
            orientation="vertical", size_hint=(None, 1), width=dp(54),
            padding=[dp(3), dp(5)], spacing=dp(4),
            bg_color=(0.045, 0.058, 0.087, 1), radius=13
        )

        self.colors = [
            (0.94, 0.96, 1, 1),
            (0.18, 0.49, 1, 1),
            (1, 0.28, 0.43, 1),
            (0.18, 0.82, 0.58, 1),
            (0.65, 0.43, 1, 1),
            (1, 0.72, 0.22, 1),
        ]
        self.color_dots = []
        self.palette_popup = None

        self.pen_button = self.make_icon_tool("pen", "Pen: write on the canvas", (0.12, 0.17, 0.27, 1))
        self.select_action = self.make_icon_tool("select", "Select: draw a dotted box around the code", (0.12, 0.17, 0.27, 1))
        self.eraser_button = self.make_icon_tool("erase", "Eraser: erase strokes by drawing over them", (0.12, 0.17, 0.27, 1))
        self.color_button = MobileButton(
            text="COLOR", bg_color=(0.12, 0.17, 0.27, 1), fg_color=(0.94, 0.97, 1, 1),
            radius=9, size_hint=(1, None), height=dp(34), font_size="7.5sp", bold=True,
            hint="Choose ink colour"
        )
        self.color_button.bind(on_release=self.show_palette)
        self.capture_btn = self.make_icon_tool("capture", "Capture: save the selected writing area", (0.07, 0.31, 0.43, 1))
        self.recognize_btn = self.make_icon_tool("read", "Read: convert captured handwriting to Python", (0.25, 0.17, 0.48, 1))
        self.run_btn = self.make_icon_tool("run", "Run: execute the Python code in the editor", (0.05, 0.36, 0.24, 1))
        self.clear_btn = self.make_icon_tool("clear", "Clear: erase the canvas and editor", (0.14, 0.17, 0.23, 1))
        self.undo_button = self.make_icon_tool("undo", "Undo the last pen stroke", (0.10, 0.14, 0.21, 1))
        self.redo_button = self.make_icon_tool("redo", "Redo the last undone stroke", (0.10, 0.14, 0.21, 1))
        self.select_button = self.select_action

        self.pen_button.bind(on_release=lambda *_: self.activate_pen())
        self.select_action.bind(on_release=lambda *_: self.activate_select())
        self.eraser_button.bind(on_release=lambda *_: self.activate_eraser())
        self.undo_button.bind(on_release=lambda *_: self.canvas_area.undo())
        self.redo_button.bind(on_release=lambda *_: self.canvas_area.redo())
        self.capture_btn.bind(on_release=self.capture_code)
        self.recognize_btn.bind(on_release=self.recognize_code)
        self.run_btn.bind(on_release=self.run_code)
        self.clear_btn.bind(on_release=self.clear_code)

        self.populate_toolbar()
        self.workspace.add_widget(self.tool_bar)
        self.workspace.add_widget(self.canvas_panel)
        self.main_layout.add_widget(self.header)
        self.main_layout.add_widget(self.workspace)
        root.add_widget(self.main_layout)

        self.create_drawer(root)
        self.ribbon = RibbonHint(text="", size_hint=(None, None), size=(dp(100), dp(28)), opacity=0, pos=(0, 0))
        root.add_widget(self.ribbon)
        root.bind(size=self.adapt_layout)
        Clock.schedule_once(self.adapt_layout, 0)
        self.choose_color(self.colors[0])
        self.pen_button.set_active(True)
        return root

    def make_icon_tool(self, icon_name, hint, bg_color=(0.10, 0.14, 0.21, 1)):
        # Keep toolbar controls clearly labelled; avoid ambiguous pictograms.
        labels = {
            "pen": "PEN", "select": "SELECT", "erase": "ERASE",
            "capture": "CAPTURE", "read": "READ", "run": "RUN",
            "clear": "CLEAR", "undo": "UNDO", "redo": "REDO"
        }
        label = labels.get(icon_name, icon_name.upper())
        return MobileButton(
            text=label,
            bg_color=bg_color,
            fg_color=(0.94, 0.97, 1, 1),
            radius=9,
            size_hint=(1, None),
            height=dp(34),
            font_size="7.5sp",
            bold=True,
            hint=hint
        )

    def make_tool(self, text, width=dp(44), bg_color=(0.10, 0.14, 0.21, 1), hint=""):
        return MobileButton(
            text=text, bg_color=bg_color, fg_color=(0.91, 0.94, 1, 1),
            radius=9, size_hint=(None, 1), width=width,
            font_size="9sp", bold=True, hint=hint
        )

    def make_action(self, text, color, hint=""):
        return MobileButton(
            text=text, bg_color=color, fg_color=(1, 1, 1, 1),
            radius=9, font_size="8sp", bold=True,
            size_hint_x=1, hint=hint
        )

    def populate_toolbar(self):
        self.tool_bar.clear_widgets()
        # Selection captures and reads automatically, so CAPTURE and READ do
        # not occupy permanent toolbar space. RUN executes the recognized/editable code.
        controls = (
            self.pen_button,
            self.select_action,
            self.eraser_button,
            self.color_button,
            self.run_btn,
            self.clear_btn,
        )
        for index, button in enumerate(controls):
            button.size_hint = (1, None)
            button.height = dp(31)
            self.tool_bar.add_widget(button)
            if index in (2, 3):
                self.tool_bar.add_widget(Widget(size_hint_y=None, height=dp(5)))
        self.tool_bar.add_widget(Widget(size_hint_y=1))
        for button in (self.undo_button, self.redo_button):
            button.size_hint = (1, None)
            button.height = dp(31)
            self.tool_bar.add_widget(button)

    def adapt_layout(self, *args):
        if not hasattr(self, "workspace") or self.root_layout.width <= 0:
            return
        width = self.root_layout.width
        height = self.root_layout.height
        compact = height < dp(650) or width < dp(360)
        very_short = height < dp(500)
        self.header.height = dp(38 if very_short else (40 if compact else 45))
        self.tool_bar.width = dp(54 if width < dp(360) else (60 if width < dp(410) else (66 if width < dp(760) else 72)))
        self.tool_bar.spacing = dp(2 if very_short else 3)
        self.tool_bar.padding = [dp(3), dp(3 if very_short else 5)]
        button_height = dp(23 if very_short else (27 if compact else (30 if width < dp(410) else 34)))
        for button in (
            self.pen_button, self.select_action, self.eraser_button, self.color_button,
            self.capture_btn, self.recognize_btn, self.run_btn,
            self.clear_btn, self.undo_button, self.redo_button
        ):
            button.height = button_height
        self.resize_drawer()
        if hasattr(self, "ribbon") and self.ribbon.opacity > 0 and self.ribbon_source is not None:
            self.show_ribbon(self.ribbon.text, self.ribbon_source, transient=False)

    def resize_action_ribbon(self, *args):
        self.adapt_layout()

    def toggle_actions(self):
        self.open_actions() if not self.actions_open else self.close_actions()

    def open_actions(self):
        self.actions_open = True

    def close_actions(self):
        self.actions_open = False

    def show_ribbon(self, text, widget, transient=True):
        if not hasattr(self, "ribbon") or not text or widget is None:
            return
        if self.ribbon_event is not None:
            Clock.unschedule(self.ribbon_event)
            self.ribbon_event = None
        self.ribbon_source = widget
        self.ribbon.text = text
        max_width = min(self.root_layout.width - dp(16), dp(250))
        width = min(max_width, max(dp(112), dp(22 + len(text) * 5.3)))
        self.ribbon.size = (width, dp(30))

        # Use a window -> root coordinate conversion, then place the ribbon next
        # to the icon (not at the screen origin). Flip it left on the right side.
        wx, wy = widget.to_window(widget.width, widget.height * 0.5, initial=True)
        rx, ry = self.root_layout.to_widget(wx, wy)
        if widget.center_x < self.root_layout.width * 0.42:
            x = rx + dp(8)
        else:
            x = rx - width - dp(8)
        x = min(max(dp(8), x), self.root_layout.width - width - dp(8))
        y = min(max(dp(8), ry - dp(15)), self.root_layout.height - dp(38))
        self.ribbon.pos = (x, y)
        self.ribbon.opacity = 1
        if transient:
            self.ribbon_event = Clock.schedule_once(
                lambda _dt, source=widget: self.hide_ribbon_for(source), 1.8
            )

    def hide_ribbon_for(self, widget=None):
        if widget is not None and self.ribbon_source is not widget:
            return
        if self.ribbon_event is not None:
            Clock.unschedule(self.ribbon_event)
            self.ribbon_event = None
        if hasattr(self, "ribbon"):
            self.ribbon.opacity = 0
        self.ribbon_source = None

    def create_drawer(self, root):
        self.root_layout = root
        self.drawer_handle = MobileButton(
            text="IDE", bg_color=(0.12, 0.17, 0.26, 0.98),
            fg_color=(0.72, 0.85, 1, 1), radius=9, font_size="8sp", bold=True,
            size_hint=(None, None), size=(dp(32), dp(54)),
            pos_hint={"right": 1, "center_y": 0.5}, hint="Open the code editor and output"
        )
        self.drawer_handle.bind(on_release=lambda *_: self.open_drawer("code"))
        root.add_widget(self.drawer_handle)

        self.drawer = Panel(
            orientation="vertical", size_hint=(None, None), width=0,
            height=max(dp(300), root.height * 0.92), opacity=0,
            pos_hint={"right": 0.985, "center_y": 0.5},
            padding=dp(10), spacing=dp(8),
            bg_color=(0.045, 0.058, 0.087, 1), radius=17
        )
        drawer_header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        drawer_title_box = BoxLayout(orientation="vertical")
        drawer_title = Label(
            text="Workspace", color=(0.95, 0.97, 1, 1),
            font_size="16sp", bold=True, halign="left", valign="middle"
        )
        drawer_title.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        drawer_subtitle = Label(
            text="Edit, run and inspect Python · code drawer", color=(0.58, 0.68, 0.84, 1),
            font_size="9sp", halign="left", valign="middle"
        )
        drawer_subtitle.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        drawer_title_box.add_widget(drawer_title)
        drawer_title_box.add_widget(drawer_subtitle)
        close = CloseButton(size_hint=(None, None), size=(dp(36), dp(36)))
        close.bind(on_release=lambda *_: self.close_drawer())
        drawer_header.add_widget(drawer_title_box)
        drawer_header.add_widget(close)
        self.drawer.add_widget(drawer_header)

        tabs = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        self.code_tab = self.make_tab("CODE")
        self.output_tab = self.make_tab("OUTPUT")
        self.history_tab = self.make_tab("HISTORY")
        self.connect_tab = self.make_tab("CONNECT")
        for tab in (self.code_tab, self.output_tab, self.history_tab, self.connect_tab):
            tabs.add_widget(tab)
        self.code_tab.bind(on_release=lambda *_: self.show_code_tab())
        self.output_tab.bind(on_release=lambda *_: self.show_output_tab())
        self.history_tab.bind(on_release=lambda *_: self.show_history_tab())
        self.connect_tab.bind(on_release=lambda *_: self.show_connect_tab())
        self.drawer.add_widget(tabs)

        self.drawer_content = BoxLayout(orientation="vertical", spacing=dp(8))
        self.drawer.add_widget(self.drawer_content)

        editor_class = CodeInput if CODE_HIGHLIGHTING else TextInput
        editor_options = dict(
            text="", hint_text="Type or edit Python here…", multiline=True,
            auto_indent=True, tab_width=4, font_size="13sp",
            background_color=(0.025, 0.035, 0.055, 1),
            foreground_color=(0.91, 0.94, 1, 1),
            cursor_color=(0.42, 0.66, 1, 1),
            padding=[dp(10), dp(10)],
            write_tab=False
        )
        if CODE_HIGHLIGHTING:
            editor_options["lexer"] = PythonLexer()
            editor_options["style_name"] = "monokai"
        self.code_box = editor_class(**editor_options)
        self.output_box = TextInput(
            text="Program output will appear here.", multiline=True, readonly=True,
            font_size="13sp", background_color=(0.025, 0.035, 0.055, 1),
            foreground_color=(0.62, 0.95, 0.77, 1), padding=[dp(10), dp(10)]
        )
        # Activity bar: intentionally indeterminate (not a fake percentage).
        self.read_progress = ProgressBar(
            max=100, value=0, size_hint_y=None, height=dp(6),
            opacity=1
        )
        self.read_progress_label = Label(
            text="READING HANDWRITING — keep the app open",
            size_hint_y=None, height=dp(20),
            color=(0.32, 0.88, 1, 1), font_size="10sp",
            bold=True, halign="left", valign="middle"
        )
        self.read_progress_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self._read_progress_animation = None
        self.root_layout.add_widget(self.drawer)
        self.root_layout.bind(size=self.resize_drawer)
        self.resize_drawer()
        self.show_code_tab()

    def resize_drawer(self, *args):
        if not hasattr(self, "drawer"):
            return
        root = self.root_layout
        self.drawer.height = max(dp(240), min(root.height - dp(14), root.height * 0.94))
        self.drawer.pos_hint = {"right": 0.985, "center_y": 0.5}
        if self.drawer_open:
            self.drawer.width = min(dp(500), root.width * 0.94)

    def make_tab(self, text):
        return Button(
            text=text, background_normal="", background_down="",
            background_color=(0.10, 0.14, 0.24, 1),
            color=(0.72, 0.78, 0.88, 1), font_size="8sp", bold=True
        )

    def set_active_tab(self, active):
        for tab in [self.code_tab, self.output_tab, self.history_tab, self.connect_tab]:
            tab.background_color = (0.10, 0.14, 0.24, 1)
            tab.color = (0.72, 0.78, 0.88, 1)
        active.background_color = (0.25, 0.31, 0.95, 1)
        active.color = (1, 1, 1, 1)

    def show_code_tab(self):
        self.set_active_tab(self.code_tab)
        self.drawer_content.clear_widgets()
        hint_text = "PYTHON EDITOR  ·  syntax highlighting" if CODE_HIGHLIGHTING else "PYTHON EDITOR  ·  highlighting unavailable"
        title = Label(
            text=hint_text, size_hint_y=None, height=dp(25),
            color=(0.62, 0.73, 0.90, 1), bold=True, font_size="10sp",
            halign="left", valign="middle"
        )
        title.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        actions = BoxLayout(size_hint_y=None, height=dp(39), spacing=dp(5))
        example = self.make_drawer_button("SAMPLE CODE", (0.13, 0.18, 0.29, 1))
        save = self.make_drawer_button("SAVE", (0.13, 0.18, 0.29, 1))
        open_button = self.make_drawer_button("OPEN", (0.13, 0.18, 0.29, 1))
        run = self.make_drawer_button("RUN CODE", (0.04, 0.60, 0.37, 1))
        example.bind(on_release=self.load_example)
        save.bind(on_release=self.save_code_dialog)
        open_button.bind(on_release=self.open_code_dialog)
        run.bind(on_release=self.run_code)
        for button in (example, save, open_button, run):
            actions.add_widget(button)
        self.drawer_content.add_widget(title)
        if self.recognition_in_progress:
            progress_block = BoxLayout(
                orientation="vertical", size_hint_y=None,
                height=dp(36), spacing=dp(2)
            )
            self.drawer_content.add_widget(progress_block)

            for widget in (self.read_progress_label, self.read_progress):
                if widget.parent is not None:
                    widget.parent.remove_widget(widget)

            progress_block.add_widget(self.read_progress_label)
            progress_block.add_widget(self.read_progress)
        self.drawer_content.add_widget(self.code_box)
        self.drawer_content.add_widget(actions)

    def make_drawer_button(self, text, bg):
        return MobileButton(
            text=text, bg_color=bg, fg_color=(0.95, 0.97, 1, 1),
            radius=8, font_size="9sp", bold=True, size_hint_x=1
        )

    def load_example(self, instance=None):
        self.code_box.text = (
            "import math\n\n"
            "radius = 5\n"
            "area = math.pi * radius ** 2\n\n"
            "print(f\"Area: {area:.2f}\")\n"
        )
        self.current_file_path = os.path.join(writable_dir(), "example.py")
        self.status.text = "SAMPLE LOADED"
        self.open_drawer("code")

    def show_output_tab(self):
        self.set_active_tab(self.output_tab)
        self.drawer_content.clear_widgets()
        title = Label(
            text="PROGRAM OUTPUT", size_hint_y=None, height=dp(25),
            color=(0.62, 0.73, 0.90, 1), bold=True, font_size="10sp", halign="left"
        )
        self.drawer_content.add_widget(title)
        self.drawer_content.add_widget(self.output_box)

    def show_history_tab(self):
        self.set_active_tab(self.history_tab)
        self.drawer_content.clear_widgets()
        title = Label(
            text="RECENT RUNS", size_hint_y=None, height=dp(25),
            color=(0.62, 0.73, 0.90, 1), bold=True, font_size="10sp", halign="left"
        )
        history_text = "\n\n".join(self.history) if self.history else "No code history yet."
        self.history_box = TextInput(
            text=history_text, readonly=True, multiline=True, font_size="12sp",
            background_color=(0.025, 0.04, 0.08, 1),
            foreground_color=(0.82, 0.87, 0.96, 1), padding=[dp(10), dp(10)]
        )
        self.drawer_content.add_widget(title)
        self.drawer_content.add_widget(self.history_box)

    def show_connect_tab(self):
        self.set_active_tab(self.connect_tab)
        self.drawer_content.clear_widgets()
        title = Label(
            text="PHONE LINK · OPTIONAL", size_hint_y=None, height=dp(26),
            color=(0.62, 0.73, 0.90, 1), bold=True, font_size="10sp", halign="left"
        )
        detail = Label(
            text="OPTIONAL: only needed for handwriting READ on Android.\nDrawing, editing and RUN do not need this. Desktop READ uses the local model.\nTo read handwriting on your phone: start the Qwen server on this laptop, then enter the laptop's Wi-Fi IPv4 address (http://192.168.x.x:8080) on the phone. Both devices must use the same trusted Wi-Fi.", 
            size_hint_y=None, height=dp(112), color=(0.74, 0.80, 0.91, 1),
            font_size="10sp", halign="left", valign="top"
        )
        detail.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.server_url_input = TextInput(
            text=self.qwen_url, hint_text="http://192.168.1.5:8080",
            multiline=False, size_hint_y=None, height=dp(42), font_size="12sp",
            background_color=(0.025, 0.035, 0.055, 1),
            foreground_color=(0.93, 0.96, 1, 1), cursor_color=(0.42, 0.66, 1, 1),
            padding=[dp(9), dp(10)]
        )
        self.connection_message = Label(
            text=self.connection_message_text, color=(0.70, 0.78, 0.90, 1),
            font_size="10sp", halign="left", valign="top"
        )
        self.connection_message.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(7))
        save = self.make_drawer_button("SAVE + TEST", (0.20, 0.31, 0.82, 1))
        default = self.make_drawer_button("LOCAL DEFAULT", (0.13, 0.18, 0.29, 1))
        save.bind(on_release=self.save_connection)
        default.bind(on_release=self.reset_connection)
        buttons.add_widget(save)
        buttons.add_widget(default)
        self.drawer_content.add_widget(title)
        self.drawer_content.add_widget(detail)
        self.drawer_content.add_widget(self.server_url_input)
        self.drawer_content.add_widget(buttons)
        if platform not in ("android", "ios"):
            start_phone_server = self.make_drawer_button("START QWEN SERVER FOR PHONE", (0.04, 0.46, 0.29, 1))
            start_phone_server.size_hint_y = None
            start_phone_server.height = dp(40)
            start_phone_server.bind(on_release=self.start_server_for_phone)
            self.drawer_content.add_widget(start_phone_server)
        self.drawer_content.add_widget(self.connection_message)

    def start_server_for_phone(self, instance=None):
        if platform in ("android", "ios"):
            self.connection_message.text = "Start this service from the laptop app, not the phone."
            return
        self.connection_message.text = "Starting Qwen server; first startup may take a few minutes..."
        self.status.text = "STARTING"
        if instance is not None:
            instance.disabled = True
        def worker():
            ok = self.start_qwen_server()
            message = ("Qwen server is running. Find this laptop's IPv4 address with ipconfig and enter http://LAPTOP-IP:8080 in the phone app."
                       if ok else "Could not start server. Check that llama-server.exe exists and review the terminal for errors.")
            def finish(_dt):
                self.connection_message_text = message
                if hasattr(self, "connection_message"):
                    self.connection_message.text = message
                self.status.text = "SERVER ON" if ok else "OFFLINE"
                if instance is not None:
                    instance.disabled = False
            Clock.schedule_once(finish)
        threading.Thread(target=worker, daemon=True).start()

    def reset_connection(self, instance=None):
        self.qwen_url = QWEN_URL if platform not in ("android", "ios") else ""
        if hasattr(self, "server_url_input"):
            self.server_url_input.text = self.qwen_url
        self.connection_message_text = "Local default restored."
        if hasattr(self, "connection_message"):
            self.connection_message.text = self.connection_message_text

    def save_connection(self, instance=None):
        url = self.server_url_input.text.strip().rstrip("/")
        if url and not url.startswith(("http://", "https://")):
            self.connection_message.text = "Address must begin with http:// or https://"
            return
        self.qwen_url = url
        try:
            with open(os.path.join(writable_dir(), "codecanvas_settings.json"), "w", encoding="utf-8") as stream:
                json.dump({"qwen_url": self.qwen_url}, stream)
        except Exception as error:
            self.connection_message.text = f"Could not save settings: {error}"
            return
        self.connection_message.text = "Saved. Testing connection..."
        self.status.text = "TESTING"
        threading.Thread(target=self.test_connection_worker, daemon=True).start()

    def test_connection_worker(self):
        ok = self.server_ready()
        message = "Connected to Qwen server." if ok else "No connection. Check the server address, laptop server and firewall."
        Clock.schedule_once(lambda _dt, msg=message: self.connection_test_finished(msg, ok))

    def connection_test_finished(self, message, ok):
        self.connection_message_text = message
        if hasattr(self, "connection_message"):
            self.connection_message.text = message
        self.status.text = "ONLINE" if ok else "OFFLINE"

    def save_code_dialog(self, instance=None):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        filename = TextInput(
            text=os.path.basename(self.current_file_path or "untitled.py"),
            multiline=False, size_hint_y=None, height=dp(42)
        )
        buttons = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        popup = Popup(title="Save Python file", content=content, size_hint=(0.88, 0.42))
        save = self.make_drawer_button("SAVE FILE", (0.04, 0.60, 0.37, 1))
        cancel = self.make_drawer_button("CANCEL", (0.13, 0.18, 0.29, 1))
        def do_save(*_):
            name = os.path.basename(filename.text.strip())
            if not name:
                return
            if not name.lower().endswith(".py"):
                name += ".py"
            path = os.path.join(writable_dir(), name)
            try:
                with open(path, "w", encoding="utf-8") as stream:
                    stream.write(self.code_box.text)
                self.current_file_path = path
                self.status.text = "SAVED"
                popup.dismiss()
            except Exception as error:
                self.output_box.text = f"Could not save file: {error}"
                popup.dismiss()
                self.open_drawer("output")
        save.bind(on_release=do_save)
        cancel.bind(on_release=lambda *_: popup.dismiss())
        buttons.add_widget(save)
        buttons.add_widget(cancel)
        content.add_widget(filename)
        content.add_widget(buttons)
        popup.open()

    def open_code_dialog(self, instance=None):
        content = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        chooser = FileChooserListView(
            path=writable_dir(), filters=["*.py"], dirselect=False,
            multiselect=False
        )
        buttons = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        popup = Popup(title="Open Python file", content=content, size_hint=(0.94, 0.88))
        open_button = self.make_drawer_button("OPEN FILE", (0.20, 0.31, 0.82, 1))
        cancel = self.make_drawer_button("CANCEL", (0.13, 0.18, 0.29, 1))
        def do_open(*_):
            if not chooser.selection:
                return
            path = chooser.selection[0]
            try:
                with open(path, "r", encoding="utf-8") as stream:
                    self.code_box.text = stream.read()
                self.current_file_path = path
                self.status.text = "OPENED"
                popup.dismiss()
                self.open_drawer("code")
            except Exception as error:
                self.output_box.text = f"Could not open file: {error}"
                popup.dismiss()
                self.open_drawer("output")
        open_button.bind(on_release=do_open)
        cancel.bind(on_release=lambda *_: popup.dismiss())
        buttons.add_widget(open_button)
        buttons.add_widget(cancel)
        content.add_widget(chooser)
        content.add_widget(buttons)
        popup.open()

    def toggle_drawer(self):
        if self.drawer_open:
            self.close_drawer()
        else:
            self.open_drawer("code")

    def open_drawer(self, tab="code"):
        if tab == "output":
            self.show_output_tab()
        elif tab == "history":
            self.show_history_tab()
        elif tab == "connect":
            self.show_connect_tab()
        else:
            self.show_code_tab()
        self.drawer_open = True
        self.drawer.disabled = False
        self.drawer_handle.opacity = 0
        self.drawer_handle.disabled = True
        target_width = min(dp(500), self.root_layout.width * 0.94)
        target_height = max(dp(240), min(self.root_layout.height - dp(14), self.root_layout.height * 0.94))
        self.drawer.height = target_height
        self.drawer.opacity = 1
        Animation.cancel_all(self.drawer, "width", "opacity")
        Animation(width=target_width, opacity=1, duration=0.18, t="out_quad").start(self.drawer)

    def close_drawer(self):
        if not getattr(self, "drawer_open", False):
            return
        self.drawer_open = False
        animation = Animation(width=0, opacity=0, duration=0.16, t="in_quad")
        def finished(*args):
            self.drawer_handle.opacity = 1
            self.drawer_handle.disabled = False
        animation.bind(on_complete=lambda *_: finished())
        animation.start(self.drawer)

    def activate_pen(self):
        self.canvas_area.set_pen_color(self.canvas_area.pen_color)
        self.status.text = 'Pen'
        self.pen_button.set_active(True)
        self.eraser_button.set_active(False)
        self.select_action.set_active(False)
        self.close_actions()

    def activate_select(self):
        self.canvas_area.set_select_mode()
        self.status.text = 'Draw selection'
        self.select_action.set_active(True)
        self.pen_button.set_active(False)
        self.eraser_button.set_active(False)
        self.close_actions()

    def selection_finished(self, selected_box):
        if not selected_box or selected_box[2] < dp(4) or selected_box[3] < dp(4):
            self.status.text = 'SELECT AREA'
            self.show_ribbon('Drag a rectangle around your handwriting', self.select_action, transient=True)
            return

        self.status.text = 'CAPTURING'
        if not self.canvas_area.capture_selected():
            detail = getattr(self, 'last_capture_error', '')
            self.output_box.text = 'Could not capture the selected region.'
            if detail:
                self.output_box.text += '\n\n' + detail
            self.status.text = 'CAPTURE FAILED'
            self.open_drawer('output')
            return

        # Capture is automatic; immediately start READ and show progress to the user.
        self.code_box.text = '# Reading selected handwriting...\n# Please wait.'
        self.output_box.text = 'Selection captured. Reading handwriting...'
        self.status.text = 'READING'
        self.open_drawer('code')
        self.recognize_code(None)

    def activate_eraser(self):
        self.canvas_area.set_eraser_mode()
        self.status.text = 'Erase'
        self.pen_button.set_active(False)
        self.eraser_button.set_active(True)
        self.select_action.set_active(False)
        self.close_actions()

    def show_palette(self, instance=None):
        if self.palette_popup is not None:
            try:
                self.palette_popup.dismiss()
            except Exception:
                pass
        content = BoxLayout(
            orientation="horizontal", spacing=dp(7),
            padding=[dp(10), dp(8)], size_hint=(1, 1)
        )
        popup = Popup(
            title="Choose ink colour", content=content,
            size_hint=(None, None), size=(dp(285), dp(105)),
            auto_dismiss=True
        )
        self.palette_popup = popup
        self.color_dots = []
        for color in self.colors:
            dot = ColorDot(
                color_value=color, callback=self.choose_color,
                size_hint=(None, None), size=(dp(32), dp(32))
            )
            dot.set_selected(color == self.canvas_area.pen_color)
            self.color_dots.append(dot)
            content.add_widget(dot)
        popup.open()

    def choose_color(self, color):
        self.canvas_area.set_pen_color(color)
        for dot in self.color_dots:
            dot.set_selected(dot.color_value == color)
        self.color_button.bg_color = color
        self.color_button.shape_color.rgba = color
        self.status.text = 'Pen'
        if hasattr(self, 'pen_button'):
            self.pen_button.set_active(True)
            self.eraser_button.set_active(False)
            self.select_action.set_active(False)
        if self.palette_popup is not None:
            popup = self.palette_popup
            self.palette_popup = None
            Clock.schedule_once(lambda _dt, pop=popup: pop.dismiss(), 0)

    def capture_code(self, instance=None):
        # Compatibility method; normal workflow captures in selection_finished().
        if self.canvas_area.capture_selected():
            self.status.text = 'CAPTURED'
            return True
        self.status.text = 'SELECT AREA'
        self.show_ribbon('Tap SELECT, then drag a rectangle', self.select_action, transient=True)
        return False

    def on_start(self):
        # Warm up one persistent Qwen server in the background on desktop.
        # This avoids restarting/reloading the vision model for every READ.
        if platform in ("android", "ios"):
            self.status.text = "CONNECT" if not self.qwen_url else "READY"
            return
        self.status.text = "LOADING MODEL..."
        threading.Thread(target=self.prepare_qwen, daemon=True).start()

    def start_image_server(self):
        try:
            handler = partial(ImageHandler, directory=writable_dir())
            self.image_server = socketserver.ThreadingTCPServer(('127.0.0.1', 8765), handler)
            self.image_server.allow_reuse_address = True
            threading.Thread(target=self.image_server.serve_forever, daemon=True).start()
        except Exception:
            self.status.text = 'Image server error'

    def server_ready(self):
        base_url = getattr(self, "qwen_url", QWEN_URL).strip().rstrip("/")
        if not base_url:
            return False
        try:
            request = urllib.request.Request(base_url + "/health", method="GET")
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def start_qwen_server(self):
        if self.server_ready():
            return True
        if platform in ("android", "ios"):
            return False
        base_url = getattr(self, "qwen_url", QWEN_URL).rstrip("/")
        # Only auto-start the bundled/local Windows model. Remote endpoints
        # are expected to be started by their owner.
        if not base_url.startswith(("http://127.0.0.1:", "http://localhost:", "https://127.0.0.1:", "https://localhost:")):
            return False
        with self.server_lock:
            if self.server_ready():
                return True
            if self.server_starting:
                pass
            else:
                self.server_starting = True
                try:
                    if not os.path.exists(LLAMA_SERVER):
                        self.server_starting = False
                        return False
                    command = [
                        LLAMA_SERVER, "-hf", MODEL, "--host", "0.0.0.0",
                        "--port", "8080", "-ngl", "99", "--ctx-size", "4096"
                    ]
                    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    self.server_process = subprocess.Popen(
                        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=creation_flags
                    )
                except Exception:
                    self.server_starting = False
                    return False
        for _ in range(240):
            if self.server_ready():
                self.server_starting = False
                return True
            if self.server_process and self.server_process.poll() is not None:
                self.server_starting = False
                return False
            time.sleep(0.5)
        self.server_starting = False
        return False

    def prepare_qwen(self):
        Clock.schedule_once(lambda dt: setattr(self.status, 'text', 'Loading...'))
        ready = self.start_qwen_server()
        if ready:
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', 'Ready'))
        else:
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', 'Offline'))

    def preprocess_image(self, image_path):
        """Prepare a compact, high-contrast crop for faster vision inference.

        The previous 3x resize could turn an ordinary selected region into a
        very large image, making Qwen spend longer processing visual tokens.
        Keep the crop clear while limiting the longest side to 1280 pixels.
        """
        processed_path = os.path.join(writable_dir(), 'selected_code_processed.png')
        with Image.open(image_path) as opened:
            image = opened.convert('L')

        if ImageStat.Stat(image).mean[0] < 128:
            image = ImageOps.invert(image)

        background = Image.new('L', image.size, 255)
        difference = ImageChops.difference(image, background)
        bbox = difference.getbbox()
        background.close()

        if bbox:
            pad = max(12, int(min(image.size) * 0.035))
            left = max(0, bbox[0] - pad)
            top = max(0, bbox[1] - pad)
            right = min(image.width, bbox[2] + pad)
            bottom = min(image.height, bbox[3] + pad)
            cropped = image.crop((left, top, right, bottom))
            image.close()
            image = cropped

        image = ImageOps.autocontrast(image, cutoff=1)
        image = ImageEnhance.Contrast(image).enhance(1.35)

        max_side = max(image.size)
        if max_side > 1280:
            scale = 1280 / max_side
            new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
            resized = image.resize(new_size, Image.Resampling.LANCZOS)
            image.close()
            image = resized
        elif max_side < 900:
            # Upscale smaller handwriting moderately, not 3x.
            scale = min(1.5, 1200 / max_side)
            new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
            resized = image.resize(new_size, Image.Resampling.LANCZOS)
            image.close()
            image = resized

        sharpened = image.filter(ImageFilter.SHARPEN)
        image.close()
        sharpened.save(processed_path, optimize=True)
        sharpened.close()
        return processed_path

    def clean_output(self, text):
        text = text.replace('\r', '')
        text = text.replace('Exiting...', '')
        text = text.replace('```python', '')
        text = text.replace('```', '')
        lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.lower() in ['here is the code:', "here's the code:", 'recognized code:', 'python code:']:
                continue
            if stripped.startswith('Do not '):
                continue
            if stripped.startswith('Read every '):
                continue
            if stripped.startswith('Preserve '):
                continue
            if stripped.startswith('Pay special '):
                continue
            if stripped.startswith('Return ONLY'):
                continue
            if stripped.startswith('Look carefully'):
                continue
            lines.append(line.rstrip())
        text = '\n'.join(lines).strip()
        text = re.sub(r'(?im)^(\s*)(?:Point|Print|PRINT|prlnt)(\s*\()', r'\1print\2', text)
        return text.strip()

    def recognize_code(self, instance=None):
        image_path = os.path.join(writable_dir(), "selected_code.png")
        if not os.path.isfile(image_path):
            self.status.text = "SELECT AREA"
            self.output_box.text = (
                "No captured image exists yet. Choose SELECT and draw a box "
                "around the handwriting; capture and reading happen automatically."
            )
            self.open_drawer("output")
            return

        if self.recognition_in_progress:
            return

        if platform in ("android", "ios") and not getattr(self, "qwen_url", "").strip():
            self.connection_message_text = (
                "Set the laptop's Qwen server address in PHONE LINK. "
                "This is needed only for Android handwriting recognition."
            )
            if hasattr(self, "connection_message"):
                self.connection_message.text = self.connection_message_text
            self.status.text = "PHONE LINK"
            self.open_drawer("connect")
            return

        self.recognition_in_progress = True
        self.status.text = "READING..."
        self.start_read_progress()
        self.open_drawer("code")

        # Use a persistent llama-server API for both desktop and Android.
        # On Windows, start it if needed; on Android, connect to the configured
        # laptop endpoint. Keeping the model resident avoids a full reload per read.
        if platform not in ("android", "ios") and not self.server_ready():
            threading.Thread(target=self.wait_and_recognize, daemon=True).start()
        else:
            threading.Thread(target=self.do_recognition, args=(image_path,), daemon=True).start()

    def start_read_progress(self):
        """Show an animated activity bar while the model is reading handwriting.

        This loops as an activity indicator; it is not a percentage estimate,
        because the local vision model does not report reliable progress.
        """
        if not hasattr(self, "read_progress"):
            return
        Animation.cancel_all(self.read_progress, "value")
        self.read_progress.value = 0
        self.read_progress.opacity = 1
        self.read_progress_label.text = "READING HANDWRITING — keep the app open"
        self._read_progress_animation = Animation(
            value=100, duration=1.35, t="in_out_quad"
        )
        self._read_progress_animation.bind(on_complete=self._loop_read_progress)
        self._read_progress_animation.start(self.read_progress)

    def _loop_read_progress(self, animation, widget):
        if not self.recognition_in_progress:
            return
        widget.value = 0
        self._read_progress_animation = Animation(
            value=100, duration=1.35, t="in_out_quad"
        )
        self._read_progress_animation.bind(on_complete=self._loop_read_progress)
        self._read_progress_animation.start(widget)

    def stop_read_progress(self):
        if hasattr(self, "read_progress"):
            Animation.cancel_all(self.read_progress, "value")
            self.read_progress.value = 0
        self._read_progress_animation = None

    def wait_and_recognize(self):
        if not self.start_qwen_server():
            Clock.schedule_once(lambda _dt: self.recognition_error(
                'Could not start the local recognition engine. Check that llama-server.exe exists and the model can load.'
            ))
            return
        image_path = os.path.join(writable_dir(), 'selected_code.png')
        self.do_recognition(image_path)

    def do_recognition(self, image_path):
        try:
            processed_path = self.preprocess_image(image_path)
            prompt = (
                "Transcribe the handwritten Python code in this image. Output only source code, "
                "with no explanation or markdown. Preserve all characters, quotes, punctuation, "
                "indentation, and every letter inside strings. Do not invent missing code. "
                "The Python function name is print, not Point or Print."
            )

            with open(processed_path, "rb") as image_file:
                image_b64 = base64.b64encode(image_file.read()).decode("ascii")
            image_data_url = "data:image/png;base64," + image_b64

            base_url = getattr(self, "qwen_url", QWEN_URL).strip().rstrip("/")
            if not base_url:
                raise RuntimeError(
                    "Recognition server address is empty. Open PHONE LINK to configure it."
                )

            data = {
                "model": MODEL,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]}],
                # 384 tokens is enough for many handwritten snippets while
                # still leaving room for longer examples. The persistent server
                # keeps the model loaded between requests.
                "max_tokens": 512,
                "temperature": 0,
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False}
            }
            request = urllib.request.Request(
                base_url + "/v1/chat/completions",
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            choices = response_data.get("choices") or []
            if not choices:
                raise RuntimeError(
                    "The recognition server returned no choices: "
                    + str(response_data)[:1200]
                )
            message = choices[0].get("message", {}).get("content", "")
            if isinstance(message, list):
                message = "\n".join(
                    str(part.get("text", ""))
                    for part in message if isinstance(part, dict)
                )
            text = self.clean_output(str(message))
            if not text:
                raise RuntimeError(
                    "The recognition server returned an empty response. "
                    "Check that the Qwen vision model is loaded correctly."
                )
            Clock.schedule_once(lambda _dt, value=text: self.recognition_finished(value))

        except urllib.error.HTTPError as error:
            try:
                body = error.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            error_message = f"HTTP {error.code}: {body[:1800] or error.reason}"
            Clock.schedule_once(lambda _dt, value=error_message: self.recognition_error(value))
        except urllib.error.URLError as error:
            error_message = (
                "Could not connect to the recognition server. "
                "Check that llama-server is running and the address is correct.\n\n"
                + str(error)
            )
            Clock.schedule_once(lambda _dt, value=error_message: self.recognition_error(value))
        except TimeoutError:
            Clock.schedule_once(lambda _dt: self.recognition_error(
                "Recognition took longer than 3 minutes. Select a smaller, clearer region and try again."
            ))
        except Exception as error:
            error_message = f"{type(error).__name__}: {error}"
            Clock.schedule_once(lambda _dt, value=error_message: self.recognition_error(value))

    def recognition_finished(self, text):
        self.recognition_in_progress = False
        self.stop_read_progress()
        self.code_box.text = text
        self.history.insert(0, time.strftime('%H:%M:%S') + '\n' + text)
        self.history = self.history[:10]
        self.status.text = 'CODE READY'
        self.recognize_btn.disabled = False
        if self.run_after_recognition:
            self.run_after_recognition = False
            Clock.schedule_once(lambda _dt: self.run_code(None), 0.1)
        else:
            self.open_drawer('code')

    def recognition_error(self, error):
        self.recognition_in_progress = False
        self.stop_read_progress()
        self.recognize_btn.disabled = False
        self.run_after_recognition = False
        error_text = str(error).strip() or 'The recognition engine returned no details.'
        self.code_box.text = ''
        self.output_box.text = 'READ FAILED\n\n' + error_text
        self.status.text = 'READ FAILED'
        self.open_drawer('output')

    def run_code(self, instance=None):
        self.close_actions()
        if self.recognition_in_progress:
            self.run_after_recognition = True
            self.output_box.text = 'Reading handwriting first. The program will run automatically when recognition finishes.'
            self.status.text = 'WAITING FOR READ'
            self.open_drawer('output')
            return

        code = self.code_box.text.strip()
        if not code:
            self.output_box.text = 'No Python code yet. Tap SELECT and draw a rectangle around handwriting; capture and recognition happen automatically.'
            self.open_drawer('output')
            return
        if code.startswith('Recognition error:') or code.startswith('# Reading selected handwriting'):
            self.output_box.text = 'Code is not ready to run. Select the handwriting again and wait for the recognized code to appear in the CODE tab.'
            self.open_drawer('output')
            return
        try:
            ast.parse(code)
        except SyntaxError as error:
            self.output_box.text = 'Syntax Error\n\n' + str(error)
            self.status.text = 'FIX CODE'
            self.open_drawer('output')
            return
        self.run_btn.disabled = True
        self.output_box.text = 'Running Python...'
        self.status.text = 'RUNNING'
        threading.Thread(target=self.execute_code, args=(code,), daemon=True).start()

    def execute_code(self, code):
        try:
            if platform in ('android', 'ios'):
                started = time.monotonic()
                stdout = io.StringIO()
                stderr = io.StringIO()
                namespace = {'__name__': '__main__'}
                old_trace = sys.gettrace()
                def timeout_trace(frame, event, arg):
                    if time.monotonic() - started > 8:
                        raise TimeoutError('Code exceeded the 8 second limit.')
                    return timeout_trace
                try:
                    sys.settrace(timeout_trace)
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        exec(compile(code, '<Code Canvas>', 'exec'), namespace, namespace)
                    output = stdout.getvalue().strip() or 'Program finished with no output.'
                    Clock.schedule_once(lambda dt: self.run_finished(output))
                except Exception as e:
                    message = stderr.getvalue().strip() or f'{type(e).__name__}: {e}'
                    Clock.schedule_once(lambda dt: self.run_finished(message, True))
                finally:
                    sys.settrace(old_trace)
                return
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            result = subprocess.run([sys.executable, '-c', code], cwd=APP_DIR, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10, env=env)
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            if result.returncode == 0:
                output = stdout or 'Program finished with no output.'
                Clock.schedule_once(lambda dt: self.run_finished(output))
            else:
                output = stderr or 'Program exited with an error.'
                Clock.schedule_once(lambda dt: self.run_finished(output, True))
        except subprocess.TimeoutExpired:
            Clock.schedule_once(lambda dt: self.run_finished('Program exceeded the 10 second limit.', True))
        except Exception as e:
            message = str(e)
            Clock.schedule_once(lambda dt: self.run_finished(message, True))

    def run_finished(self, output, error=False):
        self.output_box.text = output
        if error:
            self.status.text = 'Run error'
        else:
            self.status.text = 'Done'
        self.run_btn.disabled = False
        self.open_drawer('output')

    def clear_code(self, instance):
        self.canvas_area.clear_canvas()
        self.code_box.text = ''
        self.output_box.text = 'Program output will appear here.'
        self.recognition_in_progress = False
        self.run_after_recognition = False
        self.status.text = 'READY'
        self.select_action.set_active(False)
        self.pen_button.set_active(True)
        self.eraser_button.set_active(False)
        self.close_actions()
        self.close_drawer()

    def on_stop(self):
        if self.image_server is not None:
            try:
                self.image_server.shutdown()
                self.image_server.server_close()
            except:
                pass
        if self.server_process is not None:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                pass
CodeCanvasApp().run()
