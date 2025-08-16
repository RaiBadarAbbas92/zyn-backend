from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.crud import (
    create_video_review, get_video_review_by_id, get_all_video_reviews, update_video_review,
    update_video_review_status, delete_video_review, create_coupon_code, get_coupon_by_code,
    get_user_coupons, get_all_coupons, validate_coupon, use_coupon, deactivate_coupon,
    get_user_by_email
)
from app.schemas import VideoReviewCreate, VideoReviewUpdate, VideoReviewResponse, CouponCodeCreate, CouponCodeResponse, UserResponse
from app.models import User, VideoReview, CouponCode

router = APIRouter(prefix="/loyalty", tags=["Loyalty Program"])


# Video Review endpoints
@router.post("/video-reviews", response_model=VideoReviewResponse)
def submit_video_review(
    video_review: VideoReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit a video review for loyalty program."""
    # Validate platform
    valid_platforms = ["youtube", "instagram", "tiktok", "facebook", "twitter", "other"]
    if video_review.platform.lower() not in valid_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform. Must be one of: {valid_platforms}"
        )
    
    # Create video review data
    video_review_data = {
        "video_url": video_review.video_url,
        "description": video_review.description,
        "platform": video_review.platform.lower()
    }
    
    db_video_review = create_video_review(db=db, video_review=video_review_data, user_id=current_user.id)
    
    # Create user response
    user_response = UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        phone=current_user.phone,
        address=current_user.address,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )
    
    return VideoReviewResponse(
        id=db_video_review.id,
        user_id=db_video_review.user_id,
        video_url=db_video_review.video_url,
        description=db_video_review.description,
        platform=db_video_review.platform,
        status=db_video_review.status,
        admin_notes=db_video_review.admin_notes,
        created_at=db_video_review.created_at,
        updated_at=db_video_review.updated_at,
        user=user_response
    )


@router.get("/video-reviews", response_model=List[VideoReviewResponse])
def get_video_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """Get all video reviews with optional filtering."""
    video_reviews = get_all_video_reviews(db, skip=skip, limit=limit, status=status, user_id=user_id)
    
    # Convert to response format
    video_reviews_response = []
    for video_review in video_reviews:
        # Get user info for each video review
        user_response = UserResponse(
            id=video_review.user.id,
            email=video_review.user.email,
            username=video_review.user.username,
            full_name=video_review.user.full_name,
            phone=video_review.user.phone,
            address=video_review.user.address,
            is_active=video_review.user.is_active,
            is_verified=video_review.user.is_verified,
            created_at=video_review.user.created_at,
            updated_at=video_review.user.updated_at
        )
        
        video_review_response = VideoReviewResponse(
            id=video_review.id,
            user_id=video_review.user_id,
            video_url=video_review.video_url,
            description=video_review.description,
            platform=video_review.platform,
            status=video_review.status,
            admin_notes=video_review.admin_notes,
            created_at=video_review.created_at,
            updated_at=video_review.updated_at,
            user=user_response
        )
        video_reviews_response.append(video_review_response)
    
    return video_reviews_response


@router.get("/video-reviews/{video_review_id}", response_model=VideoReviewResponse)
def get_video_review(
    video_review_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific video review by ID."""
    video_review = get_video_review_by_id(db, video_review_id)
    if not video_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video review not found"
        )
    
    # Get user info
    user_response = UserResponse(
        id=video_review.user.id,
        email=video_review.user.email,
        username=video_review.user.username,
        full_name=video_review.user.full_name,
        phone=video_review.user.phone,
        address=video_review.user.address,
        is_active=video_review.user.is_active,
        is_verified=video_review.user.is_verified,
        created_at=video_review.user.created_at,
        updated_at=video_review.user.updated_at
    )
    
    return VideoReviewResponse(
        id=video_review.id,
        user_id=video_review.user_id,
        video_url=video_review.video_url,
        description=video_review.description,
        platform=video_review.platform,
        status=video_review.status,
        admin_notes=video_review.admin_notes,
        created_at=video_review.created_at,
        updated_at=video_review.updated_at,
        user=user_response
    )


