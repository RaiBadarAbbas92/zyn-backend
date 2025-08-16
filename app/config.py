from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://neondb_owner:npg_eF53RABZmaJw@ep-noisy-forest-afr0tfd1-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    # JWT Settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Email settings (for password reset)
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Cloudinary Configuration
    cloudinary_cloud_name: str = "dufcjjaav"
    cloudinary_api_key: str = "272941854117965"
    cloudinary_api_secret: str = "Y7QIdlz5fDybIBoT-kEEC_svUrk"
    
    # Application
    debug: bool = True
    allowed_hosts: List[str] = ["*"]
    
    model_config = {"env_file": ".env"}


settings = Settings()
