from models import db, Equipment, User
from app import app
import os

def add_sample_equipment():
    with app.app_context():
        # Check if equipment already exists
        existing_equipment = Equipment.query.first()
        if existing_equipment:
            print("Equipment already exists in database:")
            all_equipment = Equipment.query.all()
            for eq in all_equipment:
                print(f"- {eq.name} - ₹{eq.price}/day")
            return
        
        # Create a default system user for the equipment if none exists
        system_user = User.query.filter_by(email='system@AgroRent.com').first()
        if not system_user:
            system_user = User(
                full_name='AgroRent System',
                username='9999999999',
                email='system@AgroRent.com',
                password='$5$rounds=535000$K5z8J9O0n.PQz3iw$eQ2b8YgKwPzE1Zq7X4A9rF2sH3dG5kL6mN0pT8vW1yC',  # dummy hash
                role='admin'
            )
            db.session.add(system_user)
            db.session.commit()
        
        # Sample equipment data using correct column names
        sample_equipment = [
            {
                'name': 'John Deere 5055E Tractor',
                'description': 'Powerful 55 HP tractor suitable for farming operations',
                'price': 2500.0,
                'owner_id': system_user.id,
                'contact_number': '9876543210',
                'location': 'Bangalore, Karnataka',
                'latitude': 12.9716,
                'longitude': 77.5946,
                'image_filename': 'homeTractor.jpg'
            },
            {
                'name': 'Mahindra Rotavator',
                'description': 'Efficient soil preparation equipment for better crop yield',
                'price': 1500.0,
                'owner_id': system_user.id,
                'contact_number': '9876543210',
                'location': 'Bangalore, Karnataka',
                'latitude': 12.9716,
                'longitude': 77.5946,
                'image_filename': 'homeRotavator.jpg'
            },
            {
                'name': 'Power Sprayer Pro',
                'description': 'High-pressure sprayer for pesticide and fertilizer application',
                'price': 800.0,
                'owner_id': system_user.id,
                'contact_number': '9876543210',
                'location': 'Bangalore, Karnataka',
                'latitude': 12.9716,
                'longitude': 77.5946,
                'image_filename': 'homeSprayer.jpg'
            },
            {
                'name': 'Combine Harvester XL',
                'description': 'Advanced harvesting machine for efficient crop collection',
                'price': 5000.0,
                'owner_id': system_user.id,
                'contact_number': '9876543210',
                'location': 'Bangalore, Karnataka',
                'latitude': 12.9716,
                'longitude': 77.5946,
                'image_filename': 'homeHarvestor.jpg'
            },
            {
                'name': 'Compact Tractor 3016',
                'description': 'Compact tractor ideal for small to medium farms',
                'price': 2000.0,
                'owner_id': system_user.id,
                'contact_number': '9876543210',
                'location': 'Jayanagar, Bangalore',
                'latitude': 12.9150,
                'longitude': 77.5800,
                'image_filename': 'homeTractor.jpg'
            },
            {
                'name': 'Multi-Purpose Sprayer',
                'description': 'Versatile sprayer for various agricultural applications',
                'price': 1200.0,
                'owner_id': system_user.id,
                'contact_number': '9876543210',
                'location': 'Whitefield, Bangalore',
                'latitude': 12.9350,
                'longitude': 77.6250,
                'image_filename': 'homeSprayer.jpg'
            }
        ]
        
        print("Adding sample equipment to database...")
        
        for eq_data in sample_equipment:
            equipment = Equipment(**eq_data)
            db.session.add(equipment)
        
        db.session.commit()
        print(f"Successfully added {len(sample_equipment)} equipment items!")
        
        # Verify the data
        all_equipment = Equipment.query.all()
        print(f"\nTotal equipment in database: {len(all_equipment)}")
        for eq in all_equipment:
            print(f"- {eq.name} - ₹{eq.price}/day at {eq.location}")

if __name__ == "__main__":
    add_sample_equipment()