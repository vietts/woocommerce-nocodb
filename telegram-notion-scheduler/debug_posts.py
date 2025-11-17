"""
Debug script to see raw data from Notion
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

print("=" * 80)
print("FETCHING ALL POSTS FROM NOTION (NO FILTER)")
print("=" * 80)

import requests

response = requests.post(
    f"{notion.base_url}/data_sources/{notion.data_source_id}/query",
    headers=notion.headers,
    json={"page_size": 100}
)

if response.status_code == 200:
    data = response.json()
    posts = data.get("results", [])
    print(f"\n✅ Found {len(posts)} records in Notion\n")

    for i, post in enumerate(posts, 1):
        print(f"\n{'='*80}")
        print(f"POST #{i}")
        print(f"{'='*80}")

        properties = post.get("properties", {})

        print("\nRAW PROPERTIES:")
        print(json.dumps(properties, indent=2, ensure_ascii=False))

        print("\nPARSED VALUES:")
        # Extract Nome
        if "Nome" in properties:
            nome = properties["Nome"]
            print(f"  Nome type: {nome.get('type')}")
            print(f"  Nome value: {nome.get('title')}")

        # Extract Messaggio
        if "Messaggio" in properties:
            msg = properties["Messaggio"]
            print(f"  Messaggio type: {msg.get('type')}")
            print(f"  Messaggio value: {msg.get('rich_text')}")

        # Extract Tipo
        if "Tipo" in properties:
            tipo = properties["Tipo"]
            print(f"  Tipo type: {tipo.get('type')}")
            print(f"  Tipo value: {tipo.get('select')}")

        # Extract Uscita
        if "Uscita" in properties:
            uscita = properties["Uscita"]
            print(f"  Uscita type: {uscita.get('type')}")
            print(f"  Uscita value: {uscita.get('date')}")

        # Extract Status
        if "Status" in properties:
            status = properties["Status"]
            print(f"  Status type: {status.get('type')}")
            print(f"  Status value: {status.get('select')}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
