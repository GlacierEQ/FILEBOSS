        @self.app.get("/tasks")
        async def get_all_tasks():
            """Get all tasks"""
            with self.task_lock:
                tasks = {}
                for task_id, task in self.tasks.items():
                    tasks[task_id] = {
                        "status": task["status"],
                        "type": task["type"],
                        "created_at": time.time() - task.get("created_at", 0) if "created_at" in task else None,
                        "result": task.get("result")
                    }
                return {"tasks": tasks}
        
        @self.app.get("/stats")
        async def get_stats():
            """Get service statistics"""
            if not self.service:
                raise HTTPException(status_code=503, detail="Service not available")
            
            return self.service.get_stats()
        
        @self.app.post("/shutdown")
        async def shutdown():
            """Shutdown the API server"""
            if not self.service:
                raise HTTPException(status_code=503, detail="Service not available")
            
            # Schedule shutdown
            background_tasks = BackgroundTasks()
            background_tasks.add_task(self._shutdown)
            
            return {
                "message": "Shutdown initiated",
                "timestamp": time.time()
            }
    
    def start(self):
        """Start the API server"""
        if not HAS_FASTAPI:
            logger.error("FastAPI is not installed, cannot start API server")
            return False
        
        # Start server in a thread
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()
        
        logger.info(f"API server started at http://{self.host}:{self.port}")
        return True
    
    def _run_server(self):
        """Run the FastAPI server"""
        try:
            import uvicorn
            uvicorn.run(self.app, host=self.host, port=self.port)
        except Exception as e:
            logger.error(f"Error running API server: {e}")
    
    def _shutdown(self):
        """Shutdown the server"""
        import sys
        import os
        
        # Shutdown uvicorn server
        pid = os.getpid()
        logger.info(f"Shutting down API server (PID: {pid})")
        
        # Wait briefly then exit
        time.sleep(1)
        os._exit(0)
    
    def _handle_analyze_task(self, task_id: str, code: str, language: str, filename: Optional[str] = None):
        """Handle code analysis task"""
        try:
            # Update task status
            with self.task_lock:
                self.tasks[task_id]["status"] = "running"
            
            # Analyze code
            if self.service and hasattr(self.service, 'deepsoul'):
                deepsoul = self.service.deepsoul
                result = deepsoul.analyze_code(code, language)
                
                # Update task with result
                with self.task_lock:
                    self.tasks[task_id]["status"] = "completed"
                    self.tasks[task_id]["result"] = result
            else:
                # No DeepSoul instance available
                with self.task_lock:
                    self.tasks[task_id]["status"] = "failed"
                    self.tasks[task_id]["message"] = "DeepSoul model not available"
        
        except Exception as e:
            logger.error(f"Error in analysis task {task_id}: {str(e)}")
            with self.task_lock:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)
    
    def _handle_enhance_task(self, task_id: str, code: str, language: str, enhancement_type: str, filename: Optional[str] = None):
        """Handle code enhancement task"""
        try:
            # Update task status
            with self.task_lock:
                self.tasks[task_id]["status"] = "running"
            
            # Enhance code
            if self.service and hasattr(self.service, 'deepsoul'):
                deepsoul = self.service.deepsoul
                result = deepsoul.enhance_code(code, language, enhancement_type)
                
                # Update task with result
                with self.task_lock:
                    self.tasks[task_id]["status"] = "completed"
                    self.tasks[task_id]["result"] = result
            else:
                # No DeepSoul instance available
                with self.task_lock:
                    self.tasks[task_id]["status"] = "failed"
                    self.tasks[task_id]["message"] = "DeepSoul model not available"
        
        except Exception as e:
            logger.error(f"Error in enhancement task {task_id}: {str(e)}")
            with self.task_lock:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)
    
    def _handle_generate_task(self, task_id: str, prompt: str, language: str, max_tokens: int = 512, temperature: float = 0.7):
        """Handle code generation task"""
        try:
            # Update task status
            with self.task_lock:
                self.tasks[task_id]["status"] = "running"
            
            # Generate code
            if self.service and hasattr(self.service, 'deepsoul'):
                deepsoul = self.service.deepsoul
                
                # Use memory efficient generator if available
                if hasattr(deepsoul, 'generate_code'):
                    result = deepsoul.generate_code(prompt, language, max_tokens, temperature)
                else:
                    # Fallback to direct generation
                    from utils.memory_efficient_generation import create_generator
                    generator = create_generator(deepsoul.model, deepsoul.tokenizer)
                    result = generator.generate(
                        f"Generate {language} code for: {prompt}",
                        max_new_tokens=max_tokens,
                        temperature=temperature
                    )
                
                # Update task with result
                with self.task_lock:
                    self.tasks[task_id]["status"] = "completed"
                    self.tasks[task_id]["result"] = result
            else:
                # No DeepSoul instance available
                with self.task_lock:
                    self.tasks[task_id]["status"] = "failed"
                    self.tasks[task_id]["message"] = "DeepSoul model not available"
        
        except Exception as e:
            logger.error(f"Error in generation task {task_id}: {str(e)}")
            with self.task_lock:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)

def start_server(service=None, host="127.0.0.1", port=8765):
    """Start the API server"""
    server = APIServer(service, host, port)
    return server.start()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("api_server.log"),
            logging.StreamHandler()
        ]
    )
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='DeepSeek-Coder API Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8765, help='Port to listen on')
    args = parser.parse_args()
    
    # Start the server
    server = APIServer(host=args.host, port=args.port)
    server.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down API server...")
