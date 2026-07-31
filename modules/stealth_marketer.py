"""
Stealth Marketer Module — HARDENED BUILD.
Subscriber growth engine that silently scrapes competitor groups
and invites targeted users to your channel using a drip strategy.

SECURITY ARCHITECTURE:
- Uses a BURNER Telegram account (never your personal number).
- Zero-trace: scraped user IDs are NEVER printed to console or log files.
- Randomized device fingerprint to mimic a real phone.
- Graceful disconnect on shutdown (mimics closing the app normally).
- Auto-kill on any suspicious Telegram response.
- Full kill switch via frontend toggle and NOVE voice command.
"""
import logging
import asyncio
import random
import time
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from telethon import TelegramClient, events
from telethon.tl.functions.channels import (
    JoinChannelRequest, 
    InviteToChannelRequest,
    GetParticipantsRequest
)
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import ChannelParticipantsRecent
from telethon.errors import (
    FloodWaitError,
    UserPrivacyRestrictedError,
    PeerFloodError,
    ChatWriteForbiddenError,
    UserBannedInChannelError,
    UserNotMutualContactError,
    UserKickedError,
    ChatAdminRequiredError,
    UserAlreadyParticipantError,
    SessionRevokedError,
    AuthKeyUnregisteredError,
    PhoneNumberBannedError
)

# Custom logger that NEVER writes scraped user data
logger = logging.getLogger("OmniBot.Stealth")

# Keywords that trigger the reply engine
TRIGGER_KEYWORDS = [
    "rupee", "pkr", "dollar", "imf", "crypto", "bitcoin", "freelance",
    "ai", "chatgpt", "tech", "layoff", "market", "economy", "tax"
]

# Realistic device fingerprints to cycle through
DEVICE_PROFILES = [
    {"model": "Samsung SM-S928B",    "system": "Android 14",  "app": "10.14.5", "lang": "en"},
    {"model": "Google Pixel 8 Pro",  "system": "Android 14",  "app": "10.14.5", "lang": "en"},
    {"model": "OnePlus 12",          "system": "Android 14",  "app": "10.14.5", "lang": "en"},
    {"model": "Xiaomi 14 Ultra",     "system": "Android 14",  "app": "10.14.5", "lang": "en"},
    {"model": "Samsung SM-A546B",    "system": "Android 13",  "app": "10.12.0", "lang": "en"},
]


