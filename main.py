"""
Facebook News Agent Bot
Main Orchestrator

This is the central entry point. It initializes all modules,
and coordinates content production and broadcasting.
"""
import asyncio
import logging
import sys
import os
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_config
from core.ai_engine import AIEngine
from modules.image_generator import ImageGenerator
from modules.content_engine import ContentEngine
from modules.facebook_broadcaster import FacebookBroadcaster

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("omni_bot.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("OmniBot")


async def main():
    logger.info("=" * 60)
    logger.info("  Facebook News Agent Bot Starting...")
    logger.info("=" * 60)
    
    # 1. Load Configuration
    config = load_config()
    
    # 2. Initialize AI Engine
    ai_engine = AIEngine(api_keys=config.openrouter_api_keys)
    
    # 3. Initialize Modules
    images_dir = os.path.join(os.path.dirname(__file__), "assets", "generated_images")
    image_gen = ImageGenerator(output_dir=images_dir, channel_name="Stories", bing_cookie=config.bing_cookie)
    
    content_engine = ContentEngine(
        ai_engine=ai_engine,
        image_gen=image_gen
    )
    
    # 4. Initialize Facebook Broadcaster
    broadcaster = FacebookBroadcaster(
        page_id=config.facebook_page_id,
        access_token=config.facebook_access_token
    )
    
    # ========================================
    #   MAIN EVENT LOOP
    # ========================================
    logger.info(f"Entering main event loop (Targeting {config.posts_per_day} posts/day)...")
    
    # Calculate sleep time based on posts per day
    if config.posts_per_day > 0:
        sleep_interval = (24 * 3600) / config.posts_per_day
    else:
        sleep_interval = 3600 * 4 # Default 4 hours
        
    while True:
        try:
            logger.info("Starting content production cycle...")
            
            # Add human jitter (disabled for immediate testing)
            jitter = 0
            logger.info(f"Applying human jitter: waiting {jitter:.0f}s before posting...")
            await asyncio.sleep(jitter)
            
            # Produce content
            package = await content_engine.produce_content_package()
            
            if package:
                # Broadcast to Facebook
                success = await broadcaster.post(package)
                if success:
                    logger.info("Post published successfully to Facebook!")
                else:
                    logger.error("Failed to post to Facebook.")
            else:
                logger.warning("Content engine returned empty package.")
                
            logger.info(f"Cycle complete. Sleeping for {sleep_interval/3600:.1f} hours...")
            await asyncio.sleep(sleep_interval)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down...")
            break
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}", exc_info=True)
            await asyncio.sleep(60)
    
    logger.info("Bot shut down gracefully.")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
