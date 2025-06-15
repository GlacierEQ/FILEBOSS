#!/usr/bin/env python
"""
Smart Scheduling System for Sorting Hat

This module implements an intelligent scheduling system that:
1. Allows scheduling file organization tasks at optimal times
2. Learns from system usage patterns to minimize performance impact
3. Provides recurring schedules with flexible configuration
4. Manages system resource usage during organization tasks
"""
import os
import sys
import json
import time
import uuid
import logging
import datetime
import threading
import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import statistics

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler.log'),
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger("scheduler")

class Task:
    """Represents a scheduled organization task"""
    
    def __init__(self, 
                 task_id: Optional[str] = None,
                 name: str = "Untitled Task", 
                 path: str = None,
                 instruction: str = None,
                 schedule_type: str = "once",  # once, daily, weekly, monthly, adaptive
                 scheduled_time: Optional[datetime.datetime] = None,
                 days_of_week: List[int] = None,  # 0=Monday, 6=Sunday
                 day_of_month: Optional[int] = None,
                 resource_limit: int = 50,  # percentage of CPU/memory to use
                 priority: int = 1,  # 1=low, 2=medium, 3=high
                 last_run: Optional[datetime.datetime] = None,
                 enabled: bool = True):
        """Initialize a scheduled task"""
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.name = name
        self.path = path
        self.instruction = instruction
        self.schedule_type = schedule_type
        self.scheduled_time = scheduled_time
        self.days_of_week = days_of_week if days_of_week else []
        self.day_of_month = day_of_month
        self.resource_limit = resource_limit
        self.priority = priority
        self.last_run = last_run
        self.enabled = enabled
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create a Task from a dictionary"""
        # Convert string timestamps to datetime objects
        scheduled_time = None
        if data.get('scheduled_time'):
            scheduled_time = datetime.datetime.fromisoformat(data['scheduled_time'])
            
        last_run = None
        if data.get('last_run'):
            last_run = datetime.datetime.fromisoformat(data['last_run'])
            
        return cls(
            task_id=data.get('task_id'),
            name=data.get('name', 'Untitled Task'),
            path=data.get('path'),
            instruction=data.get('instruction'),
            schedule_type=data.get('schedule_type', 'once'),
            scheduled_time=scheduled_time,
            days_of_week=data.get('days_of_week', []),
            day_of_month=data.get('day_of_month'),
            resource_limit=data.get('resource_limit', 50),
            priority=data.get('priority', 1),
            last_run=last_run,
            enabled=data.get('enabled', True)
        )
        
    def to_dict(self) -> Dict:
        """Convert Task to a dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'path': self.path,
            'instruction': self.instruction,
            'schedule_type': self.schedule_type,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'days_of_week': self.days_of_week,
            'day_of_month': self.day_of_month,
            'resource_limit': self.resource_limit,
            'priority': self.priority,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'enabled': self.enabled
        }
        
    def get_next_run_time(self) -> Optional[datetime.datetime]:
        """Calculate the next scheduled run time"""
        now = datetime.datetime.now()
        
        if not self.enabled:
            return None
            
        if self.schedule_type == 'once':
            if not self.scheduled_time:
                return None
            return self.scheduled_time if self.scheduled_time > now else None
            
        elif self.schedule_type == 'daily':
            if not self.scheduled_time:
                return None
                
            # Use today's date with the scheduled time
            next_time = datetime.datetime.combine(
                now.date(), 
                self.scheduled_time.time()
            )
            
            # If today's scheduled time has already passed, use tomorrow
            if next_time <= now:
                next_time += datetime.timedelta(days=1)
            
            return next_time
            
        elif self.schedule_type == 'weekly':
            if not self.scheduled_time or not self.days_of_week:
                return None
                
            # Get current day of week (0=Monday, 6=Sunday)
            current_weekday = now.weekday()
            
            # Find the next day of week from the scheduled days
            days_ahead = None
            for day in sorted(self.days_of_week):
                if day > current_weekday:
                    days_ahead = day - current_weekday
                    break
                    
            # If no days found after current day, wrap around to next week
            if days_ahead is None and self.days_of_week:
                days_ahead = 7 - current_weekday + min(self.days_of_week)
                
            if days_ahead is None:
                return None
                
            # Calculate next date
            next_date = now.date() + datetime.timedelta(days=days_ahead)
            next_time = datetime.datetime.combine(next_date, self.scheduled_time.time())
            
            # If it's today and the time has passed, find the next occurrence
            if days_ahead == 0 and next_time <= now:
                if len(self.days_of_week) > 1:
                    # Find the next day in the list
                    for day in sorted(self.days_of_week):
                        if day > current_weekday:
                            days_ahead = day - current_weekday
                            break
                    # If no days found after current day, wrap around to next week
                    if days_ahead is None:
                        days_ahead = 7 - current_weekday + min(self.days_of_week)
                else:
                    # There's only one day in the list, so it's next week
                    days_ahead = 7
                    
                next_date = now.date() + datetime.timedelta(days=days_ahead)
                next_time = datetime.datetime.combine(next_date, self.scheduled_time.time())
                
            return next_time
            
        elif self.schedule_type == 'monthly':
            if not self.scheduled_time or not self.day_of_month:
                return None
                
            # Use current month's specified day with scheduled time
            try:
                next_date = datetime.date(now.year, now.month, self.day_of_month)
            except ValueError:
                # Handle invalid dates (e.g., February 30)
                # Move to the last day of the month
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year
                    
                next_date = datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)
                
            next_time = datetime.datetime.combine(next_date, self.scheduled_time.time())
            
            # If this month's date has passed, move to next month
            if next_time <= now:
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year
                    
                try:
                    next_date = datetime.date(next_year, next_month, self.day_of_month)
                except ValueError:
                    # Handle invalid dates (e.g., February 30)
                    # Move to the last day of the month
                    if next_month == 12:
                        next_month = 1
                        next_year += 1
                    else:
                        next_month += 1
                        
                    next_date = datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)
                    
                next_time = datetime.datetime.combine(next_date, self.scheduled_time.time())
                
            return next_time
            
        elif self.schedule_type == 'adaptive':
            # Adaptive scheduling uses usage patterns to find optimal time
            # Will be implemented by the UsagePatternAnalyzer
            return None
            
        return None

    def is_due(self) -> bool:
        """Check if the task is due to run"""
        next_run = self.get_next_run_time()
        if not next_run:
            return False
            
        return next_run <= datetime.datetime.now()

