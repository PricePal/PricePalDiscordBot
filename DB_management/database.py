# DB_management/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", DATABASE_URL)

# Create an engine and session factory
engine = create_engine(DATABASE_URL, echo=True)  # echo=True prints SQL debug logs
print("Engine set")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
print("SessionLocal set")
