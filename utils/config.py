import os
import sys
import json

class Config:
    """Application configuration settings"""
    # Application metadata
    APP_NAME = "EmuDrop" 
    
    # Base screen settings (reference resolution)
    BASE_SCREEN_WIDTH = 1280
    BASE_SCREEN_HEIGHT = 720
    
    # Current screen settings
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    
    # Scaling factors
    SCALE_X = SCREEN_WIDTH / BASE_SCREEN_WIDTH
    SCALE_Y = SCREEN_HEIGHT / BASE_SCREEN_HEIGHT
    SCALE_FACTOR = min(SCALE_X, SCALE_Y)  # Use minimum to maintain aspect ratio
    
    FPS_LIMIT_LOW_POWER = 30  # Lower FPS limit for devices like Trimui Smart Pro
    FRAME_TIME = int(1000 / FPS_LIMIT_LOW_POWER)  # Frame time in milliseconds (33.33ms for 30 FPS)

    # Directory paths
    BASE_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")  # For temporary downloads
    
    IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
    IMAGES_CONTROLS_DIR = os.path.join(IMAGES_DIR, 'controls')
    IMAGES_CONSOLES_DIR = os.path.join(IMAGES_DIR, 'consoles')
    IMAGES_CACHE_DIR = os.path.join(IMAGES_DIR, 'cache')
    FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')
    DEFAULT_IMAGE_PATH = os.path.join(IMAGES_DIR, 'default_image.png')

    # Load System OS
    with open(os.path.join(ASSETS_DIR, 'settings.json'), 'r') as f:
        SYSTEMS_OS = json.loads(f.read()).get('os', 'stock')
    
    # Load System Mapping
    with open(os.path.join(ASSETS_DIR, 'systems.json'), 'r') as f:
        SYSTEMS_MAPPING = json.loads(f.read())
    
    # Load Scrapper Config
    with open(os.path.join(ASSETS_DIR, 'settings.json'), 'r') as f:
        scrapper = json.loads(f.read())['scrapper']
        SCRAPER_API_MEDIA_TYPE = scrapper['SCRAPER_API_MEDIA_TYPE']
        SCRAPER_API_MEDIA_WIDTH = scrapper['SCRAPER_API_MEDIA_WIDTH']
        SCRAPER_API_MEDIA_HEIGHT = scrapper['SCRAPER_API_MEDIA_HEIGHT']
        SCRAPER_API_SOFTNAME = scrapper['SCRAPER_API_SOFTNAME']
        SCRAPER_ENCODED_API_USERNAME = scrapper['SCRAPER_ENCODED_API_USERNAME']
        SCRAPER_ENCODED_API_PASSWORD = scrapper['SCRAPER_ENCODED_API_PASSWORD']
        SCRAPER_API_USERSSID = scrapper['SCRAPER_API_USERSSID']
        SCRAPER_API_SSPASS = scrapper['SCRAPER_API_SSPASS']
    
    # Font settings
    BASE_FONT_SIZE = 22
    BASE_FONT_TITLE_SIZE = 34
    BASE_FONT_LARGE_SIZE = 25
    FONT_SIZE = 22
    FONT_TITLE_SIZE = 34
    FONT_LARGE_SIZE = 25
    FONT_NAME = "arial.ttf"

    # Logging settings
    LOG_FILE = f'{APP_NAME}.log'
    LOG_LEVEL = 'INFO'
    
    GAMES_PER_PAGE = 10
    CARDS_PER_ROW = 3
    CARDS_PER_PAGE = 9
    VISIBLE_DOWNLOADS = 5
    MAX_CONCURRENT_DOWNLOADS = 4
    
    # Grid and card initial settings (will be dynamically calculated by update_screen_size)
    GRID_SPACING = 10
    CARD_WIDTH = 250
    CARD_HEIGHT = 180
    CARD_IMAGE_HEIGHT = 120

    # Game list initial settings
    GAME_LIST_ITEM_HEIGHT = 40
    GAME_LIST_SPACING = 12
    GAME_LIST_WIDTH = 450
    GAME_LIST_START_Y = 120
    GAME_LIST_IMAGE_SIZE = 400
    GAME_LIST_CARD_PADDING = 20
    GAME_LIST_SPACING_BETWEEN = 120

    # Control guide initial settings
    CONTROL_HEIGHT = 32
    CONTROL_MARGIN = 25
    CONTROL_BOTTOM_MARGIN = 42
    CONTROL_ITEM_SPACING = 15

    # Dialog initial settings
    DIALOG_WIDTH = 600
    DIALOG_HEIGHT = 300
    DIALOG_PADDING = 30
    DIALOG_LINE_HEIGHT = 26
    DIALOG_TITLE_MARGIN = 35
    DIALOG_MESSAGE_MARGIN = 45
    DIALOG_BUTTON_Y = 220
    DIALOG_BUTTON_X = 250
    DIALOG_BUTTON_WIDTH = 100

    # Image cache settings
    IMAGE_CACHE_MAX_SIZE_MB = 500
    IMAGE_DOWNLOAD_MAX_RETRIES = 3
    IMAGE_DOWNLOAD_RETRY_DELAYS = [1, 3, 5]  # Delays between retries in seconds
    IMAGE_DOWNLOAD_TIMEOUT = (3, 10)  # (connect timeout, read timeout)
    
    # Loading button mapping
    with open(os.path.join(ASSETS_DIR, 'settings.json'), 'r') as f:
        buttons = json.loads(f.read())['keyMapping']
        # Controller button mapping
        CONTROLLER_BUTTON_A = buttons['CONTROLLER_BUTTON_A']      
        CONTROLLER_BUTTON_B = buttons['CONTROLLER_BUTTON_B']     
        CONTROLLER_BUTTON_X = buttons['CONTROLLER_BUTTON_X']      
        CONTROLLER_BUTTON_Y = buttons['CONTROLLER_BUTTON_Y']    
        CONTROLLER_BUTTON_L = buttons['CONTROLLER_BUTTON_L']   
        CONTROLLER_BUTTON_R = buttons['CONTROLLER_BUTTON_R']     
        CONTROLLER_BUTTON_SELECT = buttons['CONTROLLER_BUTTON_SELECT'] 
        CONTROLLER_BUTTON_START = buttons['CONTROLLER_BUTTON_START']  
        
        # D-pad button mappings
        CONTROLLER_BUTTON_UP = buttons['CONTROLLER_BUTTON_UP']     
        CONTROLLER_BUTTON_DOWN = buttons['CONTROLLER_BUTTON_DOWN']   
        CONTROLLER_BUTTON_LEFT = buttons['CONTROLLER_BUTTON_LEFT']  
        CONTROLLER_BUTTON_RIGHT = buttons['CONTROLLER_BUTTON_RIGHT'] 

    CONTROLLER_BUTTON_REPEAT_RATE = 250
    
    # Animation settings
    ANIMATION_DURATION = 300  # milliseconds
    LOADING_ANIMATION_SPEED = 100  # milliseconds per frame
    IMAGE_LOAD_DELAY = 500  # milliseconds to wait before loading game images

    # Download view initial settings
    DOWNLOAD_VIEW_START_Y = 70
    DOWNLOAD_VIEW_ITEM_HEIGHT = 100
    DOWNLOAD_VIEW_SPACING = 12
    DOWNLOAD_VIEW_PROGRESS_BAR_HEIGHT = 16
    DOWNLOAD_VIEW_SIDE_PADDING = 30
    DOWNLOAD_VIEW_INNER_PADDING = 20
    DOWNLOAD_VIEW_TEXT_PADDING = 30
    DOWNLOAD_VIEW_TEXT_START_X = 30
    DOWNLOAD_VIEW_TEXT_Y_OFFSET = 45
    DOWNLOAD_VIEW_SPEED_X_OFFSET = 180
    DOWNLOAD_VIEW_SIZE_X_OFFSET = 450
    DOWNLOAD_VIEW_ETA_X_OFFSET = 700
    DOWNLOAD_VIEW_TEXT_SPACING = 25
    DOWNLOAD_VIEW_MIN_TEXT_SPACING = 15
    DOWNLOAD_VIEW_MAX_TEXT_SPACING = 40

    # Scroll bar initial settings
    SCROLL_BAR_WIDTH = 10
    SCROLL_BAR_HEIGHT = 450
    SCROLL_BAR_X_OFFSET = 18
    SCROLL_BAR_Y_OFFSET = 70
    SCROLL_BAR_MIN_THUMB_HEIGHT = 25
    
    # Network settings
    DOWNLOAD_CHUNK_SIZE = 8192
    TIMEOUT = 10  # seconds
    
    # UI constants
    MAX_TITLE_LENGTH = 50

    @classmethod
    def update_screen_size(cls, width, height):
        """Update screen size and recalculate all scaled dimensions responsively for any aspect ratio (16:9, 4:3, etc.)"""
        cls.SCREEN_WIDTH = width
        cls.SCREEN_HEIGHT = height
        cls.SCALE_X = width / cls.BASE_SCREEN_WIDTH
        cls.SCALE_Y = height / cls.BASE_SCREEN_HEIGHT
        cls.SCALE_FACTOR = min(cls.SCALE_X, cls.SCALE_Y)
        
        # Responsive Font sizing
        font_scale = (cls.SCALE_X + cls.SCALE_Y) / 2
        cls.FONT_SIZE = max(20, int(cls.BASE_FONT_SIZE * font_scale))
        cls.FONT_TITLE_SIZE = max(30, int(cls.BASE_FONT_TITLE_SIZE * font_scale))
        cls.FONT_LARGE_SIZE = max(24, int(cls.BASE_FONT_LARGE_SIZE * font_scale))
        
        # 1. Platform & Source Cards Grid (3x3 layout filling the available area)
        side_margin = int(width * 0.04)
        top_margin = int(height * 0.08)
        bottom_margin = int(height * 0.13)
        grid_w = width - (side_margin * 2)
        grid_h = height - top_margin - bottom_margin
        
        cls.GRID_SPACING = max(8, int(12 * cls.SCALE_FACTOR))
        cls.CARD_WIDTH = (grid_w - (cls.CARDS_PER_ROW - 1) * cls.GRID_SPACING) // cls.CARDS_PER_ROW
        cls.CARD_HEIGHT = (grid_h - (cls.CARDS_PER_ROW - 1) * cls.GRID_SPACING) // cls.CARDS_PER_ROW
        cls.CARD_IMAGE_HEIGHT = int(cls.CARD_HEIGHT * 0.60)
        
        # 2. Games View (10 items filling vertical space, width distributed cleanly)
        game_list_start_y = int(height * 0.10)
        game_list_bottom_y = int(height * 0.09)
        available_game_h = height - game_list_start_y - game_list_bottom_y
        
        cls.GAME_LIST_START_Y = game_list_start_y
        cls.GAME_LIST_SPACING = max(4, int(6 * cls.SCALE_Y))
        cls.GAME_LIST_ITEM_HEIGHT = (available_game_h - (cls.GAMES_PER_PAGE - 1) * cls.GAME_LIST_SPACING) // cls.GAMES_PER_PAGE
        
        # Check aspect ratio (4:3 vs 16:9)
        aspect_ratio = width / height
        if aspect_ratio < 1.5:  # 4:3 (e.g. 1024x768 TrimUI Brick)
            cls.GAME_LIST_WIDTH = int(width * 0.52)
            cls.GAME_LIST_IMAGE_SIZE = min(int(width * 0.38), available_game_h - 10)
            cls.GAME_LIST_SPACING_BETWEEN = int(width * 0.04)
        else:  # 16:9 (e.g. 1280x720 TrimUI Smart Pro)
            cls.GAME_LIST_WIDTH = int(width * 0.46)
            cls.GAME_LIST_IMAGE_SIZE = min(int(width * 0.36), available_game_h - 10)
            cls.GAME_LIST_SPACING_BETWEEN = int(width * 0.08)
            
        cls.GAME_LIST_CARD_PADDING = max(10, int(15 * cls.SCALE_FACTOR))
        
        # 3. Control guides at bottom (icon size: ~24-26px, balanced with TTF text)
        cls.CONTROL_HEIGHT = max(24, int(26 * cls.SCALE_Y))
        cls.CONTROL_MARGIN = max(20, int(24 * cls.SCALE_X))
        cls.CONTROL_BOTTOM_MARGIN = max(28, int(32 * cls.SCALE_Y))
        cls.CONTROL_ITEM_SPACING = max(12, int(16 * cls.SCALE_X))
        
        # 4. Download View (5 items filling vertical area)
        cls.DOWNLOAD_VIEW_START_Y = int(height * 0.09)
        avail_dl_h = height - cls.DOWNLOAD_VIEW_START_Y - int(height * 0.10)
        cls.DOWNLOAD_VIEW_SPACING = max(6, int(10 * cls.SCALE_Y))
        cls.DOWNLOAD_VIEW_ITEM_HEIGHT = (avail_dl_h - (cls.VISIBLE_DOWNLOADS - 1) * cls.DOWNLOAD_VIEW_SPACING) // cls.VISIBLE_DOWNLOADS
        cls.DOWNLOAD_VIEW_SIDE_PADDING = max(15, int(width * 0.03))
        cls.DOWNLOAD_VIEW_PROGRESS_BAR_HEIGHT = max(12, int(16 * cls.SCALE_FACTOR))
        
        cls.DOWNLOAD_VIEW_TEXT_PADDING = max(15, int(30 * cls.SCALE_X))
        cls.DOWNLOAD_VIEW_TEXT_START_X = max(15, int(30 * cls.SCALE_X))
        cls.DOWNLOAD_VIEW_TEXT_Y_OFFSET = int(cls.DOWNLOAD_VIEW_ITEM_HEIGHT * 0.45)
        cls.DOWNLOAD_VIEW_SPEED_X_OFFSET = int(width * 0.18)
        cls.DOWNLOAD_VIEW_SIZE_X_OFFSET = int(width * 0.42)
        cls.DOWNLOAD_VIEW_ETA_X_OFFSET = int(width * 0.65)
        cls.DOWNLOAD_VIEW_TEXT_SPACING = max(15, int(25 * cls.SCALE_X))
        cls.DOWNLOAD_VIEW_MIN_TEXT_SPACING = max(10, int(15 * cls.SCALE_X))
        cls.DOWNLOAD_VIEW_MAX_TEXT_SPACING = max(25, int(40 * cls.SCALE_X))
        
        # Scroll bar
        cls.SCROLL_BAR_WIDTH = max(8, int(10 * cls.SCALE_FACTOR))
        cls.SCROLL_BAR_HEIGHT = cls.VISIBLE_DOWNLOADS * (cls.DOWNLOAD_VIEW_ITEM_HEIGHT + cls.DOWNLOAD_VIEW_SPACING) - cls.DOWNLOAD_VIEW_SPACING
        cls.SCROLL_BAR_X_OFFSET = max(12, int(18 * cls.SCALE_X))
        cls.SCROLL_BAR_Y_OFFSET = cls.DOWNLOAD_VIEW_START_Y
        cls.SCROLL_BAR_MIN_THUMB_HEIGHT = max(20, int(25 * cls.SCALE_FACTOR))
        
        # Dialogs
        cls.DIALOG_WIDTH = min(int(width * 0.85), int(600 * cls.SCALE_FACTOR))
        cls.DIALOG_HEIGHT = min(int(height * 0.60), int(320 * cls.SCALE_FACTOR))
        cls.DIALOG_PADDING = max(20, int(30 * cls.SCALE_FACTOR))
        cls.DIALOG_LINE_HEIGHT = max(20, int(26 * cls.SCALE_FACTOR))
        cls.DIALOG_TITLE_MARGIN = max(25, int(35 * cls.SCALE_FACTOR))
        cls.DIALOG_MESSAGE_MARGIN = max(30, int(45 * cls.SCALE_FACTOR))
        cls.DIALOG_BUTTON_Y = int(cls.DIALOG_HEIGHT * 0.72)
        cls.DIALOG_BUTTON_X = int(cls.DIALOG_WIDTH * 0.40)
        cls.DIALOG_BUTTON_WIDTH = max(80, int(100 * cls.SCALE_FACTOR))

    @classmethod
    def get_font_path(cls):
        """Find a suitable font file"""
        font_files = [
            os.path.join(cls.FONTS_DIR, cls.FONT_NAME),
        ]
        
        for font_path in font_files:
            if os.path.exists(font_path):
                return font_path
        
        return None 