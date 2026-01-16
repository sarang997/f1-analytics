import arcade
from src.utils.config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, HUD_BG_COLOR, ASH_GREY

# Config
# Config
CHAT_WIDTH = 400
CHAT_HEIGHT = 250
# Place it: 20px from Bottom Edge, to the Right of Leaderboard (300px)
CHAT_X = 300 + 30 
CHAT_Y = 80 # Above seek bar or just above bottom? Seek bar is at Y=50. Let's put it above.
# Y=80 -> Ends at 330.
# Map is at Top Right (Y>400). Safe.
# Race log is Top Center (Y=660). Safe.

class ChatWindow:
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.messages = [] 
        self.current_input = ""
        self.is_active = False 
        self.is_thinking = False
        
        # Colors
        self.bg_color = (20, 20, 20, 230)
        self.header_color = (40, 40, 40, 255)
        self.border_color = (60, 60, 60, 255)
        self.active_border = (0, 255, 0, 255)
        
        # Fonts
        self.title = arcade.Text("VIRTUAL RACE ENGINEER", CHAT_X + 10, CHAT_Y + CHAT_HEIGHT - 25, ASH_GREY, 11, bold=True)
        self.input_text = arcade.Text("", CHAT_X + 10, CHAT_Y + 12, WHITE, 11)
        self.thinking_text = arcade.Text("Processing...", CHAT_X + CHAT_WIDTH - 90, CHAT_Y + 12, arcade.color.YELLOW, 10, italic=True)
        
        # Text object pool for history
        self.max_lines = 10
        self.chat_lines = []
        # Start Y for messages (below header)
        self.msg_start_y = CHAT_Y + CHAT_HEIGHT - 50 
        
        for i in range(self.max_lines):
            # Default to left align, will adjust x per message
            t = arcade.Text("", CHAT_X + 10, self.msg_start_y - (i * 18), WHITE, 11, width=CHAT_WIDTH-30, multiline=True)
            self.chat_lines.append(t)
        
        self.add_message("System", "Radio Check. Race Engineer connected.")

    def add_message(self, sender, text):
        self.messages.append((sender, text))
        if len(self.messages) > 20:
            self.messages.pop(0)

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

    def send_message(self):
        user_msg = self.current_input
        self.add_message("You", user_msg)
        self.is_thinking = True
        
        if hasattr(self, 'context_provider'):
             context = self.context_provider()
             self.ai_client.ask_engineer(user_msg, context, self.on_ai_response)
        else:
             self.add_message("System", "Error: No radio link.")
             self.is_thinking = False

    def on_ai_response(self, response):
        self.is_thinking = False
        self.add_message("Engineer", response)

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

        # 4. Input Area Background
        input_h = 35
        arcade.draw_rect_filled(arcade.rect.XYWH(CHAT_X + CHAT_WIDTH/2, CHAT_Y + input_h/2, CHAT_WIDTH, input_h), (30, 30, 30, 255))
        arcade.draw_line(CHAT_X, CHAT_Y + input_h, CHAT_X + CHAT_WIDTH, CHAT_Y + input_h, self.border_color, 1)

        # 5. History
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

                # Truncate text if too long visually (basic wrap handled by multiline but height is fixed)
                # Ideally limiting chars per line
                clean_text = text.replace('\n', ' ')
                if len(clean_text) > 55: clean_text = clean_text[:52] + "..."
                
                text_obj.text = f"{prefix}{clean_text}"
                text_obj.draw()

        # 6. Input Text
        cursor = "_" if self.is_active else " (Press ENTER)"
        self.input_text.text = f"> {self.current_input}{cursor}"
        self.input_text.draw()
        
        if self.is_thinking:
             self.thinking_text.draw()
