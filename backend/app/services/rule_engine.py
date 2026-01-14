from sqlalchemy.orm import Session
from models import AllocationRule, DerivedVariable, Request
import logging

# Configure logger
logger = logging.getLogger("backend.engine")

class RuleEngine:
    """
    Core brain of the system.
    Evaluates dynamic strings (Variables & Rules) stored in the database
    against the actual Request data to calculate Priority Scores.
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_priority(self, request: Request, current_priority: float = 0.0) -> float:
        """
        Main entry point.
        1. Context Preparation: Converts Request object to a flat dict.
        2. Variable Evaluation: Calculates 'Derived Variables' (e.g. Risk Score).
        3. Rule Evaluation: Checks 'Allocation Rules' and adds weights.
        """
        logger.info(f"⚙️ Calculating priority for Request: {request.request_id}")
        
        # 1. Base Context from Request
        context = self._build_context(request)
        context['priority_score'] = current_priority
        
        # 2. Evaluate Dynamic Variables (Formulas)
        self._evaluate_variables(context)
        
        # 3. Evaluate Rules (Logic)
        final_score = self._evaluate_rules(context)
        
        logger.info(f"✅ Final Calculated Score: {final_score}")
        return final_score

    def _build_context(self, request: Request) -> dict:
        """Flattens the Request object into a dictionary for eval() context."""
        return {
            "urgency": request.urgency,              # 'HIGH', 'MEDIUM', 'LOW'
            "service": request.service,              # 'Superonline', 'TV+'
            "request_type": request.request_type,    # 'CONNECTION_FAILURE'
            "waiting_hours": 0,                      # Placeholder - ideally calc from created_at
            # Helper for numeric urgency
            "urgency_score": self._get_urgency_score(request.urgency)
        }

    def _get_urgency_score(self, urgency: str) -> int:
        mapping = {'HIGH': 10, 'MEDIUM': 5, 'LOW': 1}
        return mapping.get(urgency, 1)

    def _evaluate_variables(self, context: dict):
        """Fetches DerivedVariable definitions and executes them."""
        variables = self.db.query(DerivedVariable).all()
        
        for var in variables:
            try:
                # Formula example: "( urgency_score * 2 ) + 10"
                # We use eval() in a restricted scope (context)
                # Ensure context values are safe types (int, float, str)
                result = eval(var.formula, {"__builtins__": None}, context)
                
                # Add result to context so subsequent rules/vars can use it
                context[var.name] = result
                logger.debug(f"   ➕ Variable Calculated: {var.name} = {result} (Formula: {var.formula})")
                
            except Exception as e:
                logger.error(f"   ❌ Error calculating variable '{var.name}': {e}")
                context[var.name] = 0 # Fallback

    def _evaluate_rules(self, context: dict) -> float:
        """Fetches Active Rules and executes them against the context."""
        rules = self.db.query(AllocationRule).filter(AllocationRule.is_active == True).all()
        total_score = context.get('priority_score', 0.0)

        for rule in rules:
            try:
                # Condition example: "risk_score > 50 and urgency == 'HIGH'"
                # If True, add weight to total_score
                if eval(rule.condition, {"__builtins__": None}, context):
                    total_score += rule.weight
                    logger.info(f"   ✅ Rule MATCHED: {rule.rule_id} (+{rule.weight}) -> Condition: {rule.condition}")
                else:
                    logger.debug(f"   Testing Rule: {rule.rule_id} -> False")
            
            except Exception as e:
                logger.error(f"   ❌ Error evaluating rule '{rule.rule_id}': {e}")

        return float(total_score)
