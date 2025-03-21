"""
Database connection and session management module.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from .config import default_config

# Create database engine
engine = create_engine(default_config.database_uri)

# Create a scoped session
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Base class for all models
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    """Initialize the database."""
    # Import all models here to ensure they are registered properly on the metadata
    from . import models
    Base.metadata.create_all(bind=engine)

def configure_db(config=None):
    """
    Configure the database with custom settings.
    
    Args:
        config: A DatabaseConfig instance
    
    Returns:
        The engine created with the provided configuration
    """
    global engine, db_session
    
    # Create a new engine with the given configuration
    engine = create_engine(config.database_uri)
    
    # Create a new scoped session
    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    
    # Update query property
    Base.query = db_session.query_property()
    
    return engine