# -*- coding: utf-8 -*-
# telegram_bot.py
# Telegram Notification Module

import requests
import config

def send_message(message):
    """
    Sends a message to the configured Telegram chat.
    """
    token = config.TELEGRAM_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID

    # [사용자 요청] 텔레그램 발행 기능 임시 중단
    # print(f"   ⚠️ [Telegram Paused] Message would be: {message}")
    return

    if token == "YOUR_BOT_TOKEN_HERE" or chat_id == "YOUR_CHAT_ID_HERE":
        print(f"   ⚠️ [Telegram] Token/ChatID not configured. Message skipped: {message}")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            print(f"   ⚠️ [Telegram] Send failed: {response.text}")
    except Exception as e:
        print(f"   ⚠️ [Telegram] Error: {e}")

def notify_status(account_id, action, status):
    """
    Helper for standardized status updates.
    """
    icon = "✅" if status == "SUCCESS" else "❌"
    msg = f"{icon} [계정: {account_id}] {action} : {status}"
    send_message(msg)
    print(msg)
