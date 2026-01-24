import arcade
import time
from src.utils.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, BG_COLOR,
    SEEK_BAR_X, SEEK_BAR_Y, SEEK_BAR_WIDTH, SEEK_BAR_HEIGHT,
    LEADERBOARD_WIDTH,
    WHITE, RED, ASH_GREY
)
from src.ui.components.leaderboard import Leaderboard
from src.ui.components.track_map import TrackMap
from src.ui.components.telemetry_hud import TelemetryHUD
from src.ui.components.race_control_log import RaceControlLog
from src.ui.components.chat_window import EngineerSidebar
from src.utils.ai_client import AIClient
from src.utils.context_builder import build_race_context
from src.utils.proactive_engineer import ProactiveEngineer
from src.processor.data_manager import DataManager

class F1Dashboard(arcade.Window):
    def __init__(self, year, gp, session_type):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(BG_COLOR)
        
        # 1. Load Data
        print(f"Loading session data for {year} {gp}...")
        self.data = DataManager.load_and_process_session(year, gp, session_type)
        self.frames = self.data.frames
        self.driver_metadata = self.data.driver_metadata
        self.total_laps = self.data.total_laps
        
        # 2. Pre-process Track Layout (Downsampled for performance)
        first_driver = next(iter(self.driver_metadata))
        raw_track = []
        for frame in self.frames:
            if first_driver in frame.drivers:
                d = frame.drivers[first_driver]
                raw_track.append((d.x, d.y))
        
        # Downsample to ~1000 points
        step = max(1, len(raw_track) // 1000)
        self.track_line = raw_track[::step]
        
        # Bounds for map scaling
        all_x = []
        all_y = []
        for frame in self.frames:
            for d in frame.drivers.values():
                all_x.append(d.x)
                all_y.append(d.y)
        
        bounds = (min(all_x), max(all_x), min(all_y), max(all_y)) if all_x else (0,1,0,1)
        
        # 3. Components
        self.leaderboard = Leaderboard(self.driver_metadata)
        self.track_map = TrackMap(self.driver_metadata, self.track_line, bounds)
        self.telemetry_hud = TelemetryHUD(self.driver_metadata)
        self.rc_log = RaceControlLog(self.data.race_control_messages)
        
        # AI Engineer with Proactive Intelligence
        self.ai_client = AIClient()
        self.sidebar = EngineerSidebar(self.ai_client)
        self.proactive_engineer = ProactiveEngineer()
        
        # Wire up sidebar
        self.sidebar.context_provider = self.get_current_context
        self.sidebar.selected_driver_name = None  # Will be updated each frame
        
        # Sync feed messages
        self.sidebar.feed_messages = self.data.race_control_messages
        
        # 4. Playback State
        self.selected_driver = first_driver
        self._frame_index = 0.0
        self._frame_index_int = 0
        self.playback_speed = 1.0
        self.paused = False
        
        # 5. Proactive alert tracking
        self.last_proactive_check_lap = 0
        
        # 6. UI State
        self.blink_timer = 0.0
        self.show_blink = True
        
        # 7. Global Text Objects
        base_x = LEADERBOARD_WIDTH + 40
        self.clock_text = arcade.Text("", base_x, SCREEN_HEIGHT - 40, WHITE, 20, bold=True)
        self.speed_text = arcade.Text("", base_x, SCREEN_HEIGHT - 70, (255, 69, 0), 12) # RED_ORANGE
        self.lap_text = arcade.Text("", base_x, SCREEN_HEIGHT - 100, ASH_GREY, 14, bold=True)

    def on_draw(self):
        self.clear()
        current_frame = self.frames[self._frame_index_int]
        
        # Draw Components
        self.leaderboard.draw(current_frame)
        self.track_map.draw(current_frame, self.show_blink)
        self.telemetry_hud.draw(current_frame, self.selected_driver)
        # self.rc_log.draw(current_frame.t) # Removed in favor of Sidebar Feed
        self.sidebar.draw(current_frame, self.selected_driver)

        # Draw Global HUD
        self.clock_text.text = f"TIME: {current_frame.t:.1f}s"
        self.clock_text.draw()
        self.speed_text.text = f"SPEED: {self.playback_speed}x {'(PAUSED)' if self.paused else ''}"
        self.speed_text.draw()
        self.lap_text.text = f"LAP: {current_frame.lap} / {self.total_laps}"
        self.lap_text.draw()
        
        # Draw Seek Bar
        self._draw_seek_bar()

    def _draw_seek_bar(self):
        # Background
        arcade.draw_rect_filled(arcade.rect.XYWH(SEEK_BAR_X + SEEK_BAR_WIDTH/2, SEEK_BAR_Y, SEEK_BAR_WIDTH, SEEK_BAR_HEIGHT), (50, 50, 50))
        # Progress
        progress_width = (self.frame_index / (len(self.frames) - 1)) * SEEK_BAR_WIDTH
        arcade.draw_rect_filled(arcade.rect.XYWH(SEEK_BAR_X + progress_width/2, SEEK_BAR_Y, progress_width, SEEK_BAR_HEIGHT), RED)
        # Handle
        arcade.draw_circle_filled(SEEK_BAR_X + progress_width, SEEK_BAR_Y, 8, WHITE)

    def on_update(self, delta_time):
        self.blink_timer += delta_time
        if self.blink_timer >= 0.8:
            self.blink_timer = 0.0
            self.show_blink = not self.show_blink

        if self.paused:
            return
            
        frames_to_advance = (delta_time * self.playback_speed) / 0.1
        self.frame_index += frames_to_advance
        
        if self.frame_index >= len(self.frames) - 1:
            self.frame_index = float(len(self.frames) - 1)
            self.paused = True
        
        # Proactive Alerts (check every lap, not every frame)
        current_frame = self.frames[self._frame_index_int]
        if current_frame.lap != self.last_proactive_check_lap and current_frame.lap > 2:
            self.last_proactive_check_lap = current_frame.lap
            self._check_proactive_alerts(current_frame)

    @property
    def frame_index(self): return self._frame_index
    @frame_index.setter
    def frame_index(self, value):
        self._frame_index = max(0.0, min(float(len(self.frames) - 1), value))
        self._frame_index_int = int(self._frame_index)

    def on_key_press(self, key, modifiers):
        # Delegate to Sidebar first
        if self.sidebar.is_active:
            self.sidebar.on_key_press(key, modifiers)
            return

        if key == arcade.key.RIGHT: self.playback_speed += 1.0
        elif key == arcade.key.LEFT: self.playback_speed = max(0.0, self.playback_speed - 1.0)
        elif key == arcade.key.SPACE: self.paused = not self.paused
        elif key == arcade.key.ENTER: 
            # Activate chat
            self.sidebar.on_key_press(key, modifiers)

    def on_text(self, text):
        self.sidebar.on_text(text)

    def get_frame_from_mouse(self, x):
        rel_x = x - SEEK_BAR_X
        progress = max(0.0, min(1.0, rel_x / SEEK_BAR_WIDTH))
        return progress * (len(self.frames) - 1)

    def get_current_context(self):
        """Builds enhanced context for the AI with telemetry and history"""
        current_frame = self.frames[self._frame_index_int]
        
        # Update sidebar with selected driver name
        if self.selected_driver in self.driver_metadata:
            self.sidebar.selected_driver_name = self.driver_metadata[self.selected_driver].name
        
        # Build enhanced context with history
        # Get a window of recent frames (last 500 frames = ~50 seconds at 10Hz)
        history_start = max(0, self._frame_index_int - 500)
        frames_history = self.frames[history_start:self._frame_index_int + 1]
        
        return build_race_context(
            current_frame, 
            self.driver_metadata, 
            self.leaderboard.sorted_drivers,
            selected_driver=self.selected_driver,
            frames_history=frames_history,
            total_laps=self.total_laps
        )
    
    def _check_proactive_alerts(self, current_frame):
        """Check for proactive alerts and send to chat"""
        alerts = self.proactive_engineer.analyze_frame(
            current_frame,
            self.selected_driver,
            self.leaderboard.sorted_drivers,
            frames_history=self.frames[max(0, self._frame_index_int - 500):self._frame_index_int + 1]
        )
        
        for alert in alerts:
            self.sidebar.add_proactive_alert(alert)

    def on_mouse_press(self, x, y, button, modifiers):
        # 0. Check Sidebar (tabs and buttons)
        if self.sidebar.on_mouse_press(x, y):
            return
        
        # 1. Check Seek Bar
        if SEEK_BAR_X <= x <= SEEK_BAR_X + SEEK_BAR_WIDTH and SEEK_BAR_Y - 20 <= y <= SEEK_BAR_Y + 20:
            self.frame_index = self.get_frame_from_mouse(x)
            return

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if SEEK_BAR_X <= x <= SEEK_BAR_X + SEEK_BAR_WIDTH and SEEK_BAR_Y - 20 <= y <= SEEK_BAR_Y + 20:
            self.frame_index = self.get_frame_from_mouse(x)
            self.paused = True # Pause when dragging for better UX
            return

        # 2. Check Track Map Click
        current_frame = self.frames[self._frame_index_int]
        clicked_driver = self.track_map.get_driver_at_pos(x, y, current_frame)
        if clicked_driver:
            self.selected_driver = clicked_driver
            return

        # 3. Check Leaderboard Click
        if x <= LEADERBOARD_WIDTH:
            clicked_driver = self.leaderboard.get_driver_at_pos(x, y)
            if clicked_driver:
                self.selected_driver = clicked_driver
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Track mouse motion for sidebar effects"""
        self.sidebar.on_mouse_motion(x, y)
