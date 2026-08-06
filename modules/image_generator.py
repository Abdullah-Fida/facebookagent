"""
Image Generator Module.
Uses Bing DALL-E 3 for photorealistic, 
cinematic AI-generated news thumbnails.
"""
import logging
import os
import io
import random
import json
from datetime import datetime
from typing import Optional
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

import time

logger = logging.getLogger("OmniBot.ImageGen")

# ── Color palettes for different content categories ───────────────────
COLOR_PALETTES = {
    "tech_ai": {
        "gradient_start": (15, 23, 42),
        "gradient_end": (59, 130, 246),
        "accent": (139, 92, 246),
        "text": (255, 255, 255),
    },
    "tech": {
        "gradient_start": (15, 23, 42),
        "gradient_end": (59, 130, 246),
        "accent": (139, 92, 246),
        "text": (255, 255, 255),
    },
    "business_markets": {
        "gradient_start": (6, 78, 59),
        "gradient_end": (16, 185, 129),
        "accent": (245, 158, 11),
        "text": (255, 255, 255),
    },
    "business": {
        "gradient_start": (6, 78, 59),
        "gradient_end": (16, 185, 129),
        "accent": (245, 158, 11),
        "text": (255, 255, 255),
    },
    "world_news": {
        "gradient_start": (127, 29, 29),
        "gradient_end": (239, 68, 68),
        "accent": (251, 191, 36),
        "text": (255, 255, 255),
    },
    "politics": {
        "gradient_start": (30, 20, 60),
        "gradient_end": (100, 40, 120),
        "accent": (220, 180, 60),
        "text": (255, 255, 255),
    },
    "sports": {
        "gradient_start": (10, 50, 30),
        "gradient_end": (20, 140, 70),
        "accent": (255, 200, 50),
        "text": (255, 255, 255),
    },
    "crypto": {
        "gradient_start": (20, 10, 40),
        "gradient_end": (120, 60, 200),
        "accent": (255, 180, 50),
        "text": (255, 255, 255),
    },
    "pakistan": {
        "gradient_start": (0, 60, 30),
        "gradient_end": (0, 130, 60),
        "accent": (255, 255, 255),
        "text": (255, 255, 255),
    },
    "default": {
        "gradient_start": (30, 30, 50),
        "gradient_end": (80, 80, 120),
        "accent": (100, 200, 255),
        "text": (255, 255, 255),
    }
}

CATEGORY_LABELS = {
    "tech_ai": "TECH / AI",
    "tech": "TECH",
    "business_markets": "BUSINESS",
    "business": "BUSINESS",
    "world_news": "WORLD",
    "politics": "POLITICS",
    "sports": "SPORTS",
    "crypto": "CRYPTO",
    "pakistan": "PAKISTAN",
}


