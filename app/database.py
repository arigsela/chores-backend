# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
from loguru import logger
from pathlib import Path

load_dotenv()

# Check if we're in test mode
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

if TEST_MODE:
    SQLITE_URL = "sqlite:///./test.db"
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
else:
    MYSQL_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(MYSQL_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()