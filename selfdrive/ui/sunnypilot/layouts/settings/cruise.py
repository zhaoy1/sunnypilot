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
    # Read mode - get() returns int directly for INT type params
    self._mode = self._params.get("CruiseSpeedMode")
    if self._mode is None:
      self._mode = 0
    self._dialog = None
    self._button = Button(
      lambda: f"Cruise Speed Mode: {self.MODE_NAMES[self._mode]}",
      click_callback=self._show_dialog,
      button_style=ButtonStyle.NORMAL,
      text_alignment=rl.GuiTextAlignment.TEXT_ALIGN_LEFT,
      text_padding=50
    )

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
        self._params.put("CruiseSpeedMode", new_mode)
        self._mode = new_mode
        self._dialog = None
      elif result == DialogResult.CANCEL:
        self._dialog = None
      return

    # Render button
    self._button.render(rect)


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
