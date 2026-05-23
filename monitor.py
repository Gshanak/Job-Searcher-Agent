import os
import requests
from bs4 import BeautifulSoup
import hashlib
import json
import time

# --- CONFIGURATION ---
# Get credentials from GitHub Secrets (Environment Variables)
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TARGET_URL = "https://example.com"  # CHANGE THIS TO YOUR TARGET URL

# File to store state (GitHub Actions resets every run, so we use a simple file commit strategy or just compare against a known baseline if needed. 
# NOTE: For a truly stateless GitHub Action, we will compare against a 'baseline' file stored in the repo.
BASELINE_FILE = "baseline_hash.txt"

def get_website_content(url):
    """Fetches website content respectfully."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; MyMonitorBot/1.0; +http://example.com)'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Check robots.txt compliance (basic check)
        # In a production app, you'd parse robots.txt properly.
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract relevant text (Customize this selector!)
        # Example: Get all paragraph text
        content = ""
        for p in soup.find_all(['h1', 'h2', 'p']):
            if p.text:
                content += p.get_text(strip=True) + " "
        
        return content.strip()
    except Exception as e:
        print(f"Error fetching site: {e}")
        return None

def send_telegram_alert(message):
    """Sends alert via Official Telegram API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        print("Alert sent successfully.")
    except Exception as e:
        print(f"Failed to send alert: {e}")

def main():
    print("Starting monitoring check...")
    
    # 1. Get Current Content
    current_content = get_website_content(TARGET_URL)
    if not current_content:
        print("Failed to get content. Exiting.")
        return

    # 2. Generate Hash
    current_hash = hashlib.md5(current_content.encode('utf-8')).hexdigest()
    
    # 3. Check Previous State
    # We read the baseline hash from a file in the repo
    previous_hash = ""
    try:
        with open(BASELINE_FILE, 'r') as f:
            previous_hash = f.read().strip()
    except FileNotFoundError:
        print("No baseline found. Creating initial baseline.")
        with open(BASELINE_FILE, 'w') as f:
            f.write(current_hash)
        send_telegram_alert(f"🟢 <b>Monitor Initialized</b>\nTracking: {TARGET_URL}")
        return

    # 4. Compare
    if current_hash != previous_hash:
        print("CHANGE DETECTED!")
        
        # Update Baseline
        with open(BASELINE_FILE, 'w') as f:
            f.write(current_hash)
            
        # Send Alert
        msg = (
            f"🔔 <b>Update Detected!</b>\n"
            f"URL: {TARGET_URL}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        send_telegram_alert(msg)
    else:
        print("No changes detected.")

if __name__ == "__main__":
    main()
