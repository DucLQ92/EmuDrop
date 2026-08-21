"""
Multi-language translation system (i18n) for EmuDrop.
Supports English (en) and Vietnamese (vi).
"""

import json
import os
from typing import Dict, Any

from utils.config import Config
from utils.logger import logger

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # App & General
        "app_title": "EmuDrop",
        "platforms": "Platforms",
        "platform": "Platform",
        "games": "Games",
        "sources": "Sources",
        "source": "Source",
        "downloads": "Downloads",
        "settings": "Settings",
        "about": "About",
        "version": "Version",
        "device": "Device",
        "resolution": "Resolution",
        
        # Navigation & Controls
        "move": "Move",
        "select": "Select",
        "back": "Back",
        "download": "Download",
        "search": "Search",
        "prev_page": "Prev",
        "next_page": "Next",
        "pause_resume": "Pause/Resume",
        "apply": "Apply",
        
        # Pagination & Search & Views
        "page_info": "Page {current} of {total}",
        "search_placeholder": "Search games...",
        "no_games_found": "No games found",
        "found_games": "Found {count} games",
        "active_downloads": "Active Downloads: {count}",
        "hold_to_view": "Hold to view image",
        "loading": "Loading...",
        "loading_platforms": "Loading platforms",
        "loading_game_data": "Loading Game Data",
        "init_sdl": "Initializing SDL",
        "preparing_textures": "Preparing Textures",
        "ready": "Ready",
        "retrieving_games": "Retrieving Games List...",
        "type_to_search": "Type to search games...",
        "no_platforms_found": "No platforms available",
        "no_sources_found": "No sources available",
        
        # Download & Disk Space
        "game_size": "Game Size",
        "free_space": "Free Space",
        "speed": "Speed",
        "size": "Size",
        "eta": "ETA",
        "calculating": "Calculating...",
        "unknown": "Unknown",
        "insufficient_space": "Insufficient Disk Space",
        "free_space_hint": "Please free up some disk space and try again.",
        "download_in_progress": "Download in Progress",
        "already_downloading": "This game is already being downloaded.",
        "queued": "Queued",
        "queued_message": "Waiting for other downloads to complete (Queue: {position})",
        "downloading": "Downloading",
        "processing": "Processing",
        "scraping": "Scraping",
        "scraping_message": "Please wait while cover image is being scraped",
        "cancelling": "Cancelling",
        "cancelling_message": "Please wait while files are being removed",
        
        # Background operations (shown as the download sub-status)
        "op_extracting": "Extracting archive",
        "op_moving_roms": "Moving to ROM folder",
        "op_converting_chd": "Converting to CHD",
        "op_converting_cue": "Converting to CUE",
        "op_converting_bin": "Converting to BIN",
        "op_scraping_covers": "Fetching cover image",
        
        # Error messages raised by the app itself
        "err_no_download_url": "Could not retrieve the download link",
        "err_incomplete_download": "Download incomplete ({got}/{total} bytes)",
        "completed": "Completed",
        "failed": "Failed",
        "error": "Error",
        "paused": "Paused",
        "no_downloads": "No active or recent downloads",
        
        # Dialogs & Confirmations
        "confirm_download": "Download {name}?",
        "confirm_cancel": "Cancel download of {name}?",
        "confirm_exit": "Exit EmuDrop?",
        "yes": "Yes",
        "no": "No",
        "ok": "OK",
        "cancel": "Cancel",
        
        # On-screen keyboard
        "key_space": "Space",
        "key_clear": "Clear",
        "key_return": "Return",
        
        # Settings View
        "settings_title": "System Settings",
        "setting_language": "Language",
        "setting_language_desc": "Select display language",
        "setting_device": "Device Model",
        "setting_resolution": "Resolution",
        "setting_version": "EmuDrop Version",
        "lang_en": "English",
        "lang_vi": "Tiếng Việt",
        "app_tagline": "Cross-platform retro game downloader",
        "hint_change": "Press ◄ ► or A to change",
        "hint_settings_saved": "Settings saved successfully",
        "credits_box_title": "✨ EmuDrop - Custom Edition",
        "credits_mod_by": "👤 Mod & UI Optimization: Unoken",
        "credits_base_on": "🔗 Original Project: Ahmad El-khatib (https://github.com/ahmadteeb/EmuDrop)",
    },
    "vi": {
        # App & General
        "app_title": "EmuDrop",
        "platforms": "Hệ máy",
        "platform": "Hệ máy",
        "games": "Trò chơi",
        "sources": "Nguồn tải",
        "source": "Nguồn",
        "downloads": "Tải xuống",
        "settings": "Cài đặt",
        "about": "Giới thiệu",
        "version": "Phiên bản",
        "device": "Thiết bị",
        "resolution": "Độ phân giải",
        
        # Navigation & Controls
        "move": "Di chuyển",
        "select": "Chọn",
        "back": "Quay lại",
        "download": "Tải game",
        "search": "Tìm kiếm",
        "prev_page": "Trang trước",
        "next_page": "Trang sau",
        "pause_resume": "Tạm dừng / Tiếp tục",
        "apply": "Áp dụng",
        
        # Pagination & Search & Views
        "page_info": "Trang {current} / {total}",
        "search_placeholder": "Tìm kiếm trò chơi...",
        "no_games_found": "Không tìm thấy trò chơi nào",
        "found_games": "Tìm thấy {count} trò chơi",
        "active_downloads": "Đang tải: {count}",
        "hold_to_view": "Giữ để xem ảnh",
        "loading": "Đang tải...",
        "loading_platforms": "Đang tải hệ máy",
        "loading_game_data": "Đang tải dữ liệu trò chơi",
        "init_sdl": "Khởi tạo hệ thống",
        "preparing_textures": "Chuẩn bị giao diện",
        "ready": "Sẵn sàng",
        "retrieving_games": "Đang tải danh sách trò chơi...",
        "type_to_search": "Nhập tên trò chơi để tìm...",
        "no_platforms_found": "Không có hệ máy nào",
        "no_sources_found": "Không có nguồn tải nào",
        
        # Download & Disk Space
        "game_size": "Dung lượng game",
        "free_space": "Dung lượng trống",
        "speed": "Tốc độ",
        "size": "Dung lượng",
        "eta": "Thời gian còn lại",
        "calculating": "Đang tính toán...",
        "unknown": "Chưa rõ",
        "insufficient_space": "Không đủ dung lượng trống",
        "free_space_hint": "Vui lòng giải phóng bộ nhớ và thử lại.",
        "download_in_progress": "Đang trong tiến trình tải",
        "already_downloading": "Trò chơi này đang được tải xuống.",
        "queued": "Chờ tải",
        "queued_message": "Chờ các lượt tải khác hoàn tất (Vị trí: {position})",
        "downloading": "Đang tải",
        "processing": "Đang xử lý",
        "scraping": "Tìm ảnh bìa",
        "scraping_message": "Vui lòng đợi trong khi tải ảnh bìa",
        "cancelling": "Đang hủy",
        "cancelling_message": "Vui lòng đợi trong khi xóa file",
        
        # Background operations (shown as the download sub-status)
        "op_extracting": "Đang giải nén",
        "op_moving_roms": "Đang chuyển vào thư mục ROM",
        "op_converting_chd": "Đang chuyển sang CHD",
        "op_converting_cue": "Đang chuyển sang CUE",
        "op_converting_bin": "Đang chuyển sang BIN",
        "op_scraping_covers": "Đang tải ảnh bìa",
        
        # Error messages raised by the app itself
        "err_no_download_url": "Không lấy được liên kết tải",
        "err_incomplete_download": "Tải chưa hoàn tất ({got}/{total} byte)",
        "completed": "Hoàn tất",
        "failed": "Thất bại",
        "error": "Lỗi",
        "paused": "Tạm dừng",
        "no_downloads": "Chưa có lượt tải nào",
        
        # Dialogs & Confirmations
        "confirm_download": "Tải trò chơi {name}?",
        "confirm_cancel": "Hủy tải trò chơi {name}?",
        "confirm_exit": "Thoát ứng dụng EmuDrop?",
        "yes": "Có",
        "no": "Không",
        "ok": "Đồng ý",
        "cancel": "Hủy",
        
        # On-screen keyboard
        "key_space": "Cách",
        "key_clear": "Xoá hết",
        "key_return": "Xong",
        
        # Settings View
        "settings_title": "Cài đặt Hệ thống",
        "setting_language": "Ngôn ngữ",
        "setting_language_desc": "Chọn ngôn ngữ hiển thị giao diện",
        "setting_device": "Thiết bị",
        "setting_resolution": "Độ phân giải",
        "setting_version": "Phiên bản EmuDrop",
        "lang_en": "English",
        "lang_vi": "Tiếng Việt",
        "app_tagline": "Trình tải game retro đa nền tảng",
        "hint_change": "Nhấn ◄ ► hoặc A để đổi",
        "hint_settings_saved": "Đã lưu cài đặt",
        "credits_box_title": "✨ EmuDrop - Bản Việt Hóa & Tối Ưu Hệ Thống",
        "credits_mod_by": "👤 Mod & Tối ưu giao diện: Unoken",
        "credits_base_on": "🔗 Dự án gốc: Ahmad El-khatib (https://github.com/ahmadteeb/EmuDrop)",
    }
}


