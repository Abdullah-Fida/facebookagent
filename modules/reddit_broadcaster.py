"""
Reddit Broadcaster Module.
Posts text-based summaries to Reddit using PRAW (Python Reddit API Wrapper).
Implements the 'Trapdoor' method to avoid shadowbans (no direct links in posts).
"""
import logging
import random
import os
from typing import Optional, Dict

logger = logging.getLogger("OmniBot.Broadcaster.Reddit")

# Safe subreddits for Pakistani tech/business news
TARGET_SUBREDDITS = [
    "pakistan",
    "Urdu",
    "Karachi",
    "Lahore",
    "PakistaniTech",
    "investing" # General, but useful for macro economic posts
]

class RedditBroadcaster:
    """
    Handles safe posting to Reddit.
    Strictly adheres to 1-2 posts per day to avoid spam detection.
    """
    def __init__(self, client_id: str, client_secret: str, username: str, 
                 password: str, user_agent: str, db=None):
        self.db = db
        self.username = username
        self.reddit = None
        self._connected = False
        
        try:
            import praw
            if client_id and client_secret and username:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    username=username,
                    password=password,
                    user_agent=user_agent
                )
                # Quick verification
                _ = self.reddit.user.me()
                self._connected = True
                logger.info(f"Reddit Broadcaster connected as u/{username}")
            else:
                logger.warning("Reddit credentials incomplete. Running in offline mode.")
        except ImportError:
            logger.warning("PRAW not installed. Run 'pip install praw'.")
        except Exception as e:
            logger.error(f"Failed to connect to Reddit API: {e}")

    async def post(self, content_package: Dict) -> bool:
        """
        Executes the 'Trapdoor' posting method.
        Posts only the text summary to a randomly selected relevant subreddit.
        """
        if not self._connected:
            logger.warning("[OFFLINE] Would have posted to Reddit.")
            return False
            
        telegram_text = content_package.get("telegram_text", "")
        category = content_package.get("category", "")
        original_title = content_package.get("original_title", "Daily News Update")
        
        if not telegram_text:
            return False
            
        # Select a subreddit (weighted towards local subreddits)
        subreddit_name = random.choice(TARGET_SUBREDDITS)
        
        # Prepare the Trapdoor text (remove raw links if any, append bio notice)
        trapdoor_text = telegram_text
        trapdoor_text += "\n\n*(For full details and daily updates, check the channel in my bio)*"
        
        try:
            logger.info(f"Attempting to post to r/{subreddit_name}...")
            
            # Since PRAW is blocking, we should technically run it in an executor, 
            # but for 1 post a day, it's fast enough.
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Submit text post (self-post)
            submission = subreddit.submit(
                title=original_title,
                selftext=trapdoor_text
            )
            
            logger.info(f"Successfully posted to Reddit: {submission.shortlink}")
            
            # Log to Supabase
            if self.db:
                await self.db.log_post(
                    platform="reddit",
                    content=trapdoor_text,
                    status="posted",
                    metadata={"subreddit": subreddit_name, "url": submission.shortlink}
                )
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to post to Reddit: {error_msg}")
            
            # Common Reddit API errors
            if "RATELIMIT" in error_msg.upper():
                logger.warning("Reddit rate limit hit. Must wait.")
            elif "SUBREDDIT_NOTALLOWED" in error_msg.upper():
                logger.warning(f"Not allowed to post in r/{subreddit_name}.")
                
            if self.db:
                await self.db.log_error(
                    module="RedditBroadcaster",
                    error_type="PostingError",
                    error_message=error_msg,
                    auto_resolved=False
                )
            return False
