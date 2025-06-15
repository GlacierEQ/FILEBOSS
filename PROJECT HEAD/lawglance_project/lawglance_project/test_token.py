"""
Simple script to test if the Hugging Face token works.
No fancy Unicode characters, just plain ASCII.
"""
import os
import sys

def test_token(token):
    # Set the token in environment variable
    os.environ["HUGGINGFACE_API_TOKEN"] = token
    print(f"Using token: {token[:5]}...{token[-5:]}")
    
    try:
        # Import the library after setting the token
        from huggingface_hub import HfApi
        
        # Initialize API
        api = HfApi(token=token)
        print("API initialized successfully")
        
        # Test the token by getting user info
        user = api.whoami()
        print(f"Success! Logged in as: {user['name']}")
        return True
    except ImportError:
        print("Error: huggingface_hub library not installed")
        print("Install with: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"Error testing token: {str(e)}")
        return False

if __name__ == "__main__":
    # Use provided token or default
    token = sys.argv[1] if len(sys.argv) > 1 else "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"
    
    if test_token(token):
        print("\nToken is valid and working!")
        print("You can proceed with running the Lawglance system.")
    else:
        print("\nToken validation failed.")
