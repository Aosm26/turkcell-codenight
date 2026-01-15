from sqlalchemy.orm import Session
from models import Request, Resource, Allocation, AllocationRule, User
from services.rule_engine import RuleEngine
from datetime import datetime
from logging_config import allocation_logger
import uuid


class AllocationService:
    """Service for allocating requests to resources"""

    @staticmethod
    def calculate_priority(request: Request, db: Session) -> float:
        """
        Calculate priority score for a request using RuleEngine.
        Uses DerivedVariables and AllocationRules from database.
        """
        engine = RuleEngine(db)
        priority_score = engine.calculate_priority(request, current_priority=0.0)
        return priority_score

    @staticmethod
    def find_best_resource(request: Request, db: Session) -> Resource | None:
        """Find the best available resource for a request"""
        # Get user's city from the request
        user = request.user
        user_city = user.city if user else None

        # Get active allocations count per resource
        resources = db.query(Resource).filter(Resource.status == "AVAILABLE").all()

        best_resource = None
        best_score = -1

        for resource in resources:
            # Count current allocations for this resource
            active_count = (
                db.query(Allocation)
                .filter(
                    Allocation.resource_id == resource.resource_id,
                    Allocation.status == "ASSIGNED",
                )
                .count()
            )

            # Skip if at capacity
            if active_count >= resource.capacity:
                allocation_logger.debug(
                    f"Resource {resource.resource_id} at capacity ({active_count}/{resource.capacity})"
                )
                continue

            # Calculate resource score (prefer same city)
            resource_score = resource.capacity - active_count  # Available capacity
            if user_city and resource.city == user_city:
                resource_score += 10  # Bonus for same city

            if resource_score > best_score:
                best_score = resource_score
                best_resource = resource

        if best_resource:
            allocation_logger.debug(
                f"Best resource for {request.request_id}: {best_resource.resource_id} "
                f"(city={best_resource.city}, score={best_score})"
            )
        else:
            allocation_logger.warning(f"No available resource for {request.request_id}")

        return best_resource

    @staticmethod
    def allocate_request(request: Request, db: Session) -> Allocation | None:
        """Allocate a single request to best available resource"""
        allocation_logger.info(f"📋 Allocating request {request.request_id}...")

        # Calculate priority
        priority_score = AllocationService.calculate_priority(request, db)

        # Find best resource
        resource = AllocationService.find_best_resource(request, db)

        if not resource:
            allocation_logger.warning(
                f"❌ Could not allocate {request.request_id}: No available resources"
            )
            return None

        # Create allocation
        allocation = Allocation(
            allocation_id=f"AL-{uuid.uuid4().hex[:6].upper()}",
            request_id=request.request_id,
            resource_id=resource.resource_id,
            priority_score=priority_score,
            status="ASSIGNED",
            timestamp=datetime.utcnow(),
        )

        # Update request status
        request.status = "ASSIGNED"

        db.add(allocation)
        db.commit()
        db.refresh(allocation)

        allocation_logger.info(
            f"✅ Allocated {request.request_id} → {resource.resource_id} "
            f"(priority={priority_score:.1f})"
        )

        # Send notification via Auth Service (disabled - requires requests module)
        # from services.http_client import notify_user
        # message = f"Talebiniz öncelikli olarak işleme alındı. {resource.resource_type} yönlendirildi."
        # notify_user(request.user_id, message)

        return allocation

    @staticmethod
    def allocate_pending_requests(db: Session) -> list[Allocation]:
        """Allocate all pending requests by priority"""
        # Get all pending requests
        pending = db.query(Request).filter(Request.status == "PENDING").all()

        allocation_logger.info(
            f"🔄 Starting batch allocation: {len(pending)} pending requests"
        )

        # Calculate priorities and sort
        requests_with_priority = []
        for req in pending:
            priority = AllocationService.calculate_priority(req, db)
            requests_with_priority.append((req, priority))

        # Sort by priority (highest first)
        requests_with_priority.sort(key=lambda x: x[1], reverse=True)

        # Allocate in order
        allocations = []
        for req, priority in requests_with_priority:
            allocation_logger.debug(
                f"Processing {req.request_id} with priority {priority:.1f}"
            )
            allocation = AllocationService.allocate_request(req, db)
            if allocation:
                allocations.append(allocation)

        allocation_logger.info(
            f"✅ Batch allocation complete: {len(allocations)}/{len(pending)} requests allocated"
        )

        return allocations

    @staticmethod
    def get_notification_message(allocation: Allocation) -> dict:
        """Generate mock BiP notification"""
        message = {
            "user_id": allocation.request.user_id,
            "message": f"Talebiniz öncelikli olarak işleme alındı. {allocation.resource.resource_type} yönlendirildi.",
        }
        allocation_logger.info(
            f"📱 BiP notification prepared for user {allocation.request.user_id}"
        )
        return message