class I18nManager:
    """Manages application localization and translation persistence."""
    
    SUPPORTED_LANGUAGES = ["vi", "en"]
    
    def __init__(self):
        self.current_language = "vi"  # Default to Vietnamese
        # Resolve against the binary location, not __file__: under a PyInstaller
        # --onefile build __file__ points inside the temporary _MEIPASS extraction
        # dir, where assets/ does not exist, so the setting could never be read back.
        self.settings_path = os.path.join(Config.ASSETS_DIR, "settings.json")
        self.load_language_setting()
        
    def load_language_setting(self) -> None:
        """Load preferred language from settings.json."""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    lang = data.get("language")
                    if lang in self.SUPPORTED_LANGUAGES:
                        self.current_language = lang
                        logger.info(f"Loaded language setting: {self.current_language}")
        except Exception as e:
            logger.error(f"Error loading language setting: {e}", exc_info=True)

    def save_language_setting(self, lang: str) -> bool:
        """Save preferred language into settings.json."""
        if lang not in self.SUPPORTED_LANGUAGES:
            return False
            
        self.current_language = lang
        try:
            data: Dict[str, Any] = {}
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
            data["language"] = lang
            
            # Write atomically: settings.json is parsed at import time by Config
            # with no error handling, so a half-written file would brick startup.
            tmp_path = f"{self.settings_path}.tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, self.settings_path)
                
            logger.info(f"Saved language setting: {lang}")
            return True
        except Exception as e:
            logger.error(f"Error saving language setting: {e}", exc_info=True)
            return False

    def cycle_language(self, step: int = 1) -> str:
        """Move `step` places through the language list (negative goes back) and save."""
        idx = self.SUPPORTED_LANGUAGES.index(self.current_language)
        new_lang = self.SUPPORTED_LANGUAGES[(idx + step) % len(self.SUPPORTED_LANGUAGES)]
        self.save_language_setting(new_lang)
        return new_lang

    def toggle_language(self) -> str:
        """Advance to the next available language and save."""
        return self.cycle_language(1)

    def get(self, key: str, **kwargs) -> str:
        """Get translated text for the given key with optional formatting."""
        lang_dict = TRANSLATIONS.get(self.current_language, TRANSLATIONS["vi"])
        text = lang_dict.get(key)
        if text is None:
            # Fallback to English, then return key itself
            text = TRANSLATIONS["en"].get(key, key)
            
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


# Global singleton instance
i18n = I18nManager()


def _t(key: str, **kwargs) -> str:
    """Shorthand translation helper."""
    return i18n.get(key, **kwargs)
