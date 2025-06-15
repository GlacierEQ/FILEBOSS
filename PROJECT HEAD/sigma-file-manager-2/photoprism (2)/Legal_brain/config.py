import os

class Config:
    PHOTOPRISM_API_URL = os.getenv('PHOTOPRISM_API_URL', 'http://localhost:2342/api/v1') # Updated for local PhotoPrism
    PHOTOPRISM_ADMIN_USER = os.getenv('PHOTOPRISM_ADMIN_USER', 'admin')
    PHOTOPRISM_ADMIN_PASSWORD = os.getenv('PHOTOPRISM_ADMIN_PASSWORD') # Read from env
    WHISPER_API_URL = os.getenv('WHISPER_API_URL', 'http://localhost:9000/asr') # Assuming local Whisper, adjust if different
    
    # Paths for local Windows environment
    BASE_DATA_PATH = "C:/Users/casey/LegalBrainData" # Base path for data
    ORIGINALS_MOUNT_PATH = os.path.join(BASE_DATA_PATH, "photoprism_originals")
    IMPORT_MOUNT_PATH = os.path.join(BASE_DATA_PATH, "photoprism_import")
    PROCESSED_DATA_PATH = os.path.join(BASE_DATA_PATH, "processed")

    # Add other configurations as needed
    # For example, if using an external AI service API key
    # OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    @staticmethod
    def validate():
        if not Config.PHOTOPRISM_ADMIN_PASSWORD:
            raise ValueError("Missing environment variable: PHOTOPRISM_ADMIN_PASSWORD")
        # Add more critical config validations here

# Initialize config object for easy import elsewhere
# config = Config()
# try:
#     config.validate()
# except ValueError as e:
#     print(f"Configuration error: {e}")
#     # Decide how to handle this - exit, log, etc.
#     # For a service, it might be better to let it try to start and fail verbosely
#     # or rely on orchestration to report unhealthy status.
