#!/usr/bin/env python3
"""
Script to test login API directly
"""
import requests
import json

def test_login():
    url = "http://127.0.0.1:5000/login"
    
    # Test data
    test_credentials = [
        {"username": "testuser", "password": "Test123!"},
        {"username": "test@AgroRent.com", "password": "Test123!"},
        {"username": "testuser", "password": "wrongpassword"},
    ]
    
    print("=== Testing Login API ===")
    
    for i, creds in enumerate(test_credentials, 1):
        print(f"\nTest {i}: Username='{creds['username']}', Password='{creds['password']}'")
        
        try:
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(creds),
                timeout=5
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful! Role: {data.get('role')}")
            else:
                print(f"❌ Login failed")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_login()