from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import create_access_token, get_password_hash
from app.crud import create_user, get_user_by_email, update_user, authenticate_user
from app.schemas import UserCreate, UserResponse, Token, PasswordReset, PasswordResetConfirm
from app.config import settings
import secrets
from datetime import datetime, timedelta
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    db_user = create_user(db=db, user=user)
    return db_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user and return access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
def forgot_password(password_reset: PasswordReset, db: Session = Depends(get_db)):
    """Send password reset email."""
    user = get_user_by_email(db, email=password_reset.email)
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset link has been sent."}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    
    # Update user with reset token
    update_user(db, user.id, {
        "reset_token": reset_token,
        "reset_token_expires": reset_token_expires
    })
    
    # In a real application, you would send an email here
    # For now, we'll just return the token (in production, send via email)
    return {
        "message": "Password reset link sent to your email.",
        "reset_token": reset_token  # Remove this in production
    }


@router.post("/reset-password")
def reset_password(password_reset: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using token."""
    # Find user with valid reset token
    user = db.query(User).filter(
        User.reset_token == password_reset.token,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password and clear reset token
    hashed_password = get_password_hash(password_reset.new_password)
    update_user(db, user.id, {
        "hashed_password": hashed_password,
        "reset_token": None,
        "reset_token_expires": None
    })
    
    return {"message": "Password has been reset successfully"}
