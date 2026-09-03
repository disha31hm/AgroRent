#!/usr/bin/env python3
"""
Reset manu user password to correct value
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, sha256_crypt

def reset_manu_password():
    with app.app_context():
        manu_user = User.query.filter_by(email="manu@gmail.com").first()
        if manu_user:
            # Set correct password without space
            manu_user.password = sha256_crypt.hash("Raju123@")
            db.session.commit()
            print("Reset manu@gmail.com password to: Raju123@")
            
            # Verify
            is_valid = sha256_crypt.verify("Raju123@", manu_user.password)
            print(f"Password verification test: {is_valid}")
        else:
            print("Manu user not found")

if __name__ == "__main__":
    reset_manu_password()