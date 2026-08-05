import asyncio
import os
import sys
from core.config import load_config
from core.ai_engine import AIEngine
from modules.image_generator import ImageGenerator
from modules.content_engine import ContentEngine
from modules.facebook_broadcaster import FacebookBroadcaster

async def run_single_post():
    print("Loading config...")
    config = load_config()
    
    print("Initializing components...")
    ai_engine = AIEngine(config.openrouter_api_keys)
    images_dir = os.path.join(os.path.dirname(__file__), "assets", "generated_images")
    image_gen = ImageGenerator(output_dir=images_dir, channel_name="Stories", bing_cookie=config.bing_cookie)
    content_engine = ContentEngine(ai_engine=ai_engine, image_gen=image_gen)
    
    broadcaster = FacebookBroadcaster(
        page_id=config.facebook_page_id,
        access_token=config.facebook_access_token
    )
    
    print("Generating new unique AI story and image...")
    package = await content_engine.produce_content_package()
    
    if not package:
        print("Failed to generate content package.")
        sys.exit(1)
        
    print(f"Attempting to post to Facebook Page: {config.facebook_page_id}")
    success = await broadcaster.post(package)
    
    if success:
        print("✅ SUCCESS! The post is live on your Facebook Page!")
        sys.exit(0)
    else:
        print("❌ FAILED! Check logs for errors.")
        sys.exit(1)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_single_post())
