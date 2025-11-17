"""
Telegram client module for publishing posts.
Handles text, image, and poll messages.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from telegram import Bot, InputFile
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramClient:
    """Client for interacting with Telegram Bot API."""

    def __init__(self, token: str, default_channel: str):
        """
        Initialize Telegram client.

        Args:
            token: Telegram bot token
            default_channel: Default channel for posting (e.g., @probavas or -100xxxxx)
        """
        self.bot = Bot(token=token)
        self.default_channel = default_channel
        logger.info(f"Telegram client initialized for channel: {default_channel}")

    async def publish_post(self, post: Dict[str, Any]) -> Optional[int]:
        """
        Publish a post to Telegram based on its type.

        Args:
            post: Post dictionary with fields like message, type, image_url, etc.

        Returns:
            Message ID if successful, None otherwise
        """
        try:
            channel = post.get("channel_id") or self.default_channel
            post_type = post.get("type", "Telegram_testo")
            title = post.get("title", "No Title")
            message = post.get("message", "")

            logger.info(f"Publishing '{title}' ({post_type}) to {channel}")
            logger.debug(f"  Message length: {len(message)} chars")

            # Normalize post type names (handle both old and new naming conventions)
            if post_type in ["Telegram_poll", "Poll"]:
                return await self._publish_poll(channel, post)
            elif post_type in ["Telegram_testo"] or "image_url" in post and post.get("image_url"):
                # If type is Telegram_testo but has image_url, use image with text
                if post.get("image_url"):
                    return await self._publish_image_with_text(channel, post)
                else:
                    return await self._publish_text(channel, post)
            else:  # Default: Telegram_testo (text only)
                return await self._publish_text(channel, post)

        except Exception as e:
            logger.error(f"Error publishing post: {e}", exc_info=True)
            return None

    async def _publish_text(self, channel: str, post: Dict[str, Any]) -> Optional[int]:
        """Publish text message."""
        try:
            message = post.get("message", "")
            title = post.get("title", "")

            logger.debug(f"_publish_text: message='{message[:50]}...'")

            if not message or message.strip() == "":
                logger.warning(f"Text post has no message content. Title: '{title}'")
                return None

            sent_message = await self.bot.send_message(
                chat_id=channel,
                text=message,
                parse_mode="HTML"
            )

            message_id = sent_message.message_id
            logger.info(f"✓ Text post published successfully (Message ID: {message_id})")
            return message_id

        except TelegramError as e:
            logger.error(f"Telegram error publishing text: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error publishing text: {e}", exc_info=True)
            return None

    async def _publish_image_with_text(self, channel: str, post: Dict[str, Any]) -> Optional[int]:
        """Publish image with caption."""
        try:
            image_url = post.get("image_url")
            caption = post.get("message", "")

            if not image_url:
                logger.warning("Image post has no image URL")
                return None

            sent_message = await self.bot.send_photo(
                chat_id=channel,
                photo=image_url,
                caption=caption,
                parse_mode="HTML"
            )

            message_id = sent_message.message_id
            logger.info(f"✓ Image post published successfully (Message ID: {message_id})")
            return message_id

        except TelegramError as e:
            logger.error(f"Telegram error publishing image: {e}")
            return None

    async def _publish_poll(self, channel: str, post: Dict[str, Any]) -> Optional[int]:
        """Publish poll."""
        try:
            question = post.get("poll_question", "Question?")
            options_str = post.get("poll_options", "[]")

            # Parse poll options from JSON string
            try:
                if isinstance(options_str, str):
                    options = json.loads(options_str)
                else:
                    options = options_str
            except json.JSONDecodeError:
                logger.error(f"Invalid poll options JSON: {options_str}")
                return None

            if not isinstance(options, list) or len(options) < 2:
                logger.warning("Poll must have at least 2 options")
                return None

            # Limit options to 10 (Telegram limit)
            if len(options) > 10:
                options = options[:10]

            sent_message = await self.bot.send_poll(
                chat_id=channel,
                question=question,
                options=options,
                allows_multiple_answers=False,
                is_anonymous=True
            )

            message_id = sent_message.message_id
            logger.info(f"✓ Poll published successfully (Message ID: {message_id})")
            return message_id

        except TelegramError as e:
            logger.error(f"Telegram error publishing poll: {e}")
            return None

    async def test_connection(self) -> bool:
        """Test connection to Telegram bot and channel."""
        try:
            me = await self.bot.get_me()
            logger.info(f"✓ Telegram connection successful. Bot: @{me.username}")

            # Try to send test message to channel
            try:
                msg = await self.bot.send_message(
                    chat_id=self.default_channel,
                    text="🧪 Test message from scheduler"
                )
                await self.bot.delete_message(
                    chat_id=self.default_channel,
                    message_id=msg.message_id
                )
                logger.info(f"✓ Channel {self.default_channel} is accessible")
            except TelegramError as e:
                logger.warning(f"Could not send test message to channel: {e}")

            return True

        except TelegramError as e:
            logger.error(f"✗ Telegram connection failed: {e}")
            return False
