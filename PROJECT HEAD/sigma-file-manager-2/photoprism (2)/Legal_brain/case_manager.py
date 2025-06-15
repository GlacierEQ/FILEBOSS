import os
import json
from .config import Config
from .photoprism_client import PhotoPrismClient 

class CaseManager:
    def __init__(self):
        self.photoprism_client = PhotoPrismClient() # Needs PhotoPrism password to be set in env
        self.case_metadata_path = os.path.join(Config.PROCESSED_DATA_PATH, "case_metadata.json")
        self.cases = self._load_case_metadata()

    def _load_case_metadata(self):
        """Loads case metadata from a JSON file."""
        try:
            if os.path.exists(self.case_metadata_path):
                with open(self.case_metadata_path, 'r') as f:
                    data = json.load(f)
                    print(f"Loaded case metadata from {self.case_metadata_path}")
                    return data.get("cases", {}) # Expects a dict of cases: {"case_id": {details}}
            else:
                print(f"Case metadata file not found at {self.case_metadata_path}. Starting fresh.")
                return {}
        except Exception as e:
            print(f"Error loading case metadata: {e}")
            return {}

    def _save_case_metadata(self):
        """Saves the current case metadata to a JSON file."""
        try:
            os.makedirs(Config.PROCESSED_DATA_PATH, exist_ok=True)
            with open(self.case_metadata_path, 'w') as f:
                json.dump({"cases": self.cases}, f, indent=2)
            print(f"Saved case metadata to {self.case_metadata_path}")
        except Exception as e:
            print(f"Error saving case metadata: {e}")

    def get_or_create_case(self, case_name, case_description=""):
        """
        Gets an existing case by name or creates a new one.
        In PhotoPrism, a "case" could correspond to an album.
        Returns the case details (including PhotoPrism album UID if applicable).
        """
        # Check if case (album) already exists by name in our metadata
        for case_id, details in self.cases.items():
            if details.get("name") == case_name:
                print(f"Found existing case: {case_name} (ID: {case_id}, Album UID: {details.get('photoprism_album_uid')})")
                return details

        # If not found, create a new case (and corresponding album in PhotoPrism)
        print(f"Case '{case_name}' not found. Attempting to create new case and PhotoPrism album.")
        if not self.photoprism_client.is_authenticated():
            print("Cannot create case: PhotoPrism client not authenticated.")
            return None
            
        album_info = self.photoprism_client.create_album(title=case_name, description=case_description)
        
        if album_info and album_info.get("UID"):
            new_case_id = album_info["UID"] # Use PhotoPrism Album UID as our case_id for simplicity
            self.cases[new_case_id] = {
                "id": new_case_id,
                "name": case_name,
                "description": case_description,
                "photoprism_album_uid": album_info["UID"],
                "files": [] # List of file UIDs or paths associated with this case
            }
            self._save_case_metadata()
            print(f"Created new case: {case_name} (ID/Album UID: {new_case_id})")
            return self.cases[new_case_id]
        else:
            print(f"Failed to create PhotoPrism album for case '{case_name}'. Case not created.")
            return None

    def link_file_to_case(self, file_photoprism_uid, case_id):
        """
        Links a file (identified by its PhotoPrism UID) to a case.
        This might involve adding the photo to the case's album in PhotoPrism
        and updating our local case metadata.
        """
        if case_id not in self.cases:
            print(f"Error: Case ID {case_id} not found.")
            return False

        # TODO: Implement logic to add photo to album in PhotoPrism if not already done by upload
        # photo_uid = file_photoprism_uid
        # album_uid = self.cases[case_id].get("photoprism_album_uid")
        # if self.photoprism_client.is_authenticated() and photo_uid and album_uid:
        #     # This function needs to be implemented in PhotoPrismClient
        #     # success = self.photoprism_client.add_photo_to_album(photo_uid, album_uid) 
        #     # if not success:
        #     #     print(f"Failed to add photo {photo_uid} to album {album_uid} in PhotoPrism.")
        #     #     return False
        #     print(f"PhotoPrismClient would add photo {photo_uid} to album {album_uid} here.")


        if file_photoprism_uid not in self.cases[case_id].get("files", []):
            self.cases[case_id].setdefault("files", []).append(file_photoprism_uid)
            self._save_case_metadata()
            print(f"Linked file {file_photoprism_uid} to case {self.cases[case_id]['name']} (ID: {case_id}).")
            return True
        else:
            print(f"File {file_photoprism_uid} already linked to case {self.cases[case_id]['name']}.")
            return True # Already linked, so considered success

    def get_case_details(self, case_id):
        return self.cases.get(case_id)

    def list_cases(self):
        return self.cases

# Example Usage
if __name__ == '__main__':
    # Requires PhotoPrism service to be running and accessible, and admin password env var.
    print("Instantiating CaseManager...")
    case_manager = CaseManager()
    
    if case_manager.photoprism_client.is_authenticated():
        print("CaseManager's PhotoPrism client authenticated.")
        
        # Test creating/getting a case
        case_name_1 = "Case Alpha - Litigation"
        print(f"\nGetting or creating case: {case_name_1}")
        case_alpha = case_manager.get_or_create_case(case_name_1, "Documents related to the Alpha Corp litigation.")
        if case_alpha:
            print(f"Details for '{case_name_1}': {case_alpha}")

            # Simulate linking a file (assuming file_uid 'mock_file_123' was uploaded to PhotoPrism)
            mock_file_uid = "mock_file_123"
            print(f"\nLinking file '{mock_file_uid}' to case '{case_alpha['name']}'")
            case_manager.link_file_to_case(mock_file_uid, case_alpha['id'])
            
            print("\nUpdated case details:")
            print(case_manager.get_case_details(case_alpha['id']))

        case_name_2 = "Case Beta - Patent Application"
        print(f"\nGetting or creating case: {case_name_2}")
        case_beta = case_manager.get_or_create_case(case_name_2, "Files for the new patent XYX.")
        if case_beta:
            print(f"Details for '{case_name_2}': {case_beta}")

        print("\nListing all cases:")
        print(json.dumps(case_manager.list_cases(), indent=2))
    else:
        print("CaseManager's PhotoPrism client NOT authenticated. Cannot proceed with tests.")
