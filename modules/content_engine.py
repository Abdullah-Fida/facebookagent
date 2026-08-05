"""
Content Engine Module.
Produces purely AI-generated emotional local Pakistani stories.
"""
import logging
from typing import Optional, Dict
from modules.image_generator import ImageGenerator
from core.ai_engine import AIEngine

logger = logging.getLogger("OmniBot.ContentEngine")

class ContentEngine:
    """
    The core content production pipeline.
    Synthesizes purely AI-generated emotional stories using a Pakistani lens,
    generates branded images, and returns a content package ready for broadcasting.
    """
    
    def __init__(self, ai_engine: AIEngine, image_gen: ImageGenerator):
        self.ai = ai_engine
        self.image_gen = image_gen
        self.posts_generated_today = 0
        logger.info("Content Engine initialized (Pure Story Generation Mode).")
    
    async def produce_content_package(self, progress_callback=None) -> Optional[Dict]:
        """
        Orchestrates the entire content creation flow:
        1. Generate a fictional emotional local Pakistani story
        2. Generate AI image
        """
        logger.info(f"Generating new emotional AI story...")
        
        if progress_callback:
            await progress_callback({"step": "synthesis", "message": f"AI is writing a deeply emotional Pakistani story..."})
        
        # 1. AI Synthesis
        story_result = await self.ai.generate_story()
        
        if not story_result:
            logger.error("AI story generation failed.")
            return None
        
        story_text = story_result["story_text"]
        image_headline = story_result["headline"]
        
        logger.info(f"AI synthesis complete. Story post: {len(story_text)} chars.")
        
        if progress_callback:
            await progress_callback({"step": "image_gen", "message": "Generating cinematic HD AI image..."})
        
        # 2. Image Generation
        image_path = self.image_gen.generate(
            headline=image_headline,
            category="pakistan_local",
            source_credit="AI Generated Story"
        )
        
        if not image_path:
            logger.warning("Image generation failed. Proceeding without image.")
        
        # 3. Build and return content package
        self.posts_generated_today += 1
        
        package = {
            "story_text": story_text,
            "image_path": image_path,
            "category": "pakistan_local",
            "source_credits": "AI Generated Story",
            "original_title": image_headline,
            "source_count": 0,
            "real_image_url": ""
        }
        
        logger.info(f"Content package #{self.posts_generated_today} produced successfully!")
        
        if progress_callback:
            await progress_callback({"step": "complete", "message": "Post is ready!"})
            
        return package
