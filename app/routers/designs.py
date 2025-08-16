from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.crud import (
    create_design, get_design_by_id, get_all_designs, update_design, delete_design,
    update_design_status, create_vote, get_user_vote, delete_vote, get_design_votes
)
from app.schemas import DesignCreate, DesignUpdate, DesignResponse, VoteCreate, VoteResponse, UserResponse
from app.models import User, Design, DesignVote
from app.utils import save_design_image, get_design_image_url

router = APIRouter(prefix="/designs", tags=["Design Studio"])


@router.post("/upload", response_model=DesignResponse)
async def upload_design(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    design_image: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a new design."""
    try:
        # Save the design image
        image_data = await save_design_image(
            file=design_image,
            design_id=0  # Will be updated after design creation
        )
        
        # Create design data
        design_data = {
            "title": title,
            "description": description,
            "image_url": get_design_image_url(image_data["image_url"]),
            "file_name": image_data["file_name"],
            "file_size": image_data["file_size"]
        }
        
        # Create the design
        db_design = create_design(db=db, design=design_data, user_id=current_user.id)
        
        # Update the image path with the actual design ID
        db_design.image_url = get_design_image_url(image_data["image_url"].replace("0", str(db_design.id)))
        db.commit()
        db.refresh(db_design)
        
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
        
        return DesignResponse(
            id=db_design.id,
            user_id=db_design.user_id,
            title=db_design.title,
            description=db_design.description,
            image_url=db_design.image_url,
            file_name=db_design.file_name,
            file_size=db_design.file_size,
            status=db_design.status,
            total_votes=db_design.total_votes,
            created_at=db_design.created_at,
            updated_at=db_design.updated_at,
            user=user_response
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload design: {str(e)}"
        )


@router.get("/", response_model=List[DesignResponse])
def get_designs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by design status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """Get all designs with optional filtering."""
    designs = get_all_designs(db, skip=skip, limit=limit, status=status, user_id=user_id)
    
    # Convert to response format
    designs_response = []
    for design in designs:
        # Get user info for each design
        user_response = UserResponse(
            id=design.user.id,
            email=design.user.email,
            username=design.user.username,
            full_name=design.user.full_name,
            phone=design.user.phone,
            address=design.user.address,
            is_active=design.user.is_active,
            is_verified=design.user.is_verified,
            created_at=design.user.created_at,
            updated_at=design.user.updated_at
        )
        
        design_response = DesignResponse(
            id=design.id,
            user_id=design.user_id,
            title=design.title,
            description=design.description,
            image_url=design.image_url,
            file_name=design.file_name,
            file_size=design.file_size,
            status=design.status,
            total_votes=design.total_votes,
            created_at=design.created_at,
            updated_at=design.updated_at,
            user=user_response
        )
        designs_response.append(design_response)
    
    return designs_response


@router.get("/{design_id}", response_model=DesignResponse)
def get_design(
    design_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific design by ID."""
    design = get_design_by_id(db, design_id)
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    # Get user info
    user_response = UserResponse(
        id=design.user.id,
        email=design.user.email,
        username=design.user.username,
        full_name=design.user.full_name,
        phone=design.user.phone,
        address=design.user.address,
        is_active=design.user.is_active,
        is_verified=design.user.is_verified,
        created_at=design.user.created_at,
        updated_at=design.user.updated_at
    )
    
    return DesignResponse(
        id=design.id,
        user_id=design.user_id,
        title=design.title,
        description=design.description,
        image_url=design.image_url,
        file_name=design.file_name,
        file_size=design.file_size,
        status=design.status,
        total_votes=design.total_votes,
        created_at=design.created_at,
        updated_at=design.updated_at,
        user=user_response
    )


@router.put("/{design_id}", response_model=DesignResponse)
def update_my_design(
    design_id: int,
    design_update: DesignUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a design by the owner."""
    # Check if design exists and belongs to current user
    existing_design = get_design_by_id(db, design_id)
    if not existing_design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    if existing_design.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this design"
        )
    
    # Filter out None values and status (only admin can update status)
    update_data = {k: v for k, v in design_update.model_dump().items() if v is not None and k != "status"}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    updated_design = update_design(db, design_id, update_data)
    if not updated_design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
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
    
    return DesignResponse(
        id=updated_design.id,
        user_id=updated_design.user_id,
        title=updated_design.title,
        description=updated_design.description,
        image_url=updated_design.image_url,
        file_name=updated_design.file_name,
        file_size=updated_design.file_size,
        status=updated_design.status,
        total_votes=updated_design.total_votes,
        created_at=updated_design.created_at,
        updated_at=updated_design.updated_at,
        user=user_response
    )


@router.delete("/{design_id}")
def delete_my_design(
    design_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a design by the owner."""
    # Check if design exists and belongs to current user
    existing_design = get_design_by_id(db, design_id)
    if not existing_design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    if existing_design.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this design"
        )
    
    success = delete_design(db, design_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete design"
        )
    
    return {"message": "Design deleted successfully"}


# Voting endpoints
@router.post("/{design_id}/vote", response_model=VoteResponse)
def vote_on_design(
    design_id: int,
    vote: VoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Vote on a design."""
    # Check if design exists
    design = get_design_by_id(db, design_id)
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    # Validate vote type
    if vote.vote_type not in ["upvote", "downvote"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vote type must be 'upvote' or 'downvote'"
        )
    
    # Create or update vote
    db_vote = create_vote(db, design_id, current_user.id, vote.vote_type)
    
    return VoteResponse(
        id=db_vote.id,
        design_id=db_vote.design_id,
        user_id=db_vote.user_id,
        vote_type=db_vote.vote_type,
        created_at=db_vote.created_at
    )


@router.get("/{design_id}/my-vote")
def get_my_vote(
    design_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's vote on a design."""
    # Check if design exists
    design = get_design_by_id(db, design_id)
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    vote = get_user_vote(db, design_id, current_user.id)
    if not vote:
        return {"vote_type": None}
    
    return {"vote_type": vote.vote_type}


@router.delete("/{design_id}/vote")
def remove_my_vote(
    design_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove current user's vote on a design."""
    # Check if design exists
    design = get_design_by_id(db, design_id)
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    success = delete_vote(db, design_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vote found to remove"
        )
    
    return {"message": "Vote removed successfully"}


@router.get("/{design_id}/votes")
def get_design_vote_details(
    design_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed vote information for a design."""
    # Check if design exists
    design = get_design_by_id(db, design_id)
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    votes = get_design_votes(db, design_id)
    
    # Count vote types
    upvotes = sum(1 for vote in votes if vote.vote_type == "upvote")
    downvotes = sum(1 for vote in votes if vote.vote_type == "downvote")
    
    return {
        "design_id": design_id,
        "total_votes": design.total_votes,
        "upvotes": upvotes,
        "downvotes": downvotes,
        "total_voters": len(votes)
    }


# Admin endpoints
@router.put("/{design_id}/status", response_model=DesignResponse)
def update_design_status_admin(
    design_id: int,
    status_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update design status (admin only)."""
    # Check if design exists
    existing_design = get_design_by_id(db, design_id)
    if not existing_design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    # In a real application, you would check if the user has admin privileges
    # For now, we'll allow any authenticated user to update status
    
    new_status = status_update.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    # Validate status
    valid_statuses = ["pending", "approved", "rejected", "featured"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    updated_design = update_design_status(db, design_id, new_status)
    if not updated_design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    # Get user info
    user_response = UserResponse(
        id=updated_design.user.id,
        email=updated_design.user.email,
        username=updated_design.user.username,
        full_name=updated_design.user.full_name,
        phone=updated_design.user.phone,
        address=updated_design.user.address,
        is_active=updated_design.user.is_active,
        is_verified=updated_design.user.is_verified,
        created_at=updated_design.user.created_at,
        updated_at=updated_design.user.updated_at
    )
    
    return DesignResponse(
        id=updated_design.id,
        user_id=updated_design.user_id,
        title=updated_design.title,
        description=updated_design.description,
        image_url=updated_design.image_url,
        file_name=updated_design.file_name,
        file_size=updated_design.file_size,
        status=updated_design.status,
        total_votes=updated_design.total_votes,
        created_at=updated_design.created_at,
        updated_at=updated_design.updated_at,
        user=user_response
    )


@router.get("/statuses")
def get_design_statuses():
    """Get available design statuses."""
    return {
        "statuses": [
            {"id": "pending", "name": "Pending Review"},
            {"id": "approved", "name": "Approved"},
            {"id": "rejected", "name": "Rejected"},
            {"id": "featured", "name": "Featured"}
        ]
    }

