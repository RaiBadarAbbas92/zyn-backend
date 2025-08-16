from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.crud import (
    create_review, update_review, delete_review, get_product_reviews,
    get_user_review_for_product, get_review_by_id
)
from app.schemas import ReviewCreate, ReviewUpdate, ReviewResponse, UserResponse
from app.models import User, Review
from app.utils import save_review_image, get_review_image_url

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse)
def create_product_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a review for a product."""
    try:
        db_review = create_review(db=db, review=review, user_id=current_user.id)
        
        # Create user response for the review
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
        
        return ReviewResponse(
            id=db_review.id,
            user_id=db_review.user_id,
            product_id=db_review.product_id,
            rating=db_review.rating,
            comment=db_review.comment,
            image_url=db_review.image_url,
            file_name=db_review.file_name,
            file_size=db_review.file_size,
            created_at=db_review.created_at,
            updated_at=db_review.updated_at,
            user=user_response
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/upload", response_model=ReviewResponse)
async def create_review_with_image(
    product_id: int = Form(...),
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a review for a product with optional image upload."""
    # Validate rating
    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    # Create review data
    review_data = ReviewCreate(
        product_id=product_id,
        rating=rating,
        comment=comment
    )
    
    try:
        # Create review first to get the ID
        db_review = create_review(db=db, review=review_data, user_id=current_user.id)
        
        # Upload image if provided
        image_data = None
        if image:
            image_data = await save_review_image(file=image, review_id=db_review.id)
            
            # Update review with image data
            db_review.image_url = get_review_image_url(image_data["image_url"])
            db_review.file_name = image_data["file_name"]
            db_review.file_size = image_data["file_size"]
            db.commit()
            db.refresh(db_review)
        
        # Create user response for the review
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
        
        return ReviewResponse(
            id=db_review.id,
            user_id=db_review.user_id,
            product_id=db_review.product_id,
            rating=db_review.rating,
            comment=db_review.comment,
            image_url=db_review.image_url,
            file_name=db_review.file_name,
            file_size=db_review.file_size,
            created_at=db_review.created_at,
            updated_at=db_review.updated_at,
            user=user_response
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/product/{product_id}", response_model=List[ReviewResponse])
def get_reviews_for_product(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all reviews for a specific product."""
    reviews = get_product_reviews(db, product_id, skip=skip, limit=limit)
    
    # Convert to response format
    reviews_response = []
    for review in reviews:
        # Get user info for each review
        user_response = UserResponse(
            id=review.user.id,
            email=review.user.email,
            username=review.user.username,
            full_name=review.user.full_name,
            phone=review.user.phone,
            address=review.user.address,
            is_active=review.user.is_active,
            is_verified=review.user.is_verified,
            created_at=review.user.created_at,
            updated_at=review.user.updated_at
        )
        
        review_response = ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            product_id=review.product_id,
            rating=review.rating,
            comment=review.comment,
            image_url=review.image_url,
            file_name=review.file_name,
            file_size=review.file_size,
            created_at=review.created_at,
            updated_at=review.updated_at,
            user=user_response
        )
        reviews_response.append(review_response)
    
    return reviews_response


@router.get("/my-reviews", response_model=List[ReviewResponse])
def get_my_reviews(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all reviews by the current user."""
    # Get user's reviews
    user_reviews = db.query(Review).filter(Review.user_id == current_user.id).all()
    
    # Convert to response format
    reviews_response = []
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
    
    for review in user_reviews:
        review_response = ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            product_id=review.product_id,
            rating=review.rating,
            comment=review.comment,
            image_url=review.image_url,
            file_name=review.file_name,
            file_size=review.file_size,
            created_at=review.created_at,
            updated_at=review.updated_at,
            user=user_response
        )
        reviews_response.append(review_response)
    
    return reviews_response


@router.put("/{review_id}", response_model=ReviewResponse)
def update_my_review(
    review_id: int,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a review by the current user."""
    # Check if review exists and belongs to current user
    existing_review = get_review_by_id(db, review_id)
    if not existing_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    if existing_review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review"
        )
    
    # Filter out None values
    update_data = {k: v for k, v in review_update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    updated_review = update_review(db, review_id, current_user.id, update_data)
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
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
    
    return ReviewResponse(
        id=updated_review.id,
        user_id=updated_review.user_id,
        product_id=updated_review.product_id,
        rating=updated_review.rating,
        comment=updated_review.comment,
        image_url=updated_review.image_url,
        file_name=updated_review.file_name,
        file_size=updated_review.file_size,
        created_at=updated_review.created_at,
        updated_at=updated_review.updated_at,
        user=user_response
    )


@router.delete("/{review_id}")
def delete_my_review(
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a review by the current user."""
    # Check if review exists and belongs to current user
    existing_review = get_review_by_id(db, review_id)
    if not existing_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    if existing_review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review"
        )
    
    success = delete_review(db, review_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete review"
        )
    
    return {"message": "Review deleted successfully"}
