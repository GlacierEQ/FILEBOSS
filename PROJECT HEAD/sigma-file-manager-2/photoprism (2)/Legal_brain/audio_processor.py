import requests
import os
import json
from .config import Config

# For speaker diarization (optional, can be complex to integrate initially)
# from pyannote.audio import Pipeline

class AudioProcessor:
    def __init__(self):
        self.whisper_api_url = Config.WHISPER_API_URL
        # self.pyannote_pipeline = None
        # self.pyannote_auth_token = os.getenv("PYANNOTE_AUTH_TOKEN") # Needed if using pre-trained pyannote models
        # self._init_pyannote()

    # def _init_pyannote(self):
    #     # Initialize PyAnnote pipeline if auth token is provided
    #     # This is a placeholder; actual initialization might require model download
    #     # and ensuring ffmpeg is accessible.
    #     if self.pyannote_auth_token:
    #         try:
    #             # Using a diarization pipeline as an example
    #             # self.pyannote_pipeline = Pipeline.from_pretrained(
    #             #     "pyannote/speaker-diarization-3.1", # or other model
    #             #     use_auth_token=self.pyannote_auth_token
    #             # )
    #             print("PyAnnote pipeline would be initialized here (if token provided and model chosen).")
    #         except Exception as e:
    #             print(f"Failed to initialize PyAnnote pipeline: {e}")
    #             self.pyannote_pipeline = None
    #     else:
    #         print("PyAnnote auth token not found. Diarization will be skipped or use local models if configured.")


    def transcribe_audio(self, audio_file_path_on_host):
        """
        Transcribes an audio file using the whisper_service API.
        audio_file_path_on_host: Absolute path to the audio file on the legal_brain_service container's filesystem.
        """
        if not self.whisper_api_url:
            print("Whisper API URL not configured.")
            return None

        try:
            with open(audio_file_path_on_host, 'rb') as f:
                files = {'audio_file': (os.path.basename(audio_file_path_on_host), f)}
                # Parameters for the whisper service API might be sent as form data or query params
                # For example, to specify the model or task if the service supports it.
                # For onerahmet/openai-whisper-asr-webservice, it's a simple file upload.
                # The service might also support parameters like 'task' (transcribe/translate) or 'language'.
                # payload = {'task': 'transcribe', 'output': 'json'} # Example if service supports it
                
                print(f"Sending {audio_file_path_on_host} to Whisper service at {self.whisper_api_url}")
                response = requests.post(self.whisper_api_url, files=files) #, data=payload)
                response.raise_for_status()
                
                transcription_result = response.json()
                print(f"Transcription received: {transcription_result.get('text')[:100]}...") # Print first 100 chars
                return transcription_result

        except requests.exceptions.RequestException as e:
            print(f"Error during transcription request to {self.whisper_api_url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"Whisper service response content: {e.response.json()}")
                except json.JSONDecodeError:
                    print(f"Whisper service response content: {e.response.text}")
            return None
        except FileNotFoundError:
            print(f"Audio file not found at {audio_file_path_on_host}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during transcription: {e}")
            return None

    # def diarize_audio(self, audio_file_path_on_host):
    #     """
    #     Performs speaker diarization on an audio file.
    #     Returns diarization information (e.g., speaker turns).
    #     """
    #     if not self.pyannote_pipeline:
    #         print("PyAnnote pipeline not initialized. Skipping diarization.")
    #         return None
        
    #     try:
    #         print(f"Performing speaker diarization on {audio_file_path_on_host}...")
    #         # The input to pipeline might need to be a waveform or specific format
    #         diarization = self.pyannote_pipeline(audio_file_path_on_host)
            
    #         # Process diarization output into a more usable format
    #         # For example, iterating through turns and segments:
    #         speaker_turns = []
    #         for turn, _, speaker in diarization.itertracks(yield_label=True):
    #             speaker_turns.append({
    #                 "speaker": speaker,
    #                 "start_time": turn.start,
    #                 "end_time": turn.end
    #             })
    #         print(f"Diarization complete. Found {len(speaker_turns)} speaker turns.")
    #         return {"speaker_turns": speaker_turns}
    #     except Exception as e:
    #         print(f"Error during speaker diarization: {e}")
    #         return None

    def process_audio_file(self, audio_file_path_on_host):
        """
        Orchestrates transcription and (optionally) diarization.
        """
        transcription_data = self.transcribe_audio(audio_file_path_on_host)
        if not transcription_data:
            return {"error": "Transcription failed."}

        # diarization_data = self.diarize_audio(audio_file_path_on_host)
        # if not diarization_data:
        #    diarization_data = {"warning": "Diarization skipped or failed."}

        # Combine results
        # final_result = {**transcription_data, **diarization_data}
        # return final_result
        
        return transcription_data # For now, just return transcription


# Example Usage (for testing this module directly)
if __name__ == '__main__':
    # This example requires a running Whisper service and an audio file.
    # You'll need to set environment variables like WHISPER_API_URL.
    # And place a test audio file (e.g., test.mp3) in a path accessible here.
    
    processor = AudioProcessor()
    
    # Create a dummy test.mp3 for testing if it doesn't exist
    # In a real scenario, you'd have actual audio files.
    dummy_audio_path = "./dummy_test_audio.mp3" # Relative to where this script might be run from
    if not os.path.exists(dummy_audio_path):
        try:
            # Create a tiny, silent mp3 file for testing if ffmpeg is available.
            # This is a complex dependency just for a test, so ensure ffmpeg is in PATH if uncommented.
            # os.system(f"ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 -q:a 9 -acodec libmp3lame {dummy_audio_path}")
            # Simpler: create an empty file and mock the rest for now if no ffmpeg
            with open(dummy_audio_path, 'w') as f:
                f.write("dummy audio content") # This won't be a valid mp3
            print(f"Created dummy audio file: {dummy_audio_path} (not a real mp3, for path testing)")
        except Exception as e:
            print(f"Could not create dummy audio file: {e}")

    if Config.WHISPER_API_URL and os.path.exists(dummy_audio_path):
        print(f"\nAttempting to process audio file: {dummy_audio_path}")
        # Note: The dummy file is not real audio, so Whisper service will likely fail.
        # This mainly tests the request path.
        result = processor.process_audio_file(dummy_audio_path)
        print("\nProcessing Result:")
        print(json.dumps(result, indent=2))
    else:
        if not Config.WHISPER_API_URL:
            print("Skipping audio_processor test: WHISPER_API_URL not set.")
        if not os.path.exists(dummy_audio_path):
            print(f"Skipping audio_processor test: Dummy audio file {dummy_audio_path} not found.")
