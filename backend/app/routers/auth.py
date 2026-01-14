from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user,
)
from pydantic import BaseModel
from logging_config import api_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    user_id: str
    name: str
    city: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str


class UserProfile(BaseModel):
    user_id: str
    name: str
    city: str
    role: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserProfile)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing = db.query(User).filter(User.user_id == req.user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User ID already exists"
        )

    # Create new user
    user = User(
        user_id=req.user_id,
        name=req.name,
        city=req.city,
        password_hash=get_password_hash(req.password),
        role="USER",  # New registrations are always USER
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    api_logger.info(f"✅ New user registered: {user.user_id}")

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.user_id, "role": user.role})

    return TokenResponse(
        access_token=access_token, user_id=user.user_id, name=user.name, role=user.role
    )


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user
