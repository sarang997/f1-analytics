import arcade
from src.utils.config import LEADERBOARD_WIDTH, SCREEN_HEIGHT, PANEL_COLOR, ITEM_BG_COLOR, WHITE

class Leaderboard:
    def __init__(self, driver_metadata):
        self.driver_metadata = driver_metadata
        self.lb_texts = {}
        for drv, meta in self.driver_metadata.items():
            self.lb_texts[drv] = arcade.Text("", 30, 0, WHITE, 12)
        
        self.header = arcade.Text("POS   DRIVER", 20, SCREEN_HEIGHT - 40, WHITE, 14, bold=True)

    def draw(self, current_frame):
        # Draw Background
        arcade.draw_rect_filled(arcade.rect.XYWH(LEADERBOARD_WIDTH/2, SCREEN_HEIGHT/2, LEADERBOARD_WIDTH, SCREEN_HEIGHT), PANEL_COLOR)
        self.header.draw()
        
        active_drivers = current_frame.drivers.items()
        sorted_drivers = sorted(active_drivers, key=lambda x: x[1].dist, reverse=True)
        
        for i, (drv, telemetry) in enumerate(sorted_drivers):
            if drv not in self.lb_texts: continue
            meta = self.driver_metadata[drv]
            
            y_pos = SCREEN_HEIGHT - 130 - (i * 30)
            
            # Row Background
            arcade.draw_rect_filled(arcade.rect.XYWH(LEADERBOARD_WIDTH/2, y_pos + 5, LEADERBOARD_WIDTH - 10, 25), ITEM_BG_COLOR)
            
            # Team color stripe
            color = arcade.types.Color.from_hex_string(meta.color)
            arcade.draw_lrbt_rectangle_filled(5, 15, y_pos - 8, y_pos + 18, color)
            
            # Text update and draw
            text_obj = self.lb_texts[drv]
            text_obj.text = f"{i+1:02d}    {meta.abb}   {telemetry.speed} KM/H"
            text_obj.y = y_pos
            text_obj.draw()
