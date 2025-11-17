"""
Main scheduler application.
Reads scheduled posts from Notion and publishes them to Telegram.
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram.error import TelegramError

from notion_handler import NotionClient
from telegram_handler import TelegramClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PostScheduler:
    """Main scheduler for managing posts publication."""

    def __init__(self):
        """Initialize scheduler with Notion and Telegram clients."""
        self.notion_client = NotionClient(
            token=os.getenv("NOTION_TOKEN"),
            data_source_id=os.getenv("NOTION_DATA_SOURCE_ID")
        )
        self.telegram_client = TelegramClient(
            token=os.getenv("TELEGRAM_BOT_TOKEN"),
            default_channel=os.getenv("TELEGRAM_CHANNEL")
        )
        self.type_field = os.getenv("NOTION_TYPE_FIELD", "Tipo")
        self.scheduler = AsyncIOScheduler()

    async def initialize(self) -> bool:
        """
        Initialize and test connections.

        Returns:
            True if both connections are successful
        """
        logger.info("=" * 60)
        logger.info("Initializing Post Scheduler")
        logger.info("=" * 60)

        # Test Notion connection
        notion_ok = self.notion_client.test_connection()

        # Test Telegram connection
        try:
            telegram_ok = await self.telegram_client.test_connection()
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            telegram_ok = False

        if notion_ok and telegram_ok:
            logger.info("✓ All connections successful!")
            return True
        else:
            logger.error("✗ Some connections failed. Check credentials.")
            return False

    async def check_and_publish(self):
        """
        Check Notion for scheduled posts and publish them to Telegram.
        This is the main job that runs on schedule.
        """
        try:
            logger.info(f"[{datetime.now()}] Checking for scheduled posts...")

            # Fetch scheduled posts from Notion
            posts = self.notion_client.get_scheduled_posts(self.type_field)

            if not posts:
                logger.info("No scheduled posts to publish")
                return

            logger.info(f"Found {len(posts)} post(s) to publish")

            # Process each post
            for post in posts:
                success = await self._process_post(post)

                if success:
                    # Update status to "Pubblicato"
                    message_id = post.get("_telegram_message_id")
                    self.notion_client.update_post_status(
                        page_id=post["page_id"],
                        status="Pubblicato",
                        message_id=str(message_id) if message_id else None
                    )
                else:
                    # Update status to "Errore"
                    self.notion_client.update_post_status(
                        page_id=post["page_id"],
                        status="Errore"
                    )

        except Exception as e:
            logger.error(f"Error in check_and_publish: {e}", exc_info=True)

    async def _process_post(self, post: dict) -> bool:
        """
        Process a single post: validate and publish to Telegram.

        Args:
            post: Post dictionary from Notion

        Returns:
            True if post was successfully published
        """
        try:
            post_id = post.get("page_id", "Unknown")
            post_type = post.get("type", "Testo")
            title = post.get("title", "No Title")

            logger.info(f"Processing post: {title} ({post_type})")

            # Safety check: prevent duplicate publishing if post already has Pubblicato status
            # (guards against multiple scheduler instances)
            if post.get("status") == "Pubblicato":
                logger.debug(f"Post already published, skipping: {title}")
                return False

            # Validate post
            if not self._validate_post(post):
                logger.warning(f"Post validation failed: {post_id}")
                return False

            # Publish to Telegram
            message_id = await self.telegram_client.publish_post(post)

            if message_id:
                logger.info(f"✓ Post published successfully: {title}")
                post["_telegram_message_id"] = message_id
                return True
            else:
                logger.error(f"✗ Failed to publish post: {title}")
                return False

        except Exception as e:
            logger.error(f"Error processing post: {e}", exc_info=True)
            return False

    def _validate_post(self, post: dict) -> bool:
        """
        Validate post has required fields based on type.

        Args:
            post: Post dictionary

        Returns:
            True if post is valid
        """
        post_type = post.get("type", "Testo")

        # All types need a message
        if not post.get("message"):
            logger.warning("Post missing message field")
            return False

        # Image posts need an image URL
        if post_type == "Immagine+Testo" and not post.get("image_url"):
            logger.warning("Image post missing image_url")
            return False

        # Poll posts need question and options
        if post_type == "Poll":
            if not post.get("poll_question"):
                logger.warning("Poll missing question")
                return False
            if not post.get("poll_options"):
                logger.warning("Poll missing options")
                return False

        return True

    def start(self):
        """Start the scheduler and run jobs."""
        try:
            # Run initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            init_ok = loop.run_until_complete(self.initialize())
            if not init_ok:
                logger.error("Initialization failed. Exiting.")
                return

            # Schedule the check_and_publish job
            interval_minutes = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "15"))
            logger.info(f"Scheduling job to run every {interval_minutes} minutes")

            self.scheduler.add_job(
                self.check_and_publish,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="post_scheduler",
                name="Check and publish scheduled posts",
                replace_existing=True
            )

            # Start scheduler
            self.scheduler.start()
            logger.info("✓ Scheduler started successfully")

            # Keep the scheduler running
            loop.run_forever()

        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}", exc_info=True)
        finally:
            if self.scheduler.running:
                self.scheduler.shutdown()
            logger.info("Scheduler stopped")


def main():
    """Entry point."""
    scheduler = PostScheduler()
    scheduler.start()


if __name__ == "__main__":
    main()
