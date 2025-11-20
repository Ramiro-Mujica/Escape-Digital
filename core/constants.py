import os

# Asset paths
ASSETS_DIR = os.path.join(os.getcwd(), 'assets')
AVATAR_DIR = os.path.join(ASSETS_DIR, 'avatares')
POINTER_PATH = os.path.join(ASSETS_DIR, 'puntero.png')
LIFE_ICON = os.path.join(ASSETS_DIR, 'vida.png')
BG_START = os.path.join(ASSETS_DIR, 'bg_start.jpg')

# Gameplay defaults
DEFAULT_LIVES = 10

# Fonts
DEFAULT_FONT_FAMILY = 'Verdana'
FONT_SIZES = {
    'title': 40,
    'subtitle': 36,
    'text': 28,
    'small': 16,
    'huge': 56,
}

# Color palette (greyscale + accents)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (20, 24, 30)
PANEL_LIGHT = (245, 245, 245)
PANEL_MID = (230, 230, 230)
ACCENT = (20, 20, 20)
MENU_BG = (230, 230, 230)
MENU_BORDER = (0, 0, 0)
ALERT_COLOR = (240, 200, 80)
