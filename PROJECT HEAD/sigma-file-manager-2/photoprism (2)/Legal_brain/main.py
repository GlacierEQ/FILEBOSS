from flask import Flask, request, jsonify
import os
import mimetypes # For guessing file type by extension as a fallback

# Import our modules
from .config import Config
from .document_processor import DocumentProcessor
from .audio_processor import AudioProcessor
from .case_manager import CaseManager
from .photoprism_client import PhotoPrismClient

app = Flask(__name__)
# app.config.from_object(Config) # If we were using Flask config directly

# Initialize processors and clients
# These are created once when the Flask app starts.
try:
    document_processor = DocumentProcessor()
    audio_processor = AudioProcessor()
    # PhotoPrismClient might require password, which comes from Config
    # CaseManager also instantiates a PhotoPrismClient
    photoprism_client = PhotoPrismClient() 
    case_manager = CaseManager() # Relies on PhotoPrismClient being configurable
except Exception as e:
    # Log this critical error. If these fail, the app is likely non-functional.
    app.logger.error(f"CRITICAL: Failed to initialize processors or clients: {e}", exc_info=True)
    # Depending on Flask setup, app.logger might not be fully configured here.
    # Consider raising the exception to stop app startup if these are fatal.
    print(f"CRITICAL: Failed to initialize processors or clients: {e}")
    # Fallback instances that might indicate an error state or allow partial operation
    # document_processor = None 
    # audio_processor = None
    # photoprism_client = None
    # case_manager = None


SUPPORTED_AUDIO_MIMES = [
    'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/ogg', 'audio/mp4', 'audio/aac', 'audio/flac', 'audio/x-m4a'
]
SUPPORTED_DOCUMENT_MIMES = [ # For direct text extraction or OCR
    'application/pdf', 
    'application/msword', # .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', # .docx
    'text/plain',
    'image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 'image/gif' 
    # DocumentProcessor's identify_file_type uses python-magic, which is more robust
]


