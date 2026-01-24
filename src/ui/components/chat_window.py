import arcade
from src.utils.config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, HUD_BG_COLOR, ASH_GREY

# Config
SIDEBAR_WIDTH = 340
SIDEBAR_X = SCREEN_WIDTH - SIDEBAR_WIDTH
SIDEBAR_Y = 0
SIDEBAR_HEIGHT = SCREEN_HEIGHT

# Tabs
TAB_ENGINEER = 0
TAB_FEED = 1
TAB_STATS = 2

# Quick Action Button Config
BUTTON_WIDTH = 150
BUTTON_HEIGHT = 28
BUTTON_MARGIN = 8

class EngineerSidebar:
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.messages = [] 
        self.current_input = ""
        self.is_active = False 
        self.is_thinking = False
        self.active_tab = TAB_ENGINEER
        
        # Performance/Visuals
        self.bg_color = (10, 10, 12, 235)
        self.panel_color = (20, 20, 25, 255)
        self.accent_color = (255, 24, 1, 255) # F1 Red
        self.border_color = (40, 40, 45, 255)
        self.text_color_main = (240, 240, 240, 255)
        self.text_color_dim = (160, 160, 170, 255)
        
        # Tabs Config
        self.tabs = [
            {"id": TAB_ENGINEER, "label": "ENGINEER"},
            {"id": TAB_FEED, "label": "RACE FEED"},
            {"id": TAB_STATS, "label": "INSIGHTS"}
        ]
        self.tab_width = SIDEBAR_WIDTH / len(self.tabs)
        
        # Quick Actions
        self.quick_actions = [
            {"label": "Gap Analysis", "query": "What's my gap to the cars around me?"},
            {"label": "Tire Strategy", "query": "Analyze my current tire wear and life."},
            {"label": "Pace vs Leader", "query": "How is my pace compared to P1?"},
            {"label": "Pit Window", "query": "When is my predicted pit window?"}
        ]
        self.button_rects = []
        self._calculate_button_positions()
        self.hovered_button = None
        
        # Racing Feed (Sync with RaceControlLog)
        self.feed_messages = []
        
        # Performance: Text Objects for Bubbles
        self.max_bubbles = 10
        self.bubble_senders = [arcade.Text("", 0, 0, WHITE, 8, bold=True) for _ in range(self.max_bubbles)]
        self.bubble_contents = [arcade.Text("", 0, 0, WHITE, 9, width=SIDEBAR_WIDTH - 40, multiline=True) for _ in range(self.max_bubbles)]
        
        # Performance: Text Objects for Feed
        self.max_feed = 15
        self.feed_texts = [arcade.Text("", 0, 0, WHITE, 9, width=SIDEBAR_WIDTH - 40, multiline=True) for _ in range(self.max_feed)]
        
        # Performance: Text Objects for Stats
        self.stats_labels = {
            "title": arcade.Text("TELEMETRY INSIGHTS", SIDEBAR_X + 20, SCREEN_HEIGHT - 80, self.text_color_dim, 9, bold=True),
            "car": arcade.Text("", SIDEBAR_X + 20, SCREEN_HEIGHT - 120, WHITE, 12, bold=True),
            "compound": arcade.Text("", SIDEBAR_X + 20, SCREEN_HEIGHT - 150, WHITE, 11),
            "age": arcade.Text("", SIDEBAR_X + 20, SCREEN_HEIGHT - 180, WHITE, 11),
            "grip": arcade.Text("", SIDEBAR_X + 20, SCREEN_HEIGHT - 210, WHITE, 9),
            "throttle": arcade.Text("", SIDEBAR_X + 20, SCREEN_HEIGHT - 260, ASH_GREY, 10),
            "drs": arcade.Text("", SIDEBAR_X + 20, SCREEN_HEIGHT - 290, ASH_GREY, 10)
        }
        
        self.input_display = arcade.Text("", SIDEBAR_X + 20, SIDEBAR_Y + 35, self.text_color_main, 10)
        self.typing_indicator = arcade.Text("ENGINEER IS TYPING...", SIDEBAR_X + SIDEBAR_WIDTH - 120, SIDEBAR_Y + 80, arcade.color.YELLOW, 8, italic=True)

        self.add_message("System", "Comms Link Established. Ready for input.")

    def _calculate_button_positions(self):
        """Calculate button positions in a grid layout at the bottom of the engineer tab"""
        self.button_rects = []
        start_y = 120  # Height from bottom for buttons
        
        for i, action in enumerate(self.quick_actions):
            row = i // 2
            col = i % 2
            x = SIDEBAR_X + 10 + col * (BUTTON_WIDTH + BUTTON_MARGIN)
            y = start_y - row * (BUTTON_HEIGHT + BUTTON_MARGIN)
            self.button_rects.append({
                'center_x': x + BUTTON_WIDTH/2,
                'center_y': y + BUTTON_HEIGHT/2,
                'width': BUTTON_WIDTH,
                'height': BUTTON_HEIGHT,
                'action': action,
                'id': i
            })

    def add_message(self, sender, text):
        self.messages.append((sender, text))
        if len(self.messages) > 30:  # Increased from 20
            self.messages.pop(0)
    
    def add_proactive_alert(self, alert_text):
        """Add a proactive alert from the race engineer"""
        self.add_message("Engineer", alert_text)

    def on_key_press(self, key, modifiers):
        if not self.is_active:
            if key == arcade.key.ENTER:
                self.is_active = True
                self.current_input = ""
            return

        if key == arcade.key.ENTER:
            if self.current_input.strip():
                self.send_message()
            self.is_active = False
            self.current_input = ""
        elif key == arcade.key.BACKSPACE:
            self.current_input = self.current_input[:-1]
        elif key == arcade.key.ESCAPE:
            self.is_active = False
            self.current_input = ""

    def on_text(self, text):
        if self.is_active:
            self.current_input += text

    def send_message(self, custom_query=None):
        """Send message to AI (either from input or from quick action)"""
        user_msg = custom_query or self.current_input
        self.add_message("You", user_msg)
        self.is_thinking = True
        
        if hasattr(self, 'context_provider'):
             context = self.context_provider()
             # Pass selected driver if available
             selected_driver = getattr(self, 'selected_driver_name', None)
             self.ai_client.ask_engineer(user_msg, context, self.on_ai_response, selected_driver=selected_driver)
        else:
             self.add_message("System", "Error: No radio link.")
             self.is_thinking = False

    def on_ai_response(self, response):
        self.is_thinking = False
        self.add_message("Engineer", response)

    def on_mouse_press(self, x, y):
        # 1. Tab Switching
        if y > SCREEN_HEIGHT - 50:
            tab_idx = int((x - SIDEBAR_X) / self.tab_width)
            if 0 <= tab_idx < len(self.tabs):
                self.active_tab = self.tabs[tab_idx]["id"]
                return True
        
        # 2. Quick Actions (only in Engineer Tab)
        if self.active_tab == TAB_ENGINEER:
            for button in self.button_rects:
                if (abs(x - button['center_x']) < button['width']/2 and 
                    abs(y - button['center_y']) < button['height']/2):
                    self.send_message(custom_query=button['action']['query'])
                    return True
        return False
    
    def on_mouse_motion(self, x, y):
        self.hovered_button = None
        if self.active_tab == TAB_ENGINEER:
            for button in self.button_rects:
                if (abs(x - button['center_x']) < button['width']/2 and 
                    abs(y - button['center_y']) < button['height']/2):
                    self.hovered_button = button['id']
                    break

    def draw(self, current_frame=None, selected_driver=None):
        # 1. Sidebar Base
        arcade.draw_rect_filled(arcade.rect.XYWH(SIDEBAR_X + SIDEBAR_WIDTH/2, SCREEN_HEIGHT/2, SIDEBAR_WIDTH, SCREEN_HEIGHT), self.bg_color)
        arcade.draw_line(SIDEBAR_X, 0, SIDEBAR_X, SCREEN_HEIGHT, self.border_color, 2)
        
        # 2. Draw Tabs
        self._draw_tabs()
        
        # 3. Content Area
        if self.active_tab == TAB_ENGINEER:
            self._draw_engineer_tab()
        elif self.active_tab == TAB_FEED:
            self._draw_feed_tab()
        elif self.active_tab == TAB_STATS:
            self._draw_stats_tab(current_frame, selected_driver)

    def _draw_tabs(self):
        tab_h = 45
        for i, tab in enumerate(self.tabs):
            tx = SIDEBAR_X + i * self.tab_width
            is_active = self.active_tab == tab["id"]
            
            # Tab background
            color = self.panel_color if is_active else self.bg_color
            arcade.draw_rect_filled(arcade.rect.XYWH(tx + self.tab_width/2, SCREEN_HEIGHT - tab_h/2, self.tab_width, tab_h), color)
            
            # Active indicator
            if is_active:
                arcade.draw_rect_filled(arcade.rect.XYWH(tx + self.tab_width/2, SCREEN_HEIGHT - 2, self.tab_width, 4), self.accent_color)
            
            # Label
            text_color = self.text_color_main if is_active else self.text_color_dim
            arcade.draw_text(tab["label"], tx + self.tab_width/2, SCREEN_HEIGHT - tab_h/2, text_color, 10, anchor_x="center", anchor_y="center", bold=is_active)

    def _draw_engineer_tab(self):
        # Subtitle
        arcade.draw_text("LIVE RADIOLINK", SIDEBAR_X + 20, SCREEN_HEIGHT - 80, self.text_color_dim, 9, bold=True)
        
        # Chat History (Bubbles)
        history = list(reversed(self.messages))
        curr_y = 180 
        
        for i in range(min(len(history), self.max_bubbles)):
            sender, text = history[i]
            is_user = sender == "You"
            bubble_color = (40, 40, 50, 255) if is_user else (25, 25, 30, 255)
            
            # Draw bubble
            bh = 50 + (len(text) // 40) * 15
            arcade.draw_rect_filled(arcade.rect.XYWH(SIDEBAR_X + SIDEBAR_WIDTH/2, curr_y + bh/2, SIDEBAR_WIDTH - 20, bh), bubble_color)
            
            # Sender Tag
            tag_color = arcade.color.CYAN if is_user else self.accent_color
            if sender == "System": tag_color = ASH_GREY
            
            self.bubble_senders[i].text = sender.upper()
            self.bubble_senders[i].color = tag_color
            self.bubble_senders[i].position = (SIDEBAR_X + 20, curr_y + bh - 15)
            self.bubble_senders[i].draw()
            
            # Text
            clean_text = text.replace('\n', ' ')
            if len(clean_text) > 120: clean_text = clean_text[:117] + "..."
            
            self.bubble_contents[i].text = clean_text
            self.bubble_contents[i].position = (SIDEBAR_X + 20, curr_y + bh - 35)
            self.bubble_contents[i].draw()
            
            curr_y += bh + 10
            if curr_y > SCREEN_HEIGHT - 120: break

        # Input Area (Fixed at bottom)
        input_y = 40
        arcade.draw_rect_filled(arcade.rect.XYWH(SIDEBAR_X + SIDEBAR_WIDTH/2, input_y, SIDEBAR_WIDTH, 60), (30, 30, 35, 255))
        arcade.draw_line(SIDEBAR_X, input_y + 30, SCREEN_WIDTH, input_y + 30, self.border_color, 1)
        
        cursor = "_" if self.is_active else " (Press ENTER)"
        self.input_display.text = f"> {self.current_input}{cursor}"
        self.input_display.draw()
        
        if self.is_thinking:
            self.typing_indicator.draw()

        # Quick Actions (above input)
        for button in self.button_rects:
            color = (60, 60, 70, 255) if self.hovered_button == button['id'] else (40, 40, 50, 255)
            arcade.draw_rect_filled(arcade.rect.XYWH(button['center_x'], button['center_y'], button['width'], button['height']), color)
            arcade.draw_rect_outline(arcade.rect.XYWH(button['center_x'], button['center_y'], button['width'], button['height']), self.border_color, 1)
            arcade.draw_text(button['action']['label'], button['center_x'], button['center_y'], WHITE, 8, anchor_x="center", anchor_y="center")

    def _draw_feed_tab(self):
        arcade.draw_text("RACE CONTROL LOG", SIDEBAR_X + 20, SCREEN_HEIGHT - 80, self.text_color_dim, 9, bold=True)
        # Populate from feed_messages
        y = SCREEN_HEIGHT - 120
        history = list(reversed(self.feed_messages))
        for i in range(min(len(history), self.max_feed)):
            msg = history[i]
            msg_text = msg.get('message', msg.get('text', 'No content'))
            msg_time = msg.get('time', 0)
            
            display_text = f"[{int(msg_time)}s] {msg_text}"
            if len(display_text) > 120: display_text = display_text[:117] + "..."
            
            self.feed_texts[i].text = display_text
            self.feed_texts[i].position = (SIDEBAR_X + 20, y)
            self.feed_texts[i].draw()
            y -= 45
            if y < 50: break

    def _draw_stats_tab(self, current_frame, selected_driver):
        self.stats_labels["title"].draw()
        
        if not current_frame or selected_driver not in current_frame.drivers:
            arcade.draw_text("No driver selected", SIDEBAR_X + 20, SCREEN_HEIGHT - 120, self.text_color_dim, 10)
            return

        drv = current_frame.drivers[selected_driver]
        
        # Update and Draw Stats
        label_car = self.stats_labels["car"]
        label_car.text = f"CAR: {selected_driver}"
        label_car.draw()
        
        label_comp = self.stats_labels["compound"]
        label_comp.text = f"Compound: {drv.compound}"
        label_comp.draw()
        
        # Tyre Life Visual
        age = drv.tyre_age
        deg_rate = 1.0 if drv.compound == "SOFT" else (0.4 if drv.compound == "HARD" else 0.7)
        grip_est = max(0, 100 - (age * deg_rate))
        age_color = arcade.color.GREEN if grip_est > 80 else (arcade.color.YELLOW if grip_est > 60 else arcade.color.RED)
        
        label_age = self.stats_labels["age"]
        label_age.text = f"Tyre Age: {age} Laps"
        label_age.color = age_color
        label_age.draw()
        
        label_grip = self.stats_labels["grip"]
        label_grip.text = f"Est. Grip: {int(grip_est)}%"
        label_grip.color = age_color
        label_grip.draw()
        
        # Simple Progress Bar for Grip
        bar_w = 200
        arcade.draw_rect_filled(arcade.rect.XYWH(SIDEBAR_X + 20 + bar_w/2, SCREEN_HEIGHT - 225, bar_w, 10), (40, 40, 45, 255))
        arcade.draw_rect_filled(arcade.rect.XYWH(SIDEBAR_X + 20 + (bar_w * (grip_est/100.0))/2, SCREEN_HEIGHT - 225, bar_w * (grip_est/100.0), 10), age_color)

        label_thr = self.stats_labels["throttle"]
        label_thr.text = f"Throttle: {drv.throttle}%"
        label_thr.draw()
        
        drs_active = drv.drs in [10, 12, 14]
        label_drs = self.stats_labels["drs"]
        label_drs.text = f"DRS: {'ENABLED' if drs_active else 'OFF'}"
        label_drs.color = (0, 255, 0) if drs_active else ASH_GREY
        label_drs.draw()
        
        # Simple Chart Placeholder
        arcade.draw_rect_outline(arcade.rect.XYWH(SIDEBAR_X + SIDEBAR_WIDTH/2, 150, SIDEBAR_WIDTH - 40, 120), ASH_GREY)
        arcade.draw_text("LIFE CYCLE ANALYSIS", SIDEBAR_X + SIDEBAR_WIDTH/2, 220, ASH_GREY, 8, anchor_x="center")

