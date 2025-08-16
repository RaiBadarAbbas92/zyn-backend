from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from app.models import User, Product, Review, Order, OrderItem, ProductImage, PaymentProof, Design, DesignVote, VideoReview, CouponCode, CouponUsage
from app.schemas import UserCreate, ProductCreate, ReviewCreate, OrderCreate, GuestOrderCreate, OrderItemBase
from app.auth import get_password_hash, verify_password


# User CRUD operations
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return db.exec(statement).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    statement = select(User).where(User.username == username)
    return db.exec(statement).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    statement = select(User).where(User.id == user_id)
    return db.exec(statement).first()


def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        address=user.address
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: dict) -> Optional[User]:
    db_user = get_user_by_id(db, user_id)
    if db_user:
        for field, value in user_update.items():
            if value is not None:
                setattr(db_user, field, value)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_profile(db: Session, user_id: int) -> Optional[dict]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    # Get total orders count
    statement = select(Order).where(Order.user_id == user_id)
    total_orders = len(db.exec(statement).all())
    
    # Get user reviews
    statement = select(Review).where(Review.user_id == user_id)
    reviews = db.exec(statement).all()
    
    return {
        "user": user,
        "total_orders": total_orders,
        "reviews": reviews
    }


# Product CRUD operations
def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    statement = select(Product).where(Product.id == product_id)
    return db.exec(statement).first()


def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None
) -> List[Product]:
    statement = select(Product).where(Product.is_active == True)
    
    if category:
        statement = statement.where(Product.category == category)
    
    if search:
        statement = statement.where(Product.name.contains(search))
    
    statement = statement.offset(skip).limit(limit)
    return db.exec(statement).all()


def create_product(db: Session, product: ProductCreate) -> Product:
    # Extract images from product data
    product_data = product.model_dump()
    images_data = product_data.pop('images', None)
    
    # Create product without images first
    db_product = Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Add images if provided
    if images_data:
        for i, image_data in enumerate(images_data):
            db_image = ProductImage(
                product_id=db_product.id,
                **image_data
            )
            db.add(db_image)
        
        db.commit()
        db.refresh(db_product)
    
    return db_product


def update_product(db: Session, product_id: int, product_update: dict) -> Optional[Product]:
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        for field, value in product_update.items():
            if value is not None:
                setattr(db_product, field, value)
        db.commit()
        db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int) -> bool:
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False


def get_product_with_reviews(db: Session, product_id: int) -> Optional[dict]:
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    
    # Get average rating and total reviews
    review_stats = db.query(
        func.avg(Review.rating).label('average_rating'),
        func.count(Review.id).label('total_reviews')
    ).filter(Review.product_id == product_id).first()
    
    # Get all reviews for this product
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    return {
        "product": product,
        "average_rating": float(review_stats.average_rating) if review_stats.average_rating else None,
        "total_reviews": review_stats.total_reviews,
        "reviews": reviews
    }


# Review CRUD operations
def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    return db.query(Review).filter(Review.id == review_id).first()


def get_user_review_for_product(db: Session, user_id: int, product_id: int) -> Optional[Review]:
    return db.query(Review).filter(
        Review.user_id == user_id,
        Review.product_id == product_id
    ).first()


def create_review(db: Session, review: ReviewCreate, user_id: int, image_data: Optional[dict] = None) -> Review:
    # Check if user already reviewed this product
    existing_review = get_user_review_for_product(db, user_id, review.product_id)
    if existing_review:
        raise ValueError("User has already reviewed this product")
    
    db_review = Review(
        user_id=user_id,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment
    )
    
    # Add image data if provided
    if image_data:
        db_review.image_url = image_data.get("image_url")
        db_review.file_name = image_data.get("file_name")
        db_review.file_size = image_data.get("file_size")
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def update_review(db: Session, review_id: int, user_id: int, review_update: dict) -> Optional[Review]:
    db_review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user_id
    ).first()
    
    if db_review:
        for field, value in review_update.items():
            if value is not None:
                setattr(db_review, field, value)
        db.commit()
        db.refresh(db_review)
    return db_review


def delete_review(db: Session, review_id: int, user_id: int) -> bool:
    db_review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == user_id
    ).first()
    
    if db_review:
        db.delete(db_review)
        db.commit()
        return True
    return False


def get_product_reviews(db: Session, product_id: int, skip: int = 0, limit: int = 100) -> List[Review]:
    return db.query(Review).filter(Review.product_id == product_id).offset(skip).limit(limit).all()


# Order CRUD operations
def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()


def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    return db.query(Order).filter(Order.user_id == user_id).offset(skip).limit(limit).all()


def get_all_orders(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Order]:
    """Get all orders with optional filtering by status."""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.offset(skip).limit(limit).all()


