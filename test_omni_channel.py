import os
import asyncio
import logging
import sys

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
from core.config import load_config
from core.brain import BotBrain
from database.supabase_db import SupabaseDB
from modules.telegram_broadcaster import TelegramBroadcaster
from modules.twitter_broadcaster import TwitterBroadcaster
from modules.stealth_marketer import StealthMarketer
from modules.news_scraper import NewsScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test")

async def test_omni_channel():
    # Load env from current dir (omni_channel_bot) and root
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)
    
    config = load_config()
    
    # 1. Supabase Initialization
    logger.info("Initializing Supabase...")
    db = SupabaseDB(url=config.supabase_url, key=config.supabase_key)
    await db.initialize()
    
    # 2. Brain Initialization
    logger.info("Initializing Brain...")
    brain = BotBrain(db=db, weekly_goal=config.weekly_subscriber_goal)
    
    twitter_username = config.twitter_username or os.getenv("TWITTER_USERNAME")
    twitter_password = config.twitter_password or os.getenv("TWITTER_PASSWORD")
    twitter_email = config.twitter_email or os.getenv("TWITTER_EMAIL")
    twitter = TwitterBroadcaster(
        username=twitter_username,
        password=twitter_password,
        email=twitter_email,
        db=db
    )
    
    # 4. Telegram Initialization
    logger.info("Initializing Telegram Broadcaster...")
    telegram_api_id = config.telegram_api_id or int(os.getenv("API_ID", 0))
    telegram_api_hash = config.telegram_api_hash or os.getenv("API_HASH")
    channel_username = config.channel_username or os.getenv("TARGET_GROUP", "@NOVI_NETWORK")
    telegram = TelegramBroadcaster(
        api_id=telegram_api_id,
        api_hash=telegram_api_hash,
        session_string=config.telegram_session_string,
        channel_username=channel_username,
        db=db,
        brain=brain
    )
    await telegram.connect()
    
    # 5. News Scraper Test
    logger.info("Testing News Scraper for Sports Category...")
    scraper = NewsScraper(db=db)
    articles = await scraper.fetch_latest_news(category="sports_news")
    if articles:
        logger.info(f"Successfully scraped sports news. Top story: {articles[0]['title']}")
    else:
        logger.warning("No sports news scraped.")
        
    logger.info("Testing News Scraper for Pakistani Category...")
    pak_articles = await scraper.fetch_latest_news(category="pakistan")
    if pak_articles:
        logger.info(f"Successfully scraped Pakistani news. Top story: {pak_articles[0]['title']}")

    # 6. Brain Memory Test
    logger.info("Testing Brain Memory...")
    brain.record_post(category="crypto", topic="Bitcoin Halving")
    brain.record_post(category="sports_news", topic="T20 World Cup")
    brain.record_post(category="international_news", topic="Fed Interest Rates")
    
    logger.info(f"Brain posted categories: {brain.posted_categories}")
    logger.info(f"Brain posted topics: {brain.posted_topics}")
    
    # 7. Broadcaster Mock Post
    package = {
        "telegram_text": "🚨 **TEST POST** 🚨\nThis is a mock post generated in English to test NOVI's multi-platform capabilities. #NOVI #Test",
        "tweet_text": "🚨 TEST POST 🚨\nThis is a mock post generated in English to test NOVI's multi-platform capabilities. #NOVI #Test",
        "category": "sports_news",
        "original_title": "Test Title"
    }
    
    logger.info("Testing Telegram Post...")
    if telegram.is_ready:
        await telegram.post(package)
    else:
        logger.warning("Telegram Client failed to connect (network issue or invalid session). Post skipped.")
        
    logger.info("Testing Twitter Post...")
    if twitter._connected:
        await twitter.post(package)
    else:
        logger.warning("Twitter API keys missing or invalid. Post skipped.")
        
    # 8. Stealth Marketer Test
    logger.info("Testing Stealth Marketer Initialization...")
    api_id = config.telegram_api_id or int(os.getenv("API_ID", 0))
    api_hash = config.telegram_api_hash or os.getenv("API_HASH")
    phone = config.stealth_phone or config.telegram_phone or os.getenv("PHONE_NUMBER")
    
    class DummyAI:
        async def generate(self, *args, **kwargs):
            return "This is a stealth reply generated in English. Saw this on @NOVI_NETWORK btw."
            
    stealth = StealthMarketer(
        api_id=api_id,
        api_hash=api_hash,
        stealth_phone=phone,
        ai_engine=DummyAI(),
        brain=brain,
        channel_username=channel_username,
        target_groups=["@dummy_competitor"],
        db=db,
        session_string=config.stealth_session_string or config.telegram_session_string
    )
    
    await stealth.connect()
    
    if stealth.client:
        await stealth.activate()
        logger.info(f"Stealth Marketer Status: {stealth.status}")
        reply = await stealth._generate_stealth_reply("What is the price of Bitcoin?")
        logger.info(f"Generated Stealth Reply: {reply}")
        await stealth.deactivate("Test completed.")
    else:
        logger.warning("Stealth Marketer failed to connect (likely missing credentials).")

if __name__ == "__main__":
    asyncio.run(test_omni_channel())