class ImageGenerator:
    """
    Generates branded post header images using Bing Image Creator (DALL-E 3)
    for stunning AI backgrounds with professional Pillow text overlays.
    """
    
    def __init__(self, output_dir: str, channel_name: str = "Daily Pulse PK",
                 bing_cookie: str = ""):
        self.output_dir = output_dir
        self.channel_name = channel_name
        self.bing_cookie = bing_cookie
        self.width = 1280
        self.height = 720
        
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Image Generator initialized. Output: {output_dir}")
    
    def _fetch_bing_image(self, prompt: str) -> Optional[Image.Image]:
        """
        Calls Bing Image Creator (DALL-E 3) to generate an image.
        Returns a PIL Image or None on failure.
        """
        if not self.bing_cookie:
            logger.error("No Bing cookie provided.")
            return None
            
        import asyncio
        from BingImageCreator import ImageGenAsync
        
        async def fetch():
            async_gen = ImageGenAsync(self.bing_cookie)
            try:
                images = await async_gen.get_images(prompt)
                logger.info(f"Bing Image URLs: {images}")
                if not images:
                    return None
                
                # Try finding the first valid OIG image, fallback to first if none
                img_url = images[0]
                for url in images:
                    if "OIG" in url or "mm.bing.net" in url:
                        img_url = url
                        break
                        
                req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = response.read()
                    img = Image.open(io.BytesIO(data)).convert("RGB")
                    
                    # Bing images are 1024x1024. Resize and crop to 1280x720
                    img = img.resize((self.width, self.width), Image.Resampling.LANCZOS)
                    top = (self.width - self.height) // 2
                    bottom = top + self.height
                    img = img.crop((0, top, self.width, bottom))
                    return img
            except Exception as e:
                logger.warning(f"Bing Image generation failed: {e}")
                return None
                
        # Run the async function synchronously
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # If we're already in an async context, this might fail, but ImageGenerator is run in a thread usually.
            import threading
            result = None
            def run_in_thread():
                nonlocal result
                result = asyncio.run(fetch())
            t = threading.Thread(target=run_in_thread)
            t.start()
            t.join()
            return result
        else:
            return loop.run_until_complete(fetch())

    def _create_gradient(self, draw: ImageDraw.Draw, 
                         color_start: tuple, color_end: tuple):
        """Draws a smooth vertical gradient on the image."""
        for y in range(self.height):
            ratio = y / self.height
            r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
    
    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Gets a font, falling back to default if custom font not found."""
        font_names = []
        if bold:
            font_names = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", 
                          "segoeui.ttf", "calibrib.ttf"]
        else:
            font_names = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf",
                          "segoeui.ttf", "calibri.ttf"]
        
        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                continue
        
        # Absolute fallback
        try:
            return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size)
        except:
            return ImageFont.load_default()
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, 
                   max_width: int) -> list:
        """Wraps text to fit within a maximum pixel width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _add_decorative_elements(self, draw: ImageDraw.Draw, accent_color: tuple):
        """Adds subtle geometric decorations to make the image feel premium."""
        # Top-left corner accent line
        draw.line([(40, 40), (200, 40)], fill=accent_color, width=4)
        draw.line([(40, 40), (40, 100)], fill=accent_color, width=4)
        
        # Bottom-right corner accent
        draw.line([(self.width - 200, self.height - 40), 
                   (self.width - 40, self.height - 40)], fill=accent_color, width=4)
        draw.line([(self.width - 40, self.height - 100), 
                   (self.width - 40, self.height - 40)], fill=accent_color, width=4)
        
        # Subtle dot pattern (decorative)
        for i in range(5):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            size = random.randint(2, 5)
            draw.ellipse([(x, y), (x + size, y + size)], fill=accent_color)
    
    def generate(self, headline: str, category: str = "default",
                 source_credit: str = "") -> Optional[str]:
        """
        Generates a branded news image with headline overlay.
        
        Pipeline:
          1. Try Bing DALL-E 3 for a cinematic AI background
          2. Fall back to Pillow gradient if Bing is unavailable
          3. Overlay brand elements: category badge, headline, watermark, timestamp
        
        Args:
            headline: The main headline text (5-15 words)
            category: Content category for color theming
            source_credit: Source attribution text
        
        Returns:
            Path to the saved image, or None on failure.
        """
        try:
            palette = COLOR_PALETTES.get(category, COLOR_PALETTES["default"])
            
            # Category-specific prompt templates for better variety
            if "tech" in category:
                style_prefix = "Cyberpunk, neon lights, high-tech server room, glowing futuristic aesthetic"
            elif "business" in category:
                style_prefix = "Modern glass skyscraper office, Wall Street, professional stock market chart aesthetic"
            elif category == "world_news":
                style_prefix = "Global map hologram, UN assembly hall, professional international news broadcasting desk"
            elif category == "crypto":
                style_prefix = "Golden Bitcoin coins, blockchain network visualization, futuristic digital currency hologram, dark moody lighting"
            elif category == "pakistan":
                style_prefix = "Pakistani cityscape, modern Islamabad or Karachi skyline, South Asian photojournalism"
            elif category == "politics":
                style_prefix = "Parliament building, debate hall, serious political photojournalism, majestic"
            elif category == "sports":
                style_prefix = "Massive sports stadium, dramatic floodlights, intense cinematic action photography"
            else:
                style_prefix = "Ultra high quality cinematic photojournalism photograph"
            
            ai_prompt = (
                f"{style_prefix}, dramatic lighting, shallow depth of field, 8K resolution, "
                f"news category: {category}. "
                f"Visual concept: {headline}. "
                f"No text, no watermarks, no logos, pure photography."
            )
            
            # ── Step 1: Fetch AI Background ───────────────────────
            max_retries = 2
            retry_delay = 5
            img = None
            
            for attempt in range(max_retries):
                img = self._fetch_bing_image(ai_prompt)
                if img:
                    break
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"Bing Image fetch failed. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
            
            # Fallback to gradient if AI image failed
            if not img:
                logger.warning("Bing AI image failed, using gradient fallback.")
                img = Image.new("RGB", (self.width, self.height))
                draw = ImageDraw.Draw(img)
                self._create_gradient(draw, palette["gradient_start"], palette["gradient_end"])
                self._add_decorative_elements(draw, palette["accent"])
            else:
                logger.info("Successfully fetched pure AI background from Bing DALL-E 3.")
            
            # ── Step 2: Save Pure Image ──────────────────────────────────────
            filename = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100,999)}.png"
            filepath = os.path.join(self.output_dir, filename)
            img.save(filepath, "PNG", quality=95)
            
            logger.info(f"Generated pure image: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return None
