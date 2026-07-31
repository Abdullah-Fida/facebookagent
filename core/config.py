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
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    
    # AI (Multi-Key)
    openrouter_api_keys: List[str] = field(default_factory=list)
    huggingface_api_key: str = ""
    bing_cookie: str = ""
    
    # Telegram
    telegram_bot_token: str = ""
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_phone: str = ""
    stealth_phone: str = ""  # Burner phone for stealth marketer
    channel_username: str = ""
    admin_user_id: int = 0
    target_stealth_groups: List[str] = field(default_factory=list)
    
    # X (Twitter)
    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_secret: str = ""
    
    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_username: str = ""
    reddit_password: str = ""
    reddit_user_agent: str = ""
    
    # Brain Goals
    weekly_subscriber_goal: int = 100
    max_daily_reddit_posts: int = 2
    max_daily_x_posts: int = 5
    max_daily_telegram_replies: int = 8
    
    # Notifications
    email_sender: str = ""
    email_app_password: str = ""
    email_receiver: str = ""
    whatsapp_phone: str = ""
    whatsapp_api_key: str = ""


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
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_KEY", ""),
        openrouter_api_keys=api_keys,
        huggingface_api_key=os.getenv("HUGGINGFACE_API_KEY", ""),
        bing_cookie=os.getenv("BING_COOKIE", ""),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_api_id=int(os.getenv("TELEGRAM_API_ID", "0")),
        telegram_api_hash=os.getenv("TELEGRAM_API_HASH", ""),
        telegram_phone=os.getenv("TELEGRAM_PHONE", ""),
        stealth_phone=os.getenv("STEALTH_PHONE", ""),
        channel_username=os.getenv("CHANNEL_USERNAME", ""),
        admin_user_id=int(os.getenv("ADMIN_USER_ID", "0")),
        target_stealth_groups=[g.strip() for g in os.getenv("TARGET_STEALTH_GROUPS", "").split(",") if g.strip()],
        x_api_key=os.getenv("X_API_KEY", ""),
        x_api_secret=os.getenv("X_API_SECRET", ""),
        x_access_token=os.getenv("X_ACCESS_TOKEN", ""),
        x_access_secret=os.getenv("X_ACCESS_SECRET", ""),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        reddit_username=os.getenv("REDDIT_USERNAME", ""),
        reddit_password=os.getenv("REDDIT_PASSWORD", ""),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", ""),
        weekly_subscriber_goal=int(os.getenv("WEEKLY_SUBSCRIBER_GOAL", "100")),
        max_daily_reddit_posts=int(os.getenv("MAX_DAILY_REDDIT_POSTS", "2")),
        max_daily_x_posts=int(os.getenv("MAX_DAILY_X_POSTS", "5")),
        max_daily_telegram_replies=int(os.getenv("MAX_DAILY_TELEGRAM_REPLIES", "8")),
        email_sender=os.getenv("EMAIL_SENDER", ""),
        email_app_password=os.getenv("EMAIL_APP_PASSWORD", ""),
        email_receiver=os.getenv("EMAIL_RECEIVER", ""),
        whatsapp_phone=os.getenv("WHATSAPP_PHONE", ""),
        whatsapp_api_key=os.getenv("WHATSAPP_API_KEY", ""),
    )
    
    return config
