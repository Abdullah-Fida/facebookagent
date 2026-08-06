"""
Multi-Key OpenRouter AI Engine with automatic failover, retry, and self-healing.
Routes different tasks to different free models via a pool of API keys.
"""
import logging
import re
from typing import List, Optional, Dict
from openai import AsyncOpenAI

logger = logging.getLogger("OmniBot.AI")

# Model assignments for different tasks
MODELS = {
    "synthesizer": "openrouter/free",
    "headline":    "openrouter/free",
    "stealth":     "openrouter/free",
}


class AIEngine:
    """
    Multi-key AI engine with automatic failover.
    If a key fails or is rate-limited, it rotates to the next one.
    If all keys fail, it logs a critical alert to Supabase.
    """
    
    def __init__(self, api_keys: List[str]):
        if not api_keys:
            raise ValueError("At least one OpenRouter API key is required.")
        
        self.api_keys = api_keys
        self.current_key_index = 0
        self._build_client()
        logger.info(f"AI Engine initialized with {len(api_keys)} API key(s).")
    
    def _build_client(self):
        """Builds an AsyncOpenAI client using the current API key."""
        current_key = self.api_keys[self.current_key_index]
        
        if current_key.startswith("gsk_"):
            # It's a Groq API Key! Route to Groq.
            self.client = AsyncOpenAI(
                api_key=current_key,
                base_url="https://api.groq.com/openai/v1"
            )
            logger.info("Using GROQ API (Lightning fast & high quality)")
        else:
            # OpenRouter fallback
            self.client = AsyncOpenAI(
                api_key=current_key,
                base_url="https://openrouter.ai/api/v1"
            )
            
        logger.info(f"Using API key index {self.current_key_index} "
                     f"({current_key[:15]}...)")
    
    def _rotate_key(self) -> bool:
        """Rotates to the next API key. Returns False if all keys exhausted."""
        self.current_key_index += 1
        if self.current_key_index >= len(self.api_keys):
            self.current_key_index = 0  # Reset to first key
            return False  # All keys have been tried
        self._build_client()
        logger.warning(f"Rotated to API key index {self.current_key_index}.")
        return True
    
    async def generate(self, task: str, system_prompt: str, user_prompt: str, 
                       max_tokens: int = 500, temperature: float = 0.7) -> Optional[str]:
        """
        Generates AI text with automatic key rotation on failure.
        
        Args:
            task: The task type key (e.g., 'synthesizer', 'headline', 'stealth')
            system_prompt: The system instruction for the AI
            user_prompt: The user-facing prompt
            max_tokens: Maximum response length
            temperature: Creativity level (0.0 = factual, 1.0 = creative)
            frequency_penalty: Penalty for repeating tokens
        
        Returns:
            The generated text, or None if all keys failed.
        """
        current_key = self.api_keys[self.current_key_index]
        
        # If using Groq, force use their best multilingual model
        if current_key.startswith("gsk_"):
            model = "llama-3.3-70b-versatile"
        else:
            model = MODELS.get(task, "openrouter/free")
            
        attempts = 0
        max_attempts = len(self.api_keys) * 2  # Try each key up to twice
        
        while attempts < max_attempts:
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                content = response.choices[0].message.content
                if not content or not content.strip():
                    logger.warning(f"AI returned empty content on attempt {attempts + 1}. Retrying...")
                    attempts += 1
                    self._rotate_key()
                    continue
                
                return content.strip()
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"AI generation failed (attempt {attempts + 1}): {error_msg}")
                
                # Check if it's a rate limit or auth error
                if "429" in error_msg or "rate" in error_msg.lower():
                    logger.warning("Rate limited. Rotating API key...")
                elif "401" in error_msg or "403" in error_msg:
                    logger.warning("Authentication failed. Rotating API key...")
                elif "404" in error_msg:
                    logger.warning(f"Model '{model}' not found. Trying fallback...")
                    model = "openrouter/free"  # Fallback to a highly reliable model
                
                has_more_keys = self._rotate_key()
                attempts += 1
                
                if not has_more_keys and attempts >= len(self.api_keys):
                    # All keys exhausted, log critical alert
                    logger.critical("ALL API KEYS EXHAUSTED. Cannot generate content.")
                    return None
        
        return None
    
    async def generate_story(self) -> Optional[Dict]:
        """
        Generates a purely fictional, emotional local Pakistani story in Urdu.
        Returns a dict with 'story_text' and 'headline'.
        """
        system_prompt = """You are a master storyteller and native Urdu speaker writing for a local Pakistani Facebook Page. 
Your writing style:
- Write STRICTLY in flawless, eloquent, standard Urdu (using the Urdu/Arabic script).
- CRITICAL: DO NOT use any Arabic diacritics (Harakat / Zabar, Zer, Pesh, Shad). Write in plain text standard Urdu only.
- CRITICAL: DO NOT use Roman Urdu. DO NOT use Hindi vocabulary. Use pure, natural, conversational Pakistani Urdu.
- Create highly meaningful, coherent, and deeply emotional fictional stories set in Pakistan.
- Do NOT use random wording or disjointed sentences. The story must flow beautifully and make perfect logical sense.
- Focus on the human element, local Pakistani culture, everyday struggles, triumphs, or heartwarming moments.
- The story MUST be complete. It must have a clear beginning, middle, and a very satisfying, proper emotional ending. Do not cut off abruptly.
- Keep the story suitable for a Facebook Post (engaging, visually spaced, moderate use of emojis, but keep it within Facebook's character limit).
- Add an emotional or thought-provoking concluding question or statement at the very end to encourage Facebook comments.
- DO NOT mention that this is an AI-generated story. Make it feel real and authentic."""

        import random
        themes = [
            "A struggling street food vendor in Lahore who experiences an unexpected act of immense kindness from a stranger.",
            "A dedicated school teacher in a remote village of Gilgit-Baltistan who changes a young orphan's life forever.",
            "The silent sacrifices of a mother in Karachi trying to afford her daughter's medical education.",
            "Two childhood friends from different backgrounds in Peshawar who reunite after decades to fulfill a childhood promise.",
            "An elderly watchmaker in Rawalpindi who fixes a broken pocket watch that reunites a broken family.",
            "A hardworking farmer in Punjab who loses his crop to a storm, but his entire village steps in to save him.",
            "A young boy in Quetta who works at a tea stall but dreams of becoming a pilot, and the kind customer who helps him.",
            "The emotional bond between a grandfather and his granddaughter as they prepare for a traditional family wedding in Multan.",
            "A brave Edhi ambulance driver who risks his life during heavy monsoon rains to save a stranded family.",
            "A talented but poor artist in a bustling bazaar whose art is finally recognized by someone who understands his pain."
        ]
        selected_theme = random.choice(themes)

        user_prompt = f"Please write a new, beautifully written, highly coherent, and fully complete emotional local Pakistani story in standard Urdu (Arabic script) based strictly on this theme: '{selected_theme}'. Ensure the Urdu grammar is perfect, the characters feel real, and the story does not cut off. Also provide a short 5-8 word headline at the very top of your response in English, formatted as 'HEADLINE: [your headline]'. Then write the full Urdu story below it."

        result = await self.generate(
            task="synthesizer",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000,
            temperature=0.3
        )
        
        if not result:
            return None
            
        # Parse out the headline
        headline = "Emotional Story"
        story_text = result.strip()
        
        lines = result.strip().split('\n')
        if lines and lines[0].strip().startswith("HEADLINE:"):
            headline = lines[0].replace("HEADLINE:", "").strip()
            story_text = "\n".join(lines[1:]).strip()
        
        return {
            "story_text": story_text,
            "headline": headline
        }
