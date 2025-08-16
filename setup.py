#!/usr/bin/env python3
"""
Setup script for the E-commerce Backend with PostgreSQL and Cloudinary
"""

from setuptools import setup, find_packages

setup(
    name="back",
    version="0.1.0",
    description="E-commerce Backend with PostgreSQL and Cloudinary",
    packages=find_packages(exclude=["uploads*"]),
    python_requires=">=3.10",
    install_requires=[
        "alembic>=1.16.4",
        "email-validator>=2.2.0",
        "fastapi>=0.116.1",
        "passlib>=1.7.4",
        "pydantic>=2.11.7",
        "pydantic-settings>=2.10.1",
        "python-jose>=3.5.0",
        "python-multipart>=0.0.20",
        "sqlmodel>=0.0.14",
        "uvicorn>=0.35.0",
        "pillow>=10.0.0",
        "aiofiles>=23.0.0",
        "bcrypt>=4.3.0",
        "psycopg2-binary>=2.9.0",
        "cloudinary>=1.33.0",
        "python-dotenv>=1.0.0",
    ],
)

