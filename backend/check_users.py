#!/usr/bin/env python3
"""
Script to check database users and test login
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, sha256_crypt

def check_database():
    with app.app_context():
        print("=== Database User Check ===")
        
        # Get all users
        users = User.query.all()
        print(f"Total users in database: {len(users)}")
        
        for user in users:
            print(f"- ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}")
        
        # Test the testuser specifically
        test_user = User.query.filter_by(username="testuser").first()
        if test_user:
            print(f"\n=== Test User Found ===")
            print(f"Username: {test_user.username}")
            print(f"Email: {test_user.email}")
            print(f"Password Hash: {test_user.password[:50]}...")
            
            # Test password verification
            test_password = "Test123!"
            is_valid = sha256_crypt.verify(test_password, test_user.password)
            print(f"Password '{test_password}' is valid: {is_valid}")
            
        else:
            print("\n❌ Test user not found!")
            
        # Also check by email
        test_user_email = User.query.filter_by(email="test@AgroRent.com").first()
        if test_user_email:
            print(f"\n=== User found by email ===")
            print(f"Username: {test_user_email.username}")
        else:
            print("\n❌ No user found with email test@AgroRent.com")

if __name__ == "__main__":
    check_database()