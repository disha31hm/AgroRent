from models import db, User, Booking
from app import app

def check_user_and_bookings():
    with app.app_context():
        # Find the guru user
        guru_user = User.query.filter_by(email='guru@gmail.com').first()
        if guru_user:
            print(f"User found: {guru_user.full_name} (ID: {guru_user.id}, Email: {guru_user.email})")
            
            # Check bookings for this user
            bookings = Booking.query.filter_by(user_id=guru_user.id).all()
            print(f"Number of bookings for this user: {len(bookings)}")
            
            for booking in bookings:
                print(f"- Booking ID: {booking.id}, Equipment ID: {booking.equipment_id}, Start: {booking.start_date}")
        else:
            print("Guru user not found")
        
        # Also check all users
        print("\nAll users in database:")
        all_users = User.query.all()
        for user in all_users:
            booking_count = Booking.query.filter_by(user_id=user.id).count()
            print(f"- {user.full_name} (ID: {user.id}, Email: {user.email}) - {booking_count} bookings")

if __name__ == "__main__":
    check_user_and_bookings()