import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.config import settings
from fastapi import UploadFile, HTTPException, status
from typing import Optional, Dict, Any
import uuid
from pathlib import Path


# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret
)


async def upload_image_to_cloudinary(
    file: UploadFile,
    folder: str = "ecommerce",
    public_id: Optional[str] = None,
    transformation: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Upload an image to Cloudinary and return the upload result.
    
    Args:
        file: The uploaded file
        folder: Cloudinary folder to store the image
        public_id: Custom public ID for the image
        transformation: Cloudinary transformation options
    
    Returns:
        Dictionary containing upload result with URL and other metadata
    """
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Generate unique public_id if not provided
        if not public_id:
            file_extension = Path(file.filename).suffix if file.filename else '.jpg'
            public_id = f"{folder}/{uuid.uuid4()}{file_extension}"
        
        # Prepare upload options
        upload_options = {
            "folder": folder,
            "public_id": public_id,
            "resource_type": "image",
            "overwrite": True,
        }
        
        # Add transformation if provided
        if transformation:
            upload_options["transformation"] = transformation
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file.file,
            **upload_options
        )
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "bytes": result.get("bytes"),
            "created_at": result.get("created_at")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image to Cloudinary: {str(e)}"
        )


async def delete_image_from_cloudinary(public_id: str) -> bool:
    """
    Delete an image from Cloudinary.
    
    Args:
        public_id: The public ID of the image to delete
    
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        print(f"Failed to delete image from Cloudinary: {str(e)}")
        return False


async def upload_product_image(
    file: UploadFile,
    product_id: int,
    is_primary: bool = False
) -> Dict[str, Any]:
    """
    Upload a product image to Cloudinary.
    
    Args:
        file: The uploaded file
        product_id: ID of the product
        is_primary: Whether this is the primary image
    
    Returns:
        Dictionary containing upload result
    """
    folder = f"ecommerce/products/{product_id}"
    transformation = {
        "width": 800,
        "height": 800,
        "crop": "fill",
        "quality": "auto"
    }
    
    return await upload_image_to_cloudinary(
        file=file,
        folder=folder,
        transformation=transformation
    )


async def upload_design_image(
    file: UploadFile,
    design_id: int
) -> Dict[str, Any]:
    """
    Upload a design image to Cloudinary.
    
    Args:
        file: The uploaded file
        design_id: ID of the design
    
    Returns:
        Dictionary containing upload result
    """
    folder = f"ecommerce/designs/{design_id}"
    transformation = {
        "width": 1200,
        "height": 800,
        "crop": "fill",
        "quality": "auto"
    }
    
    return await upload_image_to_cloudinary(
        file=file,
        folder=folder,
        transformation=transformation
    )


async def upload_payment_proof_image(
    file: UploadFile,
    order_id: int
) -> Dict[str, Any]:
    """
    Upload a payment proof image to Cloudinary.
    
    Args:
        file: The uploaded file
        order_id: ID of the order
    
    Returns:
        Dictionary containing upload result
    """
    folder = f"ecommerce/payment_proofs/{order_id}"
    transformation = {
        "width": 800,
        "height": 600,
        "crop": "fill",
        "quality": "auto"
    }
    
    return await upload_image_to_cloudinary(
        file=file,
        folder=folder,
        transformation=transformation
    )


async def upload_review_image(
    file: UploadFile,
    review_id: int
) -> Dict[str, Any]:
    """
    Upload a review image to Cloudinary.
    
    Args:
        file: The uploaded file
        review_id: ID of the review
    
    Returns:
        Dictionary containing upload result
    """
    folder = f"ecommerce/reviews/{review_id}"
    transformation = {
        "width": 600,
        "height": 600,
        "crop": "fill",
        "quality": "auto"
    }
    
    return await upload_image_to_cloudinary(
        file=file,
        folder=folder,
        transformation=transformation
    )


def get_cloudinary_url(public_id: str, transformation: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a Cloudinary URL for an image.
    
    Args:
        public_id: The public ID of the image
        transformation: Optional transformation parameters
    
    Returns:
        The Cloudinary URL
    """
    if transformation:
        return cloudinary.CloudinaryImage(public_id).build_url(**transformation)
    else:
        return cloudinary.CloudinaryImage(public_id).build_url()

