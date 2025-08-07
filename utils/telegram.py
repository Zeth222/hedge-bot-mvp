"""Utilities for sending Telegram notifications."""

import os
from typing import Any, Optional

import requests


TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str) -> Optional[Any]:
    """Send a message via Telegram if credentials are available.

    When the necessary environment variables are not configured the message is
    printed to stdout so that the bot can operate in simulation mode without
    failing.
    """

    if not TOKEN or not CHAT_ID:
        print(f"Telegram message skipped: {message}")
        return None

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}

    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except requests.RequestException as exc:
        # Log the failure but do not raise to keep the bot running
        print(f"Failed to send Telegram message: {exc}")
        return None
