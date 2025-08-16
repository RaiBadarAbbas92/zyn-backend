#!/usr/bin/env python3
"""
Custom setup script for the E-commerce Backend with PostgreSQL and Cloudinary
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with default configuration."""
    env_content = """# Database Configuration
DATABASE_URL=postgresql://neondb_owner:npg_eF53RABZmaJw@ep-noisy-forest-afr0tfd1-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Application Configuration
DEBUG=True
ALLOWED_HOSTS=["*"]
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Created .env file with default configuration")
        print("⚠️  Please update the Cloudinary credentials in .env file")
    else:
        print("✅ .env file already exists")

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    os.system("pip install -r requirements.txt")
    print("✅ Dependencies installed")

def create_database():
    """Create database tables."""
    print("🗄️  Creating database tables...")
    try:
        from app.database import create_db_and_tables
        create_db_and_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        print("Please check your DATABASE_URL in .env file")

def main():
    """Main setup function."""
    print("🚀 Setting up E-commerce Backend with PostgreSQL and Cloudinary")
    print("=" * 60)
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    install_dependencies()
    
    # Create database tables
    create_database()
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Update Cloudinary credentials in .env file")
    print("2. Run the application: python main.py")
    print("3. Access the API documentation at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
