# Ecommerce Backend API

A complete ecommerce backend built with FastAPI, SQLAlchemy, and SQLite. This API provides endpoints for user management, product management, reviews, and order processing.

## Features

- **User Management**: Register, login, password reset, profile management
- **Product Management**: Create, read, update, delete products
- **Review System**: Users can review products, update and delete their reviews
- **Order Management**: Create orders, view order history, update order status
- **Authentication**: JWT-based authentication with password hashing
- **Database**: SQLite database with SQLAlchemy ORM
- **API Documentation**: Automatic OpenAPI documentation

## Project Structure

```
back/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication utilities
│   ├── crud.py              # CRUD operations
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # Authentication routes
│       ├── users.py         # User management routes
│       ├── products.py      # Product management routes
│       ├── reviews.py       # Review management routes
│       └── orders.py        # Order management routes
├── main.py                  # Application entry point
├── pyproject.toml           # Project dependencies
└── README.md               # This file
```

## Installation

1. **Clone the repository** (if applicable)
2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the API**:
   - API Base URL: `http://localhost:8000`
   - Interactive API Docs: `http://localhost:8000/docs`
   - Alternative API Docs: `http://localhost:8000/redoc`

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new user |
| POST | `/login` | Login user and get access token |
| POST | `/forgot-password` | Request password reset |
| POST | `/reset-password` | Reset password using token |

### Users (`/api/v1/users`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/me` | Get current user info |
| GET | `/me/profile` | Get user profile with order count and reviews |
| PUT | `/me` | Update user profile |
| GET | `/{user_id}` | Get user by ID (public info) |

### Products (`/api/v1/products`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get all products (with filtering and pagination) |
| GET | `/{product_id}` | Get specific product |
| POST | `/` | Create new product with image URLs (requires auth) |
| POST | `/upload` | Create new product with uploaded images (requires auth) |
| PUT | `/{product_id}` | Update product (requires auth) |
| DELETE | `/{product_id}` | Delete product (requires auth) |
| PUT | `/{product_id}/stock` | Update product stock quantity (requires auth) |

### Reviews (`/api/v1/reviews`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create product review (requires auth) |
| GET | `/product/{product_id}` | Get reviews for a product |
| GET | `/my-reviews` | Get current user's reviews |
| PUT | `/{review_id}` | Update user's review |
| DELETE | `/{review_id}` | Delete user's review |

### Orders (`/api/v1/orders`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create new order with contact info and payment method (requires auth) |
| GET | `/all` | Get all orders (admin functionality) |
| GET | `/my-orders` | Get user's orders |
| GET | `/{order_id}` | Get specific order |
| PUT | `/{order_id}/status` | Update order status |
| GET | `/payment-methods` | Get available payment methods |
| GET | `/order-statuses` | Get available order statuses |

## Database Models

### User
- Basic user information (email, username, password)
- Profile information (full name, phone, address)
- Account status and verification
- Password reset functionality

### Product
- Product details (name, description, original price, discount price)
- Inventory management (stock quantity with automatic decrease on orders)
- Category, tags, and colors
- Multiple product images with primary image support
- Active/inactive status

### Review
- User reviews for products
- Rating (1-5 stars) and comments
- One review per user per product

### Order
- Order information (total amount, status, shipping address)
- Payment method
- Order status tracking

### OrderItem
- Individual items in an order
- Quantity, unit price, and total price
- Links to products and orders

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

1. **Register** or **Login** to get an access token
2. Include the token in the Authorization header: `Bearer <token>`
3. Protected endpoints require valid authentication

## Example Usage

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### 3. Create a Product (with authentication)
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Smartphone",
    "description": "Latest smartphone with advanced features",
    "original_price": 999.99,
    "discount_price": 799.99,
    "stock_quantity": 50,
    "category": "Electronics",
    "tags": "smartphone, mobile, premium, 5G",
    "colors": "black, white, blue",
    "images": [
      {
        "image_url": "https://example.com/phone1.jpg",
        "alt_text": "Smartphone front view",
        "is_primary": true,
        "sort_order": 0
      },
      {
        "image_url": "https://example.com/phone2.jpg",
        "alt_text": "Smartphone back view",
        "is_primary": false,
        "sort_order": 1
      }
    ]
  }'
```

### 3.1. Create Product with File Upload
```bash
curl -X POST "http://localhost:8000/api/v1/products/upload" \
  -H "Authorization: Bearer <your_access_token>" \
  -F "name=Premium Smartphone" \
  -F "description=Latest smartphone with advanced features" \
  -F "original_price=999.99" \
  -F "discount_price=799.99" \
  -F "stock_quantity=50" \
  -F "category=Electronics" \
  -F "tags=smartphone, mobile, premium, 5G" \
  -F "colors=black, white, blue" \
  -F "primary_image_index=0" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg"
```

**Note**: 
- Use `multipart/form-data` for file uploads
- `images` can be multiple files (up to 10)
- `primary_image_index` specifies which image (0-based index) should be the primary image
- Supported formats: JPEG, PNG, WebP
- Maximum file size: 5MB per image

### 3.2. Update Product Stock
```bash
curl -X PUT "http://localhost:8000/api/v1/products/1/stock" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_quantity": 75
  }'
```

### 4. Create a Review
```bash
curl -X POST "http://localhost:8000/api/v1/reviews/" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "rating": 5,
    "comment": "Great product!"
  }'
```

### 5. Create an Order
```bash
curl -X POST "http://localhost:8000/api/v1/orders/" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ],
    "shipping_address": "123 Main St, City, Country",
    "contact_name": "John Doe",
    "contact_email": "john@example.com",
    "contact_phone": "+1234567890",
    "payment_method": "credit_card",
    "special_instructions": "Please deliver in the morning"
  }'
```

### 6. Get All Orders (Admin)
```bash
curl -X GET "http://localhost:8000/api/v1/orders/all" \
  -H "Authorization: Bearer <your_access_token>"
```

### 7. Update Order Status
```bash
curl -X PUT "http://localhost:8000/api/v1/orders/1/status" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "confirmed"
  }'
```

### 8. Get Available Payment Methods
```bash
curl -X GET "http://localhost:8000/api/v1/orders/payment-methods"
```

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=sqlite:///./ecommerce.db

# JWT Settings
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email settings (for password reset)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Development

### Running in Development Mode
```bash
python main.py
```

### Running Tests (if implemented)
```bash
pytest
```

### Database Migrations
The application automatically creates tables on startup. For production, consider using Alembic for database migrations.

## Security Considerations

1. **Change the secret key** in production
2. **Use HTTPS** in production
3. **Implement rate limiting** for API endpoints
4. **Add input validation** for all user inputs
5. **Implement proper email service** for password reset
6. **Add admin role management** for product/order management
7. **Implement proper CORS** configuration for your frontend domain

## Production Deployment

1. **Use a production database** (PostgreSQL, MySQL)
2. **Set up proper environment variables**
3. **Use a production ASGI server** (Gunicorn with Uvicorn workers)
4. **Set up reverse proxy** (Nginx)
5. **Implement monitoring and logging**
6. **Set up SSL/TLS certificates**

## License

This project is open source and available under the MIT License.
