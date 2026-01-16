import arcade
from src.utils.config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, HUD_BG_COLOR, ASH_GREY

# Config
LOG_WIDTH = 300
LOG_HEIGHT = 200
# Move to Top Center (Between Leaderboard and Map)
LOG_X = 300 + 40 # LEADERBOARD_WIDTH + Padding
LOG_Y = SCREEN_HEIGHT - 60 

class RaceControlLog:
    def __init__(self, messages):
        """
        messages: List of dicts {'time': float, 'category': str, 'message': str, 'flag': str}
        """
        self.messages = messages
        # Sort by time just in case
        self.messages.sort(key=lambda x: x['time'])
        
        self.header = arcade.Text("RACE CONTROL", LOG_X + 10, LOG_Y - 20, ASH_GREY, 10, bold=True)
        self.msg_texts = []
        
        # Pre-create N text slots
        self.max_visible = 5
        start_y = LOG_Y - 50
        for i in range(self.max_visible):
            # We will reuse these objects
            t = arcade.Text("", LOG_X + 10, start_y - (i * 30), WHITE, 10, width=LOG_WIDTH-20, multiline=True)
            self.msg_texts.append(t)

    def draw(self, current_time):
        # Filter messages that have happened up to current_time
        # Get the last N messages
        active_msgs = [m for m in self.messages if m['time'] <= current_time]
        recent_msgs = active_msgs[-self.max_visible:]
        
        if not recent_msgs:
            return

        # Background
        # Dynamic height based on visible messages? Or fixed box. Fixed box is cleaner.
        arcade.draw_rect_filled(arcade.rect.XYWH(LOG_X + LOG_WIDTH/2, LOG_Y - LOG_HEIGHT/2, LOG_WIDTH, LOG_HEIGHT), HUD_BG_COLOR)
        arcade.draw_rect_outline(arcade.rect.XYWH(LOG_X + LOG_WIDTH/2, LOG_Y - LOG_HEIGHT/2, LOG_WIDTH, LOG_HEIGHT), ASH_GREY, 1)
        
        self.header.draw()
        
        # Draw messages (reversed so newest is at bottom? Or top?)
        # Let's put newest at the bottom naturally. 
        # Actually standard feed is Newest at Top usually? Or Bottom (Matrix style)?
        # Let's do Newest at BOTTOM for a log feed.
        
        # Recent msgs is [Oldest -> Newest] among the slice
        for i, msg in enumerate(recent_msgs):
            # i=0 is oldest in this slice (top), i=4 is newest (bottom)
            text_obj = self.msg_texts[i]
            
            # Format: [LAP/TIME] Message
            # But we only have SessionTime.
            # Let's just show the message content.
            content = msg['message']
            
            # Color coding
            color = WHITE
            if "YELLOW" in content or "YELLOW" in str(msg['flag']):
                color = arcade.color.YELLOW
            elif "RED" in content or "RED" in str(msg['flag']):
                color = arcade.color.RED
            elif "SAFETY CAR" in content:
                color = arcade.color.ORANGE
            elif "GREEN" in content:
                color = arcade.color.GREEN
            elif "PENALTY" in content: # Black/White flag usually
                 pass # Keep white
            
            text_obj.text = content
            text_obj.color = color
            text_obj.draw()
