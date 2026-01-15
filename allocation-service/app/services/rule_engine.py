from sqlalchemy.orm import Session
from models import AllocationRule, DerivedVariable, Request
from datetime import datetime
from logging_config import allocation_logger


class RuleEngine:
    """
    Dynamic Rule Engine: Evaluates formulas and conditions from database.

    Flow:
    1. Build Context: Extract request data + calculate waiting_hours
    2. Evaluate Variables: Execute DerivedVariable formulas (e.g. Risk_Skoru)
    3. Evaluate Rules: Check AllocationRule conditions and sum weights
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_priority(
        self, request: Request, current_priority: float = 0.0
    ) -> float:
        """
        Main entry point for priority calculation.

        Args:
            request: The request to calculate priority for
            current_priority: Starting priority score (default 0)

        Returns:
            Final calculated priority score
        """
        allocation_logger.info(f"⚙️ Calculating priority for {request.request_id}")

        # Step 1: Build evaluation context from request
        context = self._build_context(request)
        context["priority_score"] = current_priority

        # Step 2: Evaluate derived variables (formulas)
        self._evaluate_variables(context)

        # Step 3: Evaluate allocation rules (conditions)
        final_score = self._evaluate_rules(context)

        allocation_logger.info(
            f"✅ Final priority for {request.request_id}: {final_score:.1f}"
        )
        return final_score

    def _build_context(self, request: Request) -> dict:
        """
        Build evaluation context from request data.

        Context includes:
        - Basic fields: urgency, service, request_type
        - Calculated fields: urgency_score, waiting_hours
        """
        # Calculate waiting time
        waiting_hours = 0.0
        if request.created_at:
            time_delta = datetime.utcnow() - request.created_at
            waiting_hours = time_delta.total_seconds() / 3600

        context = {
            "urgency": request.urgency,  # HIGH, MEDIUM, LOW
            "service": request.service,  # Superonline, Paycell, TV+
            "request_type": request.request_type,  # CONNECTION_ISSUE, PAYMENT_PROBLEM, etc
            "waiting_hours": waiting_hours,
            "urgency_score": self._get_urgency_score(request.urgency),
            "user_id": request.user_id,
            "request_id": request.request_id,
        }

        allocation_logger.debug(
            f"Context built: urgency={context['urgency']}, "
            f"service={context['service']}, "
            f"waiting_hours={waiting_hours:.1f}"
        )

        return context

    def _get_urgency_score(self, urgency: str) -> int:
        """Convert urgency level to numeric score"""
        mapping = {"HIGH": 10, "MEDIUM": 5, "LOW": 1}
        return mapping.get(urgency, 1)

    def _evaluate_variables(self, context: dict):
        """
        Evaluate DerivedVariable formulas and add results to context.

        Example:
            Formula: "( urgency_score * 2 ) + 10"
            Result: Risk_Skoru = 30 (when urgency_score = 10)

        Results are added to context for use in rules.
        """
        variables = self.db.query(DerivedVariable).all()

        allocation_logger.debug(f"Evaluating {len(variables)} derived variables...")

        for var in variables:
            try:
                # Execute formula in restricted scope
                # __builtins__: None prevents dangerous operations
                result = eval(var.formula, {"__builtins__": None}, context)

                # Add to context for use in rules
                context[var.name] = result

                allocation_logger.debug(
                    f"  ✓ {var.name} = {result} (formula: {var.formula})"
                )

            except Exception as e:
                allocation_logger.error(
                    f"  ✗ Error evaluating variable '{var.name}': {e}"
                )
                context[var.name] = 0  # Fallback to 0

    def _evaluate_rules(self, context: dict) -> float:
        """
        Evaluate AllocationRule conditions and sum matching weights.

        Example:
            Condition: "Risk_Skoru > 20 and service == 'Superonline'"
            If True: Add weight to total score

        Returns:
            Final priority score
        """
        rules = (
            self.db.query(AllocationRule).filter(AllocationRule.is_active == True).all()
        )

        total_score = context.get("priority_score", 0.0)
        matched_rules = []

        allocation_logger.debug(f"Evaluating {len(rules)} active rules...")

        for rule in rules:
            try:
                # Evaluate condition in restricted scope
                if eval(rule.condition, {"__builtins__": None}, context):
                    total_score += rule.weight
                    matched_rules.append(f"{rule.rule_id}(+{rule.weight})")

                    allocation_logger.info(
                        f"  ✓ MATCHED: {rule.rule_id} → +{rule.weight} "
                        f"(condition: {rule.condition})"
                    )
                else:
                    allocation_logger.debug(f"  - {rule.rule_id}: condition not met")

            except Exception as e:
                allocation_logger.error(
                    f"  ✗ Error evaluating rule '{rule.rule_id}': {e}"
                )

        allocation_logger.info(
            f"Matched rules: {', '.join(matched_rules) if matched_rules else 'none'}"
        )

        return float(total_score)
