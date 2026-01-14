from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Request, Allocation
from schemas import AllocationResponse, AllocateRequest, NotificationResponse
from services.allocation import AllocationService

router = APIRouter(prefix="/allocations", tags=["Allocations"])


@router.get("", response_model=list[AllocationResponse])
def get_allocations(status: str = None, db: Session = Depends(get_db)):
    """Get all allocations"""
    query = db.query(Allocation)

    if status:
        query = query.filter(Allocation.status == status)

    return query.order_by(Allocation.timestamp.desc()).all()


@router.post("/allocate", response_model=list[AllocationResponse])
def allocate(req: AllocateRequest = None, db: Session = Depends(get_db)):
    """Allocate pending requests to available resources"""
    if req and req.request_id:
        # Allocate specific request
        request = db.query(Request).filter(Request.request_id == req.request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        if request.status != "PENDING":
            raise HTTPException(status_code=400, detail="Request is not pending")

        allocation = AllocationService.allocate_request(request, db)
        if not allocation:
            raise HTTPException(status_code=400, detail="No available resources")
        return [allocation]
    else:
        # Allocate all pending requests
        allocations = AllocationService.allocate_pending_requests(db)
        return allocations


@router.get("/{allocation_id}", response_model=AllocationResponse)
def get_allocation(allocation_id: str, db: Session = Depends(get_db)):
    """Get a specific allocation"""
    allocation = (
        db.query(Allocation).filter(Allocation.allocation_id == allocation_id).first()
    )
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return allocation


@router.get("/{allocation_id}/notification", response_model=NotificationResponse)
def get_notification(allocation_id: str, db: Session = Depends(get_db)):
    """Get mock BiP notification for an allocation"""
    allocation = (
        db.query(Allocation).filter(Allocation.allocation_id == allocation_id).first()
    )
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    return AllocationService.get_notification_message(allocation)
