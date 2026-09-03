from models import db, Booking, Equipment, User
from app import app

def check_user_bookings():
    with app.app_context():
        # Find guru user
        guru_user = User.query.filter_by(email='guru@gmail.com').first()
        print(f"Guru user: {guru_user.full_name} (ID: {guru_user.id})")
        
        # Get all bookings for this user
        bookings = Booking.query.filter_by(user_id=guru_user.id).all()
        print(f"Total bookings for user: {len(bookings)}")
        
        for booking in bookings:
            equipment = Equipment.query.get(booking.equipment_id)
            print(f"Booking {booking.id}: {equipment.name if equipment else 'Unknown'} - Amount: {booking.total_amount}")
        
        # Test the API call manually
        print("\n--- Testing API response ---")
        from flask import Flask
        import requests
        
        # Make a test API call
        try:
            response = requests.get(f'http://127.0.0.1:5000/api/bookings?user_id={guru_user.id}')
            print(f"API Response Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"API returned {len(data)} bookings")
                for booking in data:
                    print(f"- {booking['equipment_name']}: ${booking['total_cost']}")
            else:
                print(f"API Error: {response.text}")
        except Exception as e:
            print(f"API Call failed: {e}")

if __name__ == "__main__":
    check_user_bookings()