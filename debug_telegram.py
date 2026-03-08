import requests
import config
import sys
import traceback

def debug():
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": "Debug Test Message"
    }
    
    with open("debug_log.txt", "w", encoding="utf-8") as f:
        f.write(f"Token: {config.TELEGRAM_TOKEN[:10]}...\n")
        f.write(f"Chat ID: {config.TELEGRAM_CHAT_ID}\n")
        
        try:
            f.write("Sending request...\n")
            response = requests.post(url, json=payload, timeout=10)
            f.write(f"Status Code: {response.status_code}\n")
            f.write(f"Response: {response.text}\n")
        except Exception:
            f.write(f"Error: {traceback.format_exc()}\n")

if __name__ == "__main__":
    debug()
