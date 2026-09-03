import requests
import time

# Wait a bit for server to be ready
time.sleep(2)

print("🔍 Testing AgroRent Image APIs...")
print("=" * 50)

base_url = "http://127.0.0.1:5000"

# Test 1: Equipment API
print("\n1️⃣ Testing Equipment API (/equipment)")
try:
    response = requests.get(f"{base_url}/equipment", timeout=5)
    if response.status_code == 200:
        equipment_data = response.json()
        print(f"   ✅ Equipment API working! Found {len(equipment_data)} equipment items")
        
        # Check each equipment for image_url
        for i, equipment in enumerate(equipment_data[:3]):  # Check first 3
            print(f"   📦 {equipment['name'][:30]}...")
            print(f"      Image URL: {equipment.get('image_url', 'MISSING!')}")
    else:
        print(f"   ❌ Equipment API error: Status {response.status_code}")
except Exception as e:
    print(f"   ❌ Equipment API error: {e}")

# Test 2: Individual Image URLs
print("\n2️⃣ Testing Individual Image Files")
test_images = [
    "/uploads/homeTractor.jpg",
    "/uploads/homeRotavator.jpg", 
    "/uploads/homeSprayer.jpg",
    "/uploads/homeHarvestor.jpg"
]

for image_url in test_images:
    try:
        response = requests.get(f"{base_url}{image_url}", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ {image_url} - OK (Size: {len(response.content)} bytes)")
        else:
            print(f"   ❌ {image_url} - Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ {image_url} - Error: {e}")

# Test 3: Static images
print("\n3️⃣ Testing Static Images")
static_images = [
    "/images/homelogo2.png",
    "/images/loginimage.png"
]

for image_url in static_images:
    try:
        response = requests.get(f"{base_url}{image_url}", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ {image_url} - OK (Size: {len(response.content)} bytes)")
        else:
            print(f"   ❌ {image_url} - Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ {image_url} - Error: {e}")

# Test 4: Booking History API (if it includes images)
print("\n4️⃣ Testing Booking History API")
try:
    response = requests.get(f"{base_url}/api/bookings?user_id=1", timeout=5)
    if response.status_code == 200:
        bookings_data = response.json()
        print(f"   ✅ Booking History API working! Found {len(bookings_data)} bookings")
        
        for booking in bookings_data[:2]:  # Check first 2
            equipment_image = booking.get('equipment_image_url', 'NOT FOUND')
            print(f"   📋 Booking ID {booking.get('id', 'N/A')}: Equipment image = {equipment_image}")
    else:
        print(f"   ❌ Booking History API error: Status {response.status_code}")
except Exception as e:
    print(f"   ❌ Booking History API error: {e}")

print("\n🎉 Image testing complete!")
print("=" * 50)