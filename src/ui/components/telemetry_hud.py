import arcade
from src.utils.config import HUD_X, HUD_Y, HUD_WIDTH, HUD_HEIGHT, HUD_BG_COLOR, WHITE, RED, ASH_GREY

class TelemetryHUD:
    def __init__(self, driver_metadata):
        self.driver_metadata = driver_metadata
        
        # Static Labels
        self.title_text = arcade.Text("DRIVER TELEMETRY", HUD_X + 10, HUD_Y + HUD_HEIGHT - 20, ASH_GREY, 10, bold=True)
        
        # Dynamic Text Objects (reused/updated in draw)
        self.driver_name = arcade.Text("", HUD_X + 10, HUD_Y + HUD_HEIGHT - 50, WHITE, 20, bold=True)
        self.speed_val = arcade.Text("", HUD_X + 10, HUD_Y + HUD_HEIGHT - 90, WHITE, 24, bold=True)
        self.gear_val = arcade.Text("", HUD_X + 150, HUD_Y + HUD_HEIGHT - 90, WHITE, 24, bold=True)
        self.drs_val = arcade.Text("DRS", HUD_X + 220, HUD_Y + HUD_HEIGHT - 90, ASH_GREY, 14, bold=True)

    def draw(self, frame, driver_id):
        if driver_id is None or driver_id not in frame.drivers:
            return

        telemetry = frame.drivers[driver_id]
        meta = self.driver_metadata.get(driver_id)
        
        # Background
        arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + HUD_WIDTH/2, HUD_Y + HUD_HEIGHT/2, HUD_WIDTH, HUD_HEIGHT), HUD_BG_COLOR)
        arcade.draw_rect_outline(arcade.rect.XYWH(HUD_X + HUD_WIDTH/2, HUD_Y + HUD_HEIGHT/2, HUD_WIDTH, HUD_HEIGHT), ASH_GREY, 1)
        
        # Header
        self.title_text.draw()
        
        # Driver Name
        if meta:
            self.driver_name.text = f"{meta.name} #{driver_id}"
            self.driver_name.color = arcade.types.Color.from_hex_string(meta.color)
            self.driver_name.draw()
            
        # Stats
        self.speed_val.text = f"{telemetry.speed} KPH"
        self.speed_val.draw()
        
        self.gear_val.text = f"GEAR: {telemetry.gear}"
        self.gear_val.draw()
        
        # DRS Indicator
        if telemetry.drs in [10, 12, 14]: # FastF1 DRS values often vary, 10+ usually means open/avail
             self.drs_val.color = arcade.color.GREEN
        else:
             self.drs_val.color = ASH_GREY
        self.drs_val.draw()

        # Input Bars
        bar_w = 100
        bar_h = 10
        base_y = HUD_Y + 40
        
        # Throttle
        if not hasattr(self, 'thr_label'):
            self.thr_label = arcade.Text("THR", HUD_X + 10, base_y, WHITE, 10)
        self.thr_label.draw()
        
        arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + 50 + bar_w/2, base_y + 5, bar_w, bar_h), ASH_GREY)
        thr_pct = telemetry.throttle / 100.0
        arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + 50 + (bar_w * thr_pct)/2, base_y + 5, bar_w * thr_pct, bar_h), arcade.color.GREEN)

        # Brake
        if not hasattr(self, 'brk_label'):
            self.brk_label = arcade.Text("BRK", HUD_X + 180, base_y, WHITE, 10)
        self.brk_label.draw()
        
        arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + 220 + bar_w/2, base_y + 5, bar_w, bar_h), ASH_GREY)
        brk_on = 1.0 if telemetry.brake else 0.0 # Boolean in our model
        arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + 220 + (bar_w * brk_on)/2, base_y + 5, bar_w * brk_on, bar_h), RED)
