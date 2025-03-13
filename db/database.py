# DB_management/database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from config import DATABASE_URL

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", DATABASE_URL)

# Create engine with better connection handling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Test connections before using them
    pool_recycle=3600,        # Recycle connections after an hour
    pool_size=5,              # Maintain up to 5 connections
    max_overflow=10           # Allow up to 10 more connections in high demand
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_session():
    """Get a fresh database session"""
    return SessionLocal()

def get_db():
    """Get a fresh database session with validation"""
    session = SessionLocal()
    try:
        # Test the connection
        session.execute("SELECT 1")
        yield session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
