"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import pyray as rl
from openpilot.common.params import Params
from openpilot.system.ui.lib.application import FontWeight
from openpilot.system.ui.widgets import Widget, DialogResult
from openpilot.system.ui.widgets.button import Button, ButtonStyle
from openpilot.system.ui.widgets.label import gui_label
from openpilot.system.ui.widgets.option_dialog import MultiOptionDialog
from openpilot.system.ui.widgets.scroller_tici import Scroller


class CruiseSpeedModeButton(Widget):
  """Button to select cruise speed mode"""
  MODE_NAMES = [
    "Current Speed",
    "Speed Limit",
    "Speed Limit + 10%",
    "Speed Limit + 20%"
  ]

  def __init__(self):
    super().__init__()
    self._params = Params()
    # Read mode from file since CruiseSpeedMode param requires recompiling params_pyx.so
    self._mode_file = "/data/params/d/CruiseSpeedMode"
    self._mode = self._read_mode_from_file()
    self._dialog = None

  def _read_mode_from_file(self):
    """Read cruise speed mode from file"""
    try:
      with open(self._mode_file, 'r') as f:
        return int(f.read().strip())
    except (FileNotFoundError, ValueError):
      return 0

  def _write_mode_to_file(self, mode):
    """Write cruise speed mode to file"""
    try:
      with open(self._mode_file, 'w') as f:
        f.write(str(mode))
    except Exception:
      pass

  def _show_dialog(self):
    """Show selection dialog"""
    self._dialog = MultiOptionDialog(
      "Select Cruise Speed Mode",
      self.MODE_NAMES,
      current=self.MODE_NAMES[self._mode]
    )

  def _render(self, rect):
    # Handle dialog if open
    if self._dialog:
      result = self._dialog.render(rect)
      if result == DialogResult.CONFIRM:
        # Save selection
        new_mode = self.MODE_NAMES.index(self._dialog.selection)
        self._write_mode_to_file(new_mode)
        self._mode = new_mode
        self._dialog = None
      elif result == DialogResult.CANCEL:
        self._dialog = None
      return

    # Render button manually (similar to other settings buttons)
    button_text = f"Cruise Speed Mode: {self.MODE_NAMES[self._mode]}"

    # Draw button background
    rl.draw_rectangle_rec(rect, rl.Color(40, 40, 40, 255))

    # Draw text
    from openpilot.system.ui.lib.application import gui_app
    font = gui_app.font()
    text_size = 40
    text_color = rl.WHITE

    rl.draw_text_ex(font, button_text,
                    rl.Vector2(rect.x + 50, rect.y + (rect.height - text_size) / 2),
                    text_size, 1, text_color)

    # Check for click
    if rl.check_collision_point_rec(rl.get_mouse_position(), rect):
      if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
        self._show_dialog()


class CruiseLayout(Widget):
  def __init__(self):
    super().__init__()

    self._params = Params()
    items = self._initialize_items()
    self._scroller = Scroller(items, line_separator=True, spacing=0)

  def _initialize_items(self):
    items = [
      CruiseSpeedModeButton(),
    ]
    return items

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()
