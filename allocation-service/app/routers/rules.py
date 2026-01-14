from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AllocationRule
from schemas import AllocationRuleResponse, AllocationRuleUpdate, AllocationRuleCreate

router = APIRouter(prefix="/rules", tags=["Allocation Rules"])


@router.get("", response_model=list[AllocationRuleResponse])
def get_rules(db: Session = Depends(get_db)):
    """Get all allocation rules"""
    return db.query(AllocationRule).all()


@router.post("", response_model=AllocationRuleResponse)
def create_rule(
    rule: AllocationRuleCreate, db: Session = Depends(get_db)
):
    """Create a new allocation rule"""
    # Generate ID if not provided (simple increment for now or UUID)
    if not rule.rule_id:
        import uuid
        rule.rule_id = f"AR-{str(uuid.uuid4())[:8]}"
    
    db_rule = AllocationRule(
        rule_id=rule.rule_id,
        condition=rule.condition,
        weight=rule.weight,
        is_active=rule.is_active
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.put("/{rule_id}", response_model=AllocationRuleResponse)
def update_rule(
    rule_id: str, update: AllocationRuleUpdate, db: Session = Depends(get_db)
):
    """Update an allocation rule"""
    rule = db.query(AllocationRule).filter(AllocationRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if update.weight is not None:
        rule.weight = update.weight
    if update.is_active is not None:
        rule.is_active = update.is_active

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    """Delete an allocation rule"""
    rule = db.query(AllocationRule).filter(AllocationRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}


# --- Derived Variables Endpoints ---

from models import DerivedVariable
from schemas import DerivedVariableCreate, DerivedVariableResponse

@router.get("/variables", response_model=list[DerivedVariableResponse])
def get_variables(db: Session = Depends(get_db)):
    """Get all derived variables"""
    return db.query(DerivedVariable).all()

@router.post("/variables", response_model=DerivedVariableResponse)
def create_variable(
    var: DerivedVariableCreate, db: Session = Depends(get_db)
):
    """Create a new derived variable"""
    import uuid
    db_var = DerivedVariable(
        variable_id=f"VAR-{str(uuid.uuid4())[:8]}",
        name=var.name,
        formula=var.formula,
        description=var.description
    )
    db.add(db_var)
    db.commit()
    db.refresh(db_var)
    return db_var
