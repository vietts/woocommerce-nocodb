"""
Notion client module for managing database operations.
Handles reading scheduled posts and updating their status.
Uses the new 2025-09-03 API with data_source_id.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
import requests
from notion_client import Client

# Rome timezone
ROME_TZ = pytz.timezone("Europe/Rome")

logger = logging.getLogger(__name__)


class NotionClient:
    """Client for interacting with Notion data source."""

    def __init__(self, token: str, data_source_id: str):
        """
        Initialize Notion client.

        Args:
            token: Notion integration token
            data_source_id: Data source ID (replaces database_id in new API)
        """
        self.token = token
        self.data_source_id = data_source_id
        self.client = Client(auth=token)
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
        logger.info(f"Notion client initialized with data source: {data_source_id}")

    def get_scheduled_posts(self, type_field: str = "Tipo") -> List[Dict[str, Any]]:
        """
        Fetch all posts with "Programmato" status and Uscita (publication date) <= now (Rome timezone).
        Only fetches posts from today onwards (+30 days) to minimize data transfer.

        Args:
            type_field: Name of the type field in Notion (used for filtering)

        Returns:
            List of post dictionaries
        """
        try:
            # Get current time in Rome timezone
            current_time = datetime.now(ROME_TZ)

            # Calculate date range: today to +30 days from now
            date_min = current_time.date()
            date_max = (current_time + timedelta(days=30)).date()

            logger.debug(f"Fetching posts with pagination (window: {date_min} to {date_max})")

            # Fetch all pages to get all results
            all_posts = []
            next_cursor = None

            while True:
                # Build query with pagination
                query_body = {"page_size": 100}
                if next_cursor:
                    query_body["start_cursor"] = next_cursor
                    logger.debug(f"Fetching page with cursor: {next_cursor}")

                response = requests.post(
                    f"{self.base_url}/data_sources/{self.data_source_id}/query",
                    headers=self.headers,
                    json=query_body
                )

                if response.status_code != 200:
                    logger.error(f"Notion API returned {response.status_code}")
                    logger.error(f"Request body: {query_body}")
                    logger.error(f"Response body: {response.text}")
                    break

                data = response.json()
                batch = data.get("results", [])
                all_posts.extend(batch)

                logger.debug(f"Fetched {len(batch)} posts (total so far: {len(all_posts)})")

                # Check if there are more results
                next_cursor = data.get("next_cursor")
                if not next_cursor:
                    break

            logger.info(f"Total posts fetched from Notion: {len(all_posts)}")

            # Now filter the posts in Python
            posts = []
            for item in all_posts:
                post = self._parse_post(item, type_field)
                if post:
                    # Filter by status: only "Programmato"
                    status = post.get("status", "")
                    if status != "Programmato":
                        logger.debug(f"Skipping post with status '{status}' (only Programmato allowed)")
                        continue

                    # Filter by post type: only Telegram_testo and Telegram_poll
                    post_type = post.get("type", "")
                    if post_type not in ["Telegram_testo", "Telegram_poll"]:
                        logger.debug(f"Skipping post with type '{post_type}' (only Telegram_testo/Telegram_poll allowed)")
                        continue

                    # Filter by date: only posts within -20 to +30 day window
                    publish_date_str = post.get("publish_date")
                    if publish_date_str:
                        try:
                            # Parse the date string
                            if "T" in publish_date_str:
                                # Has time component
                                publish_dt = datetime.fromisoformat(publish_date_str.replace("Z", "+00:00"))
                                # Convert to Rome timezone
                                if publish_dt.tzinfo is None:
                                    publish_dt = ROME_TZ.localize(publish_dt)
                                else:
                                    publish_dt = publish_dt.astimezone(ROME_TZ)
                            else:
                                # Only date, assume end of day in Rome timezone
                                publish_dt = ROME_TZ.localize(datetime.fromisoformat(publish_date_str).replace(hour=23, minute=59, second=59))

                            # Check if within -20 to +30 day window
                            if publish_dt.date() < date_min or publish_dt.date() > date_max:
                                logger.debug(f"Skipping post - Uscita ({publish_date_str}) outside scheduling window")
                                continue

                            # Check if past/current (for actual publishing)
                            if publish_dt > current_time:
                                post_title = post.get('title', 'Unknown')
                                logger.debug(f"Skipping post '{post_title}' - Uscita ({publish_date_str} -> {publish_dt.isoformat()}) is in the future (current: {current_time.isoformat()})")
                                continue
                        except Exception as e:
                            logger.warning(f"Could not parse date {publish_date_str}: {e}", exc_info=True)
                            continue
                    else:
                        logger.debug(f"Skipping post - no Uscita date")
                        continue

                    posts.append(post)

            logger.info(f"Found {len(posts)} scheduled posts ready for publication (from {len(all_posts)} total)")
            return posts

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching scheduled posts: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching scheduled posts: {e}")
            return []

    def _parse_post(self, notion_page: Dict, type_field: str) -> Optional[Dict[str, Any]]:
        """
        Parse a Notion page into a post dictionary.

        Args:
            notion_page: Raw Notion page response
            type_field: Name of the type field

        Returns:
            Parsed post dictionary or None if parsing fails
        """
        try:
            properties = notion_page.get("properties", {})

            post = {
                "page_id": notion_page.get("id"),
                "url": notion_page.get("url"),
            }

            # Extract text fields
            # Try both "Nome" and "Name" (Name is the default Notion field)
            if "Nome" in properties:
                post["title"] = self._extract_text(properties["Nome"])
            elif "Name" in properties:
                post["title"] = self._extract_text(properties["Name"])

            if "Messaggio" in properties:
                post["message"] = self._extract_rich_text(properties["Messaggio"])

            if type_field in properties:
                post["type"] = self._extract_select(properties[type_field])

            if "Immagine URL" in properties:
                post["image_url"] = self._extract_url(properties["Immagine URL"])

            if "Poll Domanda" in properties:
                post["poll_question"] = self._extract_text(properties["Poll Domanda"])

            if "Poll Opzioni" in properties:
                post["poll_options"] = self._extract_text(properties["Poll Opzioni"])

            if "Channel ID" in properties:
                post["channel_id"] = self._extract_text(properties["Channel ID"])

            if "Uscita" in properties:
                post["publish_date"] = self._extract_date(properties["Uscita"])

            # Extract status (can be "status" type or "select" type)
            if "Status" in properties:
                post["status"] = self._extract_status(properties["Status"])

            # Default values for optional fields
            post.setdefault("type", "Testo")
            post.setdefault("message", "")
            post.setdefault("channel_id", None)
            post.setdefault("status", None)

            return post

        except Exception as e:
            logger.warning(f"Error parsing Notion page {notion_page.get('id')}: {e}")
            return None

    def _extract_text(self, property_obj: Dict) -> str:
        """Extract text from a text property."""
        if property_obj.get("type") == "title":
            return "".join([t.get("plain_text", "") for t in property_obj.get("title", [])])
        elif property_obj.get("type") == "rich_text":
            return "".join([t.get("plain_text", "") for t in property_obj.get("rich_text", [])])
        return ""

    def _extract_rich_text(self, property_obj: Dict) -> str:
        """Extract rich text content."""
        if property_obj.get("type") == "rich_text":
            return "".join([t.get("plain_text", "") for t in property_obj.get("rich_text", [])])
        return ""

    def _extract_url(self, property_obj: Dict) -> Optional[str]:
        """Extract URL from a URL property."""
        if property_obj.get("type") == "url":
            return property_obj.get("url")
        return None

    def _extract_select(self, property_obj: Dict) -> Optional[str]:
        """Extract value from a select property."""
        if property_obj.get("type") == "select":
            select = property_obj.get("select")
            if select:
                return select.get("name")
        return None

    def _extract_status(self, property_obj: Dict) -> Optional[str]:
        """Extract value from a status property."""
        if property_obj.get("type") == "status":
            status = property_obj.get("status")
            if status:
                return status.get("name")
        # Fallback to select if type is select (for compatibility)
        elif property_obj.get("type") == "select":
            select = property_obj.get("select")
            if select:
                return select.get("name")
        return None

    def _extract_date(self, property_obj: Dict) -> Optional[str]:
        """Extract date from a date property."""
        if property_obj.get("type") == "date":
            date_obj = property_obj.get("date")
            if date_obj:
                return date_obj.get("start")
        return None

    def update_post_status(self, page_id: str, status: str, message_id: Optional[str] = None) -> bool:
        """
        Update post status in Notion using REST API.
        Updates Status field to mark post as published or errored.

        Args:
            page_id: Notion page ID
            status: New status (e.g., "Pubblicato", "Errore")
            message_id: Telegram message ID (optional)

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Build properties to update
            properties = {
                "Status": {
                    "status": {
                        "name": status
                    }
                }
            }

            # Note: Message ID field not required - only update Status field

            logger.debug(f"Updating page {page_id} with status='{status}'")

            # Use REST API to update the page
            update_payload = {"properties": properties}

            response = requests.patch(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers=self.headers,
                json=update_payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✓ Updated post {page_id} status to '{status}'")
                return True
            else:
                logger.error(f"✗ Failed to update post {page_id}")
                logger.error(f"  Status code: {response.status_code}")
                logger.error(f"  Response: {response.text}")

                # Try fallback with notion-client library
                logger.debug(f"Trying fallback with notion-client...")
                try:
                    self.client.pages.update(
                        page_id=page_id,
                        properties=properties
                    )
                    logger.info(f"✓ Updated post {page_id} status to '{status}' (via fallback)")
                    return True
                except Exception as fallback_error:
                    logger.error(f"✗ Fallback also failed: {fallback_error}")
                    return False

        except requests.exceptions.Timeout:
            logger.error(f"✗ Timeout updating post {page_id} - Notion API not responding")
            return False
        except Exception as e:
            logger.error(f"✗ Error updating post status for {page_id}: {e}", exc_info=True)
            return False

    def test_connection(self) -> bool:
        """Test connection to Notion data source."""
        try:
            # Test by querying with page_size limit (no filter needed)
            response = requests.post(
                f"{self.base_url}/data_sources/{self.data_source_id}/query",
                headers=self.headers,
                json={"page_size": 1}
            )

            if response.status_code == 200:
                logger.info("✓ Notion connection successful")
                return True
            else:
                logger.error(f"✗ Notion API returned status {response.status_code}")
                logger.error(f"   Response: {response.text}")
                logger.error(f"   Headers sent: {self.headers}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Notion connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error testing Notion connection: {e}")
            return False
