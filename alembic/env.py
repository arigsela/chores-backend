from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool, exc
from alembic import context
from dotenv import load_dotenv
import os
import time
from loguru import logger

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Load environment variables
load_dotenv()

# set sqlalchemy.url from environment variables
section = config.config_ini_section
config.set_section_option(section, "DB_USER", os.getenv("DB_USER", ""))
config.set_section_option(section, "DB_PASSWORD", os.getenv("DB_PASSWORD", ""))
config.set_section_option(section, "DB_HOST", os.getenv("DB_HOST", ""))
config.set_section_option(section, "DB_PORT", os.getenv("DB_PORT", ""))
config.set_section_option(section, "DB_NAME", os.getenv("DB_NAME", ""))

print(f"Using database: mysql+pymysql://{os.getenv('DB_USER')}:***@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

# Only add pool_recycle since we're using NullPool
config.set_section_option(section, "sqlalchemy.pool_recycle", "60")

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
from app import models
target_metadata = models.Base.metadata

def connect_with_retries(engine, max_retries=3):
    """Attempt to connect to the database with retries"""
    last_exception = None
    for i in range(max_retries):
        try:
            start_time = time.time()
            connection = engine.connect()
            logger.info(f"Connection established on attempt {i+1} in {time.time() - start_time:.2f} seconds")
            return connection
        except exc.OperationalError as e:
            last_exception = e
            if i == max_retries - 1:
                logger.error(f"Failed to connect after {max_retries} attempts")
                raise
            wait_time = 2 ** i  # Exponential backoff
            logger.warning(f"Connection attempt {i+1} failed, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    raise last_exception

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    total_start_time = time.time()
    
    # Create SQLAlchemy engine
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connect_with_retries(connectable) as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()
            
    logger.info(f"Total migration time: {time.time() - total_start_time:.2f} seconds")

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()