@router.put("/video-reviews/{video_review_id}", response_model=VideoReviewResponse)
def update_my_video_review(
    video_review_id: int,
    video_review_update: VideoReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a video review by the owner."""
    # Check if video review exists and belongs to current user
    existing_video_review = get_video_review_by_id(db, video_review_id)
    if not existing_video_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video review not found"
        )
    
    if existing_video_review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this video review"
        )
    
    # Only allow updates if status is pending
    if existing_video_review.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update video review that has been reviewed"
        )
    
    # Filter out None values
    update_data = {k: v for k, v in video_review_update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    # Validate platform if being updated
    if "platform" in update_data:
        valid_platforms = ["youtube", "instagram", "tiktok", "facebook", "twitter", "other"]
        if update_data["platform"].lower() not in valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform. Must be one of: {valid_platforms}"
            )
        update_data["platform"] = update_data["platform"].lower()
    
    updated_video_review = update_video_review(db, video_review_id, update_data)
    if not updated_video_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video review not found"
        )
    
    # Create user response
    user_response = UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        phone=current_user.phone,
        address=current_user.address,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )
    
    return VideoReviewResponse(
        id=updated_video_review.id,
        user_id=updated_video_review.user_id,
        video_url=updated_video_review.video_url,
        description=updated_video_review.description,
        platform=updated_video_review.platform,
        status=updated_video_review.status,
        admin_notes=updated_video_review.admin_notes,
        created_at=updated_video_review.created_at,
        updated_at=updated_video_review.updated_at,
        user=user_response
    )


@router.delete("/video-reviews/{video_review_id}")
def delete_my_video_review(
    video_review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a video review by the owner."""
    # Check if video review exists and belongs to current user
    existing_video_review = get_video_review_by_id(db, video_review_id)
    if not existing_video_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video review not found"
        )
    
    if existing_video_review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this video review"
        )
    
    success = delete_video_review(db, video_review_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video review"
        )
    
    return {"message": "Video review deleted successfully"}


