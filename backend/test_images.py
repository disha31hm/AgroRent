#!/usr/bin/env python3
"""
Image handling verification script
Checks that all APIs properly return image URLs
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_image_handling():
    """Test that all APIs properly include image URLs"""
    print("🔍 Testing Image Handling Across All APIs...\n")
    
    # Test equipment API
    print("1️⃣ Testing Equipment API (/equipment)")
    try:
        response = requests.get(f"{BASE_URL}/equipment")
        if response.status_code == 200:
            equipment_data = response.json()
            if equipment_data and len(equipment_data) > 0:
                first_item = equipment_data[0]
                if 'image_url' in first_item:
                    print(f"   ✅ Equipment API includes image_url: {first_item['image_url']}")
                else:
                    print("   ❌ Equipment API missing image_url")
            else:
                print("   ⚠️  No equipment data found")
        else:
            print(f"   ❌ Equipment API error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Equipment API error: {e}")
    
    # Test booking history API 
    print("\n2️⃣ Testing Booking History API (/api/bookings)")
    try:
        response = requests.get(f"{BASE_URL}/api/bookings?user_id=1")
        if response.status_code == 200:
            bookings_data = response.json()
            if bookings_data and len(bookings_data) > 0:
                first_booking = bookings_data[0]
                if 'equipment_image_url' in first_booking:
                    print(f"   ✅ Booking History includes equipment_image_url: {first_booking['equipment_image_url']}")
                else:
                    print("   ❌ Booking History missing equipment_image_url")
            else:
                print("   ⚠️  No booking data found")
        else:
            print(f"   ❌ Booking History API error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Booking History API error: {e}")
    
    # Test static image serving
    print("\n3️⃣ Testing Static Image Serving")
    test_images = [
        "/uploads/homeTractor.jpg",
        "/uploads/homeRotavator.jpg", 
        "/uploads/homeSprayer.jpg",
        "/uploads/homeHarvestor.jpg",
        "/images/homelogo2.png",
        "/images/loginimage.png"
    ]
    
    for image_path in test_images:
        try:
            response = requests.get(f"{BASE_URL}{image_path}")
            if response.status_code == 200:
                print(f"   ✅ {image_path} - Available")
            else:
                print(f"   ❌ {image_path} - Error {response.status_code}")
        except Exception as e:
            print(f"   ❌ {image_path} - Error: {e}")
    
    print("\n🎉 Image handling verification complete!")

if __name__ == "__main__":
    test_image_handling()