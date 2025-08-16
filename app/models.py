from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    reviews: List["Review"] = Relationship(back_populates="user")
    orders: List["Order"] = Relationship(back_populates="user")
    designs: List["Design"] = Relationship(back_populates="user")
    design_votes: List["DesignVote"] = Relationship(back_populates="user")
    video_reviews: List["VideoReview"] = Relationship(back_populates="user")
    coupon_codes: List["CouponCode"] = Relationship(back_populates="user", sa_relationship_kwargs={"foreign_keys": "CouponCode.user_id"})


class Product(SQLModel, table=True):
    __tablename__ = "products"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    original_price: float
    discount_price: Optional[float] = None
    stock_quantity: int = Field(default=0)
    category: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated tags
    colors: Optional[str] = None  # Comma-separated colors
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    reviews: List["Review"] = Relationship(back_populates="product")
    order_items: List["OrderItem"] = Relationship(back_populates="product")
    images: List["ProductImage"] = Relationship(back_populates="product")


class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    product_id: int = Field(foreign_key="products.id")
    rating: int
    comment: Optional[str] = None
    image_url: Optional[str] = None  # Cloudinary URL
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    user: User = Relationship(back_populates="reviews")
    product: Product = Relationship(back_populates="reviews")


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", nullable=True)
    total_amount: float
    status: str = Field(default="pending")
    shipping_address: str
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    payment_method: str
    special_instructions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order")
    payment_proofs: List["PaymentProof"] = Relationship(back_populates="order")
    coupon_usages: List["CouponUsage"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int
    unit_price: float
    total_price: float
    
    # Relationships
    order: Order = Relationship(back_populates="items")
    product: Product = Relationship(back_populates="order_items")


class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    image_url: str  # Cloudinary URL
    alt_text: Optional[str] = None
    is_primary: bool = Field(default=False)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    product: Product = Relationship(back_populates="images")


class PaymentProof(SQLModel, table=True):
    __tablename__ = "payment_proofs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    image_url: str  # Cloudinary URL
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    order: Order = Relationship(back_populates="payment_proofs")


class Design(SQLModel, table=True):
    __tablename__ = "designs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str
    description: Optional[str] = None
    image_url: str  # Cloudinary URL
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    status: str = Field(default="pending")
    total_votes: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    user: User = Relationship(back_populates="designs")
    votes: List["DesignVote"] = Relationship(back_populates="design")


class DesignVote(SQLModel, table=True):
    __tablename__ = "design_votes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    design_id: int = Field(foreign_key="designs.id")
    user_id: int = Field(foreign_key="users.id")
    vote_type: str  # "upvote", "downvote"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    design: Design = Relationship(back_populates="votes")
    user: User = Relationship(back_populates="design_votes")
    
    # Unique constraint
    class Config:
        table = True
        schema_extra = {
            "table_constraints": [
                "UNIQUE(design_id, user_id)"
            ]
        }


class VideoReview(SQLModel, table=True):
    __tablename__ = "video_reviews"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    video_url: str
    description: Optional[str] = None
    platform: str
    status: str = Field(default="pending")
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    user: User = Relationship(back_populates="video_reviews")


class CouponCode(SQLModel, table=True):
    __tablename__ = "coupon_codes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="users.id")
    discount_percentage: int = Field(default=10)
    max_uses: int = Field(default=10)
    used_count: int = Field(default=0)
    is_active: bool = Field(default=True)
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_admin: Optional[int] = Field(foreign_key="users.id", default=None)
    
    # Relationships
    user: User = Relationship(back_populates="coupon_codes", sa_relationship_kwargs={"foreign_keys": "CouponCode.user_id"})
    admin: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "CouponCode.created_by_admin"})
    usages: List["CouponUsage"] = Relationship(back_populates="coupon")


class CouponUsage(SQLModel, table=True):
    __tablename__ = "coupon_usages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    coupon_id: int = Field(foreign_key="coupon_codes.id")
    order_id: int = Field(foreign_key="orders.id")
    discount_amount: float
    used_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    coupon: CouponCode = Relationship(back_populates="usages")
    order: Order = Relationship(back_populates="coupon_usages")
