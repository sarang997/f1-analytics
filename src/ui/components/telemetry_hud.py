import arcade
from src.utils.config import HUD_X, HUD_Y, HUD_WIDTH, HUD_HEIGHT, HUD_BG_COLOR, WHITE, RED, ASH_GREY

class TelemetryHUD:
    def __init__(self, driver_metadata):
        self.driver_metadata = driver_metadata
        
        # Static Labels
        self.title_text = arcade.Text("DRIVER TELEMETRY", HUD_X + 10, HUD_Y + HUD_HEIGHT - 20, ASH_GREY, 10, bold=True)
        
        # Dynamic Text Objects (reused/updated in draw)
        self.driver_name = arcade.Text("", HUD_X + 10, HUD_Y + HUD_HEIGHT - 50, WHITE, 20, bold=True)
        self.header_text = arcade.Text("", HUD_X + 10, HUD_Y + HUD_HEIGHT - 30, WHITE, 14, bold=True)
        self.speed_label = arcade.Text("", HUD_X + 20, HUD_Y + 130, WHITE, 20, bold=True)
        self.gear_label = arcade.Text("", HUD_X + 150, HUD_Y + 130, arcade.color.CYAN, 20, bold=True)
        
        self.brk_bar = arcade.SpriteSolidColor(100, 20, (255, 0, 0)) # Red
        
        # Labels
        self.thr_label = arcade.Text("THR", HUD_X + 10, HUD_Y + 110, ASH_GREY, 10, bold=True)
        self.brk_label = arcade.Text("BRK", HUD_X + 10, HUD_Y + 80, ASH_GREY, 10, bold=True)
        
        # Pedal Trace Buffer
        # List of (rel_time, throttle, brake)
        self.trace_buffer = [] 
        self.max_trace_points = 100 # Keep last ~100 frames (10s)
        self.last_trace_time = None  # Track last timestamp to avoid duplicate entries
        
        # RPM Gauge (Visuals)
        self.leds = []
        led_w = 20
        start_x = HUD_X + 20
        y = HUD_Y + 160
        # 5 Green, 5 Red, 5 Blue
        for i in range(15):
            color = arcade.color.GREEN if i < 5 else (arcade.color.RED if i < 10 else arcade.color.BLUE)
            self.leds.append({
                'rect': arcade.rect.XYWH(start_x + (i * (led_w + 2)), y, led_w, 10),
                'color': color
            })

    def draw_rpm_gauge(self, speed, gear):
        # Simulate RPM based on Speed/Gear
        # This is a Rough approximation as we lack RPM data
        # Max speed per gear (approximate)
        gear_max = {0: 10, 1: 100, 2: 160, 3: 210, 4: 260, 5: 290, 6: 320, 7: 340, 8: 360}
        
        g_max = gear_max.get(gear, 360)
        g_min = gear_max.get(gear-1, 0) if gear > 1 else 0
        
        # Normalize speed within gear range
        if g_max == g_min: ratio = 0
        else: ratio = (speed - g_min) / (g_max - g_min)
        
        ratio = max(0.0, min(1.0, ratio))
        
        # Light up LEDs
        num_lit = int(ratio * 15)
        for i, led in enumerate(self.leds):
            if i < num_lit:
                arcade.draw_rect_filled(led['rect'], led['color'])
            else:
                # Dimmed
                c = list(led['color'])
                c = (c[0]//4, c[1]//4, c[2]//4)
                arcade.draw_rect_filled(led['rect'], c)

    def draw_pedal_trace(self, timestamp, throttle, brake):
        # Only add to buffer if timestamp has changed (avoid 60fps duplicate entries)
        if self.last_trace_time != timestamp:
            self.trace_buffer.append((timestamp, throttle, brake))
            self.last_trace_time = timestamp
            
            # Prune old
            while len(self.trace_buffer) > self.max_trace_points:
                self.trace_buffer.pop(0)

        # Draw box
        box_x = HUD_X + 150
        box_y = HUD_Y + 30
        box_w = 200
        box_h = 60
        arcade.draw_rect_filled(arcade.rect.XYWH(box_x + box_w/2, box_y + box_h/2, box_w, box_h), (30, 30, 30))
        arcade.draw_rect_outline(arcade.rect.XYWH(box_x + box_w/2, box_y + box_h/2, box_w, box_h), ASH_GREY, 1)

        if len(self.trace_buffer) < 2: return
        
        # Plot
        # X axis: Time (last 5s?) -> Map index 0..N to 0..W
        # Y axis: 0..100 -> 0..H
        
        t_points = []
        b_points = []
        
        n = len(self.trace_buffer)
        for i, (_, t, b) in enumerate(self.trace_buffer):
            px = box_x + (i / n) * box_w
            
            py_t = box_y + (t / 100) * box_h
            py_b = box_y + (b / 100) * box_h
            
            t_points.append((px, py_t))
            b_points.append((px, py_b))
            
        arcade.draw_line_strip(t_points, arcade.color.GREEN, 2)
        arcade.draw_line_strip(b_points, arcade.color.RED, 2)

    def draw(self, current_frame, selected_driver_id):
        # ... Background ...
        arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + HUD_WIDTH/2, HUD_Y + HUD_HEIGHT/2, HUD_WIDTH, HUD_HEIGHT), HUD_BG_COLOR)
        arcade.draw_rect_outline(arcade.rect.XYWH(HUD_X + HUD_WIDTH/2, HUD_Y + HUD_HEIGHT/2, HUD_WIDTH, HUD_HEIGHT), ASH_GREY, 1)
        
        if selected_driver_id not in current_frame.drivers:
            return
            
        d = current_frame.drivers[selected_driver_id]
        meta = self.driver_metadata[selected_driver_id]
        
        # Header
        self.header_text.text = f"{meta.name} #{selected_driver_id}"
        self.header_text.draw()
        
        # Stats Grid
        self.speed_label.text = f"{d.speed} KPH"
        self.speed_label.draw()
        
        self.gear_label.text = f"GEAR {d.gear}"
        self.gear_label.draw()
        
        # RPM
        self.draw_rpm_gauge(d.speed, d.gear)
        
        # Throttle Bar using XYWH
        bar_w = 200
        thr_w = (d.throttle / 100) * bar_w
        
        # BG
        # L=HUD_X+50, R=HUD_X+50+bar_w, T=HUD_Y+120, B=HUD_Y+110
        # W=bar_w, H=10, CX=HUD_X+50+bar_w/2, CY=HUD_Y+115
        arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + 50 + bar_w/2, HUD_Y + 115, bar_w, 10), (50, 50, 50))
        
        # Fill
        # L=HUD_X+50, R=HUD_X+50+thr_w, T=HUD_Y+120, B=HUD_Y+110
        # W=thr_w, H=10, CX=HUD_X+50+thr_w/2, CY=HUD_Y+115
        if thr_w > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + 50 + thr_w/2, HUD_Y + 115, thr_w, 10), arcade.color.GREEN)
        self.thr_label.draw()

        # Brake Bar
        brk_val = 100 if d.brake else 0
        brk_w = (brk_val / 100) * bar_w
        
        # BG
        # L=HUD_X+50, R=HUD_X+50+bar_w, T=HUD_Y+90, B=HUD_Y+80
        # W=bar_w, H=10, CX=HUD_X+50+bar_w/2, CY=HUD_Y+85
        arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + 50 + bar_w/2, HUD_Y + 85, bar_w, 10), (50, 50, 50))
        
        # Fill
        # L=HUD_X+50, R=HUD_X+50+brk_w, T=HUD_Y+90, B=HUD_Y+80
        # W=brk_w, H=10, CX=HUD_X+50+brk_w/2, CY=HUD_Y+85
        if brk_w > 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(HUD_X + 50 + brk_w/2, HUD_Y + 85, brk_w, 10), arcade.color.RED)
        self.brk_label.draw()
        
        # Pedal Trace
        self.draw_pedal_trace(current_frame.t, d.throttle, brk_val)
