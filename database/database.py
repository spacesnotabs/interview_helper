"""
Database connection and session management module.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

Base = declarative_base()
engine = None
db_session = None

def get_db_session():
    """
    Get the current database session.
    
    Returns:
        The current database session
    """
    global db_session
    if db_session is None:
        raise RuntimeError("Database session not initialized. Call init_db_connection first.")
    return db_session

def init_db_connection(config=None):
    """
    Initialize the database connection with the given configuration.
    If no configuration is provided, use the default.
    
    Args:
        config: A DatabaseConfig instance
    
    Returns:
        The engine created with the provided configuration
    """
    global engine, db_session
    
    if config is None:
        from .config import default_config
        config = default_config
    
    try:
        print("Initializing database connection...")
        print(f"Using DB URI: {config.database_uri}")  # Debug info (ensure you don't leak sensitive data in production)

        engine = create_engine(config.database_uri)

        # Test connection explicitly
        connection = engine.connect()
        print("Database connection established successfully.")
        connection.close()

        db_session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )
        Base.query = db_session.query_property()
    except Exception as e:
        print(f"Error initializing the database connection: {e}")
        # Optionally, re-raise or handle the error appropriately.
    
    return engine

def init_db_schema():
    """Initialize the database schema."""
    if engine is None:
        raise RuntimeError("Database connection not initialized. Call init_db_connection first.")

    # Import all models here to ensure they are registered properly on the metadata
    from . import models   # Check if the database is initialized
    Base.metadata.create_all(bind=engine)