def create_order(db: Session, order: OrderCreate, user_id: int) -> Order:
    # Calculate total amount and create order
    total_amount = 0
    order_items = []
    
    for item in order.items:
        product = get_product_by_id(db, item.product_id)
        if not product:
            raise ValueError(f"Product with id {item.product_id} not found")
        
        if product.stock_quantity < item.quantity:
            raise ValueError(f"Insufficient stock for product {product.name}")
        
        # Use discount price if available, otherwise use original price
        unit_price = product.discount_price if product.discount_price else product.original_price
        item_total = unit_price * item.quantity
        total_amount += item_total
        
        order_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "total_price": item_total
        })
    
    # Create order
    db_order = Order(
        user_id=user_id,
        total_amount=total_amount,
        shipping_address=order.shipping_address,
        contact_name=order.contact_name,
        contact_email=order.contact_email,
        contact_phone=order.contact_phone,
        payment_method=order.payment_method,
        special_instructions=order.special_instructions
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create order items and update stock
    for item_data in order_items:
        db_order_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_order_item)
        
        # Update product stock
        product = get_product_by_id(db, item_data["product_id"])
        product.stock_quantity -= item_data["quantity"]
    
    db.commit()
    return db_order


def create_guest_order(db: Session, order: GuestOrderCreate) -> Order:
    """Create a new order for guest users (without authentication)."""
    # Parse product IDs and quantities
    try:
        product_id_list = [int(pid.strip()) for pid in order.product_ids.split(',')]
        quantity_list = [int(qty.strip()) for qty in order.quantities.split(',')]
        
        if len(product_id_list) != len(quantity_list):
            raise ValueError("Number of product IDs must match number of quantities")
        
        order_items = [
            OrderItemBase(product_id=pid, quantity=qty) 
            for pid, qty in zip(product_id_list, quantity_list)
        ]
    except ValueError as e:
        raise ValueError(f"Invalid product IDs or quantities format: {str(e)}")
    
    # Calculate total amount and create order
    total_amount = 0
    order_items_data = []
    
    for item in order_items:
        product = get_product_by_id(db, item.product_id)
        if not product:
            raise ValueError(f"Product with id {item.product_id} not found")
        
        if product.stock_quantity < item.quantity:
            raise ValueError(f"Insufficient stock for product {product.name}")
        
        # Use discount price if available, otherwise use original price
        unit_price = product.discount_price if product.discount_price else product.original_price
        item_total = unit_price * item.quantity
        total_amount += item_total
        
        order_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "total_price": item_total
        })
    
    # Create order (user_id will be None for guest orders)
    db_order = Order(
        user_id=None,  # Guest order has no user
        total_amount=total_amount,
        shipping_address=order.shipping_address,
        contact_name=order.contact_name,
        contact_email=order.contact_email,
        contact_phone=order.contact_phone,
        payment_method=order.payment_method,
        special_instructions=order.special_instructions
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create order items and update stock
    for item_data in order_items_data:
        db_order_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_order_item)
        
        # Update product stock
        product = get_product_by_id(db, item_data["product_id"])
        product.stock_quantity -= item_data["quantity"]
    
    db.commit()
    return db_order


def update_order_status(db: Session, order_id: int, status: str) -> Optional[Order]:
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order:
        db_order.status = status
        db.commit()
        db.refresh(db_order)
    return db_order


def update_product_stock(db: Session, product_id: int, new_quantity: int) -> Optional[Product]:
    """Update product stock quantity."""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        db_product.stock_quantity = new_quantity
        db.commit()
        db.refresh(db_product)
    return db_product


# Payment Proof CRUD operations
def create_payment_proof(db: Session, order_id: int, image_url: str, description: Optional[str] = None, file_name: Optional[str] = None, file_size: Optional[int] = None) -> PaymentProof:
    """Create a payment proof record."""
    db_payment_proof = PaymentProof(
        order_id=order_id,
        image_url=image_url,
        description=description,
        file_name=file_name,
        file_size=file_size
    )
    db.add(db_payment_proof)
    db.commit()
    db.refresh(db_payment_proof)
    return db_payment_proof


def get_order_payment_proofs(db: Session, order_id: int) -> List[PaymentProof]:
    """Get all payment proofs for an order."""
    return db.query(PaymentProof).filter(PaymentProof.order_id == order_id).all()


def delete_payment_proof(db: Session, proof_id: int) -> bool:
    """Delete a payment proof."""
    db_proof = db.query(PaymentProof).filter(PaymentProof.id == proof_id).first()
    if db_proof:
        db.delete(db_proof)
        db.commit()
        return True
    return False


