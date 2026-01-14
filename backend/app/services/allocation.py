from sqlalchemy.orm import Session
from models import Request, Resource, Allocation, User
from services.rule_engine import RuleEngine
import logging
from datetime import datetime
import uuid


# Logger konfigürasyonu
logger = logging.getLogger("backend.services")
event_logger = logging.getLogger("backend.events")


class AllocationService:
                    if request.service == service_val:
                        score += rule.weight
                        matched_rules.append(f"{rule.rule_id}(+{rule.weight})")
                elif "request_type ==" in condition:
                    type_val = condition.split("==")[1].strip().strip("'\"")
                    if request.request_type == type_val:
                        score += rule.weight
                        matched_rules.append(f"{rule.rule_id}(+{rule.weight})")
            except Exception:
                continue

        # Add waiting time bonus (2 points per hour, max 20)
        waiting_bonus = 0.0
        if request.created_at:
            waiting_hours = (
                datetime.utcnow() - request.created_at
            ).total_seconds() / 3600
            waiting_bonus = min(waiting_hours * 2, 20)
            score += waiting_bonus

        allocation_logger.debug(
            f"Priority calculated for {request.request_id}: "
            f"base={score - waiting_bonus:.1f}, waiting_bonus={waiting_bonus:.1f}, "
            f"total={score:.1f}, rules={matched_rules}"
        )

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

        # Get allocation rules
        rules = db.query(AllocationRule).filter(AllocationRule.is_active == True).all()

        # Calculate priority
        priority_score = AllocationService.calculate_priority(request, rules, db)

        # --- STEP 2: FIND BEST RESOURCE (Placeholder Logic) ---
        # Find available resource in same city
        user = db.query(User).filter(User.user_id == request.user_id).first()
        city = user.city if user else "Istanbul"

        resource = (
            db.query(Resource)
            .filter(Resource.city == city, Resource.status == "AVAILABLE")
            .first()
        )
        
        status = "ASSIGNED"
        if not resource:
            logger.warning(f"No resource found for {request.request_id} in {city}")
            status = "PENDING"
            # Resource not allocated, but we still update priority potentially?
            # For now let's just return
            return None

        # --- STEP 3: CREATE ALLOCATION ---
        allocation = Allocation(
            allocation_id=f"AL-{request.request_id}",
            request_id=request.request_id,
            resource_id=resource.resource_id,
            priority_score=priority_score,
            status="ASSIGNED",
            timestamp=datetime.utcnow(),
        )
        
        # Update resource status
        resource.status = "BUSY"
        request.status = "ASSIGNED"
        
        db.add(allocation)
        db.commit()
        db.refresh(allocation) # Added to match original behavior
        
        event_logger.info(f"ALLOCATION_SUCCESS | Req: {request.request_id} | Res: {resource.resource_id} | Score: {priority_score}")
        
        return allocation

    @staticmethod
    def allocate_pending_requests(db: Session) -> list[Allocation]:
        """Allocate all pending requests by priority"""
        # Get all pending requests
        pending = db.query(Request).filter(Request.status == "PENDING").all()

        allocation_logger.info(
            f"🔄 Starting batch allocation: {len(pending)} pending requests"
        )

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
