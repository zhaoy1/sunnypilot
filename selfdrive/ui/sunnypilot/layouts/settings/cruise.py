"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.common.params import Params
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.scroller_tici import Scroller
from openpilot.system.ui.sunnypilot.widgets.list_view import multiple_button_item_sp


class CruiseLayout(Widget):
  def __init__(self):
    super().__init__()
    self._params = Params()

    # Read current mode from file
    mode_file = "/data/params/d/CruiseSpeedMode"
    try:
      with open(mode_file, 'r') as f:
        current_mode = int(f.read().strip())
    except (FileNotFoundError, ValueError):
      current_mode = 0

    # Create cruise speed mode selector with 4 buttons
    self._cruise_speed_mode_item = multiple_button_item_sp(
      title="Cruise Speed Mode",
      description="Select how cruise speed is set when engaging cruise control",
      buttons=["Cluster", "Speed Lmt", "10%+", "20%+"],
      selected_index=current_mode,
      button_width=250,  # Increased from 200 to prevent text overlap
      callback=self._set_cruise_speed_mode,
      icon="speed_limit.png"
    )

    items = [self._cruise_speed_mode_item]
    self._scroller = Scroller(items, line_separator=True, spacing=0)

  def _set_cruise_speed_mode(self, button_index: int):
    """Save selected cruise speed mode to file"""
    mode_file = "/data/params/d/CruiseSpeedMode"
    try:
      with open(mode_file, 'w') as f:
        f.write(str(button_index))
    except Exception:
      pass

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()
