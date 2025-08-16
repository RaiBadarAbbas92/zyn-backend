from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserProfile(UserResponse):
    total_orders: int
    reviews: List["ReviewResponse"] = []


# Auth Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# Product Image Schemas
class ProductImageBase(BaseModel):
    image_url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageUpload(BaseModel):
    """Schema for uploaded image data."""
    image_url: str
    thumbnail_url: Optional[str] = None
    alt_text: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None


class ProductImageResponse(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    original_price: float
    discount_price: Optional[float] = None
    stock_quantity: int
    category: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated tags
    colors: Optional[str] = None  # Comma-separated colors


class ProductCreate(ProductBase):
    images: Optional[List[ProductImageCreate]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    original_price: Optional[float] = None
    discount_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    colors: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    average_rating: Optional[float] = None
    total_reviews: int = 0
    images: List[ProductImageResponse] = []
    
    model_config = {"from_attributes": True}


class StockUpdate(BaseModel):
    stock_quantity: int


# Review Schemas
class ReviewBase(BaseModel):
    rating: int
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    product_id: int


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    product_id: int
    image_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserResponse
    
    model_config = {"from_attributes": True}


# Payment Proof Schemas
class PaymentProofBase(BaseModel):
    description: Optional[str] = None


class PaymentProofCreate(PaymentProofBase):
    pass


class PaymentProofResponse(PaymentProofBase):
    id: int
    order_id: int
    image_url: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Order Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    items: List[OrderItemBase]
    shipping_address: str
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    payment_method: str  # "credit_card", "debit_card", "paypal", "cash_on_delivery", "bank_transfer"
    special_instructions: Optional[str] = None


class GuestOrderCreate(BaseModel):
    product_ids: str  # Comma-separated product IDs
    quantities: str   # Comma-separated quantities
    shipping_address: str
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    payment_method: str  # "credit_card", "debit_card", "paypal", "cash_on_delivery", "bank_transfer"
    special_instructions: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    product: ProductResponse
    
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    shipping_address: str
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    payment_method: str
    special_instructions: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    payment_proofs: List[PaymentProofResponse] = []
    
    model_config = {"from_attributes": True}


class GuestOrderResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    shipping_address: str
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    payment_method: str
    special_instructions: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    payment_proofs: List[PaymentProofResponse] = []
    
    model_config = {"from_attributes": True}


# Design Schemas
class DesignBase(BaseModel):
    title: str
    description: Optional[str] = None


class DesignCreate(DesignBase):
    pass


class DesignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # Only for admin updates


class DesignResponse(DesignBase):
    id: int
    user_id: int
    image_url: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    total_votes: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserResponse
    
    model_config = {"from_attributes": True}


# Vote Schemas
class VoteCreate(BaseModel):
    design_id: int
    vote_type: str  # "upvote" or "downvote"


class VoteResponse(BaseModel):
    id: int
    design_id: int
    user_id: int
    vote_type: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Video Review Schemas
class VideoReviewBase(BaseModel):
    video_url: str
    description: Optional[str] = None
    platform: str  # youtube, instagram, tiktok, etc.


class VideoReviewCreate(VideoReviewBase):
    pass


class VideoReviewUpdate(BaseModel):
    video_url: Optional[str] = None
    description: Optional[str] = None
    platform: Optional[str] = None


class VideoReviewResponse(VideoReviewBase):
    id: int
    user_id: int
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserResponse
    
    model_config = {"from_attributes": True}


# Coupon Code Schemas
class CouponCodeBase(BaseModel):
    discount_percentage: int = 10
    max_uses: int = 10
    expires_at: Optional[datetime] = None


class CouponCodeCreate(CouponCodeBase):
    user_email: str  # Email of the user to send coupon to


class CouponCodeResponse(CouponCodeBase):
    id: int
    code: str
    user_id: int
    used_count: int
    is_active: bool
    created_at: datetime
    created_by_admin: Optional[int] = None
    user: UserResponse
    
    model_config = {"from_attributes": True}


class CouponUsageResponse(BaseModel):
    id: int
    coupon_id: int
    order_id: int
    discount_amount: float
    used_at: datetime
    
    model_config = {"from_attributes": True}


# Update forward references
UserProfile.model_rebuild()
ProductImageResponse.model_rebuild()
ProductResponse.model_rebuild()
ReviewResponse.model_rebuild()
PaymentProofResponse.model_rebuild()
OrderItemResponse.model_rebuild()
OrderResponse.model_rebuild()
DesignResponse.model_rebuild()
VoteResponse.model_rebuild()
VideoReviewResponse.model_rebuild()
CouponCodeResponse.model_rebuild()
CouponUsageResponse.model_rebuild()
