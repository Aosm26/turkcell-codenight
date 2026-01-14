from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)  # For authentication
    role = Column(String, default="USER")  # USER or ADMIN

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
    service = Column(String, nullable=False)  # Superonline, Paycell, TV+
    request_type = Column(
        String, nullable=False
    )  # CONNECTION_ISSUE, PAYMENT_PROBLEM, etc.
    urgency = Column(String, nullable=False)  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDING")  # PENDING, ASSIGNED, COMPLETED

    user = relationship("User", back_populates="requests")
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
    condition = Column(String, nullable=False)  # e.g., "urgency == 'HIGH'"
    weight = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
