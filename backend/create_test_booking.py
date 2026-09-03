from models import db, Booking, Equipment, User
from app import app
from datetime import datetime

def create_test_booking():
    with app.app_context():
        # Find the guru user
        guru_user = User.query.filter_by(email='guru@gmail.com').first()
        if not guru_user:
            print("Guru user not found!")
            return
            
        # Find an equipment item
        equipment = Equipment.query.first()
        if not equipment:
            print("No equipment found!")
            return
            
        print(f"Creating booking for user: {guru_user.full_name} (ID: {guru_user.id})")
        print(f"Equipment: {equipment.name} (ID: {equipment.id})")
        
        # Create a test booking
        booking = Booking(
            user_id=guru_user.id,
            equipment_id=equipment.id,
            start_date=datetime.now(),
            end_date=datetime.now(),
            payment_method='test',
            payment_id='test_123',
            status='completed',
            total_amount=1500.0
        )
        
        db.session.add(booking)
        db.session.commit()
        
        print(f"Booking created successfully! Booking ID: {booking.id}")
        
        # Verify it was created
        user_bookings = Booking.query.filter_by(user_id=guru_user.id).all()
        print(f"Total bookings for {guru_user.full_name}: {len(user_bookings)}")

if __name__ == "__main__":
    create_test_booking()