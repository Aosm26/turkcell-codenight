from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AllocationRule
from schemas import AllocationRuleResponse, AllocationRuleUpdate

router = APIRouter(prefix="/rules", tags=["Allocation Rules"])


@router.get("", response_model=list[AllocationRuleResponse])
def get_rules(db: Session = Depends(get_db)):
    """Get all allocation rules"""
    return db.query(AllocationRule).all()


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
