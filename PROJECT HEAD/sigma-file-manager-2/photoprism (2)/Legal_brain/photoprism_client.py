import requests
import json
import os
from .config import Config # Import from our config.py

class PhotoPrismClient:
    def __init__(self):
        self.base_url = Config.PHOTOPRISM_API_URL
        self.username = Config.PHOTOPRISM_ADMIN_USER
        self.password = Config.PHOTOPRISM_ADMIN_PASSWORD
        self.session = requests.Session()
        self.session_id = None
        self._login()

    def _login(self):
        if not self.password:
            # In a real scenario, log this error or handle it more gracefully
            print("Error: PhotoPrism admin password not set in environment variables.")
            # Potentially raise an exception or set a flag to indicate client is not usable
            return False 
            
        login_url = f"{self.base_url}/session"
        payload = {
            "username": self.username,
            "password": self.password
        }
        try:
            response = self.session.post(login_url, json=payload)
            response.raise_for_status()  # Raises an exception for bad status codes
            self.session_id = response.json().get("id")
            print(f"Successfully logged into PhotoPrism. Session ID: {self.session_id}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"PhotoPrism login failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"Response content: {e.response.json()}")
                except json.JSONDecodeError:
                    print(f"Response content: {e.response.text}")
            self.session_id = None
            return False

    def is_authenticated(self):
        return self.session_id is not None

    def upload_file(self, file_path_on_host, album_uid=None, filename_override=None):
        """
        Uploads a file to PhotoPrism.
        file_path_on_host: Absolute path to the file on the legal_brain_service container's filesystem.
        album_uid: Optional UID of the album to add the photo to.
        filename_override: Optional name to use for the file in PhotoPrism.
        Returns a dictionary with status and data (photo object from PhotoPrism if successful, including UID).
        """
        if not self.is_authenticated():
            print("Cannot upload: Not authenticated with PhotoPrism.")
            return {"status": "error", "message": "Not authenticated"}

        upload_url = f"{self.base_url}/photos"  # Standard endpoint for creating photos
        
        file_name_to_send = filename_override or os.path.basename(file_path_on_host)

        try:
            with open(file_path_on_host, 'rb') as f:
                # 'file' is a common key for the file part in multipart/form-data
                files_payload = {'file': (file_name_to_send, f)}
                
                data_payload = {}
                if album_uid:
                    # 'AlbumUID' is typically the field PhotoPrism expects for album association on upload
                    data_payload['AlbumUID'] = album_uid 
                
                # The requests.Session object (self.session) handles cookies, so X-Session-ID header isn't manually needed here after login.
                print(f"Attempting to upload '{file_path_on_host}' as '{file_name_to_send}' to album '{album_uid if album_uid else 'default (no album specified)'}'")
                response = self.session.post(upload_url, files=files_payload, data=data_payload)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
                
                response_json = response.json()
                
                # A successful POST to /photos should return the photo object JSON, including its UID.
                # This might be a single object or a list with one item if treated as an import result.
                if isinstance(response_json, dict) and response_json.get("UID"):
                    print(f"File uploaded successfully. PhotoPrism UID: {response_json.get('UID')}")
                    return {"status": "success", "data": response_json}
                elif isinstance(response_json, list) and len(response_json) > 0 and response_json[0].get("UID"):
                    # Handling cases where the API might return a list of processed items
                    print(f"File uploaded successfully (list response). PhotoPrism UID: {response_json[0].get('UID')}")
                    return {"status": "success", "data": response_json[0]}
                else:
                    # Upload might have been accepted, but UID or expected format is missing.
                    print(f"Upload response received, but UID not found in expected place or format is unexpected: {response_json}")
                    return {"status": "success_no_uid_found", "data": response_json}

        except FileNotFoundError:
            print(f"Error: File not found at {file_path_on_host}")
            return {"status": "error", "message": f"File not found: {file_path_on_host}"}
        except requests.exceptions.HTTPError as http_err:
            error_message = f"PhotoPrism upload HTTP error for {file_path_on_host}: {http_err}"
            if http_err.response is not None:
                try:
                    error_message += f" - Response: {http_err.response.json()}"
                except json.JSONDecodeError:
                    error_message += f" - Response: {http_err.response.text}"
            print(error_message)
            return {"status": "error", "message": str(http_err), "details": error_message}
        except requests.exceptions.RequestException as req_err: # Other request errors (e.g., connection)
            error_message = f"PhotoPrism upload request failed for {file_path_on_host}: {req_err}"
            print(error_message)
            return {"status": "error", "message": str(req_err), "details": error_message}
        except Exception as e:
            # Catch any other unexpected errors during the process
            print(f"An unexpected error occurred during upload of {file_path_on_host}: {e}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

    def create_album(self, title, description=""):
        if not self.is_authenticated():
            print("Cannot create album: Not authenticated with PhotoPrism.")
            return None
        
        albums_url = f"{self.base_url}/albums"
        payload = {
            "Title": title,
            "Description": description
            # Other album properties like Category, Type, etc. can be added
        }
        headers = {'X-Session-ID': self.session_id} if self.session_id else {} # Or other auth method
        
        try:
            response = self.session.post(albums_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"Album '{title}' created successfully: {response.json()}")
            return response.json() # Contains UID, etc.
        except requests.exceptions.RequestException as e:
            print(f"Failed to create album '{title}': {e}")
            return None

    # Add other methods as needed:
    # - add_photo_to_album(photo_uid, album_uid)
    # - set_photo_metadata(photo_uid, title, description, keywords, etc.)
    # - find_photo_by_hash_or_filename(hash_or_filename)
    # - get_albums()

# Example Usage (for testing this module directly, not for Flask app)
if __name__ == '__main__':
    print("Attempting to instantiate PhotoPrismClient...")
    # You'd need to set environment variables for this to work
    # PHOTOPRISM_ADMIN_PASSWORD should be set
    client = PhotoPrismClient()
    if client.is_authenticated():
        print("Client authenticated.")
        # Test creating an album
        # new_album = client.create_album("Test Case Alpha", "Documents for Test Case Alpha")
        # if new_album:
        #     print(f"New album created: {new_album.get('UID')}")
        
        # Test simulated upload
        # upload_result = client.upload_file("/path/to/some/file.pdf", album_uid=new_album.get('UID') if new_album else None)
        # if upload_result:
        #     print(f"Simulated upload result: {upload_result}")
    else:
        print("Client failed to authenticate.")
