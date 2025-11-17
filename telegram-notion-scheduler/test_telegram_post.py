"""
Quick test script to send a test message to Telegram.
Useful for verifying channel connectivity.
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram_handler import TelegramClient

load_dotenv()


async def main():
    """Send test message."""
    print("=" * 60)
    print("Telegram Post Test")
    print("=" * 60)

    telegram = TelegramClient(
        token=os.getenv("TELEGRAM_BOT_TOKEN"),
        default_channel=os.getenv("TELEGRAM_CHANNEL")
    )

    # Test text post
    print("\n📝 Sending test text message...")
    test_post = {
        "title": "Test Post Telegram",
        "type": "Telegram_testo",
        "message": "✅ Test message from Telegram-Notion Scheduler\n\nSe vedi questo messaggio, tutto funziona correttamente!",
        "channel_id": None  # Uses default
    }

    message_id = await telegram.publish_post(test_post)

    if message_id:
        print(f"✅ Message sent successfully! Message ID: {message_id}")
    else:
        print("❌ Failed to send message")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
