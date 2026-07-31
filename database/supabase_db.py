"""
Supabase Database Manager.
Handles all interactions with the Supabase PostgreSQL database.
Stores posts, metrics, alerts, error logs, and brain state.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List

logger = logging.getLogger("OmniBot.Database")


class SupabaseDB:
    """
    Manages all database operations via the Supabase REST API.
    Tables are created via the Supabase Dashboard (SQL editor).
    """
    
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client = None
        self._initialized = False
    
    async def initialize(self):
        """Connect to Supabase and verify tables exist."""
        try:
            from supabase import create_client
            self.client = create_client(self.url, self.key)
            self._initialized = True
            logger.info("Supabase connection established successfully.")
        except ImportError:
            logger.warning("Supabase SDK not installed. Running in offline mode. "
                          "Install with: pip install supabase")
            self._initialized = False
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self._initialized = False
    
    # ========================
    #   POST LOGGING
    # ========================
    
    async def log_post(self, platform: str, content: str, 
                       image_path: str = "", status: str = "posted",
                       metadata: Dict = None) -> Optional[str]:
        """
        Logs a published post to the 'posts' table.
        
        Args:
            platform: 'telegram', 'twitter', or 'reddit'
            content: The text content of the post
            image_path: Path to the generated image (if any)
            status: 'posted', 'failed', 'scheduled'
            metadata: Any extra data (source URLs, etc.)
        """
        if not self._initialized:
            logger.warning(f"[OFFLINE] Would log {platform} post: {content[:50]}...")
            return None
        
        try:
            data = {
                "platform": platform,
                "content": content[:2000],  # Truncate for safety
                "image_path": image_path,
                "status": status,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            result = self.client.table("posts").insert(data).execute()
            logger.info(f"Logged {platform} post to Supabase (status: {status}).")
            return result.data[0].get("id") if result.data else None
        except Exception as e:
            logger.error(f"Failed to log post to Supabase: {e}")
            return None
    
    # ========================
    #   ALERT SYSTEM (Dashboard Alerts)
    # ========================
    
    async def log_alert(self, level: str, module: str, message: str):
        """
        Logs an alert to the 'alerts' table for the frontend dashboard.
        
        Args:
            level: 'INFO', 'WARNING', 'CRITICAL'
            module: Which module raised the alert (e.g., 'AIEngine', 'Broadcaster')
            message: Human-readable description of the issue
        """
        if not self._initialized:
            logger.warning(f"[OFFLINE ALERT] [{level}] {module}: {message}")
            return
        
        try:
            data = {
                "level": level,
                "module": module,
                "message": message,
                "resolved": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.client.table("alerts").insert(data).execute()
            logger.info(f"Alert logged to dashboard: [{level}] {module} - {message[:80]}")
        except Exception as e:
            logger.error(f"Failed to log alert to Supabase: {e}")
    
    # ========================
    #   METRICS TRACKING
    # ========================
    
    async def log_metric(self, metric_name: str, value: float, metadata: Dict = None):
        """
        Logs a metric snapshot (e.g., subscriber count, posts today).
        
        Args:
            metric_name: 'subscriber_count', 'posts_today', 'replies_today', etc.
            value: The numeric value
        """
        if not self._initialized:
            logger.warning(f"[OFFLINE] Would log metric {metric_name}={value}")
            return
        
        try:
            data = {
                "metric_name": metric_name,
                "value": value,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.client.table("metrics").insert(data).execute()
        except Exception as e:
            logger.error(f"Failed to log metric: {e}")
    
    # ========================
    #   ERROR LOGGING (Self-Healing)
    # ========================
    
    async def log_error(self, module: str, error_type: str, 
                        error_message: str, auto_resolved: bool = False):
        """
        Logs an error for the self-healing system.
        If auto_resolved=True, the Brain fixed it itself.
        If auto_resolved=False, it needs human attention (shows on dashboard).
        """
        if not self._initialized:
            logger.warning(f"[OFFLINE ERROR] {module}: {error_message}")
            return
        
        try:
            data = {
                "module": module,
                "error_type": error_type,
                "error_message": error_message[:1000],
                "auto_resolved": auto_resolved,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.client.table("error_logs").insert(data).execute()
            
            # If NOT auto-resolved, also create a dashboard alert
            if not auto_resolved:
                await self.log_alert(
                    level="WARNING",
                    module=module,
                    message=f"Unresolved error: {error_message[:200]}"
                )
        except Exception as e:
            logger.error(f"Failed to log error to Supabase: {e}")
    
    # ========================
    #   DAILY COUNTERS
    # ========================
    
    async def get_today_post_count(self, platform: str) -> int:
        """Returns how many posts were made today on a given platform."""
        if not self._initialized:
            return 0
        
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            result = (self.client.table("posts")
                      .select("id", count="exact")
                      .eq("platform", platform)
                      .eq("status", "posted")
                      .gte("created_at", f"{today}T00:00:00Z")
                      .execute())
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to get today's post count: {e}")
            return 0
    
    async def get_active_alerts(self) -> List[Dict]:
        """Returns all unresolved alerts for the dashboard."""
        if not self._initialized:
            return []
        
        try:
            result = (self.client.table("alerts")
                      .select("*")
                      .eq("resolved", False)
                      .order("created_at", desc=True)
                      .limit(50)
                      .execute())
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to fetch active alerts: {e}")
            return []
