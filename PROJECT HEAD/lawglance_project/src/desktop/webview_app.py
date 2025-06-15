"""
Desktop application wrapper for LawGlance.
This module uses PyWebView to create a desktop application that wraps the Streamlit web app.
"""
import os
import sys
import time
import signal
import atexit
import logging
import subprocess
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("lawglance_desktop.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("LawGlance-Desktop")

# Try to import webview, install if not found
try:
    import webview
except ImportError:
    logger.info("PyWebView not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview"])
    import webview

# Determine the project root directory
ROOT_DIR = Path(__file__).parent.parent.parent
STREAMLIT_PORT = 8501

class LawGlanceApp:
    """Desktop application wrapper for LawGlance."""
    
    def __init__(self):
        """Initialize the desktop application."""
        self.streamlit_process = None
        self.window = None
    
    def start_streamlit_server(self) -> subprocess.Popen:
        """
        Start the Streamlit server for the LawGlance application.
        
        Returns:
            The Streamlit server process
        """
        logger.info("Starting Streamlit server...")
        env = os.environ.copy()
        
        # Ensure Python path includes our project
        python_path = str(ROOT_DIR)
        if "PYTHONPATH" in env:
            python_path = f"{python_path}{os.pathsep}{env['PYTHONPATH']}"
        env["PYTHONPATH"] = python_path
        
        # Start Streamlit server
        try:
            # On Windows, hide the console window
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = 0
                
            proc = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", 
                 str(ROOT_DIR / "app.py"),
                 "--server.port", str(STREAMLIT_PORT),
                 "--browser.serverAddress", "localhost",
                 "--server.headless", "true",
                 "--server.enableCORS", "false",
                 "--server.enableXsrfProtection", "false"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            
            logger.info(f"Streamlit server started with PID {proc.pid}")
            return proc
            
        except Exception as e:
            logger.error(f"Error starting Streamlit: {e}")
            raise
    
    def wait_for_streamlit(self, timeout=30) -> bool:
        """
        Wait for Streamlit server to start and be ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if Streamlit is ready, False otherwise
        """
        import socket
        import time
        
        logger.info(f"Waiting for Streamlit to start on port {STREAMLIT_PORT}...")
        
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                # Try to connect to the Streamlit port
                with socket.create_connection(("localhost", STREAMLIT_PORT), timeout=1):
                    logger.info("Streamlit is running!")
                    return True
            except (socket.timeout, ConnectionRefusedError):
                time.sleep(1)
        
        logger.error(f"Timed out waiting for Streamlit after {timeout} seconds")
        return False
    
    def create_window(self) -> None:
        """Create and configure the application window."""
        logger.info("Creating application window...")
        
        # Load custom CSS for the webview
        js_api = {
            'exit': self.terminate
        }
        
        # Create the window
        self.window = webview.create_window(
            title='LawGlance - AI Legal Assistant',
            url=f'http://localhost:{STREAMLIT_PORT}',
            js_api=js_api,
            width=1200,
            height=800,
            min_size=(800, 600),
            text_select=True,
            zoomable=True
        )
        
        # Set up handlers for window events
        self.window.events.closed += self.on_closed
    
    def on_closed(self) -> None:
        """Handle window close event."""
        logger.info("Window closed. Terminating Streamlit...")
        self.terminate()
    
    def terminate(self) -> None:
        """Clean up resources and terminate the application."""
        if self.streamlit_process and self.streamlit_process.poll() is None:
            logger.info(f"Terminating Streamlit process (PID: {self.streamlit_process.pid})...")
            try:
                # On Windows
                if sys.platform == "win32":
                    self.streamlit_process.terminate()
                # On Unix-like systems
                else:
                    os.killpg(os.getpgid(self.streamlit_process.pid), signal.SIGTERM)
                
                # Give it a moment to terminate gracefully
                try:
                    self.streamlit_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Streamlit did not terminate gracefully, forcing...")
                    self.streamlit_process.kill()
                    
                logger.info("Streamlit process terminated.")
            except Exception as e:
                logger.error(f"Error terminating Streamlit: {e}")
    
    def run(self) -> None:
        """Run the desktop application."""
        try:
            # Start Streamlit
            self.streamlit_process = self.start_streamlit_server()
            
            # Wait for Streamlit to be ready
            if not self.wait_for_streamlit():
                logger.error("Failed to start Streamlit. Exiting.")
                self.terminate()
                return
            
            # Create and show the window
            self.create_window()
            
            # Register cleanup handler
            atexit.register(self.terminate)
            
            # Start the application
            logger.info("Starting webview application...")
            webview.start(debug=False)
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            self.terminate()


def main():
    """Main entry point for the desktop application."""
    print("Starting LawGlance Desktop Application...")
    app = LawGlanceApp()
    app.run()

if __name__ == "__main__":
    main()
