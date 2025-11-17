"""
Find posts with Tipo = Telegram_testo or Telegram_poll
"""

import os
import json
from dotenv import load_dotenv
from notion_handler import NotionClient

load_dotenv()

notion = NotionClient(
    token=os.getenv("NOTION_TOKEN"),
    data_source_id=os.getenv("NOTION_DATA_SOURCE_ID")
)

import requests

response = requests.post(
    f"{notion.base_url}/data_sources/{notion.data_source_id}/query",
    headers=notion.headers,
    json={"page_size": 100}
)

if response.status_code == 200:
    data = response.json()
    posts = data.get("results", [])

    print(f"\n{'='*80}")
    print(f"POSTS WITH TIPO = TELEGRAM_TESTO OR TELEGRAM_POLL")
    print(f"{'='*80}\n")

    count = 0
    for post in posts:
        properties = post.get("properties", {})

        # Get title
        title = ""
        if "Name" in properties:
            name_obj = properties["Name"]
            title_list = name_obj.get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_list])

        # Get Tipo
        tipo = None
        if "Tipo" in properties:
            tipo_obj = properties["Tipo"]
            tipo_select = tipo_obj.get("select")
            if tipo_select:
                tipo = tipo_select.get("name")

        # Only show Telegram posts
        if tipo in ["Telegram_testo", "Telegram_poll"]:
            count += 1
            print(f"\n{'─'*80}")
            print(f"POST #{count}")
            print(f"{'─'*80}")

            print(f"  Title (Name): {title}")
            print(f"  Tipo: {tipo}")

            # Status
            if "Status" in properties:
                status_obj = properties["Status"]
                status_val = status_obj.get("status")
                if status_val:
                    print(f"  Status: {status_val.get('name')}")
                else:
                    print(f"  Status: (empty)")

            # Uscita
            if "Uscita" in properties:
                uscita_obj = properties["Uscita"]
                uscita_date = uscita_obj.get("date")
                if uscita_date:
                    print(f"  Uscita: {uscita_date.get('start')}")
                else:
                    print(f"  Uscita: (empty)")

            # Messaggio
            if "Messaggio" in properties:
                msg_obj = properties["Messaggio"]
                msg_list = msg_obj.get("rich_text", [])
                msg_text = "".join([t.get("plain_text", "") for t in msg_list])
                if msg_text:
                    print(f"  Messaggio: {msg_text[:80]}...")
                else:
                    print(f"  Messaggio: (empty)")

    if count == 0:
        print("❌ No posts found with Tipo = Telegram_testo or Telegram_poll")
    else:
        print(f"\n\n✅ Found {count} Telegram post(s)")

else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
