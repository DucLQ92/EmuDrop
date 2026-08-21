"""
Base view class that provides common functionality for all views.
"""
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple
import sdl2
import math
import time
import os
import ctypes
from utils.theme import Theme
from utils.config import Config
from utils.logger import logger
from utils.i18n import _t, i18n

class BaseView:
    """Base class for all views in the application"""
    
    # Class-level cache for static background and text textures (saves huge CPU load)
    _bg_texture = None
    _bg_texture_size = (0, 0)
    # Ordered by least-recently-used: a cache hit moves its key to the end so
    # the strings drawn every frame are never the ones evicted.
    _text_cache: "OrderedDict[Tuple, Tuple[sdl2.SDL_Texture, int, int]]" = OrderedDict()
    # Fonts are shared process-wide, keyed by (size, bold). Every view used to
    # open its own copy of the same 275KB TTF, and the text cache keys on the
    # font pointer, so sharing also lets views reuse each other's glyph textures.
    _font_cache: Dict[Tuple[int, bool], object] = {}
    
    def __init__(self, renderer, font=None, title_font=None, card_font=None, control_font=None):
        """Initialize the base view with common components and scalable typography"""
        self.renderer = renderer
        self.font = font if font else self._load_font(Config.FONT_SIZE)
        self.title_font = title_font if title_font else (self._load_font(Config.FONT_TITLE_SIZE) or self.font)
        self.card_font = card_font if card_font else (self._load_font(Config.FONT_LARGE_SIZE) or self.font)
        control_font_size = max(15, int(17 * Config.SCALE_FACTOR))
        self.control_font = control_font if control_font else (self._load_font(control_font_size) or self.font)
        self.texture_manager = None
        self._ensure_bg_texture()
        
    @classmethod
    def clear_cache(cls):
        """Clear all cached textures on shutdown or language change"""
        if cls._bg_texture:
            sdl2.SDL_DestroyTexture(cls._bg_texture)
            cls._bg_texture = None
            cls._bg_texture_size = (0, 0)
            
        for tex, _, _ in cls._text_cache.values():
            if tex:
                sdl2.SDL_DestroyTexture(tex)
        cls._text_cache.clear()
        
    @classmethod
    def load_font(cls, size: int = None, bold: bool = True):
        """Open a font through the shared cache, or return the cached instance."""
        font_size = size if size else Config.FONT_SIZE
        cache_key = (font_size, bold)
        cached = cls._font_cache.get(cache_key)
        if cached:
            return cached
            
        font_path = Config.get_font_path()
        if not font_path:
            return None
        try:
            font = sdl2.sdlttf.TTF_OpenFont(font_path.encode('utf-8'), font_size)
            if font:
                if bold:
                    sdl2.sdlttf.TTF_SetFontStyle(font, sdl2.sdlttf.TTF_STYLE_BOLD)
                cls._font_cache[cache_key] = font
                logger.info(f"Font loaded successfully: {font_path} (size={font_size}, bold={bold})")
                return font
        except Exception as e:
            logger.error(f"Failed to load font: {e}")
        return None
        
    @classmethod
    def clear_fonts(cls):
        """Close every cached font. Drops the text cache too, since its keys
        reference font pointers that a later TTF_OpenFont may well reuse."""
        cls.clear_cache()
        for font in cls._font_cache.values():
            try:
                sdl2.sdlttf.TTF_CloseFont(font)
            except Exception:
                pass
        cls._font_cache.clear()
        
    def _ensure_bg_texture(self) -> None:
        """Pre-bake a sleek static gradient background texture once (0.1ms creation, 0 CPU overhead in render loop)"""
        if BaseView._bg_texture:
            return
            
        try:
            w, h = 1, 128
            surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, w, h, 32, sdl2.SDL_PIXELFORMAT_RGBA32)
            if not surface:
                surface = sdl2.SDL_CreateRGBSurface(0, w, h, 32, 0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)
                
            if surface:
                pixels = ctypes.cast(surface.contents.pixels, ctypes.POINTER(ctypes.c_uint32))
                pitch = surface.contents.pitch // 4
                r0, g0, b0 = Theme.BG_DARKER[:3]
                r1, g1, b1 = Theme.BG_DARK[:3]
                
                for y in range(h):
                    prog = y / h
                    r = int(r0 + (r1 - r0) * prog)
                    g = int(g0 + (g1 - g0) * prog)
                    b = int(b0 + (b1 - b0) * prog)
                    pixels[y * pitch] = (255 << 24) | (b << 16) | (g << 8) | r
                        
                BaseView._bg_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
                BaseView._bg_texture_size = (w, h)
                sdl2.SDL_FreeSurface(surface)
        except Exception as e:
            logger.error(f"Error pre-baking background texture: {e}", exc_info=True)
            BaseView._bg_texture = None
        
    def set_texture_manager(self, texture_manager):
        """Set the texture manager instance"""
        self.texture_manager = texture_manager
    
    def get_texture(self, image_path: str) -> Optional[sdl2.SDL_Texture]:
        """Get a texture using the texture manager"""
        if self.texture_manager:
            return self.texture_manager.get_texture(image_path)
        return None
    
    def _load_font(self, size: int = None, bold: bool = True):
        """Load the font with the specified scaled size and bold style"""
        return BaseView.load_font(size, bold)
        
    def render_title(self, title: str) -> None:
        """Render a large bold title at the top of the view"""
        self.render_text(
            title,
            Config.SCREEN_WIDTH // 2,
            int(18 * Config.SCALE_Y),  # Scaled top position
            color=Theme.TEXT_HIGHLIGHT,
            center=True,
            font=self.title_font
        )
        
    def render_background(self, simplified=False) -> None:
        """Render background instantly with 0 CPU overhead using pre-baked GPU texture"""
        try:
            self._ensure_bg_texture()
            if BaseView._bg_texture:
                sdl2.SDL_RenderCopy(self.renderer, BaseView._bg_texture, None, None)
            else:
                sdl2.SDL_SetRenderDrawColor(self.renderer, *Theme.BG_DARK, 255)
                bg_rect = sdl2.SDL_Rect(0, 0, Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
                sdl2.SDL_RenderFillRect(self.renderer, bg_rect)
        except Exception as e:
            logger.error(f"Error rendering background: {e}", exc_info=True)
            
    def render_card(self, x: int, y: int, width: int, height: int, 
                   selected: bool = False, hovered: bool = False) -> None:
        """Render a modern card with shadow and hover effects"""
        try:
            # Scale shadow offset
            shadow_offset = int(4 * Config.SCALE_FACTOR)
            
            # Draw shadow
            shadow_rect = sdl2.SDL_Rect(
                int(x + shadow_offset),
                int(y + shadow_offset),
                int(width),
                int(height)
            )
            sdl2.SDL_SetRenderDrawBlendMode(self.renderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(self.renderer, *Theme.SHADOW_COLOR)
            sdl2.SDL_RenderFillRect(self.renderer, shadow_rect)
            
            # Draw card background
            bg_color = Theme.CARD_SELECTED if selected else Theme.CARD_BG
            if hovered:
                bg_color = Theme.get_hover_color(bg_color)
            
            card_rect = sdl2.SDL_Rect(int(x), int(y), int(width), int(height))
            sdl2.SDL_SetRenderDrawColor(self.renderer, *bg_color, 255)
            sdl2.SDL_RenderFillRect(self.renderer, card_rect)
            
            # Draw border
            sdl2.SDL_SetRenderDrawColor(self.renderer, *Theme.CARD_BORDER, 255)
            sdl2.SDL_RenderDrawRect(self.renderer, card_rect)
            
            # Draw glow effect for selected cards
            if selected:
                glow_size = int(2 * Config.SCALE_FACTOR)
                sdl2.SDL_SetRenderDrawBlendMode(self.renderer, sdl2.SDL_BLENDMODE_BLEND)
                sdl2.SDL_SetRenderDrawColor(self.renderer, *Theme.GLOW_COLOR)
                glow_rect = sdl2.SDL_Rect(
                    int(x - glow_size),
                    int(y - glow_size),
                    int(width + glow_size * 2),
                    int(height + glow_size * 2)
                )
                sdl2.SDL_RenderFillRect(self.renderer, glow_rect)

        except Exception as e:
            logger.error(f"Error rendering card: {e}", exc_info=True)
            
    def get_cached_text_texture(self, text: str, color: tuple = Theme.TEXT_PRIMARY, font=None) -> Tuple[Optional[sdl2.SDL_Texture], int, int]:
        """Get or create cached texture from text using UTF-8 encoding (avoids per-frame font rasterization)"""
        try:
            target_font = font if font else self.font
            if not target_font or not text:
                return None, 0, 0
                
            font_id = ctypes.cast(target_font, ctypes.c_void_p).value
            color_rgb = (int(color[0]), int(color[1]), int(color[2]))
            cache_key = (text, color_rgb, font_id)
            
            cached = BaseView._text_cache.get(cache_key)
            if cached is not None:
                BaseView._text_cache.move_to_end(cache_key)
                return cached
                
            text_color = sdl2.SDL_Color(*color_rgb)
            surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(target_font, text.encode('utf-8'), text_color)
            if surface:
                texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
                width = surface.contents.w
                height = surface.contents.h
                sdl2.SDL_FreeSurface(surface)
                if texture:
                    # LRU eviction: keep the cache bounded to 256 textures
                    while len(BaseView._text_cache) >= 256:
                        _, (old_tex, _, _) = BaseView._text_cache.popitem(last=False)
                        if old_tex:
                            sdl2.SDL_DestroyTexture(old_tex)
                    
                    BaseView._text_cache[cache_key] = (texture, width, height)
                    return texture, width, height
        except Exception as e:
            logger.error(f"Error getting cached text texture: {e}", exc_info=True)
        return None, 0, 0

    def create_text_texture(self, text: str, color: tuple = Theme.TEXT_PRIMARY, font=None) -> Tuple[Optional[sdl2.SDL_Texture], int, int]:
        """Get text texture with caching"""
        return self.get_cached_text_texture(text, color, font)

    def render_text(self, text: str, x: int, y: int, 
                   color: tuple = Theme.TEXT_PRIMARY, 
                   center: bool = False,
                   font=None) -> None:
        """Render text at the specified position using zero-allocation texture caching"""
        try:
            texture, width, height = self.get_cached_text_texture(text, color, font=font)
            if texture:
                if center:
                    x -= width // 2
                rect = sdl2.SDL_Rect(int(x), int(y), int(width), int(height))
                sdl2.SDL_RenderCopy(self.renderer, texture, None, rect)
        except Exception as e:
            logger.error(f"Error rendering text: {e}", exc_info=True)
            
    def _render_page_navigation(self, current_page: int, total_pages: int, search_text_result: str = None) -> None:
        """Render page navigation controls above the bottom controller guide bar with ample padding"""
        page_text = _t("page_info", current=current_page + 1, total=total_pages)
        nav_y = Config.SCREEN_HEIGHT - Config.CONTROL_BOTTOM_MARGIN - int(38 * Config.SCALE_Y)
        
        if search_text_result:
            combined_text = f"{search_text_result}  •  {page_text}"
            self.render_text(
                combined_text,
                Config.SCREEN_WIDTH // 2,
                nav_y,
                color=Theme.TEXT_HIGHLIGHT,
                center=True
            )
        else:
            self.render_text(
                page_text,
                Config.SCREEN_WIDTH // 2,
                nav_y,
                color=Theme.TEXT_SECONDARY,
                center=True
            )

    CONTROL_LABEL_KEYS = {
        "select.png": "select",
        "back.png": "back",
        "downloads.png": "downloads",
        "search.png": "search",
        "sources.png": "sources",
        "settings.png": "settings",
        "pause-resume.png": "pause_resume",
        "grid-controls.png": "move",
        "list-controls.png": "move",
        "previous-page.png": "prev_page",
        "next-page.png": "next_page",
    }

    def _get_texture_dimensions(self, texture) -> Tuple[int, int]:
        """Get the width and height of a texture"""
        if not texture:
            return 0, 0
        w = ctypes.c_int()
        h = ctypes.c_int()
        sdl2.SDL_QueryTexture(texture, None, None, ctypes.byref(w), ctypes.byref(h))
        return w.value, h.value

    def _get_text_size(self, text: str, font=None) -> Tuple[int, int]:
        """Calculate text dimensions using TTF"""
        target_font = font if font else self.font
        if not target_font or not text:
            return (len(text) * 10, 20)
        w = ctypes.c_int()
        h = ctypes.c_int()
        if sdl2.sdlttf.TTF_SizeUTF8(target_font, text.encode('utf-8'), ctypes.byref(w), ctypes.byref(h)) == 0:
            return (w.value, h.value)
        return (len(text) * 10, 20)

    def _render_control_item(self, image_name: str, x: int, y: int) -> int:
        """Render icon texture directly with crisp TTF text label beside it"""
        try:
            actual_image = "sources.png" if image_name == "settings.png" else image_name
            image_path = os.path.join(Config.IMAGES_CONTROLS_DIR, actual_image)
            texture = self.get_texture(image_path)
            if not texture:
                return 0
                
            orig_w, orig_h = self._get_texture_dimensions(texture)
            if orig_h <= 0:
                return 0
                
            aspect_ratio = orig_w / orig_h
            render_height = Config.CONTROL_HEIGHT
            render_width = int(render_height * aspect_ratio)
            
            # 1. Render icon texture directly
            dst_rect = sdl2.SDL_Rect(int(x), int(y), int(render_width), int(render_height))
            sdl2.SDL_RenderCopy(self.renderer, texture, None, dst_rect)
            
            # 2. Render label text next to icon using control_font with caching
            label_key = self.CONTROL_LABEL_KEYS.get(image_name)
            label_text = _t(label_key) if label_key else ""
            if label_text:
                label_tex, label_w, label_h = self.get_cached_text_texture(label_text, (225, 230, 240), font=self.control_font)
                if label_tex:
                    gap = max(4, int(6 * Config.SCALE_FACTOR))
                    text_y = y + (render_height - label_h) // 2
                    text_dst = sdl2.SDL_Rect(int(x + render_width + gap), int(text_y), int(label_w), int(label_h))
                    sdl2.SDL_RenderCopy(self.renderer, label_tex, None, text_dst)
                    return render_width + gap + label_w
                    
            return render_width
        except Exception as e:
            logger.error(f"Error rendering control item {image_name}: {e}", exc_info=True)
            return 0

    def _get_control_item_width(self, image_name: str) -> int:
        """Calculate total width of control icon + label"""
        try:
            actual_image = "sources.png" if image_name == "settings.png" else image_name
            image_path = os.path.join(Config.IMAGES_CONTROLS_DIR, actual_image)
            texture = self.get_texture(image_path)
            if texture:
                orig_w, orig_h = self._get_texture_dimensions(texture)
                if orig_h > 0:
                    render_width = int(Config.CONTROL_HEIGHT * (orig_w / orig_h))
                    label_key = self.CONTROL_LABEL_KEYS.get(image_name)
                    label_text = _t(label_key) if label_key else ""
                    if label_text:
                        l_w, _ = self._get_text_size(label_text, font=self.control_font)
                        gap = max(4, int(6 * Config.SCALE_FACTOR))
                        return render_width + gap + l_w
                    return render_width
        except Exception:
            pass
        return 60

    def render_control_guides(self, controls: Dict[str, List[str]]) -> None:
        """Render control guides at the bottom of the screen with authentic icons and readable TTF text"""
        try:
            bottom_y = Config.SCREEN_HEIGHT - Config.CONTROL_BOTTOM_MARGIN
            item_spacing = max(10, int(14 * Config.SCALE_X))
            
            # Render left controls (e.g. D-Pad, A, B)
            cur_left_x = Config.CONTROL_MARGIN
            for image_name in controls.get('left', []):
                rendered_w = self._render_control_item(image_name, cur_left_x, bottom_y)
                if rendered_w > 0:
                    cur_left_x += rendered_w + item_spacing
            
            # Render right controls (e.g. L, R, Sources, Settings)
            cur_right_x = Config.SCREEN_WIDTH - Config.CONTROL_MARGIN
            for image_name in reversed(controls.get('right', [])):
                item_w = self._get_control_item_width(image_name)
                if cur_right_x - item_w < cur_left_x:
                    break
                cur_right_x -= item_w
                self._render_control_item(image_name, cur_right_x, bottom_y)
                cur_right_x -= item_spacing
                
        except Exception as e:
            logger.error(f"Error rendering control guides: {e}", exc_info=True)
            
    def _render_active_download_count(self, count):
        """Render the active download count"""
        download_text = _t("active_downloads", count=count)
        text_surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(
            self.font,
            download_text.encode('utf-8'),
            sdl2.SDL_Color(*Theme.TEXT_HIGHLIGHT)
        )
        text_width = text_surface.contents.w
        sdl2.SDL_FreeSurface(text_surface)
        
        x_pos = Config.SCREEN_WIDTH - text_width - int(20 * Config.SCALE_X)
        self.render_text(
            download_text,
            x_pos,
            int(18 * Config.SCALE_Y),
            color=Theme.TEXT_HIGHLIGHT,
            center=False
        )