"""
Settings View for EmuDrop.
Allows changing language (Vietnamese / English) and viewing device/app information.
"""

import sdl2
import sdl2.sdlttf
from typing import List, Dict, Any, Tuple

from ui.base_view import BaseView
from utils.config import Config
from utils.theme import Theme
from utils.i18n import _t, i18n
from utils.logger import logger


class SettingsView(BaseView):
    """View for configuring application settings."""

    def __init__(self, renderer, font=None, bold_font=None, texture_callback=None):
        super().__init__(renderer, font)
        self.bold_font = bold_font if bold_font else font
        self.selected_index = 0
        self.items_count = 3  # 0: Language, 1: Device, 2: Version

    def handle_navigation(self, direction: int) -> None:
        """Handle Up/Down navigation in settings list."""
        self.selected_index = (self.selected_index + direction) % self.items_count

    def handle_action(self, change_dir: int = 1) -> None:
        """Handle Left/Right or A button action on selected setting."""
        if self.selected_index == 0:
            # Toggle language
            i18n.toggle_language()
            BaseView.clear_cache()

    def render(self, active_downloads_count: int = 0) -> None:
        """Render the Settings view."""
        try:
            # 1. Render Header
            header_y = int(18 * Config.SCALE_Y)
            self.render_text(
                _t("settings_title"),
                Config.CONTROL_MARGIN,
                header_y,
                color=Theme.TEXT_HIGHLIGHT,
                center=False
            )

            # Show active downloads count if any
            if active_downloads_count:
                self._render_active_download_count(active_downloads_count)

            # 2. Render Settings Cards / Items
            card_start_y = int(Config.SCREEN_HEIGHT * 0.14)
            card_w = Config.SCREEN_WIDTH - (Config.CONTROL_MARGIN * 2)
            card_h = max(70, int(85 * Config.SCALE_Y))
            card_spacing = max(12, int(18 * Config.SCALE_Y))

            settings_data = [
                {
                    "title": _t("setting_language"),
                    "desc": _t("setting_language_desc"),
                    "value": f"◄  {_t('lang_vi') if i18n.current_language == 'vi' else _t('lang_en')}  ►",
                    "is_interactive": True,
                    "accent_val": True,
                },
                {
                    "title": _t("setting_device"),
                    "desc": f"Allwinner A133P / {Config.SCREEN_WIDTH}x{Config.SCREEN_HEIGHT}",
                    "value": "TrimUI Brick (4:3)" if Config.SCREEN_WIDTH / Config.SCREEN_HEIGHT < 1.5 else "TrimUI Smart Pro (16:9)",
                    "is_interactive": False,
                    "accent_val": False,
                },
                {
                    "title": _t("setting_version"),
                    "desc": "Cross-Platform Retro Downloader",
                    "value": "v2.1 (ARM64 NextUI)",
                    "is_interactive": False,
                    "accent_val": False,
                }
            ]

            for idx, item in enumerate(settings_data):
                is_selected = (idx == self.selected_index)
                cur_y = card_start_y + idx * (card_h + card_spacing)

                card_rect = sdl2.SDL_Rect(
                    int(Config.CONTROL_MARGIN),
                    int(cur_y),
                    int(card_w),
                    int(card_h)
                )

                # Draw Card Background
                sdl2.SDL_SetRenderDrawBlendMode(self.renderer, sdl2.SDL_BLENDMODE_BLEND)
                if is_selected:
                    # Highlighted selection card
                    sdl2.SDL_SetRenderDrawColor(self.renderer, 45, 75, 115, 230)
                    sdl2.SDL_RenderFillRect(self.renderer, card_rect)
                    
                    # Highlight border
                    sdl2.SDL_SetRenderDrawColor(self.renderer, 90, 160, 255, 255)
                    sdl2.SDL_RenderDrawRect(self.renderer, card_rect)
                    
                    # Subtle inner glow line on left
                    left_bar = sdl2.SDL_Rect(int(Config.CONTROL_MARGIN), int(cur_y), 6, int(card_h))
                    sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 210, 255, 255)
                    sdl2.SDL_RenderFillRect(self.renderer, left_bar)
                else:
                    # Normal card
                    sdl2.SDL_SetRenderDrawColor(self.renderer, 30, 34, 42, 200)
                    sdl2.SDL_RenderFillRect(self.renderer, card_rect)
                    
                    sdl2.SDL_SetRenderDrawColor(self.renderer, 60, 65, 75, 180)
                    sdl2.SDL_RenderDrawRect(self.renderer, card_rect)

                # Draw Setting Title
                title_x = Config.CONTROL_MARGIN + max(16, int(22 * Config.SCALE_X))
                title_y = cur_y + max(10, int(14 * Config.SCALE_Y))
                self.render_text(
                    item["title"],
                    title_x,
                    title_y,
                    color=Theme.TEXT_HIGHLIGHT if is_selected else Theme.TEXT_PRIMARY,
                    center=False,
                    font=self.card_font
                )

                # Draw Setting Description (sub-text)
                desc_y = title_y + max(24, int(30 * Config.SCALE_Y))
                self.render_text(
                    item["desc"],
                    title_x,
                    desc_y,
                    color=Theme.TEXT_SECONDARY,
                    center=False
                )

                # Draw Value on the Right Side of Card
                val_text = item["value"]
                val_w, _ = self._get_text_size(val_text, font=self.card_font)
                right_pad = max(20, int(28 * Config.SCALE_X))
                val_x = Config.SCREEN_WIDTH - Config.CONTROL_MARGIN - val_w - right_pad
                val_y = cur_y + (card_h - Config.FONT_LARGE_SIZE) // 2
                
                val_color = (0, 230, 255) if (is_selected and item["accent_val"]) else Theme.TEXT_ACCENT if item["accent_val"] else Theme.TEXT_PRIMARY
                self.render_text(
                    val_text,
                    val_x,
                    val_y,
                    color=val_color,
                    center=False,
                    font=self.card_font
                )

            # 3. Hint below cards
            hint_y = card_start_y + len(settings_data) * (card_h + card_spacing) + int(10 * Config.SCALE_Y)
            self.render_text(
                _t("hint_change"),
                Config.SCREEN_WIDTH // 2,
                hint_y,
                color=Theme.TEXT_SECONDARY,
                center=True
            )

            # 4. Render Bottom Control Guides
            controls = {
                'left': [
                    "list-controls.png",  # Move
                    "select.png",         # Change
                ],
                'right': [
                    "back.png"            # Back
                ]
            }
            self.render_control_guides(controls)

        except Exception as e:
            logger.error(f"Error rendering settings view: {e}", exc_info=True)