# Admin endpoints for video reviews
@router.put("/video-reviews/{video_review_id}/status", response_model=VideoReviewResponse)
def update_video_review_status_admin(
    video_review_id: int,
    status_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update video review status (admin only)."""
    # Check if video review exists
    existing_video_review = get_video_review_by_id(db, video_review_id)
    if not existing_video_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video review not found"
        )
    
    # In a real application, you would check if the user has admin privileges
    # For now, we'll allow any authenticated user to update status
    
    new_status = status_update.get("status")
    admin_notes = status_update.get("admin_notes")
    
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    # Validate status
    valid_statuses = ["pending", "approved", "rejected"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    updated_video_review = update_video_review_status(db, video_review_id, new_status, admin_notes)
    if not updated_video_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video review not found"
        )
    
    # Get user info
    user_response = UserResponse(
        id=updated_video_review.user.id,
        email=updated_video_review.user.email,
        username=updated_video_review.user.username,
        full_name=updated_video_review.user.full_name,
        phone=updated_video_review.user.phone,
        address=updated_video_review.user.address,
        is_active=updated_video_review.user.is_active,
        is_verified=updated_video_review.user.is_verified,
        created_at=updated_video_review.user.created_at,
        updated_at=updated_video_review.user.updated_at
    )
    
    return VideoReviewResponse(
        id=updated_video_review.id,
        user_id=updated_video_review.user_id,
        video_url=updated_video_review.video_url,
        description=updated_video_review.description,
        platform=updated_video_review.platform,
        status=updated_video_review.status,
        admin_notes=updated_video_review.admin_notes,
        created_at=updated_video_review.created_at,
        updated_at=updated_video_review.updated_at,
        user=user_response
    )


# Coupon Code endpoints
@router.post("/coupons", response_model=CouponCodeResponse)
def create_coupon_for_user(
    coupon_data: CouponCodeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a coupon code for a user (admin only)."""
    # In a real application, you would check if the user has admin privileges
    # For now, we'll allow any authenticated user to create coupons
    
    # Find user by email
    user = get_user_by_email(db, coupon_data.user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with this email"
        )
    
    # Create coupon code
    db_coupon = create_coupon_code(
        db=db,
        user_id=user.id,
        discount_percentage=coupon_data.discount_percentage,
        max_uses=coupon_data.max_uses,
        expires_at=coupon_data.expires_at,
        created_by_admin=current_user.id
    )
    
    # Create user response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        address=user.address,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
    
    return CouponCodeResponse(
        id=db_coupon.id,
        code=db_coupon.code,
        user_id=db_coupon.user_id,
        discount_percentage=db_coupon.discount_percentage,
        max_uses=db_coupon.max_uses,
        used_count=db_coupon.used_count,
        is_active=db_coupon.is_active,
        expires_at=db_coupon.expires_at,
        created_at=db_coupon.created_at,
        created_by_admin=db_coupon.created_by_admin,
        user=user_response
    )


@router.get("/coupons", response_model=List[CouponCodeResponse])
def get_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get all coupons with optional filtering."""
    coupons = get_all_coupons(db, skip=skip, limit=limit, is_active=is_active)
    
    # Convert to response format
    coupons_response = []
    for coupon in coupons:
        # Get user info for each coupon
        user_response = UserResponse(
            id=coupon.user.id,
            email=coupon.user.email,
            username=coupon.user.username,
            full_name=coupon.user.full_name,
            phone=coupon.user.phone,
            address=coupon.user.address,
            is_active=coupon.user.is_active,
            is_verified=coupon.user.is_verified,
            created_at=coupon.user.created_at,
            updated_at=coupon.user.updated_at
        )
        
        coupon_response = CouponCodeResponse(
            id=coupon.id,
            code=coupon.code,
            user_id=coupon.user_id,
            discount_percentage=coupon.discount_percentage,
            max_uses=coupon.max_uses,
            used_count=coupon.used_count,
            is_active=coupon.is_active,
            expires_at=coupon.expires_at,
            created_at=coupon.created_at,
            created_by_admin=coupon.created_by_admin,
            user=user_response
        )
        coupons_response.append(coupon_response)
    
    return coupons_response


@router.get("/coupons/my", response_model=List[CouponCodeResponse])
def get_my_coupons(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's coupons."""
    coupons = get_user_coupons(db, current_user.id)
    
    # Convert to response format
    coupons_response = []
    for coupon in coupons:
        # Get user info for each coupon
        user_response = UserResponse(
            id=coupon.user.id,
            email=coupon.user.email,
            username=coupon.user.username,
            full_name=coupon.user.full_name,
            phone=coupon.user.phone,
            address=coupon.user.address,
            is_active=coupon.user.is_active,
            is_verified=coupon.user.is_verified,
            created_at=coupon.user.created_at,
            updated_at=coupon.user.updated_at
        )
        
        coupon_response = CouponCodeResponse(
            id=coupon.id,
            code=coupon.code,
            user_id=coupon.user_id,
            discount_percentage=coupon.discount_percentage,
            max_uses=coupon.max_uses,
            used_count=coupon.used_count,
            is_active=coupon.is_active,
            expires_at=coupon.expires_at,
            created_at=coupon.created_at,
            created_by_admin=coupon.created_by_admin,
            user=user_response
        )
        coupons_response.append(coupon_response)
    
    return coupons_response


@router.get("/coupons/validate/{code}")
def validate_my_coupon(
    code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Validate if a coupon code can be used by current user."""
    coupon = validate_coupon(db, code, current_user.id)
    if not coupon:
        return {
            "valid": False,
            "message": "Invalid or expired coupon code"
        }
    
    return {
        "valid": True,
        "coupon": {
            "id": coupon.id,
            "code": coupon.code,
            "discount_percentage": coupon.discount_percentage,
            "max_uses": coupon.max_uses,
            "used_count": coupon.used_count,
            "expires_at": coupon.expires_at
        },
        "message": f"Valid coupon code for {coupon.discount_percentage}% discount"
    }


@router.put("/coupons/{coupon_id}/deactivate")
def deactivate_coupon_admin(
    coupon_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate a coupon (admin only)."""
    # In a real application, you would check if the user has admin privileges
    # For now, we'll allow any authenticated user to deactivate coupons
    
    deactivated_coupon = deactivate_coupon(db, coupon_id)
    if not deactivated_coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    return {"message": "Coupon deactivated successfully"}


@router.get("/platforms")
def get_social_media_platforms():
    """Get available social media platforms for video reviews."""
    return {
        "platforms": [
            {"id": "youtube", "name": "YouTube"},
            {"id": "instagram", "name": "Instagram"},
            {"id": "tiktok", "name": "TikTok"},
            {"id": "facebook", "name": "Facebook"},
            {"id": "twitter", "name": "Twitter"},
            {"id": "other", "name": "Other"}
        ]
    }


@router.get("/video-review-statuses")
def get_video_review_statuses():
    """Get available video review statuses."""
    return {
        "statuses": [
            {"id": "pending", "name": "Pending Review"},
            {"id": "approved", "name": "Approved"},
            {"id": "rejected", "name": "Rejected"}
        ]
    }

