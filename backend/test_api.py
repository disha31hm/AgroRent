import requests
import json

def test_booking_api():
    # Test the booking API endpoint
    api_url = "http://127.0.0.1:5000/api/bookings?user_id=4"
    print(f"Testing API: {api_url}")
    
    try:
        response = requests.get(api_url)
        print(f"Status Code: {response.status_code}")
        print(f"Response OK: {response.ok}")
        
        if response.ok:
            data = response.json()
            print(f"Number of bookings: {len(data)}")
            if data:
                print("First booking:")
                print(json.dumps(data[0], indent=2))
            else:
                print("No bookings found for user 4")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_booking_api()