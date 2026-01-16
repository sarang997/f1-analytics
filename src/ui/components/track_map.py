import arcade
from src.utils.config import MAP_START_X, MAP_START_Y, MAP_BOX_W, MAP_BOX_H, ASH_GREY, DARK_GRAY, WHITE, LIGHT_YELLOW, STATUS_NAMES

class TrackMap:
    def __init__(self, driver_metadata, track_line, bounds):
        self.driver_metadata = driver_metadata
        self.track_line = track_line
        self.min_x, self.max_x, self.min_y, self.max_y = bounds
        
        self.map_label = arcade.Text("LIVE TRACK MAP", MAP_START_X, MAP_START_Y + MAP_BOX_H + 5, ASH_GREY, 10, font_name="Arial")
        self.status_text = arcade.Text("", MAP_START_X + 200, MAP_START_Y + 20, WHITE, 16, bold=True, anchor_x="center")
        
        # Pre-initialize car map labels
        self.map_labels = {}
        for drv, meta in driver_metadata.items():
            self.map_labels[drv] = arcade.Text(str(meta.abb), 0, 0, WHITE, 8)
            
        self.scaled_track = []
        self._cache_track()
        
    def _cache_track(self):
        if self.track_line:
            self.scaled_track = [self.map_to_box(p[0], p[1]) for p in self.track_line]

    def get_driver_at_pos(self, x, y, current_frame):
        """Returns the driver abbreviation if the mouse x,y hits a driver dot."""
        CLICK_RADIUS = 10
        for drv, telemetry in current_frame.drivers.items():
            if drv not in self.driver_metadata: continue
            
            mx, my = self.map_to_box(telemetry.x, telemetry.y)
            
            # Simple distance check
            if (x - mx)**2 + (y - my)**2 <= CLICK_RADIUS**2:
                return drv
        return None

    def map_to_box(self, x, y):
        """Scales raw F1 coordinates to fit inside the map box."""
        if self.max_x == self.min_x: nx = 0.5
        else: nx = (x - self.min_x) / (self.max_x - self.min_x)
        
        if self.max_y == self.min_y: ny = 0.5
        else: ny = (y - self.min_y) / (self.max_y - self.min_y)
        
        pad = 20
        screen_x = MAP_START_X + pad + (nx * (MAP_BOX_W - pad * 2))
        screen_y = MAP_START_Y + pad + (ny * (MAP_BOX_H - pad * 2))
        return screen_x, screen_y

    def get_track_color(self, status, show_blink):
        if status == 1: return DARK_GRAY
        if not show_blink: return DARK_GRAY
        
        if status == 2: return LIGHT_YELLOW
        if status == 5: return arcade.color.RED
        if status in [4, 6, 7]: return LIGHT_YELLOW
        return DARK_GRAY

    def draw(self, current_frame, show_blink):
        # Draw Box
        arcade.draw_rect_outline(arcade.rect.XYWH(MAP_START_X + MAP_BOX_W/2, MAP_START_Y + MAP_BOX_H/2, MAP_BOX_W, MAP_BOX_H), ASH_GREY, 2)
        self.map_label.draw()

        # Draw Circuit
        track_color = self.get_track_color(current_frame.status, show_blink)
        if self.scaled_track:
            arcade.draw_line_strip(self.scaled_track, track_color, 2)

        # Draw Cars
        for drv, telemetry in current_frame.drivers.items():
            if drv not in self.driver_metadata: continue
            meta = self.driver_metadata[drv]
            
            mx, my = self.map_to_box(telemetry.x, telemetry.y)
            color = arcade.types.Color.from_hex_string(meta.color)
            arcade.draw_circle_filled(mx, my, 5, color)
            
            label = self.map_labels[drv]
            label.x = mx + 7
            label.y = my + 7
            label.draw()

        # Draw Status
        if current_frame.status != 1:
            self.status_text.text = STATUS_NAMES.get(current_frame.status, "UNKNOWN")
            self.status_text.color = track_color
            self.status_text.draw()
