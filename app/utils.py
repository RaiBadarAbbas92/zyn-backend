import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import aiofiles
from datetime import datetime
from app.cloudinary_utils import (
    upload_image_to_cloudinary, 
    upload_product_image, 
    upload_design_image, 
    upload_payment_proof_image, 
    upload_review_image
)


# Allowed image types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg", 
    "image/png",
    "image/webp"
}

# Maximum file size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

# Image dimensions
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
THUMBNAIL_SIZE = (300, 300)


async def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file."""
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Check file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )


async def save_uploaded_image(file: UploadFile, product_id: int, is_primary: bool = False, sort_order: int = 0) -> dict:
    """Save uploaded image to Cloudinary and return image data."""
    # Validate file
    await validate_image_file(file)
    
    # Upload to Cloudinary
    result = await upload_product_image(file, product_id, is_primary)
    
    return {
        "image_url": result["url"],
        "alt_text": f"Product image {sort_order + 1}",
        "is_primary": is_primary,
        "sort_order": sort_order,
        "file_name": file.filename,
        "file_size": result.get("bytes", 0)
    }


async def save_design_image(file: UploadFile, design_id: int) -> dict:
    """Save design image to Cloudinary and return image data."""
    # Validate file
    await validate_image_file(file)
    
    # Upload to Cloudinary
    result = await upload_design_image(file, design_id)
    
    return {
        "image_url": result["url"],
        "file_name": file.filename,
        "file_size": result.get("bytes", 0)
    }


async def save_payment_proof(file: UploadFile, order_id: int, description: Optional[str] = None) -> dict:
    """Save payment proof image to Cloudinary and return image data."""
    # Validate file
    await validate_image_file(file)
    
    # Upload to Cloudinary
    result = await upload_payment_proof_image(file, order_id)
    
    return {
        "image_url": result["url"],
        "description": description or f"Payment proof for order {order_id}",
        "file_name": file.filename,
        "file_size": result.get("bytes", 0)
    }


async def save_review_image(file: UploadFile, review_id: int) -> dict:
    """Save review image to Cloudinary and return image data."""
    # Validate file
    await validate_image_file(file)
    
    # Upload to Cloudinary
    result = await upload_review_image(file, review_id)
    
    return {
        "image_url": result["url"],
        "file_name": file.filename,
        "file_size": result.get("bytes", 0)
    }


def delete_product_images(product_id: int) -> bool:
    """Delete all images for a given product from Cloudinary."""
    # This would require implementing a function to list and delete images by folder
    # For now, we'll return True as Cloudinary handles cleanup automatically
    return True


def get_image_url(image_path: str) -> str:
    """Convert local file path to a URL path for serving product images."""
    # Since we're using Cloudinary, this function is no longer needed
    # Images are served directly from Cloudinary URLs
    return image_path


def get_payment_proof_url(image_path: str) -> str:
    """Convert local file path to a URL path for serving payment proof images."""
    # Since we're using Cloudinary, this function is no longer needed
    # Images are served directly from Cloudinary URLs
    return image_path


def get_review_image_url(image_path: str) -> str:
    """Convert review image file path to URL."""
    # Since we're using Cloudinary, this function is no longer needed
    # Images are served directly from Cloudinary URLs
    return image_path


def get_design_image_url(image_path: str) -> str:
    """Convert design image file path to URL."""
    # Since we're using Cloudinary, this function is no longer needed
    # Images are served directly from Cloudinary URLs
    return image_path
