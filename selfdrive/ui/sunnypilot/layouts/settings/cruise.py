"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import os
from openpilot.common.params import Params
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import multiple_button_item_sp
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.scroller_tici import Scroller


class CruiseLayout(Widget):
  def __init__(self):
    super().__init__()
    self._params = Params()
    items = self._initialize_items()
    self._scroller = Scroller(items, line_separator=True, spacing=0)

  def _initialize_items(self):
    self._cruise_speed_mode = multiple_button_item_sp(
      title=lambda: tr("Cruise Speed Mode"),
      description=lambda: tr("Select how cruise speed is initialized:\n"
                           "• Cluster Speed: Use vehicle cluster speed\n"
                           "• Speed Limit: Use exact speed limit\n"
                           "• Speed Limit +10%: Add 10% to speed limit\n"
                           "• Speed Limit +20%: Add 20% to speed limit"),
      param="CruiseSpeedMode",
      buttons=[
        lambda: tr("Cluster"),
        lambda: tr("Limit"),
        lambda: tr("Limit +10%"),
        lambda: tr("Limit +20%")
      ],
      button_width=180,
      callback=self._on_cruise_mode_changed,
      inline=True,
    )

    items = [
      self._cruise_speed_mode,
    ]
    return items

  def _on_cruise_mode_changed(self, value):
    """Handle cruise speed mode change"""
    # Write to file for card.py to read
    mode_file = "/data/params/d/CruiseSpeedMode"
    try:
      os.makedirs(os.path.dirname(mode_file), exist_ok=True)
      with open(mode_file, 'w') as f:
        f.write(str(value))
      print(f"[CRUISE_UI] Set cruise speed mode to {value}")
    except Exception as e:
      print(f"[CRUISE_UI] Error setting cruise speed mode: {e}")

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()
