import os

# --- PATHS ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# --- DASHBOARD CONFIG ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "F1 Telemetry Dashboard"

# Layout Zones (Pixels)
LEADERBOARD_WIDTH = 300
SIDEBAR_WIDTH = 340 # New Engineer Sidebar

MAP_BOX_W = 450
MAP_BOX_H = 350
MAP_START_X = SCREEN_WIDTH - SIDEBAR_WIDTH - MAP_BOX_W - 20
MAP_START_Y = SCREEN_HEIGHT - MAP_BOX_H - 120 # Above HUD area

# Seek Bar
SEEK_BAR_WIDTH = SCREEN_WIDTH - LEADERBOARD_WIDTH - SIDEBAR_WIDTH - 40
SEEK_BAR_HEIGHT = 10
SEEK_BAR_X = LEADERBOARD_WIDTH + 20
SEEK_BAR_Y = 50

# Telemetry HUD
HUD_WIDTH = 550
HUD_HEIGHT = 200
HUD_X = SCREEN_WIDTH - SIDEBAR_WIDTH - HUD_WIDTH - 20
HUD_Y = 50 + 40 # Above seek bar
HUD_BG_COLOR = (20, 20, 20, 220)

# --- COLORS ---
BG_COLOR = (15, 15, 15)
PANEL_COLOR = (25, 25, 25)
ITEM_BG_COLOR = (40, 40, 40)
SEEK_BAR_BG = (50, 50, 50)
ASH_GREY = (178, 190, 181) # approx from arcade.color.ASH_GREY
LIGHT_YELLOW = (255, 255, 150)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
DARK_GRAY = (64, 64, 64)

COMPOUND_COLORS = {
    "SOFT": (255, 0, 0),        # Red
    "MEDIUM": (255, 255, 0),    # Yellow
    "HARD": (255, 255, 255),    # White
    "INTERMEDIATE": (0, 255, 0),# Green
    "WET": (0, 0, 255),         # Blue
    "UNKNOWN": (128, 128, 128)  # Grey
}

# --- TRACK STATUS MAPPING ---
STATUS_NAMES = {
    1: "TRACK CLEAR",
    2: "YELLOW FLAG",
    4: "SAFETY CAR",
    5: "RED FLAG",
    6: "VIRTUAL SAFETY CAR",
    7: "VSC ENDING"
}
