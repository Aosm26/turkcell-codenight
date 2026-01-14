from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import AppOption
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/options", tags=["Options"])


class OptionItem(BaseModel):
    key: str
    value: str
    icon: str | None = None

    class Config:
        from_attributes = True


class ServiceWithTypes(BaseModel):
    """Service with its specific request types"""

    key: str
    value: str
    icon: str | None = None
    request_types: List[OptionItem]


@router.get("/services", response_model=List[ServiceWithTypes])
def get_services_with_types(db: Session = Depends(get_db)):
    """Get services with their specific request types"""
    services = (
        db.query(AppOption)
        .filter(AppOption.category == "SERVICE")
        .order_by(AppOption.order)
        .all()
    )

    result = []
    for service in services:
        # Get request types for this service
        request_types = (
            db.query(AppOption)
            .filter(
                AppOption.category == "REQUEST_TYPE",
                AppOption.parent_key == service.key,
            )
            .order_by(AppOption.order)
            .all()
        )

        result.append(
            ServiceWithTypes(
                key=service.key,
                value=service.value,
                icon=service.icon,
                request_types=[
                    OptionItem(key=rt.key, value=rt.value, icon=rt.icon)
                    for rt in request_types
                ],
            )
        )

    return result


@router.get("/urgency", response_model=List[OptionItem])
def get_urgency_levels(db: Session = Depends(get_db)):
    """Get urgency levels"""
    urgency = (
        db.query(AppOption)
        .filter(AppOption.category == "URGENCY")
        .order_by(AppOption.order)
        .all()
    )

    return [OptionItem(key=u.key, value=u.value, icon=u.icon) for u in urgency]