class StealthMarketer:
    """
    Subscriber growth engine with full anti-detection measures.

    Two modes of operation:
    1. REPLY MODE: Monitors competitor groups and replies to relevant questions
       with helpful answers that subtly mention your channel.
    2. SCRAPE & INVITE MODE: Silently scrapes active user IDs from competitor 
       groups and adds 1-2 per day to your channel using a drip strategy.

    Safety:
    - Uses a BURNER account (separate phone number).
    - Never adds more than 2 users per day.
    - Randomized delays between all actions.
    - Auto-kills on any suspicious Telegram error.
    - Can be instantly disabled via frontend toggle or NOVE voice command.
    """

    def __init__(self, api_id: int, api_hash: str, stealth_phone: str,
                 ai_engine: Any, brain: Any, channel_username: str,
                 target_groups: list, engagement_rate: float = 0.01,
                 notification_manager: Any = None, db: Any = None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = stealth_phone
        self.ai = ai_engine
        self.brain = brain
        self.channel_username = channel_username
        self.target_groups = target_groups
        self.engagement_rate = engagement_rate
        self.nm = notification_manager
        self.db = db

        self.client = None
        self._active = False          # Master kill switch
        self._scraping_active = False # Scrape & invite mode switch
        self._reply_active = False    # Reply mode switch
        self._emergency_stop = False  # Set by auto-kill, blocks reactivation

        # Anti-detection counters
        self._invites_today = 0
        self._invites_max_per_day = 2
        self._last_invite_time = 0
        self._last_scrape_time = 0
        self._session_start = 0

        # Pick a random device fingerprint for this session
        self._device = random.choice(DEVICE_PROFILES)

    # ═══════════════════════════════════════════════════════════
    #  CONNECTION & LIFECYCLE
    # ═══════════════════════════════════════════════════════════

    async def connect(self):
        """Initializes its own Telethon client using the stealth burner phone."""
        if not self.api_id or not self.api_hash or not self.phone:
            logger.warning("Stealth Marketer credentials missing. It will not function.")
            return

        session_path = os.path.join(os.path.dirname(__file__), "..", "sessions", "stealth")
        os.makedirs(os.path.dirname(session_path), exist_ok=True)

        try:
            self.client = TelegramClient(
                session_path,
                self.api_id,
                self.api_hash,
                device_model=self._device["model"],
                system_version=self._device["system"],
                app_version=self._device["app"],
                lang_code=self._device["lang"],
                system_lang_code=self._device["lang"]
            )
            
            await self.client.start(phone=self.phone)  # type: ignore
            me = await self.client.get_me()
            self._session_start = time.time()
            
            if self.target_groups:
                @self.client.on(events.NewMessage(chats=self.target_groups))
                async def handler(event):
                    if self._active and self._reply_active:
                        await self._handle_new_message(event)

            logger.info(
                f"Stealth Marketer connected as: {me.first_name}. "  # type: ignore
                f"Device: {self._device['model']}. "
                f"Listening to {len(self.target_groups)} groups. "
                f"Engagement rate: {self.engagement_rate * 100}%."
            )
        except Exception as e:
            logger.error(f"Failed to connect Stealth Marketer client: {e}")
            self.client = None

    # ═══════════════════════════════════════════════════════════
    #  KILL SWITCH — The most important part
    # ═══════════════════════════════════════════════════════════

    async def activate(self):
        """Activates the Stealth Marketer. Sends email notification."""
        if self._emergency_stop:
            logger.error("Cannot activate: emergency stop is engaged. Manual reset required.")
            return False

        self._active = True
        self._reply_active = True
        self._scraping_active = True
        logger.info("Stealth Marketer ACTIVATED.")

        if self.nm:
            await self.nm.send_notification(
                subject="Stealth Marketer ACTIVATED",
                message="The Stealth Marketer has been turned ON. It is now monitoring competitor groups and running the drip invite strategy.",
                is_critical=False
            )
        return True

    async def deactivate(self, reason: str = "Manual shutdown"):
        """
        Immediately kills all stealth operations.
        Gracefully disconnects the Telethon session to avoid suspicion.
        """
        self._active = False
        self._reply_active = False
        self._scraping_active = False
        logger.info(f"Stealth Marketer DEACTIVATED. Reason: {reason}")

        if self.nm:
            await self.nm.send_notification(
                subject="Stealth Marketer DEACTIVATED",
                message=f"The Stealth Marketer has been turned OFF.\nReason: {reason}",
                is_critical="emergency" in reason.lower() or "auto" in reason.lower()
            )

    async def emergency_kill(self, reason: str):
        """
        Emergency shutdown triggered by auto-detection of suspicious Telegram responses.
        Sets _emergency_stop to True, which BLOCKS reactivation until manual reset.
        """
        self._emergency_stop = True
        await self.deactivate(reason=f"EMERGENCY AUTO-KILL: {reason}")
        logger.error(f"EMERGENCY KILL ENGAGED: {reason}")

        if self.nm:
            await self.nm.send_notification(
                subject="⚠️ EMERGENCY: Stealth Marketer Auto-Killed",
                message=(
                    f"The Stealth Marketer has AUTOMATICALLY shut itself down.\n\n"
                    f"Reason: {reason}\n\n"
                    f"This likely means Telegram detected suspicious activity on the burner account.\n"
                    f"The module is now LOCKED and cannot be reactivated until you manually reset it.\n\n"
                    f"Recommendation: Wait 24-48 hours before reactivating."
                ),
                is_critical=True
            )

    def reset_emergency(self):
        """Manual reset of the emergency stop flag. Only call after waiting 24-48 hours."""
        self._emergency_stop = False
        self._invites_today = 0
        logger.info("Emergency stop flag has been manually reset.")

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def status(self) -> Dict:
        """Returns the current status for the dashboard."""
        return {
            "active": self._active,
            "reply_mode": self._reply_active,
            "scrape_mode": self._scraping_active,
            "emergency_stop": self._emergency_stop,
            "invites_today": self._invites_today,
            "max_invites_per_day": self._invites_max_per_day,
            "device_fingerprint": self._device["model"],
            "target_groups": len(self.target_groups),
            "uptime_minutes": round((time.time() - self._session_start) / 60, 1) if self._session_start else 0
        }

    # ═══════════════════════════════════════════════════════════
    #  REPLY MODE — Stealth replies in competitor groups
    # ═══════════════════════════════════════════════════════════

    async def _handle_new_message(self, event):
        """Processes incoming messages in target groups."""
        if not self._active or not self._reply_active:
            return

        if self.brain.is_sleeping() or not self.brain.can_reply():
            return

        message_text = event.message.message
        if not message_text:
            return

        # 1. Keyword check
        message_lower = message_text.lower()
        has_trigger = any(kw in message_lower for kw in TRIGGER_KEYWORDS)

        if not has_trigger or "?" not in message_lower:
            return

        # 2. Probability check
        if random.random() > self.engagement_rate:
            return

        logger.info(f"Stealth reply triggered on a message in competitor group.")

        # 3. Generate Reply
        reply_text = await self._generate_stealth_reply(message_text)
        if not reply_text:
            return

        # 4. Send with human-like jitter
        await self._send_reply_with_jitter(event, reply_text)

    async def _generate_stealth_reply(self, user_message: str) -> Optional[str]:
        """Uses AI to generate a highly human reply with a subtle channel plug."""
        system_prompt = f"""You are a regular Pakistani Telegram user hanging out in a group.
Someone just asked a question. Write a helpful, conversational, and casual response.
Mix English with a tiny bit of Roman Urdu. Don't sound formal.
At the very end of your response, subtly mention that you read about this on {self.channel_username} 
(e.g., "saw a good breakdown of this on {self.channel_username} btw").
Keep it under 3 sentences."""

        user_prompt = f"User asked: {user_message}"

        try:
            reply = await self.ai.generate(
                task="stealth",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=150,
                temperature=0.8
            )
            return reply
        except Exception as e:
            logger.error(f"AI reply generation failed: {e}")
            return None

    async def _send_reply_with_jitter(self, event, reply_text: str):
        """Applies mathematical jitter before typing/sending to evade anti-spam."""
        # Wait 2 to 5 minutes before replying (mimics reading, thinking, then typing)
        delay = random.uniform(120.0, 300.0)
        logger.info(f"Stealth reply: waiting {delay:.0f}s before sending.")
        await asyncio.sleep(delay)

        # Check if we were deactivated during the wait
        if not self._active or not self._reply_active:
            logger.info("Stealth reply aborted: module was deactivated during wait.")
            return

        try:
            # Simulate "typing..." status for a realistic duration
            typing_duration = min(len(reply_text) / 10.0, 15.0)
            async with self.client.action(event.chat_id, 'typing'):  # type: ignore
                await asyncio.sleep(typing_duration)

            await event.reply(reply_text)
            self.brain.record_reply()
            logger.info("Stealth reply sent successfully.")

            # Log to database (only the reply text, never user IDs)
            if self.db:
                await self.db.log_post(
                    platform="telegram_group",
                    content=reply_text,
                    status="posted",
                    metadata={"type": "stealth_reply"}
                )

        except FloodWaitError as e:
            await self._handle_flood_wait(e, "reply")
        except Exception as e:
            logger.error(f"Failed to send stealth reply: {e}")
            await self.brain.handle_error("StealthMarketer", e, can_auto_fix=True, fix_action="Skipped reply")

    # ═══════════════════════════════════════════════════════════
    #  SCRAPE & INVITE MODE — The most sensitive part
    # ═══════════════════════════════════════════════════════════

    async def scrape_and_invite_cycle(self):
        """
        Main scrape-and-invite loop. Designed to run as a background task.
        Scrapes active users from competitor groups and invites 1-2 per day.

        ZERO-TRACE: User IDs are only stored in Supabase, never logged to console.
        """
        if not self._active or not self._scraping_active:
            return

        if self._invites_today >= self._invites_max_per_day:
            logger.info("Daily invite limit reached. Sleeping until tomorrow.")
            return

        logger.info("Starting scrape & invite cycle.")

        for group in self.target_groups:
            if not self._active or not self._scraping_active:
                break

            if self._invites_today >= self._invites_max_per_day:
                break

            try:
                # Scrape active users from this group
                scraped_ids = await self._scrape_group_members(group)

                if not scraped_ids:
                    continue

                # Filter out already-invited users
                fresh_ids = await self._filter_already_invited(scraped_ids)

                if not fresh_ids:
                    continue

                # Pick ONE random user to invite
                target_id = random.choice(fresh_ids)
                success = await self._invite_user(target_id)

                if success:
                    self._invites_today += 1

                # Random cool-down between groups (30-90 minutes)
                if self._active and self._scraping_active:
                    cooldown = random.uniform(1800, 5400)
                    logger.info(f"Cooling down for {cooldown / 60:.0f} minutes before next group.")
                    await asyncio.sleep(cooldown)

            except Exception as e:
                logger.error(f"Scrape cycle error: {e}")
                # Do NOT log the group name or user data to prevent trace

    async def _scrape_group_members(self, group_username: str) -> List[int]:
        """
        Scrapes recent active participants from a group.
        Returns a list of user IDs. NEVER logs them to console.
        """
        if not self.client:
            return []

        try:
            entity = await self.client.get_entity(group_username)

            # Mimic human behavior: scroll through the group for a bit
            await asyncio.sleep(random.uniform(3.0, 8.0))

            participants = await self.client(GetParticipantsRequest(  # type: ignore
                channel=entity,
                filter=ChannelParticipantsRecent(),
                offset=0,
                limit=50,  # Small batch to avoid suspicion
                hash=0
            ))

            user_ids = []
            for user in participants.users:  # type: ignore
                if user.bot or user.deleted:
                    continue
                user_ids.append(user.id)

            # Store scraped IDs to Supabase ONLY (zero console trace)
            if self.db:
                for uid in user_ids:
                    try:
                        await self.db.client.table("scraped_users").upsert({
                            "user_id": uid,
                            "source_group": group_username,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                            "invited": False
                        }).execute()
                    except Exception:
                        pass  # Silently skip duplicates

            return user_ids

        except FloodWaitError as e:
            await self._handle_flood_wait(e, "scrape")
            return []
        except (SessionRevokedError, AuthKeyUnregisteredError, PhoneNumberBannedError) as e:
            await self.emergency_kill(f"Critical auth error during scrape: {type(e).__name__}")
            return []
        except Exception as e:
            logger.error(f"Scrape failed: {type(e).__name__}")
            return []

    async def _filter_already_invited(self, user_ids: List[int]) -> List[int]:
        """Filters out users we've already invited using the Supabase database."""
        if not self.db or not self.db._initialized:
            return user_ids

        try:
            result = self.db.client.table("scraped_users").select("user_id").eq("invited", True).execute()
            already_invited = {row["user_id"] for row in (result.data or [])}
            return [uid for uid in user_ids if uid not in already_invited]
        except Exception:
            return user_ids

    async def _invite_user(self, user_id: int) -> bool:
        """
        Invites a single user to the channel.
        Uses extreme caution with full error handling for every possible Telegram error.
        """
        if not self.client or not self._active:
            return False

        try:
            # Resolve our channel entity
            channel = await self.client.get_entity(self.channel_username)

            # Random pre-invite delay (30s to 2 min) to mimic human thought
            await asyncio.sleep(random.uniform(30, 120))

            # Check kill switch again after the delay
            if not self._active or not self._scraping_active:
                return False

            # Attempt the invite
            user_entity = await self.client.get_entity(user_id)
            await self.client(InviteToChannelRequest(  # type: ignore
                channel=channel,
                users=[user_entity]
            ))

            self._last_invite_time = time.time()

            # Mark as invited in Supabase (zero console trace)
            if self.db:
                try:
                    self.db.client.table("scraped_users").update({
                        "invited": True,
                        "invited_at": datetime.now(timezone.utc).isoformat()
                    }).eq("user_id", user_id).execute()
                except Exception:
                    pass

            logger.info("Successfully invited 1 user to the channel.")

            # Notify via email
            if self.nm:
                await self.nm.send_notification(
                    subject="Stealth Marketer: User Invited",
                    message=f"1 user has been invited to {self.channel_username}.\nTotal invites today: {self._invites_today + 1}",
                    is_critical=False
                )

            return True

        except UserAlreadyParticipantError:
            logger.info("User is already a member. Skipping.")
            if self.db:
                try:
                    self.db.client.table("scraped_users").update({"invited": True}).eq("user_id", user_id).execute()
                except Exception:
                    pass
            return False

        except UserPrivacyRestrictedError:
            logger.info("User has privacy restrictions. Skipping.")
            return False

        except UserNotMutualContactError:
            logger.info("User requires mutual contact. Skipping.")
            return False

        except UserKickedError:
            logger.info("User was previously kicked. Skipping.")
            return False

        except PeerFloodError:
            await self.emergency_kill("PeerFloodError detected — Telegram flagged too many invites.")
            return False

        except FloodWaitError as e:
            await self._handle_flood_wait(e, "invite")
            return False

        except UserBannedInChannelError:
            await self.emergency_kill("UserBannedInChannelError — our burner may be flagged.")
            return False

        except ChatAdminRequiredError:
            logger.error("Admin rights required to invite users. Check channel permissions.")
            await self.deactivate("Missing admin permissions on channel.")
            return False

        except (SessionRevokedError, AuthKeyUnregisteredError, PhoneNumberBannedError) as e:
            await self.emergency_kill(f"Critical auth error: {type(e).__name__} — burner account may be banned.")
            return False

        except Exception as e:
            logger.error(f"Invite failed: {type(e).__name__}")
            return False

    # ═══════════════════════════════════════════════════════════
    #  ANTI-DETECTION UTILITIES
    # ═══════════════════════════════════════════════════════════

    async def _handle_flood_wait(self, error: FloodWaitError, context: str):
        """
        Handles FloodWaitError intelligently.
        Short waits (< 60s): just wait it out.
        Long waits (> 60s): auto-kill the module because Telegram is suspicious.
        """
        wait_time = error.seconds

        if wait_time > 60:
            await self.emergency_kill(
                f"FloodWaitError ({wait_time}s) during {context}. "
                f"Telegram is rate-limiting aggressively — this is a warning sign."
            )
        else:
            logger.warning(f"Short FloodWait ({wait_time}s) during {context}. Waiting it out.")
            await asyncio.sleep(wait_time + random.uniform(5, 15))

    async def join_group(self, group_username: str) -> bool:
        """Allows NOVE to command the bot to join a new group for monitoring."""
        if not self.client or not self._active:
            return False

        try:
            # Random delay before joining (mimics finding the group, reading it, then clicking join)
            await asyncio.sleep(random.uniform(10, 30))

            await self.client(JoinChannelRequest(group_username))  # type: ignore
            if group_username not in self.target_groups:
                self.target_groups.append(group_username)
            logger.info(f"Joined new target group: {group_username}")

            if self.nm:
                await self.nm.send_notification(
                    subject="Stealth Marketer: Joined New Group",
                    message=f"Joined {group_username} for monitoring and scraping.",
                    is_critical=False
                )
            return True

        except FloodWaitError as e:
            await self._handle_flood_wait(e, "join_group")
            return False
        except Exception as e:
            logger.error(f"Failed to join {group_username}: {type(e).__name__}")
            return False

    async def global_search_and_join(self, query: str):
        """Searches Telegram globally for a keyword and joins a relevant group."""
        if not self.client or not self._active:
            return

        try:
            await asyncio.sleep(random.uniform(5, 15))
            result = await self.client(SearchRequest(q=query, limit=5))
            for chat in result.chats:  # type: ignore
                if getattr(chat, 'username', None):
                    await self.join_group(chat.username)
                    break
        except Exception as e:
            logger.error(f"Global search failed: {type(e).__name__}")

    async def graceful_disconnect(self):
        """
        Gracefully disconnects the Telethon session.
        Mimics a normal user closing the Telegram app.
        """
        if self.client:
            try:
                await self.client.disconnect()  # type: ignore
                logger.info("Stealth Marketer session gracefully disconnected.")
            except Exception:
                pass  # Silently fail — we don't want crash traces
