from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth import get_current_active_user
from app.crud import get_user_profile, update_user, get_user_by_id
from app.schemas import UserResponse, UserUpdate, UserProfile, ReviewResponse
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.get("/me/profile", response_model=UserProfile)
def get_user_profile_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user profile with order count and reviews."""
    profile_data = get_user_profile(db, current_user.id)
    if not profile_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Convert to response format
    user_response = UserResponse.model_validate(profile_data["user"])
    
    # Convert reviews to response format
    reviews_response = []
    for review in profile_data["reviews"]:
        review_response = ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            product_id=review.product_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
            user=user_response
        )
        reviews_response.append(review_response)
    
    return UserProfile(
        **user_response.model_dump(),
        total_orders=profile_data["total_orders"],
        reviews=reviews_response
    )


@router.put("/me", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    # Filter out None values
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    updated_user = update_user(db, current_user.id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID (public information only)."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
