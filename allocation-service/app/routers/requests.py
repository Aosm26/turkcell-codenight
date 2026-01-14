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

    # Validate: user can only create requests for their own service
    if user.role == "USER":
        if not user.service_id:
            raise HTTPException(status_code=400, detail="User has no service assigned")
        if req.service_id != user.service_id:
            raise HTTPException(
                status_code=403,
                detail=f"User can only create requests for their service: {user.service_id}",
            )

    # Create request
    new_request = Request(
        request_id=f"REQ-{uuid.uuid4().hex[:6].upper()}",
        user_id=req.user_id,
        service_id=req.service_id,
        request_type_id=req.request_type_id,
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
    user_id: str = None,
    status: str = None,
    urgency: str = None,
    service_id: str = None,
    db: Session = Depends(get_db),
):
    """Get requests with optional filters

    - If user_id provided (USER role): automatically filters by user's service
    - If no user_id (ADMIN): returns all requests or filtered by service_id
    """
    query = db.query(Request)

    # If user_id is provided, filter by that user's service (for USER role)
    if user_id:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user and user.role == "USER" and user.service_id:
            # User can only see requests for their service
            query = query.filter(Request.service_id == user.service_id)
        elif user and user.role == "ADMIN":
            # Admin can see all, but can filter by service_id if provided
            pass

    # Apply other filters
    if status:
        query = query.filter(Request.status == status)
    if urgency:
        query = query.filter(Request.urgency == urgency)
    if service_id:
        query = query.filter(Request.service_id == service_id)

    return query.order_by(Request.created_at.desc()).all()


@router.get("/{request_id}", response_model=RequestResponse)
def get_request(request_id: str, user_id: str = None, db: Session = Depends(get_db)):
    """Get a specific request by ID

    - USER can only view requests in their service
    - ADMIN can view any request
    """
    request = db.query(Request).filter(Request.request_id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Check if user has permission to view this request
    if user_id:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user and user.role == "USER" and user.service_id:
            if request.service_id != user.service_id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only view requests for your service",
                )

    return request
