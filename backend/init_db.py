#!/usr/bin/env python3
"""
Database initialization script to create tables with correct schema
"""

import os
import sys
from app import app, db

def init_database():
    """Initialize database with correct schema"""
    with app.app_context():
        # Drop all existing tables and recreate them
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating new tables with correct schema...")
        db.create_all()
        
        print("Database initialized successfully!")
        print("All tables created with the latest schema.")

if __name__ == "__main__":
    # Remove existing database file if it exists
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    if os.path.exists(db_path):
        print(f"Database file exists: {db_path}")
        try:
            os.remove(db_path)
            print("Removed existing database file")
        except PermissionError:
            print("Could not remove database file - it may be in use")
    else:
        print("No existing database file found")
    
    init_database()