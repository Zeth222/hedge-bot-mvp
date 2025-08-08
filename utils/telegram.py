import os
import requests


def send_telegram_message(message: str) -> None:
    """Send a message to Telegram or log to console if not configured."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[TELEGRAM] {message}")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as exc:
        print(f"[TELEGRAM ERROR] {exc}")
