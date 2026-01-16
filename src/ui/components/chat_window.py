import arcade
from src.utils.config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, HUD_BG_COLOR, ASH_GREY

# Config
CHAT_WIDTH = 350
CHAT_HEIGHT = 200
CHAT_X = 20
CHAT_Y = 140 # Above bottom left, below... something? 
# If Leaderboard is Left, we might overlap. Leaderboard is Full Height on Left.
# Leaderboard width is 300.
# So CHAT_X must be > 300.
# Let's put Chat Window in the Bottom Center/Left area, to the right of Leaderboard.
# Leaderboard ends at 300.
CHAT_X = 300 + 40 
CHAT_Y = 150 # Height 200 -> Ends at 250. 
# Telemetry HUD is at Right.
# Seek Bar is at Bottom Center.
# This should be safe.

class ChatWindow:
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.messages = [] # List of (sender, text)
        self.current_input = ""
        self.is_active = False # Is typing
        self.is_thinking = False
        
        self.title = arcade.Text("VIRTUAL RACE ENGINEER", CHAT_X + 10, CHAT_Y + CHAT_HEIGHT - 20, ASH_GREY, 10, bold=True)
        self.input_text = arcade.Text("> ", CHAT_X + 10, CHAT_Y + 10, WHITE, 12)
        self.thinking_text = arcade.Text("Thinking...", CHAT_X + CHAT_WIDTH - 80, CHAT_Y + 10, arcade.color.YELLOW, 10, italic=True)
        
        # Text object pool for history
        self.max_lines = 12
        self.chat_lines = []
        start_y = CHAT_Y + CHAT_HEIGHT - 40
        for i in range(self.max_lines):
            t = arcade.Text("", CHAT_X + 10, start_y - (i * 15), WHITE, 10, width=CHAT_WIDTH-20)
            self.chat_lines.append(t)
        
        # Initial greeting
        self.add_message("System", "Radio Check. Race Engineer connected.")

    def add_message(self, sender, text):
        self.messages.append((sender, text))
        # Keep history manageable
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
        else:
            pass 

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
             self.add_message("System", "Error: No radio link (Context missing).")
             self.is_thinking = False

    def on_ai_response(self, response):
        self.is_thinking = False
        self.add_message("Engineer", response)

    def draw(self):
        # Background
        arcade.draw_rect_filled(arcade.rect.XYWH(CHAT_X + CHAT_WIDTH/2, CHAT_Y + CHAT_HEIGHT/2, CHAT_WIDTH, CHAT_HEIGHT), HUD_BG_COLOR)
        color = arcade.color.GREEN if self.is_active else ASH_GREY
        arcade.draw_rect_outline(arcade.rect.XYWH(CHAT_X + CHAT_WIDTH/2, CHAT_Y + CHAT_HEIGHT/2, CHAT_WIDTH, CHAT_HEIGHT), color, 1)
        
        self.title.draw()
        
        # Draw History using pool
        # reversed(messages) -> Newest first
        history = list(reversed(self.messages))
        
        for i, text_obj in enumerate(self.chat_lines):
            if i < len(history):
                sender, text = history[i]
                color = arcade.color.CYAN if sender == "You" else (arcade.color.YELLOW if sender == "Engineer" else ASH_GREY)
                text_obj.text = f"{sender}: {text}"
                text_obj.color = color
                text_obj.draw()
            else:
                # Clear unused lines (or just don't draw them)
                # Not drawing is better
                pass

        # Draw Input Area
        self.input_text.text = f"> {self.current_input}" + ("_" if self.is_active else " (Press ENTER to talk)")
        self.input_text.draw()
        
        if self.is_thinking:
             self.thinking_text.draw()
