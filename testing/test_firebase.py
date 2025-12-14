"""
Firestore Test Script - Run on your computer to test Firestore setup
This script simulates what the Pico W will do when syncing data
"""

import json
import requests
from datetime import datetime

def test_firestore_connection():
    """Test Firestore connection and data upload"""
    
    print("=" * 60)
    print("Firestore Air Quality Monitor - Connection Test")
    print("=" * 60)
    
    # Load Firebase configuration
    try:
        with open("firebase_config.json", "r") as f:
            config = json.load(f)
            project_id = config.get("project_id")
            api_key = config.get("api_key")
    except FileNotFoundError:
        print("❌ Error: firebase_config.json not found!")
        print("Please create this file with your Firebase credentials.")
        return False
    except json.JSONDecodeError:
        print("❌ Error: firebase_config.json is not valid JSON!")
        return False
    
    if not project_id or not api_key:
        print("❌ Error: project_id or api_key not found in firebase_config.json")
        return False
    
    print(f"✓ Project ID: {project_id}")
    print(f"✓ API Key: {api_key[:20]}...")
    print()
    
    # Create test data (similar to what Pico W sends)
    test_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "temperature_C": 22.8,
        "humidity_%": 44.6,
        "pressure_hPa": 1012.4,
        "gas_ohms": 11690
    }
    
    print("Test data to upload:")
    print(json.dumps(test_data, indent=2))
    print()
    
    # Convert to Firestore format
    firestore_data = {
        "fields": {
            "timestamp": {"stringValue": test_data["timestamp"]},
            "temperature_C": {"doubleValue": test_data["temperature_C"]},
            "humidity_percent": {"doubleValue": test_data["humidity_%"]},
            "pressure_hPa": {"doubleValue": test_data["pressure_hPa"]},
            "gas_ohms": {"integerValue": str(test_data["gas_ohms"])}
        }
    }
    
    # Construct Firestore URL
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/air_quality_readings?key={api_key}"
    
    print(f"Uploading to Firestore...")
    print()
    
    # Try to upload data
    try:
        response = requests.post(
            url,
            json=firestore_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print("✅ SUCCESS! Data uploaded to Firestore")
            result = response.json()
            doc_id = result.get('name', '').split('/')[-1]
            print(f"Generated Document ID: {doc_id}")
            print()
            print("Your Firestore setup is working correctly! 🎉")
            print()
            print("Next steps:")
            print("1. Upload all files to your Raspberry Pi Pico W")
            print("2. The device will sync data every 60 seconds")
            print("3. View your data at: https://console.firebase.google.com")
            return True
        else:
            print(f"❌ FAILED! HTTP {response.status_code}")
            print(f"Response: {response.text}")
            print()
            print("Common issues:")
            print("- Firestore may not be enabled in Firebase Console")
            print("- Check Firestore security rules")
            print("- Verify API key is correct")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("- Check your internet connection")
        print("- Verify the project ID is correct")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request Timeout!")
        print("- Firestore took too long to respond")
        print("- Check your internet connection")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def read_firestore_data():
    """Read and display existing data from Firestore"""
    
    print("\n" + "=" * 60)
    print("Reading existing data from Firestore...")
    print("=" * 60 + "\n")
    
    try:
        with open("firebase_config.json", "r") as f:
            config = json.load(f)
            project_id = config.get("project_id")
            api_key = config.get("api_key")
    except:
        print("❌ Cannot read firebase_config.json")
        return
    
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/air_quality_readings?key={api_key}&pageSize=5&orderBy=timestamp desc"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get('documents', [])
            
            if not documents:
                print("No data found in Firestore yet.")
                print("Upload some test data first!")
                return
            
            print(f"Last {len(documents)} readings:\n")
            for doc in documents:
                fields = doc.get('fields', {})
                doc_id = doc.get('name', '').split('/')[-1]
                
                print(f"Document ID: {doc_id}")
                print(f"  Timestamp: {fields.get('timestamp', {}).get('stringValue', 'N/A')}")
                print(f"  Temperature: {fields.get('temperature_C', {}).get('doubleValue', 'N/A')} °C")
                print(f"  Humidity: {fields.get('humidity_percent', {}).get('doubleValue', 'N/A')} %")
                print(f"  Pressure: {fields.get('pressure_hPa', {}).get('doubleValue', 'N/A')} hPa")
                print(f"  Gas: {fields.get('gas_ohms', {}).get('integerValue', 'N/A')} Ω")
                print()
        else:
            print(f"❌ Failed to read data: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error reading data: {e}")

if __name__ == "__main__":
    # Test connection and upload
    success = test_firestore_connection()
    
    # If successful, also try reading data
    if success:
        read_firestore_data()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
