from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# User Schemas
class UserBase(BaseModel):
    user_id: str
    name: str
    city: str


class UserResponse(UserBase):
    class Config:
        from_attributes = True


# Resource Schemas
class ResourceBase(BaseModel):
    resource_id: str
    resource_type: str
    capacity: int
    city: str
    status: str = "AVAILABLE"


class ResourceResponse(ResourceBase):
    class Config:
        from_attributes = True


# Request Schemas
class RequestCreate(BaseModel):
    user_id: str
    service: str
    request_type: str
    urgency: str


class RequestResponse(BaseModel):
    request_id: str
    user_id: str
    service: str
    request_type: str
    urgency: str
    created_at: datetime
    status: str

    class Config:
        from_attributes = True


# Allocation Schemas
class AllocationResponse(BaseModel):
    allocation_id: str
    request_id: str
    resource_id: str
    priority_score: float
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


class AllocateRequest(BaseModel):
    request_id: Optional[str] = None  # If None, allocate all pending


# AllocationRule Schemas
class AllocationRuleBase(BaseModel):
    rule_id: str
    condition: str
    weight: int
    is_active: bool = True


class AllocationRuleResponse(AllocationRuleBase):
    class Config:
        from_attributes = True


class AllocationRuleUpdate(BaseModel):
    weight: Optional[int] = None
    is_active: Optional[bool] = None


class AllocationRuleCreate(BaseModel):
    rule_id: Optional[str] = None
    condition: str
    weight: int
    is_active: bool = True


# Dashboard Schemas
class DashboardSummary(BaseModel):
    pending_requests: int
    active_allocations: int
    total_resources: int
    resource_utilization: float
    requests_by_urgency: dict
    requests_by_service: dict


# Notification Schema (Mock BiP)
class NotificationResponse(BaseModel):
    user_id: str
    message: str


# Derived Variable Schemas
class DerivedVariableBase(BaseModel):
    name: str
    formula: str
    description: Optional[str] = None


class DerivedVariableCreate(DerivedVariableBase):
    pass


class DerivedVariableResponse(DerivedVariableBase):
    variable_id: str

    class Config:
        from_attributes = True
