"""
Test script to verify uvicorn server functionality.
"""
import uvicorn
import sys
import os

def main():
    print("=" * 60)
    print("🚀 Testing Uvicorn Server")
    print("=" * 60)
    
    # Simple FastAPI app
    app = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
    """
    
    # Write the app to a temporary file
    with open("temp_app.py", "w") as f:
        f.write(app)
    
    print("✅ Created temporary FastAPI app")
    
    # Start the uvicorn server
    print("\n🔄 Starting Uvicorn server...")
    print("   - Endpoint: http://127.0.0.1:8000/")
    print("   - Health:   http://127.0.0.1:8000/health")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        uvicorn.run(
            "temp_app:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"\n❌ Error starting Uvicorn: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up the temporary file
        try:
            os.remove("temp_app.py")
            print("\n🧹 Cleaned up temporary files")
        except:
            pass

if __name__ == "__main__":
    main()
