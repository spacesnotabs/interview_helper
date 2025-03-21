"""
Example script that demonstrates how to use the database package in other applications.
"""
import os
from database import DatabaseConfig, init_db, configure_db, db_session, User

def example_custom_application():
    """Example function showing how to configure and use the database in another application."""
    print("=== Example: Using the database package in another application ===")
    
    # Example 1: Using default configuration
    print("\n1. Using default configuration:")
    init_db()  # This creates tables using default SQLite configuration
    
    # Create a test user
    test_user = User(username="test_user", password="secure_password")
    db_session.add(test_user)
    db_session.commit()
    
    # Query the user
    user = User.query.filter_by(username="test_user").first()
    print(f"User created with default config: {user}")
    
    # Clean up
    db_session.delete(user)
    db_session.commit()
    db_session.remove()
    
    # Example 2: Custom configuration for another application
    print("\n2. Using custom configuration for another application:")
    
    # Create a directory for your new application's database
    new_db_path = os.path.join(os.path.dirname(__file__), 'example_app_data')
    if not os.path.exists(new_db_path):
        os.makedirs(new_db_path)
    
    # Create custom configuration
    custom_config = DatabaseConfig(
        db_name='another_application',
        db_path=new_db_path
        # Can also configure for MySQL/PostgreSQL:
        # db_type='postgresql',
        # db_host='localhost',
        # db_user='postgres',
        # db_password='password',
        # db_port=5432
    )
    
    # Configure database with custom settings
    configure_db(custom_config)
    
    # Initialize the database with new configuration
    init_db()
    
    # Create another test user in the new database
    another_user = User(username="app2_user", password="another_password")
    db_session.add(another_user)
    db_session.commit()
    
    # Query the user
    user = User.query.filter_by(username="app2_user").first()
    print(f"User created with custom config: {user}")
    print(f"Database location: {os.path.join(new_db_path, 'another_application.db')}")
    
    # Clean up
    db_session.delete(user)
    db_session.commit()
    db_session.remove()

if __name__ == "__main__":
    example_custom_application()