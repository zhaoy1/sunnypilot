import pyray as rl
from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget


class CruiseButton(Widget):
  def __init__(self):
    super().__init__()
    self._params = Params()
    self._is_cruise_set: bool = False
    self._engageable: bool = False

    self._white_color: rl.Color = rl.Color(255, 255, 255, 255)
    self._plus_rect = rl.Rectangle(50, 300, 250, 250)  # "+" button position
    self._minus_rect = rl.Rectangle(50, 570, 250, 250)  # "-" button position (20px gap below +)
    self._font_size = 240  # large text size as specified

  def set_rect(self, rect: rl.Rectangle) -> None:
    self._plus_rect.x, self._plus_rect.y = rect.x, rect.y
    self._minus_rect.x, self._minus_rect.y = rect.x, rect.y + 270  # 20px gap

  def _update_state(self) -> None:
    selfdrive_state = ui_state.sm["selfdriveState"]
    controls_state = ui_state.sm["controlsState"]

    self._engageable = selfdrive_state.engageable or selfdrive_state.enabled

    # Check if cruise is set
    v_cruise = controls_state.vCruiseDEPRECATED
    self._is_cruise_set = 0 < v_cruise < 255

  def handle_mouse_event(self) -> bool:
    # Only handle mouse events when cruise is set
    if not self._is_cruise_set:
      return False

    mouse_pos = rl.get_mouse_position()

    # Check "+" button
    if rl.check_collision_point_rec(mouse_pos, self._plus_rect):
      if rl.is_mouse_button_released(rl.MouseButton.MOUSE_BUTTON_LEFT):
        # Increment cruise speed delta
        try:
          current_delta = self._params.get("CruiseSpeedDelta", encoding='utf-8')
          delta_value = int(current_delta) if current_delta else 0
          delta_value += 1
          self._params.put("CruiseSpeedDelta", str(delta_value))
        except Exception:
          self._params.put("CruiseSpeedDelta", "1")
      return True

    # Check "-" button
    if rl.check_collision_point_rec(mouse_pos, self._minus_rect):
      if rl.is_mouse_button_released(rl.MouseButton.MOUSE_BUTTON_LEFT):
        # Decrement cruise speed delta
        try:
          current_delta = self._params.get("CruiseSpeedDelta", encoding='utf-8')
          delta_value = int(current_delta) if current_delta else 0
          delta_value -= 1
          self._params.put("CruiseSpeedDelta", str(delta_value))
        except Exception:
          self._params.put("CruiseSpeedDelta", "-1")
      return True

    return False

  def _render(self, rect: rl.Rectangle) -> None:
    # Only render buttons when cruise is set
    if not self._is_cruise_set:
      return

    # White text color, fully opaque
    self._white_color.a = 255
    font = gui_app.font()

    # Draw "+" button
    plus_center_x = int(self._plus_rect.x + self._plus_rect.width // 2)
    plus_center_y = int(self._plus_rect.y + self._plus_rect.height // 2)
    plus_text = "+"
    plus_text_size = measure_text_cached(font, plus_text, self._font_size)
    plus_text_x = plus_center_x - plus_text_size.x / 2
    plus_text_y = plus_center_y - plus_text_size.y / 2
    rl.draw_text_ex(font, plus_text, rl.Vector2(plus_text_x, plus_text_y), self._font_size, 0, self._white_color)

    # Draw "-" button
    minus_center_x = int(self._minus_rect.x + self._minus_rect.width // 2)
    minus_center_y = int(self._minus_rect.y + self._minus_rect.height // 2)
    minus_text = "-"
    minus_text_size = measure_text_cached(font, minus_text, self._font_size)
    minus_text_x = minus_center_x - minus_text_size.x / 2
    minus_text_y = minus_center_y - minus_text_size.y / 2
    rl.draw_text_ex(font, minus_text, rl.Vector2(minus_text_x, minus_text_y), self._font_size, 0, self._white_color)
