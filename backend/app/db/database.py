from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Create engine
sqlite_args = {"check_same_thread": False}
engine = create_engine(
    settings.database_url,
    connect_args=sqlite_args if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database and create tables"""
    # Import all models so Base knows about them
    from app.models.headline import Headline  # noqa: F401
    from app.models.token_usage import TokenUsage  # noqa: F401

    Base.metadata.create_all(bind=engine)
