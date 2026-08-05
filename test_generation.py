import asyncio
import os
from core.config import load_config
from core.ai_engine import AIEngine
from modules.image_generator import ImageGenerator
from modules.content_engine import ContentEngine

async def main():
    print("Loading config...")
    config = load_config()
    
    print("Initializing AI Engine...")
    ai_engine = AIEngine(api_keys=config.openrouter_api_keys)
    
    print("Initializing Image Generator...")
    images_dir = os.path.join(os.path.dirname(__file__), "assets", "generated_images")
    os.makedirs(images_dir, exist_ok=True)
    image_gen = ImageGenerator(output_dir=images_dir, channel_name="Stories", bing_cookie=config.bing_cookie)
    
    print("Initializing Content Engine...")
    content_engine = ContentEngine(ai_engine=ai_engine, image_gen=image_gen)
    
    print("\n--- Generating Story ---")
    package = await content_engine.produce_content_package()
    
    if package:
        with open("sample_post.txt", "w", encoding="utf-8") as f:
            f.write("=== HEADLINE ===\n")
            f.write(package.get("original_title") + "\n\n")
            
            f.write("=== STORY TEXT ===\n")
            f.write(package.get("story_text") + "\n\n")
            
            f.write("=== IMAGE PATH ===\n")
            f.write(package.get("image_path") + "\n")
        print("Success! Output written to sample_post.txt")
    else:
        print("\nFailed to generate package.")

if __name__ == "__main__":
    asyncio.run(main())
