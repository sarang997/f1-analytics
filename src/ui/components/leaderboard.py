import arcade
from src.utils.config import LEADERBOARD_WIDTH, SCREEN_HEIGHT, PANEL_COLOR, ITEM_BG_COLOR, WHITE, COMPOUND_COLORS

class Leaderboard:
    def __init__(self, driver_metadata):
        self.driver_metadata = driver_metadata
        self.lb_texts = {}
        for drv, meta in self.driver_metadata.items():
            self.lb_texts[drv] = arcade.Text("", 30, 0, WHITE, 12)
        
        self.header = arcade.Text("POS   DRIVER     GAP", 20, SCREEN_HEIGHT - 40, WHITE, 14, bold=True)
        self.sorted_drivers = []

    def get_driver_at_pos(self, x, y):
        """Returns the driver abbreviation if the mouse x,y hits a leaderboard row."""
        # ... (unchanged)
        if x > LEADERBOARD_WIDTH: return None
        if not self.sorted_drivers: return None
        
        for i, (drv, _) in enumerate(self.sorted_drivers):
            y_pos = SCREEN_HEIGHT - 130 - (i * 30)
            center_y = y_pos + 5
            if abs(y - center_y) < 15:
                return drv
        return None

    def draw(self, current_frame):
        # Draw Background
        arcade.draw_rect_filled(arcade.rect.XYWH(LEADERBOARD_WIDTH/2, SCREEN_HEIGHT/2, LEADERBOARD_WIDTH, SCREEN_HEIGHT), PANEL_COLOR)
        self.header.draw()
        
        active_drivers = current_frame.drivers.items()
        self.sorted_drivers = sorted(active_drivers, key=lambda x: x[1].dist, reverse=True)
        
        leader_dist = self.sorted_drivers[0][1].dist if self.sorted_drivers else 0
        
        for i, (drv, telemetry) in enumerate(self.sorted_drivers):
            if drv not in self.lb_texts: continue
            meta = self.driver_metadata[drv]
            
            y_pos = SCREEN_HEIGHT - 130 - (i * 30)
            
            # Row Background
            arcade.draw_rect_filled(arcade.rect.XYWH(LEADERBOARD_WIDTH/2, y_pos + 5, LEADERBOARD_WIDTH - 10, 25), ITEM_BG_COLOR)
            
            # Team color stripe
            color = arcade.types.Color.from_hex_string(meta.color)
            arcade.draw_lrbt_rectangle_filled(5, 15, y_pos - 8, y_pos + 18, color)
            
            # Tyre Compound Indicator
            comp_color = COMPOUND_COLORS.get(telemetry.compound, COMPOUND_COLORS["UNKNOWN"])
            arcade.draw_circle_filled(25, y_pos + 5, 4, comp_color)
            
            # Interval Calculation (Distance Delta / Speed -> Time Delta)
            # This is an approximation. 
            gap_str = "LEADER"
            if i > 0:
                dist_delta = leader_dist - telemetry.dist
                # Speed is in KPH -> m/s
                speed_ms = max(1, telemetry.speed) / 3.6 
                time_gap = dist_delta / speed_ms
                gap_str = f"+{time_gap:.1f}s"
            
            # Text update and draw
            text_obj = self.lb_texts[drv]
            # OLD: text_obj.text = f"{i+1:02d}    {meta.abb}   {telemetry.speed} KM/H"
            # NEW: POS  ABB  GAP
            text_obj.text = f"{i+1:02d}    {meta.abb}   {gap_str}"
            text_obj.y = y_pos
            text_obj.draw()
