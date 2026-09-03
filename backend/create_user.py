#!/usr/bin/env python3
"""
Script to create a test user for login
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, sha256_crypt

def create_test_user():
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(username="testuser").first()
        if existing_user:
            print("Test user already exists!")
            print("Credentials: username=testuser, password=Test123!")
            return

        # Create test user
        test_user = User(
            username="testuser",
            password=sha256_crypt.hash("Test123!"),
            role="user",
            full_name="Test User",
            email="test@AgroRent.com",
            address="Test Address, Karnataka",
            language="English"
        )
        
        db.session.add(test_user)
        db.session.commit()
        
        print("Test user created successfully!")
        print("Credentials:")
        print("  Username: testuser")
        print("  Password: Test123!")
        print("  Email: test@AgroRent.com")

if __name__ == "__main__":
    create_test_user()