# Design CRUD operations
def create_design(db: Session, design: dict, user_id: int) -> Design:
    """Create a new design."""
    db_design = Design(
        user_id=user_id,
        title=design["title"],
        description=design.get("description"),
        image_url=design["image_url"],
        file_name=design.get("file_name"),
        file_size=design.get("file_size")
    )
    db.add(db_design)
    db.commit()
    db.refresh(db_design)
    return db_design


def get_design_by_id(db: Session, design_id: int) -> Optional[Design]:
    """Get a design by ID."""
    return db.query(Design).filter(Design.id == design_id).first()


def get_all_designs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    user_id: Optional[int] = None
) -> List[Design]:
    """Get all designs with optional filtering."""
    query = db.query(Design)
    
    if status:
        query = query.filter(Design.status == status)
    
    if user_id:
        query = query.filter(Design.user_id == user_id)
    
    return query.order_by(Design.created_at.desc()).offset(skip).limit(limit).all()


def update_design(db: Session, design_id: int, design_update: dict) -> Optional[Design]:
    """Update a design."""
    db_design = db.query(Design).filter(Design.id == design_id).first()
    if db_design:
        for field, value in design_update.items():
            if value is not None:
                setattr(db_design, field, value)
        db.commit()
        db.refresh(db_design)
    return db_design


def delete_design(db: Session, design_id: int, user_id: int) -> bool:
    """Delete a design (only by the owner)."""
    db_design = db.query(Design).filter(
        Design.id == design_id,
        Design.user_id == user_id
    ).first()
    if db_design:
        db.delete(db_design)
        db.commit()
        return True
    return False


def update_design_status(db: Session, design_id: int, status: str) -> Optional[Design]:
    """Update design status (admin only)."""
    db_design = db.query(Design).filter(Design.id == design_id).first()
    if db_design:
        db_design.status = status
        db.commit()
        db.refresh(db_design)
    return db_design


# Vote CRUD operations
def create_vote(db: Session, design_id: int, user_id: int, vote_type: str) -> DesignVote:
    """Create a vote for a design."""
    # Check if user already voted on this design
    existing_vote = db.query(DesignVote).filter(
        DesignVote.design_id == design_id,
        DesignVote.user_id == user_id
    ).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.vote_type = vote_type
        db.commit()
        db.refresh(existing_vote)
        return existing_vote
    
    # Create new vote
    db_vote = DesignVote(
        design_id=design_id,
        user_id=user_id,
        vote_type=vote_type
    )
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)
    
    # Update design vote count
    update_design_vote_count(db, design_id)
    
    return db_vote


def get_user_vote(db: Session, design_id: int, user_id: int) -> Optional[DesignVote]:
    """Get user's vote on a specific design."""
    return db.query(DesignVote).filter(
        DesignVote.design_id == design_id,
        DesignVote.user_id == user_id
    ).first()


def delete_vote(db: Session, design_id: int, user_id: int) -> bool:
    """Delete a user's vote on a design."""
    db_vote = db.query(DesignVote).filter(
        DesignVote.design_id == design_id,
        DesignVote.user_id == user_id
    ).first()
    if db_vote:
        db.delete(db_vote)
        db.commit()
        
        # Update design vote count
        update_design_vote_count(db, design_id)
        return True
    return False


def update_design_vote_count(db: Session, design_id: int) -> None:
    """Update the total vote count for a design."""
    design = db.query(Design).filter(Design.id == design_id).first()
    if design:
        # Count upvotes and downvotes
        upvotes = db.query(DesignVote).filter(
            DesignVote.design_id == design_id,
            DesignVote.vote_type == "upvote"
        ).count()
        
        downvotes = db.query(DesignVote).filter(
            DesignVote.design_id == design_id,
            DesignVote.vote_type == "downvote"
        ).count()
        
        # Calculate total votes (upvotes - downvotes)
        design.total_votes = upvotes - downvotes
        db.commit()


def get_design_votes(db: Session, design_id: int) -> List[DesignVote]:
    """Get all votes for a design."""
    return db.query(DesignVote).filter(DesignVote.design_id == design_id).all()


# Video Review CRUD operations
def create_video_review(db: Session, video_review: dict, user_id: int) -> VideoReview:
    """Create a new video review."""
    db_video_review = VideoReview(
        user_id=user_id,
        video_url=video_review["video_url"],
        description=video_review.get("description"),
        platform=video_review["platform"]
    )
    db.add(db_video_review)
    db.commit()
    db.refresh(db_video_review)
    return db_video_review


def get_video_review_by_id(db: Session, video_review_id: int) -> Optional[VideoReview]:
    """Get a video review by ID."""
    return db.query(VideoReview).filter(VideoReview.id == video_review_id).first()


