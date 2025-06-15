"""
Utility script to verify Hugging Face token is working correctly.
"""
import os
import sys
from huggingface_hub import HfApi, HfFolder

# Use ASCII alternatives to avoid encoding issues on Windows
SUCCESS_MARK = "[SUCCESS]"  # instead of ✅
ERROR_MARK = "[ERROR]"      # instead of ❌
INFO_MARK = "[INFO]"        # instead of ℹ️

def verify_token(token=None):
    """Verify that the Hugging Face token is valid and working."""
    if token:
        os.environ["HUGGINGFACE_API_TOKEN"] = token
    elif "HUGGINGFACE_API_TOKEN" in os.environ:
        token = os.environ["HUGGINGFACE_API_TOKEN"]
    else:
        token = HfFolder.get_token()
        
    if not token:
        print(f"{ERROR_MARK} No Hugging Face token found!")
        print("Please provide a token as argument or set the HUGGINGFACE_API_TOKEN environment variable.")
        return False
        
    try:
        # Initialize the API with the token
        api = HfApi(token=token)
        
        # Try to get user info to verify token
        user_info = api.whoami()
        
        print(f"{SUCCESS_MARK} Token verified successfully! Logged in as: {user_info['name']}")
        print(f"   User email: {user_info.get('email', 'Not available')}")
        
        # Check if token has write access
        if user_info.get("auth", {}).get("accessToken") == token:
            print(f"{SUCCESS_MARK} Token has full access capabilities")
        else:
            print(f"{INFO_MARK} Token may have limited access")
            
        return True
        
    except Exception as e:
        print(f"{ERROR_MARK} Token verification failed: {str(e)}")
        print("Please make sure you're using a valid Hugging Face token.")
        return False

if __name__ == "__main__":
    # Get token from command line if provided
    token = sys.argv[1] if len(sys.argv) > 1 else None
    
    # If no command line token, use the one we want to install
    if not token:
        token = "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"
        
    # Verify the token
    if verify_token(token):
        # Save the token to the HF folder for future use
        HfFolder.save_token(token)
        print("\nToken has been saved for future use.")
        print("You can now run your Lawglance system!")
    else:
        print("\nToken verification failed. Please check your token and try again.")
