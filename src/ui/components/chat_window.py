import arcade
from src.utils.config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, HUD_BG_COLOR, ASH_GREY

# Config
CHAT_WIDTH = 500  # Expanded from 400
CHAT_HEIGHT = 350  # Expanded from 250
# Place it: 20px from Bottom Edge, to the Right of Leaderboard (300px)
CHAT_X = 300 + 30 
CHAT_Y = 80 # Above seek bar or just above bottom? Seek bar is at Y=50. Let's put it above.

# Quick Action Button Config
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 22
BUTTON_MARGIN = 5

class ChatWindow:
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.messages = [] 
        self.current_input = ""
        self.is_active = False 
        self.is_thinking = False
        
        # Colors
        self.bg_color = (20, 20, 20, 240)
        self.header_color = (40, 40, 40, 255)
        self.border_color = (60, 60, 60, 255)
        self.active_border = (0, 255, 0, 255)
        self.button_color = (45, 45, 45, 255)
        self.button_hover_color = (70, 70, 70, 255)
        self.button_text_color = (200, 200, 200, 255)
        
        # Fonts
        self.title = arcade.Text("VIRTUAL RACE ENGINEER", CHAT_X + 10, CHAT_Y + CHAT_HEIGHT - 25, ASH_GREY, 11, bold=True)
        self.input_text = arcade.Text("", CHAT_X + 10, CHAT_Y + 12, WHITE, 10)
        self.thinking_text = arcade.Text("Processing...", CHAT_X + CHAT_WIDTH - 90, CHAT_Y + 12, arcade.color.YELLOW, 10, italic=True)
        
        # Text object pool for history (increased from 10 to 15 lines)
        self.max_lines = 15
        self.chat_lines = []
        # Start Y for messages (below header, above buttons)
        self.msg_start_y = CHAT_Y + CHAT_HEIGHT - 50 
        
        for i in range(self.max_lines):
            # More compact line spacing
            t = arcade.Text("", CHAT_X + 10, self.msg_start_y - (i * 20), WHITE, 10, width=CHAT_WIDTH-20, multiline=True)
            self.chat_lines.append(t)
        
        # Quick Action Buttons
        self.quick_actions = [
            {"label": "Gap to P1", "query": "What's my gap to the leader?"},
            {"label": "Tire Status", "query": "What's my tire status and degradation?"},
            {"label": "Strategy", "query": "What's the optimal strategy from here?"},
            {"label": "Battle", "query": "Who am I racing with right now?"}
        ]
        self.button_rects = []
        self._calculate_button_positions()
        self.hovered_button = None
        
        # Proactive alerts queue
        self.pending_alerts = []
        
        self.add_message("System", "Radio Check. Race Engineer connected.")

    def _calculate_button_positions(self):
        """Calculate button positions in a grid"""
        self.button_rects = []
        buttons_start_y = CHAT_Y + 42  # Just above input area
        
        # 2x2 grid
        for i, action in enumerate(self.quick_actions):
            row = i // 2
            col = i % 2
            x = CHAT_X + 10 + col * (BUTTON_WIDTH + BUTTON_MARGIN)
            y = buttons_start_y - row * (BUTTON_HEIGHT + BUTTON_MARGIN)
            self.button_rects.append({
                'x': x, 'y': y,
                'width': BUTTON_WIDTH,
                'height': BUTTON_HEIGHT,
                'action': action
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
        """Handle quick action button clicks"""
        if self.is_active or self.is_thinking:
            return  # Don't interfere with active input
        
        for button in self.button_rects:
            if (button['x'] <= x <= button['x'] + button['width'] and
                button['y'] <= y <= button['y'] + button['height']):
                # Button clicked!
                self.send_message(custom_query=button['action']['query'])
                return True
        return False
    
    def on_mouse_motion(self, x, y):
        """Track button hover states"""
        self.hovered_button = None
        for i, button in enumerate(self.button_rects):
            if (button['x'] <= x <= button['x'] + button['width'] and
                button['y'] <= y <= button['y'] + button['height']):
                self.hovered_button = i
                break

    def draw(self):
        # 1. Main Background
        arcade.draw_rect_filled(arcade.rect.XYWH(CHAT_X + CHAT_WIDTH/2, CHAT_Y + CHAT_HEIGHT/2, CHAT_WIDTH, CHAT_HEIGHT), self.bg_color)
        
        # 2. Border
        b_col = self.active_border if self.is_active else self.border_color
        arcade.draw_rect_outline(arcade.rect.XYWH(CHAT_X + CHAT_WIDTH/2, CHAT_Y + CHAT_HEIGHT/2, CHAT_WIDTH, CHAT_HEIGHT), b_col, 2)
        
        # 3. Header Bar
        header_h = 35
        arcade.draw_rect_filled(arcade.rect.XYWH(CHAT_X + CHAT_WIDTH/2, CHAT_Y + CHAT_HEIGHT - header_h/2, CHAT_WIDTH, header_h), self.header_color)
        arcade.draw_line(CHAT_X, CHAT_Y + CHAT_HEIGHT - header_h, CHAT_X + CHAT_WIDTH, CHAT_Y + CHAT_HEIGHT - header_h, self.border_color, 1)
        self.title.draw()

        # 4. Quick Action Buttons
        for i, button in enumerate(self.button_rects):
            # Determine color (hover effect)
            btn_color = self.button_hover_color if i == self.hovered_button else self.button_color
            
            # Draw button background
            btn_center_x = button['x'] + button['width'] / 2
            btn_center_y = button['y'] + button['height'] / 2
            arcade.draw_rect_filled(
                arcade.rect.XYWH(btn_center_x, btn_center_y, button['width'], button['height']),
                btn_color
            )
            
            # Draw button border
            arcade.draw_rect_outline(
                arcade.rect.XYWH(btn_center_x, btn_center_y, button['width'], button['height']),
                self.border_color, 1
            )
            
            # Draw button text
            label = button['action']['label']
            arcade.draw_text(
                label, 
                button['x'] + button['width']/2, 
                button['y'] + button['height']/2,
                self.button_text_color, 
                9, 
                anchor_x="center", 
                anchor_y="center",
                bold=False
            )
        
        # 5. Input Area Background
        input_h = 30
        arcade.draw_rect_filled(arcade.rect.XYWH(CHAT_X + CHAT_WIDTH/2, CHAT_Y + input_h/2, CHAT_WIDTH, input_h), (30, 30, 30, 255))
        arcade.draw_line(CHAT_X, CHAT_Y + input_h, CHAT_X + CHAT_WIDTH, CHAT_Y + input_h, self.border_color, 1)

        # 6. Message History
        history = list(reversed(self.messages))
        for i, text_obj in enumerate(self.chat_lines):
            if i < len(history):
                sender, text = history[i]
                
                # Visual Differentiation
                if sender == "You":
                    text_obj.color = arcade.color.CYAN
                    text_obj.bold = False
                    prefix = "You: "
                elif sender == "System":
                    text_obj.color = ASH_GREY
                    text_obj.bold = False
                    prefix = ">> "
                else: # Engineer
                    text_obj.color = arcade.color.YELLOW
                    text_obj.bold = False
                    prefix = "Eng: "

                # Better text wrapping (increased from 55 to 75 chars)
                clean_text = text.replace('\n', ' ')
                max_chars = 75
                if len(clean_text) > max_chars: 
                    clean_text = clean_text[:max_chars-3] + "..."
                
                text_obj.text = f"{prefix}{clean_text}"
                text_obj.draw()

        # 7. Input Text
        cursor = "_" if self.is_active else " (Press ENTER)"
        self.input_text.text = f"> {self.current_input}{cursor}"
        self.input_text.draw()
        
        if self.is_thinking:
             self.thinking_text.draw()

