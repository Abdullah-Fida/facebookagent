"""
Configuration Manager for the Omni-Channel Bot.
Loads environment variables and provides validated access to all settings.
"""
import os
import logging
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

logger = logging.getLogger("OmniBot.Config")

@dataclass
class BotConfig:
    """Immutable configuration object loaded from .env"""
    
    # AI (Multi-Key)
    openrouter_api_keys: List[str] = field(default_factory=list)
    huggingface_api_key: str = ""
    bing_cookie: str = ""
    
    # Buffer
    buffer_access_token: str = ""
    
    # Scheduling
    posts_per_day: int = 5

def load_config() -> BotConfig:
    """Loads configuration from .env file and returns a BotConfig object."""
    load_dotenv()
    
    # Parse comma-separated API keys
    raw_keys = os.getenv("OPENROUTER_API_KEYS", "")
    api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    
    if not api_keys:
        logger.warning("No OpenRouter API keys found in .env! AI features will not work.")
    else:
        logger.info(f"Loaded {len(api_keys)} OpenRouter API key(s).")
    
    config = BotConfig(
        openrouter_api_keys=api_keys,
        huggingface_api_key=os.getenv("HUGGINGFACE_API_KEY", ""),
        bing_cookie=os.getenv("BING_COOKIE", ""),
        buffer_access_token=os.getenv("BUFFER_ACCESS_TOKEN", ""),
        posts_per_day=int(os.getenv("POSTS_PER_DAY", "5")),
    )
    
    return config