def _process_single_file(file_path_in_container, case_name=None):
    """Internal function to process a single file."""
    app.logger.info(f"Starting internal processing for file: {file_path_in_container}, Case: {case_name}")

    if not os.path.exists(file_path_in_container):
        app.logger.error(f"_process_single_file: File not found at path: {file_path_in_container}")
        return {"error": f"File not found at specified path: {file_path_in_container}", "file_path": file_path_in_container, "status": "error"}, 404

    # Initialize response payload for this file
    response_payload = {
        "file_path": file_path_in_container,
        "case_name": case_name,
        "status": "processing_failed", # Default status
        "photoprism_file_uid": None,
        "album_uid": None,
        "content_type": None,
        "extracted_content": None, # Or transcription
        "processed_data_path": None, # Path where extracted text/transcription is saved
        "message": ""
    }

    # 1. Handle Case (Album in PhotoPrism)
    case_details = None
    photoprism_album_uid_for_upload = None
    if case_name:
        if not case_manager:
            app.logger.error("_process_single_file: CaseManager not initialized.")
            response_payload["message"] = "CaseManager not initialized."
            return response_payload, 500
        try:
            case_details = case_manager.get_or_create_case(case_name)
            photoprism_album_uid_for_upload = case_details.get('album_uid')
            response_payload["album_uid"] = photoprism_album_uid_for_upload
            app.logger.info(f"_process_single_file: Case '{case_name}' (Album UID: {photoprism_album_uid_for_upload}) ensured.")
        except Exception as e:
            app.logger.error(f"_process_single_file: Error handling case '{case_name}': {e}", exc_info=True)
            response_payload["message"] = f"Error handling case: {e}"
            return response_payload, 500

    # 2. Determine file type
    file_type = None
    content_type_from_processor = None
    try:
        if document_processor:
            content_type_from_processor = document_processor.identify_file_type(file_path_in_container)
            response_payload["content_type"] = content_type_from_processor
            app.logger.info(f"_process_single_file: Identified file type via processor: {content_type_from_processor} for {file_path_in_container}")
    except Exception as e:
        app.logger.warning(f"_process_single_file: Could not identify file type using DocumentProcessor for {file_path_in_container}: {e}. Falling back to mimetypes.", exc_info=True)
    
    if not content_type_from_processor:
        # Fallback to mimetypes if python-magic (via DocumentProcessor) fails or is unavailable
        content_type_mimetype, _ = mimetypes.guess_type(file_path_in_container)
        response_payload["content_type"] = content_type_mimetype
        app.logger.info(f"_process_single_file: Identified file type via mimetypes: {content_type_mimetype} for {file_path_in_container}")
        file_type = content_type_mimetype # Use this for logic below
    else:
        file_type = content_type_from_processor

    if not file_type:
        app.logger.warning(f"_process_single_file: Could not determine file type for {file_path_in_container}. Skipping content processing.")
        response_payload["message"] = "Could not determine file type."
        response_payload["status"] = "skipped_unknown_type"
        # Try to upload to PhotoPrism anyway, as it might handle unknown types
        # return response_payload, 415 # Unsupported Media Type or custom error

    # 3. Upload to PhotoPrism (Original File)
    photoprism_file_uid = None
    if photoprism_client:
        try:
            upload_response = photoprism_client.upload_file(file_path_in_container, album_uid=photoprism_album_uid_for_upload)
            if upload_response and isinstance(upload_response, list) and len(upload_response) > 0 and 'UID' in upload_response[0]:
                photoprism_file_uid = upload_response[0]['UID']
                response_payload["photoprism_file_uid"] = photoprism_file_uid
                app.logger.info(f"_process_single_file: File {file_path_in_container} uploaded to PhotoPrism. UID: {photoprism_file_uid}")
            elif upload_response and 'error' in upload_response:
                app.logger.error(f"_process_single_file: PhotoPrism upload failed for {file_path_in_container}: {upload_response['error']}")
                response_payload["message"] = f"PhotoPrism upload error: {upload_response['error']}"
                # Decide if this is fatal for the file or if content extraction should proceed
            else:
                app.logger.warning(f"_process_single_file: PhotoPrism upload for {file_path_in_container} did not return expected UID. Response: {upload_response}")
                response_payload["message"] = "PhotoPrism upload did not return UID."
        except Exception as e:
            app.logger.error(f"_process_single_file: Exception during PhotoPrism upload for {file_path_in_container}: {e}", exc_info=True)
            response_payload["message"] = f"PhotoPrism upload exception: {e}"
    else:
        app.logger.warning("_process_single_file: PhotoPrismClient not initialized. Skipping upload.")
        response_payload["message"] = "PhotoPrismClient not available for upload."

    # 4. Link File to Case in CaseManager (if applicable)
    if case_name and photoprism_file_uid and case_manager and photoprism_album_uid_for_upload: # Ensure album_uid is also present
        try:
            case_manager.link_file_to_case(case_name, file_path_in_container, photoprism_file_uid)
            app.logger.info(f"_process_single_file: File UID {photoprism_file_uid} linked to case '{case_name}'.")
        except Exception as e:
            app.logger.error(f"_process_single_file: Error linking file {photoprism_file_uid} to case '{case_name}': {e}", exc_info=True)
            # Non-fatal, but log it. Add to message if important.
            response_payload["message"] += f" (Error linking to case: {e})"

    # 5. Content Extraction (Audio/Document)
    extracted_data = None
    if file_type:
        if file_type in SUPPORTED_AUDIO_MIMES and audio_processor:
            app.logger.info(f"_process_single_file: Processing as audio file: {file_path_in_container}")
            try:
                extracted_data = audio_processor.process_audio_file(file_path_in_container)
                response_payload["extracted_content"] = extracted_data
                app.logger.info(f"_process_single_file: Audio processed for {file_path_in_container}. Transcription length: {len(extracted_data) if extracted_data else 0}")
            except Exception as e:
                app.logger.error(f"_process_single_file: Error processing audio file {file_path_in_container}: {e}", exc_info=True)
                extracted_data = f"Error during audio processing: {e}"
                response_payload["extracted_content"] = extracted_data # Store error message
                response_payload["message"] += f" (Audio processing error: {e})"

        elif file_type in SUPPORTED_DOCUMENT_MIMES and document_processor:
            app.logger.info(f"_process_single_file: Processing as document/image file: {file_path_in_container}")
            try:
                extracted_data = document_processor.process_document(file_path_in_container)
                response_payload["extracted_content"] = extracted_data
                app.logger.info(f"_process_single_file: Document processed for {file_path_in_container}. Extracted text length: {len(extracted_data) if extracted_data else 0}")
            except Exception as e:
                app.logger.error(f"_process_single_file: Error processing document file {file_path_in_container}: {e}", exc_info=True)
                extracted_data = f"Error during document processing: {e}"
                response_payload["extracted_content"] = extracted_data # Store error message
                response_payload["message"] += f" (Document processing error: {e})"
        else:
            app.logger.info(f"_process_single_file: File type {file_type} is not actively supported for content extraction or processor missing.")
            response_payload["message"] += " (File type not supported for content extraction)"
            extracted_data = "File type not supported for content extraction or processor unavailable."
            # This doesn't mean an error in processing, just that content wasn't extracted.
            response_payload["status"] = "processed_no_extraction"
    else:
        # This case was handled earlier (unknown file type)
        # If we reached here, it means file_type was None initially but we still tried to upload.
        pass 

    # 6. Store Extracted Content (Optional: Save to a file in PROCESSED_DATA_PATH)
    if extracted_data and not isinstance(extracted_data, str) or (isinstance(extracted_data, str) and not extracted_data.startswith("Error")):
        # Construct a path for the processed data
        if Config.PROCESSED_DATA_PATH:
            os.makedirs(Config.PROCESSED_DATA_PATH, exist_ok=True)
            base_filename = os.path.basename(file_path_in_container)
            # Create a unique name for the processed file, e.g., original_filename.txt
            processed_filename = f"{os.path.splitext(base_filename)[0]}_extracted.txt"
            processed_file_path = os.path.join(Config.PROCESSED_DATA_PATH, processed_filename)
            try:
                with open(processed_file_path, 'w', encoding='utf-8') as f:
                    f.write(str(extracted_data)) # Ensure extracted_data is string
                response_payload["processed_data_path"] = processed_file_path
                app.logger.info(f"_process_single_file: Extracted content saved to {processed_file_path}")
            except Exception as e:
                app.logger.error(f"_process_single_file: Failed to save extracted content to {processed_file_path}: {e}", exc_info=True)
                response_payload["message"] += f" (Failed to save extracted content: {e})"
        else:
            app.logger.warning("_process_single_file: PROCESSED_DATA_PATH not configured. Extracted content not saved to file.")

    # Final status update based on outcomes
    if response_payload.get("extracted_content") and not (isinstance(response_payload.get("extracted_content"), str) and response_payload.get("extracted_content").startswith("Error")):
        response_payload["status"] = "processed_successfully"
    elif response_payload["status"] == "processing_failed": # If not already set to something more specific
        if response_payload["photoprism_file_uid"]:
             # If uploaded but content extraction failed or wasn't applicable
            response_payload["status"] = "uploaded_extraction_issue_or_skipped"
        # else: it remains 'processing_failed' or was set by other errors

    app.logger.info(f"_process_single_file: Finished processing for {file_path_in_container}. Status: {response_payload['status']}")
    return response_payload, 200 # Default to 200, specific errors might have returned earlier with other codes


