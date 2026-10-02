#!/usr/bin/env python3
"""
Subscribe Facebook Pages to Webhook using Meta Graph API

Usage:
  python scripts/subscribe_facebook_pages.py <PAGE_ID> <PAGE_ACCESS_TOKEN>

Example:
  python scripts/subscribe_facebook_pages.py 123456789 EAAabc123...
"""

import sys
import requests

def subscribe_page(page_id: str, access_token: str):
    url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
    payload = {
        "subscribed_fields": "feed",
        "access_token": access_token
    }
    
    print(f"Subscribing page {page_id} to 'feed' webhook...")
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        print("✅ Successfully subscribed page!")
        print(response.json())
    else:
        print(f"❌ Failed to subscribe page. Status: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python subscribe_facebook_pages.py <PAGE_ID> <PAGE_ACCESS_TOKEN>")
        sys.exit(1)
        
    page_id = sys.argv[1]
    access_token = sys.argv[2]
    subscribe_page(page_id, access_token)
