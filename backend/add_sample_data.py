#!/usr/bin/env python3
"""
Script to add sample equipment data to the database
"""

import os
import sys
from app import app, db
from models import User, Equipment

def add_sample_data():
    """Add sample equipment and user data"""
    with app.app_context():
        print("Adding sample data to database...")
        
        # Create a sample owner user if none exists
        owner = User.query.filter_by(role='owner').first()
        if not owner:
            print("Creating sample owner user...")
            owner = User(
                username='owner123',
                password='$5$rounds=80000$WGXfgJqL9JQKC0ld$8qjdvYrN1g8R6EZhKxPHUFTQmCzO.zVf2sXwYgBcNdE3',  # password: Owner123!
                role='owner',
                full_name='Equipment Owner',
                email='owner@example.com',
                address='Karnataka, India',
                language='English'
            )
            db.session.add(owner)
            db.session.commit()
            print(f"Created owner user with ID: {owner.id}")
        
        # Check if equipment already exists
        existing_count = Equipment.query.count()
        if existing_count > 0:
            print(f"Database already has {existing_count} equipment items.")
            print("Clearing existing equipment and re-adding sample data...")
            Equipment.query.delete()
            db.session.commit()
        
        # Sample equipment data
        sample_equipment = [
            {
                'name': 'Tractor - John Deere 5045D',
                'description': 'Powerful 45 HP tractor perfect for farming operations. Includes all attachments.',
                'price': 1500.0,
                'contact_number': '+91 9876543210',
                'location': 'Kundapura, Udupi, Karnataka, India',
                'latitude': 13.6288,
                'longitude': 74.6850,
                'image_filename': 'homeTractor.jpg'
            },
            {
                'name': 'Rotavator - Heavy Duty',
                'description': 'High-quality rotavator for soil preparation. Suitable for all types of soil.',
                'price': 800.0,
                'contact_number': '+91 9876543211',
                'location': 'Udupi, Karnataka, India',
                'latitude': 13.3409,
                'longitude': 74.7421,
                'image_filename': 'homeRotavator.jpg'
            },
            {
                'name': 'Agricultural Sprayer',
                'description': 'Efficient crop sprayer for pesticides and fertilizers. Large tank capacity.',
                'price': 600.0,
                'contact_number': '+91 9876543212',
                'location': 'Mangalore, Karnataka, India',
                'latitude': 12.9141,
                'longitude': 74.8560,
                'image_filename': 'homeSprayer.jpg'
            },
            {
                'name': 'Harvester - Combine',
                'description': 'Modern combine harvester for efficient crop harvesting. Saves time and labor.',
                'price': 2500.0,
                'contact_number': '+91 9876543213',
                'location': 'Shimoga, Karnataka, India',
                'latitude': 13.9299,
                'longitude': 75.5681,
                'image_filename': 'homeHarvestor.jpg'
            },
            {
                'name': 'Mini Tractor',
                'description': 'Compact tractor ideal for small farms and gardens. Easy to operate.',
                'price': 1000.0,
                'contact_number': '+91 9876543214',
                'location': 'Mysore, Karnataka, India',
                'latitude': 12.2958,
                'longitude': 76.6394,
                'image_filename': 'homeTractor.jpg'
            },
            {
                'name': 'Power Tiller',
                'description': 'Versatile power tiller for cultivation, plowing, and other farm operations.',
                'price': 500.0,
                'contact_number': '+91 9876543215',
                'location': 'Hassan, Karnataka, India',
                'latitude': 13.0033,
                'longitude': 76.1004,
                'image_filename': 'homeRotavator.jpg'
            }
        ]
        
        # Add equipment to database
        for equipment_data in sample_equipment:
            equipment = Equipment(
                name=equipment_data['name'],
                description=equipment_data['description'],
                price=equipment_data['price'],
                owner_id=owner.id,
                contact_number=equipment_data['contact_number'],
                location=equipment_data['location'],
                latitude=equipment_data['latitude'],
                longitude=equipment_data['longitude'],
                image_filename=equipment_data['image_filename']
            )
            db.session.add(equipment)
        
        db.session.commit()
        print(f"✅ Successfully added {len(sample_equipment)} equipment items!")
        
        # Verify images exist
        images_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
        print(f"\n📁 Checking images in: {images_dir}")
        for equipment_data in sample_equipment:
            image_path = os.path.join(images_dir, equipment_data['image_filename'])
            if os.path.exists(image_path):
                print(f"✅ {equipment_data['image_filename']} - Found")
            else:
                print(f"❌ {equipment_data['image_filename']} - Not found")
        
        print("\n🎉 Sample data setup complete!")
        print("You can now see equipment on the homepage!")

if __name__ == "__main__":
    add_sample_data()