import asyncio
import os
from core.config import load_config
from core.ai_engine import AIEngine

async def test_generation():
    print("Loading config...")
    config = load_config()
    
    print("Initializing AIEngine...")
    ai_engine = AIEngine(config.openrouter_api_keys)
    
    print("Generating story (No image, no posting)...")
    story_package = await ai_engine.generate_story()
    
    if story_package:
        output_text = f"HEADLINE: {story_package['headline']}\n\nSTORY:\n{story_package['story_text']}"
        with open("story_test_output.txt", "w", encoding="utf-8") as f:
            f.write(output_text)
        print("\u2705 Story generated! Check story_test_output.txt")
    else:
        print("\u274c Story generation failed.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_generation())
