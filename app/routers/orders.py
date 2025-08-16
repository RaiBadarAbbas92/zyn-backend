from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.crud import create_order, create_guest_order, get_user_orders, get_order_by_id, update_order_status, get_all_orders, create_payment_proof, get_order_payment_proofs, delete_payment_proof
from app.schemas import OrderCreate, OrderResponse, OrderItemResponse, ProductResponse, PaymentProofResponse, OrderItemBase, GuestOrderCreate, GuestOrderResponse
from app.models import User, Order, OrderItem, Product, PaymentProof
from app.utils import save_payment_proof, get_payment_proof_url

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
def create_new_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new order with user contact information and payment method."""
    # Validate payment method
    valid_payment_methods = ["credit_card", "debit_card", "paypal", "cash_on_delivery", "bank_transfer"]
    if order.payment_method not in valid_payment_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment method. Must be one of: {valid_payment_methods}"
        )
    
    try:
        db_order = create_order(db=db, order=order, user_id=current_user.id)
        
        # Convert to response format
        order_items_response = []
        for item in db_order.items:
            # Get product info
            product = db.query(Product).filter(Product.id == item.product_id).first()
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
                average_rating=None,
                total_reviews=0,
                images=[]
            )
            
            order_item_response = OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                product=product_response
            )
            order_items_response.append(order_item_response)
        
        return OrderResponse(
            id=db_order.id,
            user_id=db_order.user_id,
            total_amount=db_order.total_amount,
            status=db_order.status,
            shipping_address=db_order.shipping_address,
            contact_name=db_order.contact_name,
            contact_email=db_order.contact_email,
            contact_phone=db_order.contact_phone,
            payment_method=db_order.payment_method,
            special_instructions=db_order.special_instructions,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
            items=order_items_response,
            payment_proofs=[]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/upload", response_model=OrderResponse)
async def create_order_with_payment_proof(
    product_ids: str = Form(...),  # Comma-separated product IDs
    quantities: str = Form(...),   # Comma-separated quantities
    shipping_address: str = Form(...),
    contact_name: str = Form(...),
    contact_email: str = Form(...),
    contact_phone: Optional[str] = Form(None),
    payment_method: str = Form(...),
    special_instructions: Optional[str] = Form(None),
    payment_proofs: Optional[List[UploadFile]] = File(None),
    proof_descriptions: Optional[str] = Form(None),  # JSON string of descriptions
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new order with optional payment proof uploads."""
    import json
    
    # Validate payment method
    valid_payment_methods = ["credit_card", "debit_card", "paypal", "cash_on_delivery", "bank_transfer"]
    if payment_method not in valid_payment_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment method. Must be one of: {valid_payment_methods}"
        )
    
    # Parse product IDs and quantities
    try:
        product_id_list = [int(pid.strip()) for pid in product_ids.split(',')]
        quantity_list = [int(qty.strip()) for qty in quantities.split(',')]
        
        if len(product_id_list) != len(quantity_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of product IDs must match number of quantities"
            )
        
        order_items = [
            OrderItemBase(product_id=pid, quantity=qty) 
            for pid, qty in zip(product_id_list, quantity_list)
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid product IDs or quantities format: {str(e)}"
        )
    
    # Parse proof descriptions JSON
    proof_descriptions_list = []
    if proof_descriptions:
        try:
            proof_descriptions_list = json.loads(proof_descriptions)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid proof descriptions format"
            )
    
    # Create order data
    order_data = OrderCreate(
        items=order_items,
        shipping_address=shipping_address,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        payment_method=payment_method,
        special_instructions=special_instructions
    )
    
    try:
        # Create the order
        db_order = create_order(db=db, order=order_data, user_id=current_user.id)
        
        # Upload payment proofs if provided
        payment_proofs_response = []
        if payment_proofs:
            for i, proof_file in enumerate(payment_proofs):
                description = proof_descriptions_list[i] if i < len(proof_descriptions_list) else None
                
                # Save the payment proof image
                proof_data = await save_payment_proof(
                    file=proof_file,
                    order_id=db_order.id,
                    description=description
                )
                
                # Create payment proof record
                db_proof = create_payment_proof(
                    db=db,
                    order_id=db_order.id,
                    image_url=get_payment_proof_url(proof_data["image_url"]),
                    description=proof_data["description"],
                    file_name=proof_data["file_name"],
                    file_size=proof_data["file_size"]
                )
                
                payment_proofs_response.append(PaymentProofResponse(
                    id=db_proof.id,
                    order_id=db_proof.order_id,
                    image_url=db_proof.image_url,
                    description=db_proof.description,
                    file_name=db_proof.file_name,
                    file_size=db_proof.file_size,
                    created_at=db_proof.created_at
                ))
        
        # Convert to response format
        order_items_response = []
        for item in db_order.items:
            # Get product info
            product = db.query(Product).filter(Product.id == item.product_id).first()
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
                average_rating=None,
                total_reviews=0,
                images=[]
            )
            
            order_item_response = OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                product=product_response
            )
            order_items_response.append(order_item_response)
        
        return OrderResponse(
            id=db_order.id,
            user_id=db_order.user_id,
            total_amount=db_order.total_amount,
            status=db_order.status,
            shipping_address=db_order.shipping_address,
            contact_name=db_order.contact_name,
            contact_email=db_order.contact_email,
            contact_phone=db_order.contact_phone,
            payment_method=db_order.payment_method,
            special_instructions=db_order.special_instructions,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
            items=order_items_response,
            payment_proofs=payment_proofs_response
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/all", response_model=List[OrderResponse])
def get_all_orders_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by order status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all orders (admin functionality)."""
    # In a real application, you would check if the user has admin privileges
    # For now, we'll allow any authenticated user to view all orders
    
    orders = get_all_orders(db, skip=skip, limit=limit, status=status)
    
    # Convert to response format
    orders_response = []
    for order in orders:
        order_items_response = []
        for item in order.items:
            # Get product info
            product = db.query(Product).filter(Product.id == item.product_id).first()
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
                average_rating=None,
                total_reviews=0,
                images=[]
            )
            
            order_item_response = OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                product=product_response
            )
            order_items_response.append(order_item_response)
        
        # Get payment proofs for this order
        payment_proofs = get_order_payment_proofs(db, order.id)
        payment_proofs_response = [
            PaymentProofResponse(
                id=proof.id,
                order_id=proof.order_id,
                image_url=proof.image_url,
                description=proof.description,
                file_name=proof.file_name,
                file_size=proof.file_size,
                created_at=proof.created_at
            )
            for proof in payment_proofs
        ]
        
        order_response = OrderResponse(
            id=order.id,
            user_id=order.user_id,
            total_amount=order.total_amount,
            status=order.status,
            shipping_address=order.shipping_address,
            contact_name=order.contact_name,
            contact_email=order.contact_email,
            contact_phone=order.contact_phone,
            payment_method=order.payment_method,
            special_instructions=order.special_instructions,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=order_items_response,
            payment_proofs=payment_proofs_response
        )
        orders_response.append(order_response)
    
    return orders_response


@router.get("/my-orders", response_model=List[OrderResponse])
def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all orders by the current user."""
    orders = get_user_orders(db, current_user.id, skip=skip, limit=limit)
    
    # Convert to response format
    orders_response = []
    for order in orders:
        order_items_response = []
        for item in order.items:
            # Get product info
            product = db.query(Product).filter(Product.id == item.product_id).first()
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
                average_rating=None,
                total_reviews=0,
                images=[]
            )
            
            order_item_response = OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                product=product_response
            )
            order_items_response.append(order_item_response)
        
        # Get payment proofs for this order
        payment_proofs = get_order_payment_proofs(db, order.id)
        payment_proofs_response = [
            PaymentProofResponse(
                id=proof.id,
                order_id=proof.order_id,
                image_url=proof.image_url,
                description=proof.description,
                file_name=proof.file_name,
                file_size=proof.file_size,
                created_at=proof.created_at
            )
            for proof in payment_proofs
        ]
        
        order_response = OrderResponse(
            id=order.id,
            user_id=order.user_id,
            total_amount=order.total_amount,
            status=order.status,
            shipping_address=order.shipping_address,
            contact_name=order.contact_name,
            contact_email=order.contact_email,
            contact_phone=order.contact_phone,
            payment_method=order.payment_method,
            special_instructions=order.special_instructions,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=order_items_response,
            payment_proofs=payment_proofs_response
        )
        orders_response.append(order_response)
    
    return orders_response


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific order by ID."""
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if the order belongs to the current user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    # Convert to response format
    order_items_response = []
    for item in order.items:
        # Get product info
        product = db.query(Product).filter(Product.id == item.product_id).first()
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
            average_rating=None,
            total_reviews=0,
            images=[]
        )
        
        order_item_response = OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            product=product_response
        )
        order_items_response.append(order_item_response)
    
    # Get payment proofs
    payment_proofs = get_order_payment_proofs(db, order_id)
    payment_proofs_response = [
        PaymentProofResponse(
            id=proof.id,
            order_id=proof.order_id,
            image_url=proof.image_url,
            description=proof.description,
            file_name=proof.file_name,
            file_size=proof.file_size,
            created_at=proof.created_at
        )
        for proof in payment_proofs
    ]
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status,
        shipping_address=order.shipping_address,
        contact_name=order.contact_name,
        contact_email=order.contact_email,
        contact_phone=order.contact_phone,
        payment_method=order.payment_method,
        special_instructions=order.special_instructions,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=order_items_response,
        payment_proofs=payment_proofs_response
    )


@router.get("/payment-methods")
def get_payment_methods():
    """Get available payment methods."""
    return {
        "payment_methods": [
            {"id": "credit_card", "name": "Credit Card"},
            {"id": "debit_card", "name": "Debit Card"},
            {"id": "paypal", "name": "PayPal"},
            {"id": "cash_on_delivery", "name": "Cash on Delivery"},
            {"id": "bank_transfer", "name": "Bank Transfer"}
        ]
    }


@router.get("/order-statuses")
def get_order_statuses():
    """Get available order statuses."""
    return {
        "order_statuses": [
            {"id": "pending", "name": "Pending"},
            {"id": "confirmed", "name": "Confirmed"},
            {"id": "shipped", "name": "Shipped"},
            {"id": "delivered", "name": "Delivered"},
            {"id": "cancelled", "name": "Cancelled"}
        ]
    }


# Payment Proof Management Endpoints
@router.post("/{order_id}/payment-proofs", response_model=PaymentProofResponse)
async def add_payment_proof(
    order_id: int,
    proof_file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add payment proof to an existing order."""
    # Check if order exists and belongs to user
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add payment proof to this order"
        )
    
    # Save the payment proof image
    proof_data = await save_payment_proof(
        file=proof_file,
        order_id=order_id,
        description=description
    )
    
    # Create payment proof record
    db_proof = create_payment_proof(
        db=db,
        order_id=order_id,
        image_url=get_payment_proof_url(proof_data["image_url"]),
        description=proof_data["description"],
        file_name=proof_data["file_name"],
        file_size=proof_data["file_size"]
    )
    
    return PaymentProofResponse(
        id=db_proof.id,
        order_id=db_proof.order_id,
        image_url=db_proof.image_url,
        description=db_proof.description,
        file_name=db_proof.file_name,
        file_size=db_proof.file_size,
        created_at=db_proof.created_at
    )


