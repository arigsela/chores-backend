# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from loguru import logger
from pathlib import Path


# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Load .env from project root
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
print(f"Looking for .env file at: {env_path}")

load_dotenv(env_path)

load_dotenv()

MYSQL_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
try:
    engine = create_engine(MYSQL_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.error(f"Failed to connect to database: {str(e)}")
    # For development, you could use SQLite as a fallback
    SQLITE_URL = "sqlite:///./test.db"
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()