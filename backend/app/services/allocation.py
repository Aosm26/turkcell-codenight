from sqlalchemy.orm import Session
from models import Request, Resource, Allocation, AllocationRule
from datetime import datetime
import uuid


class AllocationService:
    @staticmethod
    def calculate_priority(
        request: Request, rules: list[AllocationRule], db: Session
    ) -> float:
        """Calculate priority score based on active rules"""
        score = 0.0

        for rule in rules:
            if not rule.is_active:
                continue

            # Evaluate condition
            condition = rule.condition
            try:
                # Create context for evaluation
                context = {
                    "urgency": request.urgency,
                    "service": request.service,
                    "request_type": request.request_type,
                }

                # Simple condition evaluation
                if "urgency ==" in condition:
                    urgency_val = condition.split("==")[1].strip().strip("'\"")
                    if request.urgency == urgency_val:
                        score += rule.weight
                elif "service ==" in condition:
                    service_val = condition.split("==")[1].strip().strip("'\"")
                    if request.service == service_val:
                        score += rule.weight
                elif "request_type ==" in condition:
                    type_val = condition.split("==")[1].strip().strip("'\"")
                    if request.request_type == type_val:
                        score += rule.weight
            except:
                continue

        # Add waiting time bonus (2 points per hour, max 20)
        if request.created_at:
            waiting_hours = (
                datetime.utcnow() - request.created_at
            ).total_seconds() / 3600
            score += min(waiting_hours * 2, 20)

        return score

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
                continue

            # Calculate resource score (prefer same city)
            resource_score = resource.capacity - active_count  # Available capacity
            if user_city and resource.city == user_city:
                resource_score += 10  # Bonus for same city

            if resource_score > best_score:
                best_score = resource_score
                best_resource = resource

        return best_resource

    @staticmethod
    def allocate_request(request: Request, db: Session) -> Allocation | None:
        """Allocate a single request to best available resource"""
        # Get allocation rules
        rules = db.query(AllocationRule).filter(AllocationRule.is_active == True).all()

        # Calculate priority
        priority_score = AllocationService.calculate_priority(request, rules, db)

        # Find best resource
        resource = AllocationService.find_best_resource(request, db)

        if not resource:
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

        return allocation

    @staticmethod
    def allocate_pending_requests(db: Session) -> list[Allocation]:
        """Allocate all pending requests by priority"""
        # Get all pending requests
        pending = db.query(Request).filter(Request.status == "PENDING").all()

        # Get rules for priority calculation
        rules = db.query(AllocationRule).filter(AllocationRule.is_active == True).all()

        # Calculate priorities and sort
        requests_with_priority = []
        for req in pending:
            priority = AllocationService.calculate_priority(req, rules, db)
            requests_with_priority.append((req, priority))

        # Sort by priority (highest first)
        requests_with_priority.sort(key=lambda x: x[1], reverse=True)

        # Allocate in order
        allocations = []
        for req, _ in requests_with_priority:
            allocation = AllocationService.allocate_request(req, db)
            if allocation:
                allocations.append(allocation)

        return allocations

    @staticmethod
    def get_notification_message(allocation: Allocation) -> dict:
        """Generate mock BiP notification"""
        return {
            "user_id": allocation.request.user_id,
            "message": f"Talebiniz öncelikli olarak işleme alındı. {allocation.resource.resource_type} yönlendirildi.",
        }
