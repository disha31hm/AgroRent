#!/usr/bin/env python3
"""
Script to create the user that was being attempted to login
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, sha256_crypt

def create_additional_users():
    with app.app_context():
        # Create the user that was attempted to login
        existing_user = User.query.filter_by(email="manu@gmail.com").first()
        if not existing_user:
            manu_user = User(
                username="manu@gmail.com",
                password=sha256_crypt.hash("Raju123@"),
                role="user",
                full_name="Manu User",
                email="manu@gmail.com",
                address="Karnataka, India",
                language="English"
            )
            db.session.add(manu_user)
            print("Created user: manu@gmail.com / Raju123@")
        else:
            print("User manu@gmail.com already exists")

        # Create a simple admin user too
        existing_admin = User.query.filter_by(username="admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin",
                password=sha256_crypt.hash("admin123"),
                role="admin",
                full_name="Administrator",
                email="admin@AgroRent.com",
                address="AgroRent HQ",
                language="English"
            )
            db.session.add(admin_user)
            print("Created admin user: admin / admin123")
        else:
            print("Admin user already exists")
        
        db.session.commit()
        
        print("\n=== All Available Users ===")
        users = User.query.all()
        for user in users:
            print(f"- Username: {user.username}, Email: {user.email}, Role: {user.role}")

if __name__ == "__main__":
    create_additional_users()