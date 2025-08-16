from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.database import create_db_and_tables
from app.routers import auth, users, products, reviews, orders, designs, loyalty

# Create database tables
create_db_and_tables()

# Create FastAPI app
app = FastAPI(
    title="Ecommerce Backend API",
    description="A complete ecommerce backend with user management, products, reviews, and orders",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving is no longer needed as we're using Cloudinary for image storage

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(designs.router, prefix="/api/v1")
app.include_router(loyalty.router, prefix="/api/v1")


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "Welcome to Ecommerce Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
