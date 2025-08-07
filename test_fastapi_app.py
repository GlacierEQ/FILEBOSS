"""
Simple FastAPI test application.
"""
from fastapi import FastAPI
import uvicorn

# Create a simple FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    print("Starting test FastAPI server on http://127.0.0.1:8000")
    print("Endpoints:")
    print("  - GET /           - Simple hello world")
    print("  - GET /health     - Health check")
    print("\nPress Ctrl+C to stop the server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
