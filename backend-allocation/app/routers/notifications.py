from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Notification
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    notification_id: str
    user_id: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: str, db: Session = Depends(get_db)):
    """Get notifications for a user"""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return notifications


@router.post("/{user_id}/mark-read")
def mark_notifications_read(user_id: str, db: Session = Depends(get_db)):
    """Mark all notifications as read for a user"""
    db.query(Notification).filter(
        Notification.user_id == user_id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "ok"}
