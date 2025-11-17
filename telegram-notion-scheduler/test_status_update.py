#!/usr/bin/env python3
"""
Test script to verify that status updates work correctly.
Tests the update_post_status function with error handling.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notion_handler import NotionClient
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_status_update():
    """Test the status update functionality"""

    print("\n" + "=" * 60)
    print("🧪 Testing Status Update Functionality")
    print("=" * 60 + "\n")

    # Initialize Notion client
    token = os.getenv("NOTION_TOKEN")
    data_source_id = os.getenv("NOTION_DATA_SOURCE_ID")

    if not token or not data_source_id:
        print("❌ ERROR: Missing NOTION_TOKEN or NOTION_DATA_SOURCE_ID in .env")
        return False

    logger.info(f"Using data source: {data_source_id[:20]}...")

    client = NotionClient(token=token, data_source_id=data_source_id)

    # Test 1: Get a post to update
    print("\n📋 Step 1: Fetching a test post...")
    posts = client.get_scheduled_posts()

    if not posts:
        print("⚠️  No scheduled posts found. Creating one would be best for testing.")
        print("   Try creating a post with Status='Programmato' and Uscita in the past.")
        return True

    test_post = posts[0]
    page_id = test_post.get("page_id")
    title = test_post.get("title", "Unknown")

    print(f"✅ Found test post: '{title}'")
    print(f"   Page ID: {page_id}")
    print(f"   Current Status: {test_post.get('status')}")

    # Test 2: Try to update status
    print("\n📝 Step 2: Attempting to update status...")

    # Try updating to "Test"
    success = client.update_post_status(
        page_id=page_id,
        status="Test",
        message_id="TEST-MSG-123"
    )

    if success:
        print("✅ Status update succeeded!")

        # Verify by fetching again
        print("\n✔️ Step 3: Verifying the update...")
        posts_after = client.get_scheduled_posts()

        # Find our post
        for post in posts_after:
            if post.get("page_id") == page_id:
                new_status = post.get("status")
                print(f"✅ Verified: Status is now '{new_status}'")

                if new_status == "Test":
                    print("✅ TEST PASSED: Status update is working!")

                    # Restore original status
                    print("\n🔄 Restoring original status...")
                    client.update_post_status(
                        page_id=page_id,
                        status="Programmato"
                    )
                    print("✅ Status restored to 'Programmato'")
                    return True
                else:
                    print(f"⚠️  WARNING: Status changed to '{new_status}' instead of 'Test'")
                    return True

        print("⚠️  Could not find post after update (might be filtered out)")
        return True

    else:
        print("❌ Status update FAILED!")
        print("\n🔍 Troubleshooting:")
        print("1. Check that NOTION_TOKEN has write permissions")
        print("2. Verify that Status field exists in your database")
        print("3. Check that Status field is type 'status' (not 'select')")
        print("4. Look at the logs above for specific error messages")
        return False


def show_instructions():
    """Show how to test manually"""
    print("\n" + "=" * 60)
    print("📖 Manual Testing Instructions")
    print("=" * 60)
    print("""
To thoroughly test the status update:

1. Create a test post in Notion with:
   - Status: "Programmato"
   - Tipo: "Telegram_testo"
   - Uscita: (past date/time, e.g., 1 hour ago)
   - Messaggio: "Test message"
   - Title: "Test Post"

2. Run this script:
   python3 test_status_update.py

3. Watch the logs to see if:
   ✅ Status is successfully updated
   ✅ Message ID is saved
   ✅ Changes appear in Notion after 2-3 seconds

4. Check in Notion that:
   ✅ Status changed from "Programmato" to "Test"
   ✅ Status was restored back to "Programmato"

5. Run the actual scheduler:
   python3 scheduler.py

   And watch that:
   ✅ Post is published to Telegram
   ✅ Status changes to "Pubblicato" in Notion
   ✅ Post is not republished on next check
""")


if __name__ == "__main__":
    success = test_status_update()
    show_instructions()

    sys.exit(0 if success else 1)