class UsagePatternAnalyzer:
    """Analyzes system usage patterns to determine optimal scheduling times"""
    
    def __init__(self, db_path: str):
        """Initialize the analyzer with a database path"""
        self.db_path = db_path
        self._setup_database()
        self.collection_thread = None
        self.collecting = False
        self.collection_interval = 300  # 5 minutes
        
    def _setup_database(self):
        """Create necessary database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for system usage data
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_usage (
            timestamp INTEGER,
            cpu_percent REAL,
            memory_percent REAL,
            disk_io_percent REAL,
            day_of_week INTEGER,
            hour INTEGER,
            minute INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def start_collection(self):
        """Start collecting system usage data in the background"""
        if self.collecting:
            return
            
        self.collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
    def stop_collection(self):
        """Stop collecting system usage data"""
        self.collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=1.0)
            
    def _collection_loop(self):
        """Background thread that collects system usage data"""
        try:
            import psutil
        except ImportError:
            logger.error("psutil is required for usage pattern analysis. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            import psutil
            
        while self.collecting:
            try:
                # Collect current system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                # Disk I/O is more complex to normalize
                disk_io = psutil.disk_io_counters()
                if hasattr(self, 'last_disk_io'):
                    read_diff = disk_io.read_bytes - self.last_disk_io.read_bytes
                    write_diff = disk_io.write_bytes - self.last_disk_io.write_bytes
                    # Normalize to a percentage (approximate)
                    disk_io_percent = min(100, (read_diff + write_diff) / (1024 * 1024) * 2)
                else:
                    disk_io_percent = 0
                self.last_disk_io = disk_io
                
                # Get current time information
                now = datetime.datetime.now()
                day_of_week = now.weekday()
                hour = now.hour
                minute = now.minute
                
                # Store in database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO system_usage VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (int(time.time()), cpu_percent, memory_percent, disk_io_percent, 
                     day_of_week, hour, minute)
                )
                conn.commit()
                conn.close()
                
                # Sleep until next collection
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error collecting usage data: {e}")
                time.sleep(60)  # Sleep briefly then retry
                
    def find_optimal_time(self, path: str, required_resources: int = 30) -> Tuple[int, int]:
        """Find the optimal time to schedule a task based on usage patterns
        
        Args:
            path: The path to analyze (different paths may have different optimal times)
            required_resources: The percentage of system resources needed (higher means more idle time needed)
            
        Returns:
            Tuple of (hour, minute) for optimal execution
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current day of week
        current_day = datetime.datetime.now().weekday()
        
        # Query for usage patterns on this day of week
        cursor.execute('''
        SELECT hour, minute, AVG(cpu_percent), AVG(memory_percent), AVG(disk_io_percent)
        FROM system_usage
        WHERE day_of_week = ?
        GROUP BY hour, minute
        ORDER BY (AVG(cpu_percent) + AVG(memory_percent) + AVG(disk_io_percent)) ASC
        ''', (current_day,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            # No data yet, use a reasonable default (3 AM)
            return (3, 0)
            
        # Find the time with the lowest resource usage
        optimal_hour, optimal_minute = results[0][0], results[0][1]
        
        # If the optimal time has already passed today, add one day to it
        now = datetime.datetime.now()
        optimal_time = now.replace(hour=optimal_hour, minute=optimal_minute, second=0, microsecond=0)
        if optimal_time < now:
            # Return same time tomorrow
            return (optimal_hour, optimal_minute)
        
        return (optimal_hour, optimal_minute)
    
    def get_system_usage_report(self) -> Dict:
        """Generate a report of system usage patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get hourly averages by day of week
        cursor.execute('''
        SELECT day_of_week, hour, 
               AVG(cpu_percent + memory_percent + disk_io_percent) as total_load
        FROM system_usage
        GROUP BY day_of_week, hour
        ORDER BY day_of_week, hour
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        # Organize by day of week
        days = {i: {} for i in range(7)}  # 0=Monday, 6=Sunday
        for day, hour, load in results:
            days[day][hour] = load
            
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        report = {day_names[i]: hours for i, hours in days.items()}
        
        return report

class Scheduler:
    """Main scheduler class that manages tasks and their execution"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the scheduler"""
        self.base_dir = base_dir if base_dir else os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.tasks_file = os.path.join(self.data_dir, 'scheduled_tasks.json')
        self.db_path = os.path.join(self.data_dir, 'scheduler.db')
        
        self.tasks = self._load_tasks()
        self.running = False
        self.run_thread = None
        self.lock = threading.RLock()
        
        # Initialize pattern analyzer
        self.analyzer = UsagePatternAnalyzer(self.db_path)
        
    def _load_tasks(self) -> Dict[str, Task]:
        """Load tasks from storage"""
        if not os.path.exists(self.tasks_file):
            return {}
            
        try:
            with open(self.tasks_file, 'r') as f:
                task_dicts = json.load(f)
                
            tasks = {}
            for task_dict in task_dicts:
                task = Task.from_dict(task_dict)
                tasks[task.task_id] = task
                
            return tasks
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return {}
            
    def _save_tasks(self):
        """Save tasks to storage"""
        try:
            task_dicts = [task.to_dict() for task in self.tasks.values()]
            with open(self.tasks_file, 'w') as f:
                json.dump(task_dicts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            
    def add_task(self, task: Task) -> str:
        """Add a new task to the scheduler"""
        with self.lock:
            self.tasks[task.task_id] = task
            self._save_tasks()
            logger.info(f"Added task: {task.name} (ID: {task.task_id})")
            return task.task_id
            
    def update_task(self, task: Task) -> bool:
        """Update an existing task"""
        with self.lock:
            if task.task_id not in self.tasks:
                logger.warning(f"Cannot update nonexistent task: {task.task_id}")
                return False
                
            self.tasks[task.task_id] = task
            self._save_tasks()
            logger.info(f"Updated task: {task.name} (ID: {task.task_id})")
            return True
            
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the scheduler"""
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"Cannot remove nonexistent task: {task_id}")
                return False
                
            task = self.tasks.pop(task_id)
            self._save_tasks()
            logger.info(f"Removed task: {task.name} (ID: {task.task_id})")
            return True
            
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
        
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return list(self.tasks.values())
        
    def get_due_tasks(self) -> List[Task]:
        """Get all tasks that are due to run"""
        return [task for task in self.tasks.values() if task.enabled and task.is_due()]
        
    def get_upcoming_tasks(self, limit: int = 5) -> List[Dict]:
        """Get upcoming tasks with their next run times"""
        tasks_with_times = []
        for task in self.tasks.values():
            if not task.enabled:
                continue
                
            next_run = task.get_next_run_time()
            if next_run:
                tasks_with_times.append({
                    'task_id': task.task_id,
                    'name': task.name,
                    'next_run': next_run
                })
                
        # Sort by next run time
        tasks_with_times.sort(key=lambda x: x['next_run'])
        return tasks_with_times[:limit]
        
    def create_adaptive_task(self, name: str, path: str, instruction: str) -> Task:
        """Create a task with adaptive scheduling based on system usage patterns"""
        # Find optimal hour and minute
        optimal_hour, optimal_minute = self.analyzer.find_optimal_time(path)
        
        # Create a scheduled time object
        now = datetime.datetime.now()
        scheduled_time = now.replace(
            hour=optimal_hour, 
            minute=optimal_minute,
            second=0,
            microsecond=0
        )
        
        # If the time is in the past, schedule for tomorrow
        if scheduled_time < now:
            scheduled_time += datetime.timedelta(days=1)
            
        # Create the task (using daily schedule type)
        task = Task(
            name=name,
            path=path,
            instruction=instruction,
            schedule_type='daily',
            scheduled_time=scheduled_time,
            resource_limit=30,  # Lower resource limit for adaptive tasks
            priority=1,
            enabled=True
        )
        
        return task
        
    def execute_task(self, task: Task) -> bool:
        """Execute a scheduled task"""
        logger.info(f"Executing task: {task.name} (ID: {task.task_id})")
        
        try:
            # Execute the file organization command
            # Here we're using the same structure as the chat API call
            api_request = {
                "path": task.path,
                "instruction": task.instruction,
                "incognito": False,
                "resource_limit": task.resource_limit
            }
            
            server_url = "http://localhost:8000/chat"
            
            # Use subprocess to call curl or similar to make the API request
            # For Windows
            if os.name == 'nt':
                curl_cmd = [
                    "curl", "-X", "POST", 
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(api_request),
                    server_url
                ]
                subprocess.run(curl_cmd, check=True)
            else:
                # For Unix systems
                import requests
                requests.post(server_url, json=api_request)
                
            # Update last_run time
            task.last_run = datetime.datetime.now()
            self.update_task(task)
            
            logger.info(f"Task executed successfully: {task.name}")
            return True
        except Exception as e:
            logger.error(f"Error executing task {task.name}: {e}")
            return False
            
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
            
        self.running = True
        self.analyzer.start_collection()
        self.run_thread = threading.Thread(target=self._run_loop)
        self.run_thread.daemon = True
        self.run_thread.start()
        logger.info("Scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        self.analyzer.stop_collection()
        if self.run_thread:
            self.run_thread.join(timeout=5.0)
        logger.info("Scheduler stopped")
        
    def _run_loop(self):
        """Main scheduler loop that checks and executes due tasks"""
        while self.running:
            try:
                # Get tasks that are due
                due_tasks = self.get_due_tasks()
                
                # Execute due tasks
                for task in due_tasks:
                    self.execute_task(task)
                
                # Sleep for a short time to avoid excessive CPU usage
                # We check frequently for precision
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in scheduler run loop: {e}")
                time.sleep(60)  # Sleep longer after error
                
    def create_common_task(self, task_type: str, path: str = None) -> Task:
        """Create a common predefined task based on type"""
        now = datetime.datetime.now()
        
        if task_type == 'daily_cleanup':
            # Set time to 2 AM
            scheduled_time = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if scheduled_time < now:
                scheduled_time += datetime.timedelta(days=1)
                
            return Task(
                name="Daily Cleanup",
                path=path or os.path.join(os.path.expanduser("~"), "Downloads"),
                instruction="Move all files older than 7 days into an Archive folder. Group files by type into Documents, Images, Videos, and Other categories.",
                schedule_type="daily",
                scheduled_time=scheduled_time,
                resource_limit=40,
                priority=2,
                enabled=True
            )
            
        elif task_type == 'weekly_organization':
            # Schedule for Sunday at 3 AM
            days_until_sunday = 6 - now.weekday() if now.weekday() != 6 else 7
            sunday = now.date() + datetime.timedelta(days=days_until_sunday)
            scheduled_time = datetime.datetime.combine(sunday, datetime.time(3, 0))
            
            return Task(
                name="Weekly Deep Organization",
                path=path or os.path.join(os.path.expanduser("~"), "Documents"),
                instruction="Perform deep organization of all files. Create content-based categories and move files based on their content and type. Rename files with inconsistent naming patterns to follow a standard format.",
                schedule_type="weekly",
                scheduled_time=scheduled_time,
                days_of_week=[6],  # Sunday
                resource_limit=70,
                priority=3,
                enabled=True
            )
            
        elif task_type == 'monthly_archive':
            # Schedule for 1st of next month
            if now.month == 12:
                next_month = datetime.date(now.year + 1, 1, 1)
            else:
                next_month = datetime.date(now.year, now.month + 1, 1)
                
            scheduled_time = datetime.datetime.combine(next_month, datetime.time(4, 0))
            
            return Task(
                name="Monthly Archiving",
                path=path or os.path.join(os.path.expanduser("~")),
                instruction="Archive files that haven't been accessed in 3 months. Compress large files and folders. Generate a report of disk space usage and cleanup recommendations.",
                schedule_type="monthly",
                scheduled_time=scheduled_time,
                day_of_month=1,
                resource_limit=60,
                priority=2,
                enabled=True
            )
            
        else:
            # Default to an adaptive nightly task
            return self.create_adaptive_task(
                name="Smart Maintenance",
                path=path or os.path.join(os.path.expanduser("~"), "Documents"),
                instruction="Organize loose files into appropriate folders based on content and file type. Remove empty directories. Create logical category structure."
            )

# Script execution section
def main():
    """Command-line interface for the scheduler"""
    scheduler = Scheduler()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Sorting Hat Task Scheduler")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the scheduler")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the scheduler")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all tasks")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("--name", required=True, help="Task name")
    add_parser.add_argument("--path", required=True, help="Path to organize")
    add_parser.add_argument("--instruction", required=True, help="Organization instruction")
    add_parser.add_argument("--type", choices=["once", "daily", "weekly", "monthly", "adaptive"], 
                           default="once", help="Schedule type")
    add_parser.add_argument("--time", help="Time in HH:MM format")
    add_parser.add_argument("--days", help="Days of week (0-6, comma separated)")
    add_parser.add_argument("--day", type=int, help="Day of month")
    add_parser.add_argument("--priority", type=int, default=1, help="Priority (1-3)")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a task")
    remove_parser.add_argument("task_id", help="Task ID to remove")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a task immediately")
    run_parser.add_argument("task_id", help="Task ID to run")
    
    # Add common task
    common_parser = subparsers.add_parser("common", help="Add a common predefined task")
    common_parser.add_argument("type", choices=["daily_cleanup", "weekly_organization", "monthly_archive", "smart"],
                              help="Type of common task")
    common_parser.add_argument("--path", help="Optional path to organize")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate a system usage report")
    
    args = parser.parse_args()
    
    try:
        # Handle commands
        if args.command == "start":
            scheduler.start()
            print("Scheduler started")
            
        elif args.command == "stop":
            scheduler.stop()
            print("Scheduler stopped")
            
        elif args.command == "list":
            tasks = scheduler.get_all_tasks()
            if not tasks:
                print("No tasks scheduled")
            else:
                print(f"{'ID':<36} {'Name':<20} {'Next Run':<20} {'Status'}")
                print("-" * 80)
                for task in tasks:
                    next_run = task.get_next_run_time()
                    next_run_str = next_run.strftime("%Y-%m-%d %H:%M") if next_run