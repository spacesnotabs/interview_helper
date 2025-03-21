"""
Database configuration module.
This module allows for easy configuration of database settings.
"""
import os

class DatabaseConfig:
    """Database configuration class for interview helper application."""
    
    def __init__(self, db_name=None, db_type='sqlite', db_host=None, db_user=None, 
                 db_password=None, db_port=None, db_path=None):
        """
        Initialize database configuration.
        
        Args:
            db_name: Database name
            db_type: Database type (sqlite, mysql, postgresql)
            db_host: Database host
            db_user: Database user
            db_password: Database password
            db_port: Database port
            db_path: Custom path for SQLite database files
        """
        self.db_name = db_name or 'interview_helper'
        self.db_type = db_type
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_port = db_port
        
        print(f"Database type: {self.db_type}")
        print(f"Database name: {self.db_name}")
        print(f"Database host: {self.db_host}")
        print(f"Database user: {self.db_user}")
        print(f"Database port: {self.db_port}")

        # Set default database directory
        if db_path:
            self.db_path = db_path
        else:
            # Default to 'instance' folder in project root
            self.db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                'instance'
            )
            
            # Create the directory if it doesn't exist
            if not os.path.exists(self.db_path):
                os.makedirs(self.db_path)
    
        print(f"Database path: {self.db_path}")
    @property
    def database_uri(self):
        """Get database URI based on configuration."""
        if self.db_type == 'sqlite':
            return f'sqlite:///{os.path.join(self.db_path, f"{self.db_name}.db")}'
        elif self.db_type == 'mysql':
            return f'mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port or 3306}/{self.db_name}'
        elif self.db_type == 'postgresql':
            return f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port or 5432}/{self.db_name}'
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

# Default configuration
default_config = DatabaseConfig()