@router.get("/{order_id}/payment-proofs", response_model=List[PaymentProofResponse])
def get_order_payment_proofs_endpoint(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all payment proofs for an order."""
    # Check if order exists and belongs to user
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view payment proofs for this order"
        )
    
    payment_proofs = get_order_payment_proofs(db, order_id)
    
    return [
        PaymentProofResponse(
            id=proof.id,
            order_id=proof.order_id,
            image_url=proof.image_url,
            description=proof.description,
            file_name=proof.file_name,
            file_size=proof.file_size,
            created_at=proof.created_at
        )
        for proof in payment_proofs
    ]


@router.delete("/payment-proofs/{proof_id}")
def delete_payment_proof_endpoint(
    proof_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a payment proof."""
    # Get the payment proof
    proof = db.query(PaymentProof).filter(PaymentProof.id == proof_id).first()
    if not proof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment proof not found"
        )
    
    # Check if the order belongs to the user
    order = get_order_by_id(db, proof.order_id)
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this payment proof"
        )
    
    # Delete the payment proof
    success = delete_payment_proof(db, proof_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete payment proof"
        )
    
    return {"message": "Payment proof deleted successfully"}


@router.put("/{order_id}/status")
def update_order_status_endpoint(
    order_id: int,
    status_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update order status (admin functionality)."""
    # Check if order exists
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # In a real application, you would check if the user has admin privileges
    # For now, we'll allow any authenticated user to update status
    
    new_status = status_update.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    # Validate status values
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    updated_order = update_order_status(db, order_id, new_status)
    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )
    
    return {"message": f"Order status updated to {new_status}"}


# Guest Order Endpoints (No Authentication Required)
@router.post("/guest", response_model=GuestOrderResponse)
def create_guest_order_endpoint(
    order: GuestOrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new order for guest users (without authentication)."""
    # Validate payment method
    valid_payment_methods = ["credit_card", "debit_card", "paypal", "cash_on_delivery", "bank_transfer"]
    if order.payment_method not in valid_payment_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment method. Must be one of: {valid_payment_methods}"
        )
    
    try:
        db_order = create_guest_order(db=db, order=order)
        
        # Convert to response format
        order_items_response = []
        for item in db_order.items:
            # Get product info
            product = db.query(Product).filter(Product.id == item.product_id).first()
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
                average_rating=None,
                total_reviews=0,
                images=[]
            )
            
            order_item_response = OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                product=product_response
            )
            order_items_response.append(order_item_response)
        
        return GuestOrderResponse(
            id=db_order.id,
            total_amount=db_order.total_amount,
            status=db_order.status,
            shipping_address=db_order.shipping_address,
            contact_name=db_order.contact_name,
            contact_email=db_order.contact_email,
            contact_phone=db_order.contact_phone,
            payment_method=db_order.payment_method,
            special_instructions=db_order.special_instructions,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
            items=order_items_response,
            payment_proofs=[]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/guest/upload", response_model=GuestOrderResponse)
async def create_guest_order_with_payment_proof(
    product_ids: str = Form(...),  # Comma-separated product IDs
    quantities: str = Form(...),   # Comma-separated quantities
    shipping_address: str = Form(...),
    contact_name: str = Form(...),
    contact_email: str = Form(...),
    contact_phone: Optional[str] = Form(None),
    payment_method: str = Form(...),
    special_instructions: Optional[str] = Form(None),
    payment_proofs: Optional[List[UploadFile]] = File(None),
    proof_descriptions: Optional[str] = Form(None),  # JSON string of descriptions
    db: Session = Depends(get_db)
):
    """Create a new guest order with optional payment proof uploads."""
    import json
    
    # Validate payment method
    valid_payment_methods = ["credit_card", "debit_card", "paypal", "cash_on_delivery", "bank_transfer"]
    if payment_method not in valid_payment_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment method. Must be one of: {valid_payment_methods}"
        )
    
    # Create guest order data
    order_data = GuestOrderCreate(
        product_ids=product_ids,
        quantities=quantities,
        shipping_address=shipping_address,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        payment_method=payment_method,
        special_instructions=special_instructions
    )
    
    # Parse proof descriptions JSON
    proof_descriptions_list = []
    if proof_descriptions:
        try:
            proof_descriptions_list = json.loads(proof_descriptions)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid proof descriptions format"
            )
    
    try:
        # Create the guest order
        db_order = create_guest_order(db=db, order=order_data)
        
        # Upload payment proofs if provided
        payment_proofs_response = []
        if payment_proofs:
            for i, proof_file in enumerate(payment_proofs):
                description = proof_descriptions_list[i] if i < len(proof_descriptions_list) else None
                
                # Save the payment proof image
                proof_data = await save_payment_proof(
                    file=proof_file,
                    order_id=db_order.id,
                    description=description
                )
                
                # Create payment proof record
                db_proof = create_payment_proof(
                    db=db,
                    order_id=db_order.id,
                    image_url=get_payment_proof_url(proof_data["image_url"]),
                    description=proof_data["description"],
                    file_name=proof_data["file_name"],
                    file_size=proof_data["file_size"]
                )
                
                payment_proofs_response.append(PaymentProofResponse(
                    id=db_proof.id,
                    order_id=db_proof.order_id,
                    image_url=db_proof.image_url,
                    description=db_proof.description,
                    file_name=db_proof.file_name,
                    file_size=db_proof.file_size,
                    created_at=db_proof.created_at
                ))
        
        # Convert to response format
        order_items_response = []
        for item in db_order.items:
            # Get product info
            product = db.query(Product).filter(Product.id == item.product_id).first()
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
                average_rating=None,
                total_reviews=0,
                images=[]
            )
            
            order_item_response = OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                product=product_response
            )
            order_items_response.append(order_item_response)
        
        return GuestOrderResponse(
            id=db_order.id,
            total_amount=db_order.total_amount,
            status=db_order.status,
            shipping_address=db_order.shipping_address,
            contact_name=db_order.contact_name,
            contact_email=db_order.contact_email,
            contact_phone=db_order.contact_phone,
            payment_method=db_order.payment_method,
            special_instructions=db_order.special_instructions,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
            items=order_items_response,
            payment_proofs=payment_proofs_response
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/guest/{order_id}", response_model=GuestOrderResponse)
def get_guest_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific guest order by ID (no authentication required)."""
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if this is a guest order (user_id is None)
    if order.user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a guest order"
        )
    
    # Convert to response format
    order_items_response = []
    for item in order.items:
        # Get product info
        product = db.query(Product).filter(Product.id == item.product_id).first()
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
            average_rating=None,
            total_reviews=0,
            images=[]
        )
        
        order_item_response = OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            product=product_response
        )
        order_items_response.append(order_item_response)
    
    # Get payment proofs
    payment_proofs = get_order_payment_proofs(db, order_id)
    payment_proofs_response = [
        PaymentProofResponse(
            id=proof.id,
            order_id=proof.order_id,
            image_url=proof.image_url,
            description=proof.description,
            file_name=proof.file_name,
            file_size=proof.file_size,
            created_at=proof.created_at
        )
        for proof in payment_proofs
    ]
    
    return GuestOrderResponse(
        id=order.id,
        total_amount=order.total_amount,
        status=order.status,
        shipping_address=order.shipping_address,
        contact_name=order.contact_name,
        contact_email=order.contact_email,
        contact_phone=order.contact_phone,
        payment_method=order.payment_method,
        special_instructions=order.special_instructions,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=order_items_response,
        payment_proofs=payment_proofs_response
    )
