import os

try:
    import requests
except Exception:
    requests = None


def send_telegram_message(message: str):
    """Send a message via Telegram or print to console if not configured."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id or requests is None:
        print(message)
        return {"status": "console"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    return response.json()

