#!/usr/bin/env python3
"""
Test script to verify database connection and schema for guest orders.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.database import engine, create_db_and_tables
from app.models import SQLModel, Order
from sqlmodel import Session, select
from app.crud import create_guest_order
from app.schemas import GuestOrderCreate

def test_database_connection():
    """Test database connection and schema."""
    print("Testing database connection and schema...")
    
    try:
        # Test connection
        with Session(engine) as session:
            # Check if orders table exists
            result = session.exec(select(Order).limit(1))
            print("✓ Database connection successful")
            print("✓ Orders table exists")
            
            # Check table schema
            from sqlalchemy import inspect
            inspector = inspect(engine)
            columns = inspector.get_columns('orders')
            
            user_id_column = None
            for col in columns:
                if col['name'] == 'user_id':
                    user_id_column = col
                    break
            
            if user_id_column:
                print(f"✓ user_id column found")
                print(f"  - Nullable: {user_id_column['nullable']}")
                print(f"  - Type: {user_id_column['type']}")
                
                if user_id_column['nullable']:
                    print("✓ user_id column allows NULL values (good for guest orders)")
                else:
                    print("✗ user_id column does NOT allow NULL values (needs migration)")
            else:
                print("✗ user_id column not found")
                
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    return True

def test_guest_order_creation():
    """Test creating a guest order."""
    print("\nTesting guest order creation...")
    
    try:
        # Create a test guest order
        test_order = GuestOrderCreate(
            product_ids="1",
            quantities="1",
            shipping_address="Test Address",
            contact_name="Test User",
            contact_email="test@example.com",
            payment_method="credit_card"
        )
        
        with Session(engine) as session:
            # Try to create the guest order
            order = create_guest_order(session, test_order)
            print(f"✓ Guest order created successfully")
            print(f"  - Order ID: {order.id}")
            print(f"  - User ID: {order.user_id} (should be None)")
            print(f"  - Total Amount: {order.total_amount}")
            
            # Clean up
            session.delete(order)
            session.commit()
            print("✓ Test order cleaned up")
            
    except Exception as e:
        print(f"✗ Guest order creation failed: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("Database Test for Guest Orders")
    print("=" * 40)
    
    # Test database connection and schema
    if not test_database_connection():
        print("\nDatabase connection failed. Please check your configuration.")
        return
    
    # Test guest order creation
    if not test_guest_order_creation():
        print("\nGuest order creation failed. Please run the migration script.")
        return
    
    print("\n✓ All tests passed! Guest orders should work correctly.")

if __name__ == "__main__":
    main()
