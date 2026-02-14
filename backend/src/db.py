"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the absolute path to the data directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "leads.db")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# SQLite database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
# connect_args needed only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal class for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session
    Yields a database session and ensures it's closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables
    Creates all tables defined in models
    """
    from src.models import Lead, Import, Export, ExportLead  # Import here to avoid circular imports
    Base.metadata.create_all(bind=engine)
    _ensure_leads_schema_columns()
    print(f"Database initialized at: {DATABASE_PATH}")


def _ensure_leads_schema_columns():
    """
    Lightweight schema guard for existing SQLite DBs.
    Adds columns that may not exist in older local databases.
    """
    with engine.begin() as conn:
        table_info = conn.execute(text("PRAGMA table_info(leads)")).fetchall()
        existing_columns = {row[1] for row in table_info}

        if "icp_score" not in existing_columns:
            conn.execute(text("ALTER TABLE leads ADD COLUMN icp_score FLOAT"))
