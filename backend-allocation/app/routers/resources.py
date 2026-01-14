from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Resource
from schemas import ResourceResponse

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("", response_model=list[ResourceResponse])
def get_resources(
    status: str = None,
    city: str = None,
    resource_type: str = None,
    db: Session = Depends(get_db),
):
    """Get all resources with optional filters"""
    query = db.query(Resource)

    if status:
        query = query.filter(Resource.status == status)
    if city:
        query = query.filter(Resource.city == city)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)

    return query.all()


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: str, db: Session = Depends(get_db)):
    """Get a specific resource by ID"""
    resource = db.query(Resource).filter(Resource.resource_id == resource_id).first()
    if not resource:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Resource not found")
    return resource
