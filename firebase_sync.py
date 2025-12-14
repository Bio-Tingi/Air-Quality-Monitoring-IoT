# firebase_sync.py
# Helper module for Firestore sync

import urequests
import ujson

class FirebaseSync:
    def __init__(self, project_id, api_key):
        """
        Initialize Firestore sync handler.
        
        Args:
            project_id: Your Firebase project ID (e.g., "climate-app-9baca")
            api_key: Your Firebase API key
        """
        self.project_id = project_id
        self.api_key = api_key
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
    
    def send_data(self, collection, data):
        """
        Send data to Firestore.
        
        Args:
            collection: Collection name (e.g., "air_quality_readings")
            data: Dictionary containing the data to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Construct Firestore URL
            url = f"{self.base_url}/{collection}?key={self.api_key}"
            
            # Convert data to Firestore format
            firestore_data = {
                "fields": {
                    "timestamp": {"stringValue": data.get("timestamp", "")},
                    "temperature_C": {"doubleValue": data.get("temperature_C", 0)},
                    "humidity_percent": {"doubleValue": data.get("humidity_%", 0)},
                    "pressure_hPa": {"doubleValue": data.get("pressure_hPa", 0)},
                    "gas_ohms": {"integerValue": str(data.get("gas_ohms", 0))}
                }
            }
            
            json_data = ujson.dumps(firestore_data)
            
            # Send POST request to Firestore
            response = urequests.post(
                url,
                data=json_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Check if request was successful
            if response.status_code in [200, 201]:
                print(f"Firestore sync successful")
                response.close()
                return True
            else:
                print(f"Firestore sync failed: {response.status_code} - {response.text}")
                response.close()
                return False
                
        except Exception as e:
            print(f"Firestore sync error: {e}")
            return False
    
    def update_data(self, collection, document_id, data):
        """
        Update existing data in Firestore.
        
        Args:
            collection: Collection name
            document_id: Document ID to update
            data: Dictionary containing the data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/{collection}/{document_id}?key={self.api_key}"
            
            # Convert data to Firestore format
            firestore_data = {
                "fields": {
                    "timestamp": {"stringValue": data.get("timestamp", "")},
                    "temperature_C": {"doubleValue": data.get("temperature_C", 0)},
                    "humidity_percent": {"doubleValue": data.get("humidity_%", 0)},
                    "pressure_hPa": {"doubleValue": data.get("pressure_hPa", 0)},
                    "gas_ohms": {"integerValue": str(data.get("gas_ohms", 0))}
                }
            }
            
            json_data = ujson.dumps(firestore_data)
            
            response = urequests.patch(
                url,
                data=json_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"Firestore update successful")
                response.close()
                return True
            else:
                print(f"Firestore update failed: {response.status_code}")
                response.close()
                return False
                
        except Exception as e:
            print(f"Firestore update error: {e}")
            return False


def load_firebase_config():
    """Load Firebase configuration from firebase_config.json"""
    try:
        with open("firebase_config.json", "r") as f:
            config = ujson.load(f)
            return config.get("project_id"), config.get("api_key")
    except Exception as e:
        print(f"Error loading Firebase config: {e}")
        return None, None
