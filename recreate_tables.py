#!/usr/bin/env python3
"""
Script to recreate database tables with updated schema for guest orders support.
This will drop and recreate all tables with the new schema.
WARNING: This will delete all existing data!
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.database import engine, create_db_and_tables
from app.models import SQLModel
from sqlmodel import Session

def recreate_tables():
    """Recreate all database tables with the updated schema."""
    print("Recreating database tables for guest orders support...")
    print("WARNING: This will delete all existing data!")
    
    try:
        # Drop all tables
        print("Dropping existing tables...")
        SQLModel.metadata.drop_all(engine)
        
        # Create all tables with new schema
        print("Creating tables with updated schema...")
        create_db_and_tables()
        
        print("Database tables recreated successfully!")
        print("The user_id column in orders table now allows NULL values for guest orders.")
        
    except Exception as e:
        print(f"Error recreating tables: {e}")
        return False
    
    return True

def test_guest_order():
    """Test creating a guest order to verify the schema works."""
    print("\nTesting guest order creation...")
    
    try:
        from app.crud import create_guest_order
        from app.schemas import GuestOrderCreate
        
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
            # This should work without errors
            order = create_guest_order(session, test_order)
            print(f"Guest order created successfully with ID: {order.id}")
            print(f"User ID is: {order.user_id} (should be None)")
            
            # Clean up test order
            session.delete(order)
            session.commit()
            print("Test order cleaned up.")
            
    except Exception as e:
        print(f"Error testing guest order: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Database Recreation Script for Guest Orders")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("This will delete all existing data. Are you sure? (yes/no): ")
    if response.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)
    
    # Recreate tables
    if recreate_tables():
        # Test the new schema
        test_guest_order()
    
    print("\nScript completed!")
