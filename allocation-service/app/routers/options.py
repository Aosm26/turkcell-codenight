from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import AppOption
from pydantic import BaseModel
from typing import Dict, List

router = APIRouter(prefix="/options", tags=["Options"])


class OptionItem(BaseModel):
    key: str
    value: str
    icon: str | None = None

    class Config:
        from_attributes = True


class OptionsResponse(BaseModel):
    SERVICE: List[OptionItem]
    REQUEST_TYPE: List[OptionItem]
    URGENCY: List[OptionItem]
    CITY: List[OptionItem]


@router.get("", response_model=OptionsResponse)
def get_options(db: Session = Depends(get_db)):
    """Get all dynamic options grouped by category"""
    options = db.query(AppOption).order_by(AppOption.category, AppOption.order).all()

    grouped = {"SERVICE": [], "REQUEST_TYPE": [], "URGENCY": [], "CITY": []}

    for option in options:
        if option.category in grouped:
            grouped[option.category].append(
                OptionItem(key=option.key, value=option.value, icon=option.icon)
            )

    return OptionsResponse(**grouped)
