"""
Telegram Broadcaster Module.
Pushes generated content packages (image + text) directly to the Telegram channel
via the official Telegram Bot API.

Uses python-telegram-bot for reliable delivery with built-in FloodWait protection.
"""
import logging
import asyncio
import os
from typing import Optional, Dict

try:
    from telegram import Bot
except ImportError:
    Bot = None

logger = logging.getLogger("OmniBot.Broadcaster")


class TelegramBroadcaster:
    """
    Handles auto-posting of generated content to the Telegram channel.
    Uses the official Bot API (safe, no risk of ban on the bot itself).
    """

    # Telegram photo upload limit (10MB)
    MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(self, bot_token: str, channel_username: str, 
                 notification_manager=None, db=None):
        """
        Args:
            bot_token: The Telegram Bot Token from @BotFather.
            channel_username: Channel to post to, e.g. '@DailyPulsePK'.
            notification_manager: For sending email notifications after each action.
            db: Supabase DB instance for logging posts.
        """
        self.bot_token = bot_token
        self.channel_username = channel_username
        self.nm = notification_manager
        self.db = db
        self.bot: Optional[Bot] = None
        self._initialized = False
        self.posts_sent = 0

    async def connect(self):
        """Initialize the Telegram Bot client."""
        if not self.bot_token or self.bot_token == "your_bot_token":
            logger.warning("Telegram Bot Token not configured. Broadcaster disabled.")
            return

        if Bot is None:
            logger.error("python-telegram-bot not installed. Run: pip install python-telegram-bot")
            return

        try:
            self.bot = Bot(token=self.bot_token)
            me = await self.bot.get_me()
            self._initialized = True
            logger.info(f"Telegram Broadcaster initialized as @{me.username}")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram Bot: {e}")

    async def post(self, package: Dict) -> bool:
        """
        Publishes a content package to the Telegram channel.
        """
        if not self._initialized:
            logger.warning("Broadcaster not initialized. Skipping broadcast.")
            return False

        telegram_text = package.get("telegram_text", "")
        image_path = package.get("image_path", "")

        if not telegram_text:
            logger.error("Empty telegram_text in package. Aborting broadcast.")
            return False

        try:
            if image_path and os.path.exists(image_path):
                # Validate image size
                file_size = os.path.getsize(image_path)
                if file_size > self.MAX_PHOTO_SIZE_BYTES:
                    logger.warning(f"Image too large ({file_size / 1024 / 1024:.1f}MB). Sending text-only.")
                    await self._send_text_only(telegram_text)
                else:
                    await self._send_photo_with_caption(image_path, telegram_text)
            else:
                logger.info("No image found. Sending text-only post.")
                await self._send_text_only(telegram_text)

            self.posts_sent += 1
            logger.info(f"Successfully broadcast post #{self.posts_sent} to {self.channel_username}")

            # Log to database
            if self.db:
                await self.db.log_post(
                    platform="telegram_channel",
                    content=telegram_text,
                    image_path=image_path or "",
                    status="posted",
                    metadata={"category": package.get("category", ""), 
                              "source_credits": package.get("source_credits", "")}
                )

            # Send detailed email notification for the successful post
            if self.nm:
                title = package.get("original_title", "News Post")
                await self.nm.notify_post_success(
                    title=title,
                    category=package.get('category', 'N/A'),
                    channel=self.channel_username,
                    posts_today=self.posts_sent,
                    total_max=6  # Default max from brain
                )

            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Broadcast failed: {error_msg}")

            # Handle FloodWait specifically
            if "flood" in error_msg.lower() or "retry" in error_msg.lower():
                logger.warning("FloodWait detected! Backing off for 60 seconds.")
                await asyncio.sleep(60)

            if self.nm:
                await self.nm.send_notification(
                    subject="Broadcast FAILED",
                    message=f"Failed to publish post to {self.channel_username}.\nError: {error_msg}",
                    is_critical=True
                )
            return False

    async def _send_photo_with_caption(self, image_path: str, caption: str):
        """Sends a photo with caption to the channel. Truncates caption to Telegram's 1024 char limit."""
        if len(caption) > 1024:
            caption = caption[:1020] + "..."

        with open(image_path, "rb") as photo_file:
            await self.bot.send_photo(
                chat_id=self.channel_username,
                photo=photo_file,
                caption=caption,
                parse_mode="HTML"
            )
        logger.info("Photo + caption sent successfully.")

    async def _send_text_only(self, text: str):
        """Sends a text-only message to the channel."""
        if len(text) > 4096:
            text = text[:4092] + "..."

        await self.bot.send_message(
            chat_id=self.channel_username,
            text=text,
            parse_mode="HTML"
        )
        logger.info("Text-only message sent successfully.")

    async def get_subscriber_count(self) -> int:
        """Returns the current subscriber count of the channel."""
        if not self._initialized or not self.channel_username:
            return 0
        try:
            count = await self.bot.get_chat_member_count(chat_id=self.channel_username)
            return count or 0
        except Exception as e:
            logger.error(f"Failed to get subscriber count: {e}")
            return 0

    async def disconnect(self):
        """Disconnect the Telegram client (no-op for python-telegram-bot)."""
        logger.info("Telegram Broadcaster shut down.")

    @property
    def is_ready(self) -> bool:
        return self._initialized
