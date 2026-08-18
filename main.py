import argparse
import sys
from typing import NoReturn
from app import GameDownloaderApp
from utils.logger import logger

DEVICE_PRESETS = {
    'brick': (1024, 768, 'TrimUI Brick (1024x768 4:3)'),
    'smart-pro': (1280, 720, 'TrimUI Smart Pro (1280x720 16:9)'),
    'rg35xx': (640, 480, 'Anbernic RG35XX (640x480 4:3)'),
    'cube': (720, 720, 'RG CubeXX (720x720 1:1)'),
}

def main() -> NoReturn:
    """
    Main entry point for the game downloader application.
    
    Initializes the GameDownloaderApp and handles any uncaught exceptions,
    ensuring they are properly logged before the application exits.
    """
    try:
        # Load .env file if in development
        if not getattr(sys, 'frozen', False):
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("Environment variables have been loaded successfully from .env file")
            
        parser = argparse.ArgumentParser(description="EmuDrop - Game ROM Downloader")
        parser.add_argument('--device', '-d', choices=list(DEVICE_PRESETS.keys()), default=None,
                            help="Simulate specific handheld device screen (brick, smart-pro, rg35xx, cube)")
        parser.add_argument('--width', '-W', type=int, default=None, help="Custom window width in pixels")
        parser.add_argument('--height', '-H', type=int, default=None, help="Custom window height in pixels")
        args, _ = parser.parse_known_args()

        target_w, target_h = None, None
        if args.device:
            target_w, target_h, name = DEVICE_PRESETS[args.device]
            logger.info(f"Simulating device: {name}")
        elif args.width and args.height:
            target_w, target_h = args.width, args.height
            logger.info(f"Using custom window size: {target_w}x{target_h}")
        elif not getattr(sys, 'frozen', False) and sys.platform == 'darwin':
            # Default on macOS desktop dev: 1024x768 (TrimUI Brick)
            target_w, target_h = 1024, 768
            logger.info("macOS desktop debug mode: using 1024x768 (TrimUI Brick preset)")

        app = GameDownloaderApp(target_width=target_w, target_height=target_h)
        app.run()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()