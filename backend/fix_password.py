#!/usr/bin/env python3
"""
Fix password for the manu user to handle whitespace
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, sha256_crypt

def fix_manu_password():
    with app.app_context():
        # Update the manu user with both password variants
        manu_user = User.query.filter_by(email="manu@gmail.com").first()
        if manu_user:
            # Update with password that has leading space (as being sent)
            manu_user.password = sha256_crypt.hash(" Raju123@")
            db.session.commit()
            print("Updated manu@gmail.com password to handle leading space")
            
            # Test both passwords
            test_passwords = ["Raju123@", " Raju123@"]
            for pwd in test_passwords:
                is_valid = sha256_crypt.verify(pwd, manu_user.password)
                print(f"Password '{pwd}' is valid: {is_valid}")
        else:
            print("Manu user not found")

if __name__ == "__main__":
    fix_manu_password()