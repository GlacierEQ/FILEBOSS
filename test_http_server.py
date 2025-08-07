"""
Simple HTTP server for testing basic network connectivity.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        if self.path == '/health':
            response = {"status": "ok", "message": "Health check passed"}
        else:
            response = {"message": "Hello, World!", "path": self.path}
            
        self.wfile.write(json.dumps(response).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting HTTP server on port {port}...")
    print("Endpoints:")
    print(f"  - GET http://127.0.0.1:{port}/           - Simple hello world")
    print(f"  - GET http://127.0.0.1:{port}/health     - Health check")
    print("\nPress Ctrl+C to stop the server")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