@app.route('/')
def home():
    return "Legal Brain Service is running!"

@app.route('/health')
def health_check():
    # Add checks for dependencies if needed (e.g., PhotoPrism client auth)
    pp_auth = photoprism_client.is_authenticated() if photoprism_client else False
    return jsonify({
        "status": "healthy", 
        "service": "Legal Brain",
        "photoprism_authenticated": pp_auth,
        "config_paths": {
            "import_path": Config.IMPORT_PATH,
            "originals_path": Config.ORIGINALS_PATH,
            "processed_data_path": Config.PROCESSED_DATA_PATH
        }
    }), 200

@app.route('/process/file', methods=['POST'])
def process_file_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
        
    file_path_in_container = data.get('file_path')
    case_name = data.get('case_name') # Optional

    if not file_path_in_container:
        return jsonify({"error": "Missing 'file_path' in request"}), 400

    # Optional: If file_path_in_container is relative to Config.IMPORT_PATH, make it absolute:
    # if not os.path.isabs(file_path_in_container) and Config.IMPORT_PATH:
    #     file_path_in_container = os.path.join(Config.IMPORT_PATH, file_path_in_container)
    #     app.logger.info(f"Resolved relative path to: {file_path_in_container}")
    # For now, assume 'file_path' is the full path within the container's /data volume or an accessible host path.

    app.logger.info(f"Received request for /process/file: {file_path_in_container}, Case: {case_name}")

    result_payload, status_code = _process_single_file(file_path_in_container, case_name)
    
    return jsonify(result_payload), status_code

