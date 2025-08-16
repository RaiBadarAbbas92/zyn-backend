#!/usr/bin/env python3
"""
Test script to verify that models can be imported and used without errors.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    """Test that all models can be imported without errors."""
    try:
        from app.models import (
            User, Product, Review, Order, OrderItem, 
            ProductImage, PaymentProof, Design, DesignVote, 
            VideoReview, CouponCode, CouponUsage
        )
        print("✅ All models imported successfully!")
        
        # Test creating instances
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        print("✅ User model instance created successfully!")
        
        coupon = CouponCode(
            code="TEST123",
            user_id=1,
            discount_percentage=10
        )
        print("✅ CouponCode model instance created successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False

if __name__ == "__main__":
    print("Testing model imports...")
    success = test_model_imports()
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Tests failed!")
        sys.exit(1)
