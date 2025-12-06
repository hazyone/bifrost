"""
Telegram client wrapper with rate limiting and session management.
Uses Telethon library for MTProto protocol.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from telethon.tl.types import (
    Channel,
    Chat,
    User,
    Message,
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaWebPage,
)

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class TelegramMessage:
    """Exported message structure."""
    id: int
    sender_name: str
    sender_id: int | None
    text: str
    date: str  # ISO format
    date_timestamp: int
    reply_to_id: int | None
    is_from_bot: bool
    media_type: str | None
    forward_from: str | None

    def to_dict(self) -> dict:
        return asdict(self)


class RateLimiter:
    """Simple rate limiter to respect Telegram API limits."""

    def __init__(self, delay: float):
        self.delay = delay
        self._last_call: float | None = None

    async def wait(self):
        """Wait if necessary to respect rate limits."""
        if self._last_call is not None:
            elapsed = asyncio.get_event_loop().time() - self._last_call
            if elapsed < self.delay:
                wait_time = self.delay - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        self._last_call = asyncio.get_event_loop().time()

    async def backoff(self, attempt: int) -> float:
        """Exponential backoff after errors."""
        delay = min(2 ** attempt, 300)  # Max 5 minutes
        logger.warning(f"Backoff: attempt {attempt}, waiting {delay}s")
        await asyncio.sleep(delay)
        self._last_call = asyncio.get_event_loop().time()
        return delay


class TgClient:
    """Telegram client with rate limiting and session persistence."""

    def __init__(self, config: Config):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit.fetch_delay)

        # Session file path
        session_path = Path(__file__).parent / f"{config.session_name}.session"

        # Create client with TDesktop device info to appear as official client
        self.client = TelegramClient(
            str(session_path),
            config.api_id,
            config.api_hash,
            device_model="Desktop",
            system_version="Windows 10",
            app_version="4.16.8",
            lang_code="en",
            system_lang_code="en",
        )

    async def connect(self) -> bool:
        """Connect to Telegram and check authorization."""
        await self.client.connect()
        return await self.client.is_user_authorized()

    async def login(self):
        """Interactive login with phone number and code."""
        if await self.client.is_user_authorized():
            logger.info("Already logged in")
            me = await self.client.get_me()
            logger.info(f"Logged in as: {me.first_name} (@{me.username})")
            return

        logger.info(f"Sending login code to {self.config.phone_number}")
        await self.client.send_code_request(self.config.phone_number)

        code = input("Enter the code you received: ").strip()

        try:
            await self.client.sign_in(self.config.phone_number, code)
        except Exception as e:
            if "Two-steps verification" in str(e) or "password" in str(e).lower():
                password = input("Enter your 2FA password: ").strip()
                await self.client.sign_in(password=password)
            else:
                raise

        me = await self.client.get_me()
        logger.info(f"Logged in as: {me.first_name} (@{me.username})")

    async def disconnect(self):
        """Disconnect from Telegram."""
        await self.client.disconnect()

    async def resolve_group(self, identifier: str) -> Channel | Chat:
        """
        Resolve a group/channel by username, ID, or invite link.

        Args:
            identifier: Username (@group), invite link (t.me/+xxx), or numeric ID
        """
        await self.rate_limiter.wait()

        # Handle invite links
        if "t.me/+" in identifier or "t.me/joinchat/" in identifier:
            # Extract hash from invite link
            if "t.me/+" in identifier:
                hash_part = identifier.split("+")[-1]
            else:
                hash_part = identifier.split("/")[-1]

            # Join via invite link
            result = await self.client(functions.messages.ImportChatInviteRequest(hash_part))
            return result.chats[0]

        # Handle usernames
        if identifier.startswith("@"):
            identifier = identifier[1:]

        entity = await self.client.get_entity(identifier)
        logger.info(f"Resolved: {getattr(entity, 'title', entity.first_name)} (ID: {entity.id})")
        return entity

    async def join_channel(self, channel: Channel):
        """Join a channel or supergroup."""
        await self.rate_limiter.wait()

        try:
            await self.client(functions.channels.JoinChannelRequest(channel))
            logger.info(f"Joined channel: {channel.title}")
        except Exception as e:
            if "already" in str(e).lower():
                logger.info(f"Already a member of: {channel.title}")
            else:
                raise

    async def get_messages(
        self,
        chat,
        limit: int | None = None,
        offset_id: int = 0,
    ) -> list[TelegramMessage]:
        """
        Fetch messages from a chat with rate limiting.

        Args:
            chat: Target chat/channel
            limit: Maximum messages to fetch (None for all)
            offset_id: Start from this message ID
        """
        messages = []
        batch_size = self.config.rate_limit.batch_size
        total_limit = limit or float("inf")

        logger.info(f"Fetching messages from {getattr(chat, 'title', 'chat')} (limit: {limit})")

        offset = offset_id
        fetched = 0

        while fetched < total_limit:
            await self.rate_limiter.wait()

            current_batch = min(batch_size, int(total_limit - fetched))

            try:
                batch = await self.client.get_messages(
                    chat,
                    limit=current_batch,
                    offset_id=offset,
                )
            except Exception as e:
                if "FloodWait" in str(type(e).__name__) or "flood" in str(e).lower():
                    # Extract wait time from error
                    wait_time = getattr(e, "seconds", 60)
                    logger.warning(f"FloodWait: waiting {wait_time}s as required by Telegram")
                    await asyncio.sleep(wait_time)
                    continue
                raise

            if not batch:
                break

            for msg in batch:
                if not isinstance(msg, Message):
                    continue

                messages.append(self._convert_message(msg))
                fetched += 1

                if fetched >= total_limit:
                    break

            offset = batch[-1].id
            logger.info(f"Fetched {fetched} messages...")

        logger.info(f"Total messages fetched: {len(messages)}")
        return messages

    async def iter_messages(
        self,
        chat,
        limit: int | None = None,
    ) -> AsyncIterator[TelegramMessage]:
        """
        Iterate over messages with rate limiting (memory efficient).

        Args:
            chat: Target chat/channel
            limit: Maximum messages to fetch
        """
        count = 0
        total_limit = limit or float("inf")

        async for msg in self.client.iter_messages(chat, limit=limit):
            if not isinstance(msg, Message):
                continue

            await self.rate_limiter.wait()

            yield self._convert_message(msg)
            count += 1

            if count >= total_limit:
                break

    async def listen_for_updates(self, chat, callback):
        """
        Listen for new messages in real-time.

        Args:
            chat: Target chat/channel
            callback: Async function to call with each new message
        """
        chat_id = chat.id if hasattr(chat, "id") else chat
        logger.info(f"Listening for new messages in chat {chat_id}")

        @self.client.on(types.UpdateNewMessage)
        async def handler(event):
            if hasattr(event.message, "peer_id"):
                msg_chat_id = getattr(event.message.peer_id, "channel_id", None) or \
                              getattr(event.message.peer_id, "chat_id", None)
                if msg_chat_id == chat_id:
                    await self.rate_limiter.wait()
                    telegram_msg = self._convert_message(event.message)
                    await callback(telegram_msg)

        await self.client.run_until_disconnected()

    def _convert_message(self, msg: Message) -> TelegramMessage:
        """Convert Telethon Message to our TelegramMessage structure."""
        # Get sender info
        sender_name = "Unknown"
        sender_id = None
        is_from_bot = False

        if msg.sender:
            if isinstance(msg.sender, User):
                sender_name = f"{msg.sender.first_name or ''} {msg.sender.last_name or ''}".strip()
                sender_id = msg.sender.id
                is_from_bot = msg.sender.bot or False
            elif hasattr(msg.sender, "title"):
                sender_name = msg.sender.title
                sender_id = msg.sender.id

        # Get media type
        media_type = None
        if msg.media:
            if isinstance(msg.media, MessageMediaPhoto):
                media_type = "photo"
            elif isinstance(msg.media, MessageMediaDocument):
                media_type = "document"
            elif isinstance(msg.media, MessageMediaWebPage):
                media_type = "webpage"
            else:
                media_type = type(msg.media).__name__

        # Get forward info
        forward_from = None
        if msg.forward:
            if msg.forward.sender:
                forward_from = getattr(msg.forward.sender, "title", None) or \
                               getattr(msg.forward.sender, "first_name", "Unknown")

        return TelegramMessage(
            id=msg.id,
            sender_name=sender_name,
            sender_id=sender_id,
            text=msg.text or "",
            date=msg.date.isoformat() if msg.date else "",
            date_timestamp=int(msg.date.timestamp()) if msg.date else 0,
            reply_to_id=msg.reply_to.reply_to_msg_id if msg.reply_to else None,
            is_from_bot=is_from_bot,
            media_type=media_type,
            forward_from=forward_from,
        )

    async def export_to_json(
        self,
        chat,
        output_path: Path,
        limit: int | None = None,
    ):
        """Export messages to JSON file."""
        messages = await self.get_messages(chat, limit)

        data = {
            "chat": getattr(chat, "title", str(chat.id)),
            "exported_at": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": [m.to_dict() for m in messages],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(messages)} messages to {output_path}")


# Convenience function for quick usage
async def create_client(config: Config | None = None) -> TgClient:
    """Create and connect a Telegram client."""
    if config is None:
        config = Config.from_env()

    client = TgClient(config)
    await client.connect()
    return client
