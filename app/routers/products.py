from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.crud import (
    get_products, get_product_by_id, create_product, update_product, 
    delete_product, get_product_with_reviews, update_product_stock
)
from app.schemas import ProductCreate, ProductUpdate, ProductResponse, ReviewResponse, StockUpdate, ProductImageResponse, ProductImageUpload
from app.models import User
from app.utils import save_uploaded_image, get_image_url

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[ProductResponse])
def get_all_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering and pagination."""
    products = get_products(db, skip=skip, limit=limit, category=category, search=search)
    
    # Convert to response format with review stats
    products_response = []
    for product in products:
        # Get review stats for this product
        review_stats = get_product_with_reviews(db, product.id)
        
        # Get product images
        images_response = []
        for image in product.images:
            image_response = ProductImageResponse(
                id=image.id,
                product_id=image.product_id,
                image_url=image.image_url,
                alt_text=image.alt_text,
                is_primary=image.is_primary,
                sort_order=image.sort_order,
                created_at=image.created_at
            )
            images_response.append(image_response)
        
        # Sort images by sort_order
        images_response.sort(key=lambda x: x.sort_order)
        
        product_response = ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            original_price=product.original_price,
            discount_price=product.discount_price,
            stock_quantity=product.stock_quantity,
            category=product.category,
            tags=product.tags,
            colors=product.colors,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            average_rating=review_stats["average_rating"] if review_stats else None,
            total_reviews=review_stats["total_reviews"] if review_stats else 0,
            images=images_response
        )
        products_response.append(product_response)
    
    return products_response


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific product by ID."""
    product_data = get_product_with_reviews(db, product_id)
    if not product_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product = product_data["product"]
    
    # Get product images
    images_response = []
    for image in product.images:
        image_response = ProductImageResponse(
            id=image.id,
            product_id=image.product_id,
            image_url=image.image_url,
            alt_text=image.alt_text,
            is_primary=image.is_primary,
            sort_order=image.sort_order,
            created_at=image.created_at
        )
        images_response.append(image_response)
    
    # Sort images by sort_order
    images_response.sort(key=lambda x: x.sort_order)
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        original_price=product.original_price,
        discount_price=product.discount_price,
        stock_quantity=product.stock_quantity,
        category=product.category,
        tags=product.tags,
        colors=product.colors,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        average_rating=product_data["average_rating"],
        total_reviews=product_data["total_reviews"],
        images=images_response
    )


@router.post("/", response_model=ProductResponse)
def create_new_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new product with image URLs."""
    # In a real application, you might want to check if the user has admin privileges
    db_product = create_product(db=db, product=product)
    return db_product


@router.post("/upload", response_model=ProductResponse)
async def create_product_with_upload(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    original_price: float = Form(...),
    discount_price: Optional[float] = Form(None),
    stock_quantity: int = Form(...),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    colors: Optional[str] = Form(None),
    images: List[UploadFile] = File(...),
    primary_image_index: int = Form(0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new product with uploaded images."""
    # Validate number of images
    if len(images) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 images allowed per product"
        )
    
    # Create product data
    product_data = {
        "name": name,
        "description": description,
        "original_price": original_price,
        "discount_price": discount_price,
        "stock_quantity": stock_quantity,
        "category": category,
        "tags": tags,
        "colors": colors
    }
    
    # Create product without images first
    from app.schemas import ProductCreate
    product_create = ProductCreate(**product_data)
    db_product = create_product(db=db, product=product_create)
    
    # Upload and save images
    uploaded_images = []
    for i, image_file in enumerate(images):
        is_primary = (i == primary_image_index)
        image_data = await save_uploaded_image(
            file=image_file,
            product_id=db_product.id,
            is_primary=is_primary,
            sort_order=i
        )
        uploaded_images.append(image_data)
    
    # Create ProductImage records
    from app.models import ProductImage
    for image_data in uploaded_images:
        db_image = ProductImage(
            product_id=db_product.id,
            image_url=get_image_url(image_data["image_url"]),
            alt_text=image_data["alt_text"],
            is_primary=image_data["is_primary"],
            sort_order=image_data["sort_order"]
        )
        db.add(db_image)
    
    db.commit()
    db.refresh(db_product)
    
    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_existing_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing product."""
    # Check if product exists
    existing_product = get_product_by_id(db, product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Filter out None values
    update_data = {k: v for k, v in product_update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    updated_product = update_product(db, product_id, update_data)
    return updated_product


@router.delete("/{product_id}")
def delete_existing_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a product."""
    # Check if product exists
    existing_product = get_product_by_id(db, product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    success = delete_product(db, product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )
    
    return {"message": "Product deleted successfully"}


@router.put("/{product_id}/stock")
def update_product_stock_endpoint(
    product_id: int,
    stock_update: StockUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update product stock quantity."""
    # Check if product exists
    existing_product = get_product_by_id(db, product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Validate stock quantity
    if stock_update.stock_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock quantity cannot be negative"
        )
    
    updated_product = update_product_stock(db, product_id, stock_update.stock_quantity)
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product stock"
        )
    
    return {
        "message": f"Product stock updated successfully",
        "product_id": product_id,
        "new_stock_quantity": stock_update.stock_quantity
    }
