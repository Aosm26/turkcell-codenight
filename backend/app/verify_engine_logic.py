from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.rule_engine import RuleEngine
from models import Request, DerivedVariable, AllocationRule, Base
import logging

# Setup Logging to console
logging.basicConfig(level=logging.INFO)

# --- ISOLATION: Use SQLite In-Memory ---
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def seed_data():
    """Inject dummy data for testing logic"""
    # 1. Variable: Risk Score
    var = DerivedVariable(
        variable_id="v1",
        name="Risk_Skoru",
        formula="( urgency_score * 2 ) + 10",
        description="Test Var"
    )
    db.add(var)
    
    # 2. Rule: High Risk
    rule = AllocationRule(
        rule_id="AR-1",
        condition="Risk_Skoru > 20 and service == 'Superonline'",
        weight=50,
        is_active=True
    )
    db.add(rule)
    
    # 3. Request
    req = Request(
        request_id="REQ-001",
        user_id="U1",
        service="Superonline",
        request_type="CONN_ERR",
        urgency="HIGH",
        status="PENDING"
    )
    db.add(req)
    db.commit()

def verify():
    seed_data()
    
    print("\n--- 1. Checking Mock Database ---")
    vars = db.query(DerivedVariable).all()
    rules = db.query(AllocationRule).all()
    
    print(f"Found {len(vars)} Variables:")
    for v in vars:
        print(f"  - {v.name}: {v.formula}")
        
    print(f"Found {len(rules)} Rules:")
    for r in rules:
        print(f"  - {r.rule_id}: {r.condition} (Weight: {r.weight})")

    print("\n--- 2. Running Engine on Sample Request ---")
    # Get a random pending request
    request = db.query(Request).first()
    if not request:
        print("No requests found in DB to test.")
        return

    print(f"Testing with Request ID: {request.request_id}")
    print(f"  - Urgency: {request.urgency}")
    print(f"  - Service: {request.service}")
    
    engine = RuleEngine(db)
    final_score = engine.calculate_priority(request)
    
    print("\n--- 3. Result ---")
    print(f"Final Calculated Score: {final_score}")

if __name__ == "__main__":
    verify()
