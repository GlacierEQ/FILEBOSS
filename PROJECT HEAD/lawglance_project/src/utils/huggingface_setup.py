"""Utility for setting up and verifying Hugging Face API access."""
import os
import sys
import requests
from dotenv import load_dotenv
from huggingface_hub import HfApi, HfApiError, login
from typing import Optional, Dict, Any

# Terminal formatting
SUCCESS_MARK = "✅"
ERROR_MARK = "❌"
INFO_MARK = "ℹ️"
WARNING_MARK = "⚠️"

def verify_token(token: Optional[str] = None) -> bool:
    """
    Verify that the Hugging Face token is valid and working.
    
    Args:
        token: Hugging Face API token to verify
        
    Returns:
        bool: Whether the token is valid
    """
    if token is None:
        # Try to get token from environment variables
        load_dotenv()
        token = os.getenv("HUGGINGFACE_TOKEN")
        
    if not token:
        print(f"{ERROR_MARK} No Hugging Face token provided")
        print("Please set the HUGGINGFACE_TOKEN environment variable or provide a token as an argument")
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
        
    except HfApiError as e:
        print(f"{ERROR_MARK} Token verification failed: {e}")
        print("Please make sure you're using a valid Hugging Face token.")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"{ERROR_MARK} Request failed: {e}")
        print("Please check your internet connection and try again.")
        return False
    except Exception as e:
        print(f"{ERROR_MARK} Unexpected error: {e}")
        return False

def setup_huggingface() -> bool:
    """
    Set up Hugging Face access by checking/prompting for API token.
    
    Returns:
        bool: Whether setup was successful
    """
    load_dotenv()
    token = os.getenv("HUGGINGFACE_TOKEN")
    
    if token and verify_token(token):
        print(f"{SUCCESS_MARK} Hugging Face token is valid")
        try:
            login(token=token)
            print(f"{SUCCESS_MARK} Logged in to Hugging Face")
            return True
        except Exception as e:
            print(f"{ERROR_MARK} Error logging in: {e}")
            return False
    
    # If we get here, we need to prompt for a token
    print(f"{INFO_MARK} Hugging Face token not found or invalid")
    print("Please visit https://huggingface.co/settings/tokens to create a token")
    print("It's recommended to create a token with 'read' access")
    
    if "JUPYTER_RUNTIME_DIR" in os.environ or "COLAB_GPU" in os.environ:
        # Running in Jupyter/Colab
        from IPython.display import display, HTML
        display(HTML('<a href="https://huggingface.co/settings/tokens" target="_blank">Get your Hugging Face token here</a>'))
    
    new_token = input("Enter your Hugging Face token: ").strip()
    
    if verify_token(new_token):
        # Save to .env file
        with open(".env", "a") as env_file:
            env_file.write(f"\nHUGGINGFACE_TOKEN={new_token}\n")
        print(f"{SUCCESS_MARK} Token saved to .env file")
        
        try:
            login(token=new_token)
            print(f"{SUCCESS_MARK} Logged in to Hugging Face")
            return True
        except Exception as e:
            print(f"{ERROR_MARK} Error logging in: {e}")
            return False
    
    return False

if __name__ == "__main__":
    setup_huggingface()
