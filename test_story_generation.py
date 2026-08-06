import asyncio
from core.config import load_config
from core.ai_engine import AIEngine
import codecs
import sys

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

async def test_story():
    config = load_config()
    ai_engine = AIEngine(config.openrouter_api_keys)
    result = await ai_engine.generate_story()
    print("HEADLINE:", result["headline"])
    print("---------------------------------")
    print(result["story_text"])

if __name__ == "__main__":
    asyncio.run(test_story())
