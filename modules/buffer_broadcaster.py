import logging
import requests
from typing import Dict

logger = logging.getLogger("OmniBot.BufferBroadcaster")

class BufferBroadcaster:
    """
    Broadcaster for posting content directly to Buffer via GraphQL.
    """
    def __init__(self, buffer_access_token: str):
        self.access_token = buffer_access_token
        self.base_url = "https://api.buffer.com/"
        
        if not self.access_token:
            logger.warning("Buffer Broadcaster initialized without access_token. Posting will fail or be skipped.")

    async def post(self, package: Dict) -> bool:
        """
        Posts content to Buffer.
        The package should contain 'story_text' and 'image_path'.
        """
        if not self.access_token:
            logger.error("Missing Buffer credentials.")
            return False
            
        try:
            image_path = package.get("image_path")
            story_text = package.get("story_text", "")
            
            image_url = None
            if image_path:
                logger.info("Uploading image to temporary public host (Catbox.moe)...")
                image_url = self._upload_image_to_catbox(image_path)
                if not image_url:
                    logger.error("Failed to host image. Proceeding with text-only post.")
            
            return self._post_to_buffer(story_text, image_url)
                
        except Exception as e:
            logger.error(f"Failed to post to Buffer: {e}")
            return False

    def _upload_image_to_catbox(self, image_path: str) -> str:
        """Uploads a local image to Catbox.moe to get a public URL for Buffer."""
        try:
            with open(image_path, "rb") as f:
                resp = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=30
                )
            resp.raise_for_status()
            url = resp.text.strip()
            if url.startswith("http"):
                logger.info(f"Image hosted successfully at {url}")
                return url
            return None
        except Exception as e:
            logger.error(f"Error uploading image to Catbox: {e}")
            return None

    def _get_channel_id(self) -> str:
        """Dynamically fetches the first connected Channel ID from Buffer."""
        query = """
        query {
          account {
            id
            organizations {
              id
            }
          }
        }
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Step 1: Get organization ID
        resp = requests.post(self.base_url, headers=headers, json={"query": query})
        resp.raise_for_status()
        data = resp.json()
        org_id = data.get("data", {}).get("account", {}).get("organizations", [])[0].get("id")
        
        if not org_id:
            logger.error("Could not find any Buffer organizations.")
            return None
            
        # Step 2: Get channels for that organization
        query_channels = f"""
        query {{
          channels(input: {{ organizationId: "{org_id}" }}) {{
            id
            name
            service
          }}
        }}
        """
        resp2 = requests.post(self.base_url, headers=headers, json={"query": query_channels})
        resp2.raise_for_status()
        channels = resp2.json().get("data", {}).get("channels", [])
        
        if not channels:
            logger.error("Could not find any connected channels in Buffer.")
            return None
            
        logger.info(f"Found Channel: {channels[0].get('name')} ({channels[0].get('service')})")
        return channels[0].get("id")

    def _post_to_buffer(self, text: str, image_url: str = None) -> bool:
        channel_id = self._get_channel_id()
        if not channel_id:
            return False
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        mutation = """
        mutation CreatePost($input: CreatePostInput!) {
          createPost(input: $input) {
            __typename
          }
        }
        """
        
        variables = {
            "input": {
                "channelId": channel_id,
                "text": text,
                "mode": "addToQueue",
                "needsApproval": False,
                "schedulingType": "automatic"
            }
        }
        
        if image_url:
            variables["input"]["assets"] = [{"image": {"url": image_url}}]
        
        logger.info("Sending post to Buffer Queue...")
        resp = requests.post(self.base_url, headers=headers, json={"query": mutation, "variables": variables})
        resp.raise_for_status()
        
        result = resp.json()
        if "errors" in result:
            logger.error(f"Buffer API Errors: {result['errors']}")
            return False
            
        logger.info("Successfully queued post in Buffer!")
        return True
