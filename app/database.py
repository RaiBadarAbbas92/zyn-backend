from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

# Create SQLModel engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Set to True to see SQL queries in console
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,    # Recycle connections after 5 minutes
)

# Create all tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Dependency to get database session
def get_db():
    with Session(engine) as session:
        yield session
