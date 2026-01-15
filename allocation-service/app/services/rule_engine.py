from sqlalchemy.orm import Session
from models import AllocationRule, DerivedVariable, Request
from logging_config import allocation_logger


class RuleEngine:
    """
    Dynamic Rule Engine for Smart Allocation System.
    Evaluates formulas (DerivedVariables) and conditions (AllocationRules)
    against Request data to calculate priority scores.
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_priority(
        self, request: Request, current_priority: float = 0.0
    ) -> float:
        """
        Main entry point for priority calculation.
        1. Build context from request
        2. Evaluate derived variables (formulas)
        3. Evaluate allocation rules (conditions)
        """
        allocation_logger.info(
            f"⚙️ RuleEngine calculating priority for {request.request_id}"
        )

        # 1. Build base context from request
        context = self._build_context(request)
        context["priority_score"] = current_priority

        # 2. Evaluate dynamic variables
        self._evaluate_variables(context)

        # 3. Evaluate rules and calculate final score
        final_score = self._evaluate_rules(context)

        allocation_logger.info(f"✅ Final priority score: {final_score:.1f}")
        return final_score

    def _build_context(self, request: Request) -> dict:
        """
        Build evaluation context from request object.
        Includes request attributes and helper scores.
        """
        from datetime import datetime

        # Calculate waiting hours
        waiting_hours = 0.0
        if request.created_at:
            waiting_hours = (
                datetime.utcnow() - request.created_at
            ).total_seconds() / 3600

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
            f"service={context['service_id']}, "
            f"waiting_hours={waiting_hours:.1f}"
        )

        return context

    def _get_urgency_score(self, urgency: str) -> int:
        """Convert urgency level to numeric score"""
        mapping = {"HIGH": 10, "MEDIUM": 5, "LOW": 1}
        return mapping.get(urgency, 1)

    def _evaluate_variables(self, context: dict):
        """
        Fetch and evaluate DerivedVariable formulas.
        Results are added to context for use in rules.
        """
        variables = self.db.query(DerivedVariable).all()

        for var in variables:
            try:
                # Evaluate formula in restricted scope
                # Example: "( urgency_score * 2 ) + 10"
                result = eval(var.formula, {"__builtins__": None}, context)

                # Add to context for subsequent rules/variables
                context[var.name] = result
                allocation_logger.debug(
                    f"   ➕ Variable: {var.name} = {result} (formula: {var.formula})"
                )

            except Exception as e:
                allocation_logger.error(
                    f"   ❌ Error calculating variable '{var.name}': {e}"
                )
                context[var.name] = 0  # Fallback to 0

    def _evaluate_rules(self, context: dict) -> float:
        """
        Fetch and evaluate active AllocationRules.
        If condition is True, add weight to score.
        """
        rules = (
            self.db.query(AllocationRule).filter(AllocationRule.is_active == True).all()
        )

        total_score = context.get("priority_score", 0.0)
        matched_rules = []

        for rule in rules:
            try:
                # Evaluate condition in restricted scope
                # Example: "urgency_score > 5 and service_id == 'SUPERONLINE'"
                if eval(rule.condition, {"__builtins__": None}, context):
                    total_score += rule.weight
                    matched_rules.append(f"{rule.rule_id}(+{rule.weight})")
                    allocation_logger.info(
                        f"   ✅ Rule MATCHED: {rule.rule_id} (+{rule.weight}) -> {rule.condition}"
                    )
                else:
                    allocation_logger.debug(f"   Rule {rule.rule_id} -> False")

            except Exception as e:
                allocation_logger.error(
                    f"   ❌ Error evaluating rule '{rule.rule_id}': {e}"
                )

        if matched_rules:
            allocation_logger.info(f"   Matched rules: {', '.join(matched_rules)}")

        return float(total_score)
