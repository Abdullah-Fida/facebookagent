import logging
import requests
from typing import Dict

logger = logging.getLogger("OmniBot.FacebookBroadcaster")

class FacebookBroadcaster:
    """
    Broadcaster for posting content directly to a Facebook Page Timeline.
    Uses the Facebook Graph API.
    """
    def __init__(self, page_id: str, access_token: str):
        self.page_id = page_id
        self.access_token = access_token
        # v19.0 is a stable recent Graph API version
        self.base_url = f"https://graph.facebook.com/v19.0/{self.page_id}"
        
        if not self.page_id or not self.access_token:
            logger.warning("Facebook Broadcaster initialized without page_id or access_token. Posting will fail or be skipped.")

    async def post(self, package: Dict) -> bool:
        """
        Posts content to the Facebook page timeline.
        The package should contain 'story_text' and 'image_path'.
        """
        if not self.page_id or not self.access_token:
            logger.error("Missing Facebook credentials.")
            return False
            
        try:
            image_path = package.get("image_path")
            story_text = package.get("story_text", "")
            
            if image_path:
                return self._post_photo(story_text, image_path)
            else:
                return self._post_text(story_text)
                
        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")
            return False

    def _post_photo(self, message: str, image_path: str) -> bool:
        url = f"{self.base_url}/photos"
        
        try:
            with open(image_path, "rb") as image_file:
                payload = {
                    "message": message,
                    "access_token": self.access_token
                }
                files = {
                    "source": image_file
                }
                logger.info("Uploading photo to Facebook...")
                response = requests.post(url, data=payload, files=files)
                response.raise_for_status()
                logger.info(f"Successfully posted photo to Facebook! ID: {response.json().get('id')}")
                return True
        except Exception as e:
            logger.error(f"Error posting photo to Facebook: {e}")
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                logger.error(f"FB Error Details: {e.response.text}")
            return False

    def _post_text(self, message: str) -> bool:
        url = f"{self.base_url}/feed"
        
        try:
            payload = {
                "message": message,
                "access_token": self.access_token
            }
            logger.info("Posting text to Facebook...")
            response = requests.post(url, data=payload)
            response.raise_for_status()
            logger.info(f"Successfully posted text to Facebook! ID: {response.json().get('id')}")
            return True
        except Exception as e:
            logger.error(f"Error posting text to Facebook: {e}")
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                logger.error(f"FB Error Details: {e.response.text}")
            return False
