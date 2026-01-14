import os
import requests
from logging_config import api_logger

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")


def notify_user(user_id: str, message: str) -> bool:
    """Send notification via Auth Service"""
    try:
        url = f"{AUTH_SERVICE_URL}/notifications"
        data = {"user_id": user_id, "message": message}

        api_logger.info(f"📱 Sending notification to user {user_id} via Auth Service")
        response = requests.post(url, json=data, timeout=5)

        if response.ok:
            api_logger.info(f"✅ Notification sent successfully")
            return True
        else:
            api_logger.warning(f"❌ Notification failed: {response.status_code}")
            return False
    except Exception as e:
        api_logger.error(f"Error sending notification: {e}")
        return False
