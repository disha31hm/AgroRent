# File: backend/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy to be used by the Flask application
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # used as phone or login id
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Additive fields for profile
    address = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(30), nullable=True)  # e.g., 'English', 'Kannada'
    image_filename = db.Column(db.String(255), nullable=True)  # profile image stored in /uploads

    # Password reset token
    reset_token = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<User {self.full_name or self.username}>"

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    # NEW: store human-readable address + coordinates
    location = db.Column(db.String(255), nullable=True)   # e.g. "Kundapura, Udupi, Karnataka, India"
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<Equipment {self.name}>"

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    payment_method = db.Column(db.String(20), nullable=True)  # 'razorpay', 'pod', 'upi', 'card', etc.
    payment_id = db.Column(db.String(100), nullable=True)  # Payment transaction ID
    status = db.Column(db.String(20), default="confirmed", nullable=False)  # 'confirmed', 'completed', 'cancelled'
    total_amount = db.Column(db.Float, nullable=True)  # Total booking amount
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Booking for User {self.user_id} on Equipment {self.equipment_id}>"

class Operator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    # optional coordinates if you later capture GPS
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    # 'available' or 'unavailable'
    availability = db.Column(db.String(20), default="available", nullable=False)
    # Pricing fields
    price_per_day = db.Column(db.Float, default=800.0, nullable=False)  # ₹ per day
    experience_years = db.Column(db.Integer, default=5, nullable=False)
    specialization = db.Column(db.String(100), default="Tractor Operations", nullable=False)
    description = db.Column(db.String(500), default="Experienced operator", nullable=False)
    # Availability management
    unavailable_until = db.Column(db.DateTime, nullable=True)  # When they become available again
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class OperatorBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    working_days = db.Column(db.Integer, nullable=False)
    work_type = db.Column(db.String(100), nullable=False)
    field_size = db.Column(db.String(50), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'razorpay' or 'pod'
    payment_id = db.Column(db.String(100), nullable=True)  # Payment transaction ID
    status = db.Column(db.String(20), default="confirmed", nullable=False)  # 'confirmed', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<OperatorBooking User {self.user_id} booked Operator {self.operator_id}>"


# ------- CLI Helper: reset or ensure DB -------
if __name__ == "__main__":
    """
    Usage:
      python models.py --reset    -> deletes existing database.db and recreates schema
      python models.py            -> simply ensures tables exist
    """
    import argparse, os
    from flask import Flask

    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate database.db in this folder.")
    args = parser.parse_args()

    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "database.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        if args.reset:
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"Removed existing {db_path}")
            db.create_all()
            print("Recreated database with latest models.")
        else:
            db.create_all()
            print("Ensured database tables exist.")