def get_all_video_reviews(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    user_id: Optional[int] = None
) -> List[VideoReview]:
    """Get all video reviews with optional filtering."""
    query = db.query(VideoReview)
    
    if status:
        query = query.filter(VideoReview.status == status)
    
    if user_id:
        query = query.filter(VideoReview.user_id == user_id)
    
    return query.order_by(VideoReview.created_at.desc()).offset(skip).limit(limit).all()


def update_video_review(db: Session, video_review_id: int, video_review_update: dict) -> Optional[VideoReview]:
    """Update a video review."""
    db_video_review = db.query(VideoReview).filter(VideoReview.id == video_review_id).first()
    if db_video_review:
        for field, value in video_review_update.items():
            if value is not None:
                setattr(db_video_review, field, value)
        db.commit()
        db.refresh(db_video_review)
    return db_video_review


def update_video_review_status(db: Session, video_review_id: int, status: str, admin_notes: Optional[str] = None) -> Optional[VideoReview]:
    """Update video review status (admin only)."""
    db_video_review = db.query(VideoReview).filter(VideoReview.id == video_review_id).first()
    if db_video_review:
        db_video_review.status = status
        if admin_notes:
            db_video_review.admin_notes = admin_notes
        db.commit()
        db.refresh(db_video_review)
    return db_video_review


def delete_video_review(db: Session, video_review_id: int, user_id: int) -> bool:
    """Delete a video review (only by the owner)."""
    db_video_review = db.query(VideoReview).filter(
        VideoReview.id == video_review_id,
        VideoReview.user_id == user_id
    ).first()
    if db_video_review:
        db.delete(db_video_review)
        db.commit()
        return True
    return False


# Coupon Code CRUD operations
def generate_coupon_code() -> str:
    """Generate a unique coupon code."""
    import random
    import string
    
    # Generate a random 8-character code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"LOYALTY{code}"


def create_coupon_code(db: Session, user_id: int, discount_percentage: int = 10, max_uses: int = 10, expires_at: Optional[datetime] = None, created_by_admin: Optional[int] = None) -> CouponCode:
    """Create a new coupon code for a user."""
    # Generate unique coupon code
    code = generate_coupon_code()
    
    # Ensure code is unique
    while db.query(CouponCode).filter(CouponCode.code == code).first():
        code = generate_coupon_code()
    
    db_coupon = CouponCode(
        code=code,
        user_id=user_id,
        discount_percentage=discount_percentage,
        max_uses=max_uses,
        expires_at=expires_at,
        created_by_admin=created_by_admin
    )
    db.add(db_coupon)
    db.commit()
    db.refresh(db_coupon)
    return db_coupon


def get_coupon_by_code(db: Session, code: str) -> Optional[CouponCode]:
    """Get a coupon by its code."""
    return db.query(CouponCode).filter(CouponCode.code == code).first()


def get_user_coupons(db: Session, user_id: int) -> List[CouponCode]:
    """Get all coupons for a user."""
    return db.query(CouponCode).filter(CouponCode.user_id == user_id).all()


def get_all_coupons(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[CouponCode]:
    """Get all coupons with optional filtering."""
    query = db.query(CouponCode)
    
    if is_active is not None:
        query = query.filter(CouponCode.is_active == is_active)
    
    return query.order_by(CouponCode.created_at.desc()).offset(skip).limit(limit).all()


def validate_coupon(db: Session, code: str, user_id: int) -> Optional[CouponCode]:
    """Validate if a coupon can be used by a user."""
    coupon = get_coupon_by_code(db, code)
    if not coupon:
        return None
    
    # Check if coupon belongs to user
    if coupon.user_id != user_id:
        return None
    
    # Check if coupon is active
    if not coupon.is_active:
        return None
    
    # Check if coupon has expired
    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        return None
    
    # Check if coupon has reached max uses
    if coupon.used_count >= coupon.max_uses:
        return None
    
    return coupon


def use_coupon(db: Session, coupon_id: int, order_id: int, discount_amount: float) -> CouponUsage:
    """Use a coupon for an order."""
    # Create usage record
    db_usage = CouponUsage(
        coupon_id=coupon_id,
        order_id=order_id,
        discount_amount=discount_amount
    )
    db.add(db_usage)
    
    # Update coupon usage count
    coupon = db.query(CouponCode).filter(CouponCode.id == coupon_id).first()
    if coupon:
        coupon.used_count += 1
        # Deactivate coupon if max uses reached
        if coupon.used_count >= coupon.max_uses:
            coupon.is_active = False
    
    db.commit()
    db.refresh(db_usage)
    return db_usage


def deactivate_coupon(db: Session, coupon_id: int) -> Optional[CouponCode]:
    """Deactivate a coupon."""
    db_coupon = db.query(CouponCode).filter(CouponCode.id == coupon_id).first()
    if db_coupon:
        db_coupon.is_active = False
        db.commit()
        db.refresh(db_coupon)
    return db_coupon
