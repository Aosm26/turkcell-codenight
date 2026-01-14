from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Service, RequestType
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/services", tags=["Services"])


class ServiceResponse(BaseModel):
    service_id: str
    name: str
    icon: str | None
    description: str | None

    class Config:
        from_attributes = True


class RequestTypeResponse(BaseModel):
    type_id: str
    name: str
    description: str | None
    icon: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    """Get all services"""
    return db.query(Service).all()


@router.get("/{service_id}/request-types", response_model=List[RequestTypeResponse])
def get_request_types_for_service(service_id: str, db: Session = Depends(get_db)):
    """Get request types for a specific service"""
    return db.query(RequestType).filter(RequestType.service_id == service_id).all()
