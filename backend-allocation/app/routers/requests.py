from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Request, User
from schemas import RequestCreate, RequestResponse
from datetime import datetime
import uuid

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post("", response_model=RequestResponse)
def create_request(req: RequestCreate, db: Session = Depends(get_db)):
    """Create a new service request"""
    # Verify user exists
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create request
    new_request = Request(
        request_id=f"REQ-{uuid.uuid4().hex[:6].upper()}",
        user_id=req.user_id,
        service=req.service,
        request_type=req.request_type,
        urgency=req.urgency,
        created_at=datetime.utcnow(),
        status="PENDING",
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request


@router.get("", response_model=list[RequestResponse])
def get_requests(
    status: str = None,
    urgency: str = None,
    service: str = None,
    db: Session = Depends(get_db),
):
    """Get all requests with optional filters"""
    query = db.query(Request)

    if status:
        query = query.filter(Request.status == status)
    if urgency:
        query = query.filter(Request.urgency == urgency)
    if service:
        query = query.filter(Request.service == service)

    return query.order_by(Request.created_at.desc()).all()


@router.get("/{request_id}", response_model=RequestResponse)
def get_request(request_id: str, db: Session = Depends(get_db)):
    """Get a specific request by ID"""
    request = db.query(Request).filter(Request.request_id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request
