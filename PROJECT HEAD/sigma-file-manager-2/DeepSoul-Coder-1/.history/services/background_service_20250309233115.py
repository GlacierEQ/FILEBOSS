    def _update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update configuration
        
        Args:
            new_config: New configuration values
        """
        # Update config
        self.config.update(new_config)
        self.save_config()
        
        # Update watched directories if changed
        if "watched_directories" in new_config:
            self.watched_directories = new_config["watched_directories"]
            
            # Update file watcher
            current_watched = self.file_watcher.get_watched_directories()
            
            # Remove directories no longer in config
            for directory in current_watched:
                if directory not in self.watched_directories:
                    self.file_watcher.unwatch_directory(directory)
            
            # Add new directories
            for directory in self.watched_directories:
                if directory not in current_watched and os.path.isdir(directory):
                    self.file_watcher.watch_directory(directory)
    
    def _fallback_notification(self, title: str, message: str, icon_type: str = "info") -> None:
        """
        Fallback notification when Windows integration is not available
        
        Args:
            title: Notification title
            message: Notification message
            icon_type: Icon type (ignored in fallback)
        """
        print(f"NOTIFICATION: {title} - {message}")

def run_background_service():
    """Run the background service"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("deepsoul_background.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="DeepSeek-Coder Background Service")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Create and start service
    service = BackgroundService(args.config)
    service.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping service...")
    finally:
        service.stop()

if __name__ == "__main__":
    run_background_service()
