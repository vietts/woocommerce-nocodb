"""
Quick test script to verify connections to Notion and Telegram.
Run this before starting the scheduler.
"""

import os
import asyncio
from dotenv import load_dotenv
from notion_handler import NotionClient
from telegram_handler import TelegramClient

load_dotenv()


async def main():
    """Test connections."""
    print("=" * 60)
    print("Testing Telegram-Notion Scheduler Setup")
    print("=" * 60)

    # Test Notion
    print("\n📚 Testing Notion Connection...")
    notion = NotionClient(
        token=os.getenv("NOTION_TOKEN"),
        data_source_id=os.getenv("NOTION_DATA_SOURCE_ID")
    )
    notion_ok = notion.test_connection()

    if notion_ok:
        print("✅ Notion connection successful")
        # Try to fetch scheduled posts
        posts = notion.get_scheduled_posts()
        print(f"   Found {len(posts)} scheduled post(s)")
        if posts:
            for post in posts[:3]:  # Show first 3
                print(f"   - {post.get('title', 'No Title')} ({post.get('type', 'Testo')})")
    else:
        print("❌ Notion connection failed")

    # Test Telegram
    print("\n🤖 Testing Telegram Connection...")
    telegram = TelegramClient(
        token=os.getenv("TELEGRAM_BOT_TOKEN"),
        default_channel=os.getenv("TELEGRAM_CHANNEL")
    )

    try:
        telegram_ok = await telegram.test_connection()
        if telegram_ok:
            print("✅ Telegram connection successful")
        else:
            print("❌ Telegram connection failed")
    except Exception as e:
        print(f"❌ Telegram connection failed: {e}")
        telegram_ok = False

    # Summary
    print("\n" + "=" * 60)
    if notion_ok and telegram_ok:
        print("✅ All connections successful! Ready to start scheduler.")
        print("\nRun: python scheduler.py")
    else:
        print("❌ Some connections failed. Check credentials in .env")
        print("\nCommon issues:")
        print("- Notion: Invalid token or database ID")
        print("- Telegram: Invalid bot token or channel")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
