from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Request, Allocation, Resource
from schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary statistics"""

    # Pending requests count
    pending_requests = db.query(Request).filter(Request.status == "PENDING").count()

    # Active allocations count
    active_allocations = (
        db.query(Allocation).filter(Allocation.status == "ASSIGNED").count()
    )

    # Total resources
    total_resources = db.query(Resource).count()

    # Resource utilization
    total_capacity = db.query(func.sum(Resource.capacity)).scalar() or 0
    utilization = (
        (active_allocations / total_capacity * 100) if total_capacity > 0 else 0
    )

    # Requests by urgency
    urgency_counts = (
        db.query(Request.urgency, func.count(Request.request_id))
        .filter(Request.status == "PENDING")
        .group_by(Request.urgency)
        .all()
    )

    requests_by_urgency = {u: c for u, c in urgency_counts}

    # Requests by service
    service_counts = (
        db.query(Request.service, func.count(Request.request_id))
        .filter(Request.status == "PENDING")
        .group_by(Request.service)
        .all()
    )

    requests_by_service = {s: c for s, c in service_counts}

    return DashboardSummary(
        pending_requests=pending_requests,
        active_allocations=active_allocations,
        total_resources=total_resources,
        resource_utilization=round(utilization, 2),
        requests_by_urgency=requests_by_urgency,
        requests_by_service=requests_by_service,
    )
