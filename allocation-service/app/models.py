from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Service(Base):
    """Service types (Superonline, Paycell, TV+)"""

    __tablename__ = "services"

    service_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    icon = Column(String, nullable=True)
    description = Column(String, nullable=True)

    users = relationship("User", back_populates="service")
    requests = relationship("Request", back_populates="service")
    request_types = relationship("RequestType", back_populates="service")


class RequestType(Base):
    """Request types specific to each service"""

    __tablename__ = "request_types"

    type_id = Column(String, primary_key=True)
    service_id = Column(String, ForeignKey("services.service_id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)

    service = relationship("Service", back_populates="request_types")
    requests = relationship("Request", back_populates="request_type")


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    service_id = Column(
        String, ForeignKey("services.service_id"), nullable=True
    )  # USER's service
    password_hash = Column(String, nullable=True)  # For authentication
    role = Column(String, default="USER")  # USER or ADMIN

    service = relationship("Service", back_populates="users")
    requests = relationship("Request", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Notification(Base):
    """Mock BiP notifications"""

    __tablename__ = "notifications"

    notification_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Resource(Base):
    __tablename__ = "resources"

    resource_id = Column(String, primary_key=True)
    resource_type = Column(String, nullable=False)  # TECH_TEAM, SUPPORT_AGENT
    capacity = Column(Integer, nullable=False)
    city = Column(String, nullable=False)
    status = Column(String, default="AVAILABLE")  # AVAILABLE, BUSY

    allocations = relationship("Allocation", back_populates="resource")


class Request(Base):
    __tablename__ = "requests"

    request_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    service_id = Column(String, ForeignKey("services.service_id"), nullable=False)
    request_type_id = Column(
        String, ForeignKey("request_types.type_id"), nullable=False
    )
    urgency = Column(String, nullable=False)  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDING")  # PENDING, ASSIGNED, COMPLETED

    user = relationship("User", back_populates="requests")
    service = relationship("Service", back_populates="requests")
    request_type = relationship("RequestType", back_populates="requests")
    allocation = relationship("Allocation", back_populates="request", uselist=False)


class Allocation(Base):
    __tablename__ = "allocations"

    allocation_id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("requests.request_id"), nullable=False)
    resource_id = Column(String, ForeignKey("resources.resource_id"), nullable=False)
    priority_score = Column(Float, nullable=False)
    status = Column(String, default="ASSIGNED")  # ASSIGNED, COMPLETED, CANCELLED
    timestamp = Column(DateTime, default=datetime.utcnow)

    request = relationship("Request", back_populates="allocation")
    resource = relationship("Resource", back_populates="allocations")


class AllocationRule(Base):
    __tablename__ = "allocation_rules"

    rule_id = Column(String, primary_key=True)
    condition = Column(String, nullable=False)  # Dynamic condition string
    weight = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


class DerivedVariable(Base):
    """Dynamic variables calculated from formulas for rule engine"""

    __tablename__ = "derived_variables"

    variable_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)  # e.g. "Risk_Skoru"
    formula = Column(String, nullable=False)  # e.g. "( urgency_score * 2 ) + 10"
    description = Column(String, nullable=True)