@app.route('/process/directory', methods=['POST'])
def process_directory_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    directory_path_in_container = data.get('directory_path')
    case_name = data.get('case_name')  # Optional: associate all files in dir with this case

    if not directory_path_in_container:
        return jsonify({"error": "Missing 'directory_path' in request"}), 400

    # Optional: Resolve relative path similar to /process/file if needed
    # if not os.path.isabs(directory_path_in_container) and Config.IMPORT_PATH:
    #     directory_path_in_container = os.path.join(Config.IMPORT_PATH, directory_path_in_container)
    #     app.logger.info(f"Resolved relative directory path to: {directory_path_in_container}")

    if not os.path.isdir(directory_path_in_container):
        app.logger.error(f"Directory not found or not a directory: {directory_path_in_container}")
        return jsonify({"error": f"Directory not found or invalid: {directory_path_in_container}"}), 404

    app.logger.info(f"Processing request for directory: {directory_path_in_container}, Case for all files: {case_name}")

    results = []
    processed_files_count = 0
    failed_files_count = 0
    skipped_files_count = 0
    total_items_found = 0

    # Walk through the directory
    for root, _, files in os.walk(directory_path_in_container):
        for filename in files:
            item_full_path = os.path.join(root, filename)
            total_items_found += 1
            app.logger.info(f"Found file for processing in directory scan: {item_full_path}")
            
            try:
                result_payload, status_code = _process_single_file(item_full_path, case_name)
                results.append(result_payload)
                
                if status_code == 200 and result_payload.get("status") == "processed_successfully":
                    processed_files_count += 1
                elif result_payload.get("status", "").startswith("skipped") or result_payload.get("status") == "processed_no_extraction" or result_payload.get("status") == "uploaded_extraction_issue_or_skipped":
                    # Consider these as 'skipped' or 'partially successful' for counting purposes
                    # Adjust based on how you want to classify these
                    # For simplicity, let's count them as processed if an upload UID exists, otherwise skipped/failed
                    if result_payload.get("photoprism_file_uid"):
                        # It was at least uploaded, maybe content extraction wasn't applicable/failed
                        processed_files_count +=1 # Or a new category like 'partially_processed_count'
                    else:
                        skipped_files_count +=1 
                else: # Covers errors returned by _process_single_file or other non-200 status_codes implicitly
                    failed_files_count += 1
            except Exception as e:
                # This catches unexpected errors from the call to _process_single_file itself,
                # though _process_single_file is designed to catch its internal errors and return a payload.
                app.logger.error(f"Unhandled exception processing file {item_full_path} in directory scan: {e}", exc_info=True)
                results.append({
                    "file_path": item_full_path, 
                    "status": "error", 
                    "message": f"Unhandled exception: {str(e)}"
                })
                failed_files_count += 1
            
    app.logger.info(f"Directory scan complete for {directory_path_in_container}. Total: {total_items_found}, Processed: {processed_files_count}, Skipped: {skipped_files_count}, Failed: {failed_files_count}")
    return jsonify({
        "directory_path": directory_path_in_container,
        "case_name_for_batch": case_name,
        "total_items_found": total_items_found,
        "processed_successfully_count": processed_files_count,
        "skipped_or_partial_count": skipped_files_count, # Renamed for clarity
        "failed_count": failed_files_count,
        "detailed_results": results
    }), 200

if __name__ == '__main__':
    # Ensure logger is available for startup if not using flask run
    if not app.logger.handlers: # Basic check
        import logging
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    app.logger.info("Starting Legal Brain Service...")
    # For Docker, CMD in Dockerfile handles this. For local dev, flask run is preferred.
    app.run(host='0.0.0.0', port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
