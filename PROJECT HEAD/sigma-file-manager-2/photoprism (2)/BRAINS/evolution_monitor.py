"""
Evolution System Monitor

This script provides a simple command-line interface to monitor
and interact with the evolution system.
"""
import os
import sys
import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import requests
import argparse

# Constants
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'evolution.db')
API_BASE = "http://localhost:8000"

class EvolutionMonitor:
    def __init__(self):
        self.check_database()
        
    def check_database(self):
        """Check if the evolution database exists"""
        if not os.path.exists(DB_PATH):
            print("Evolution database not found at:", DB_PATH)
            print("Please run initialize_evolution.py first.")
            sys.exit(1)
    
    def check_server(self):
        """Check if the server is running"""
        try:
            response = requests.get(f"{API_BASE}/")
            return response.status_code == 200
        except:
            return False
    
    def get_evolution_report(self):
        """Get evolution report from the API"""
        try:
            response = requests.get(f"{API_BASE}/evolution/report")
            return response.json()
        except Exception as e:
            print(f"Failed to get evolution report: {e}")
            return None
    
    def get_patterns(self, min_confidence=0.5):
        """Get patterns from the API"""
        try:
            response = requests.get(f"{API_BASE}/evolution/patterns?min_confidence={min_confidence}")
            return response.json()
        except Exception as e:
            print(f"Failed to get patterns: {e}")
            return None
    
    def trigger_evolution(self, force_rebuild=False):
        """Trigger evolution process"""
        try:
            response = requests.post(
                f"{API_BASE}/evolution/trigger", 
                json={"force_rebuild": force_rebuild}
            )
            return response.json()
        except Exception as e:
            print(f"Failed to trigger evolution: {e}")
            return None
    
    def get_recent_recommendations(self, limit=10):
        """Get recent recommendations from the database"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            SELECT * FROM recommendations 
            ORDER BY timestamp DESC
            LIMIT ?
            ''',
            (limit,)
        )
        
        recommendations = []
        for row in cursor.fetchall():
            recommendations.append(dict(row))
        
        conn.close()
        return recommendations
    
    def display_patterns(self, patterns=None):
        """Display patterns in a readable format"""
        if patterns is None:
            patterns_data = self.get_patterns()
            if not patterns_data:
                print("No patterns available.")
                return
            patterns = patterns_data.get("patterns", [])
            
        if not patterns:
            print("No patterns available.")
            return
            
        print("\n=== Current Organization Patterns ===")
        for i, pattern in enumerate(patterns, 1):
            confidence = pattern.get("confidence", 0) * 100
            pattern_type = pattern.get("type", "unknown")
            data = pattern.get("data", {})
            
            if pattern_type == "extension":
                print(f"{i}. Extension: {data.get('extension', 'unknown')} → Directory: {data.get('directory', 'unknown')}")
                print(f"   Confidence: {confidence:.1f}% (Used {data.get('occurrences', 0)} times)")
            else:
                print(f"{i}. {pattern_type}: {json.dumps(data)}")
                print(f"   Confidence: {confidence:.1f}%")
        print()
    
    def display_report(self, report=None):
        """Display evolution report in a readable format"""
        if report is None:
            report = self.get_evolution_report()
            
        if not report:
            print("No report available.")
            return
            
        metrics = report.get("metrics", {})
        insights = report.get("insights", [])
        top_patterns = report.get("top_patterns", [])
            
        print("\n=== Evolution System Report ===")
        print(f"Total Recommendations: {metrics.get('total_recommendations', 0)}")
        print(f"Accepted Recommendations: {metrics.get('accepted_recommendations', 0)}")
        print(f"Acceptance Rate: {metrics.get('acceptance_rate', 0) * 100:.1f}%")
        print(f"Pattern Count: {metrics.get('pattern_count', 0)}")
        
        if insights:
            print("\nInsights:")
            for insight in insights:
                print(f"- {insight}")
        
        if top_patterns:
            print("\nTop Patterns:")
            self.display_patterns(top_patterns)
        print()
    
    def display_recommendations(self, recommendations=None):
        """Display recent recommendations"""
        if recommendations is None:
            recommendations = self.get_recent_recommendations()
            
        if not recommendations:
            print("No recommendations available.")
            return
            
        print("\n=== Recent Recommendations ===")
        for i, rec in enumerate(recommendations, 1):
            timestamp = rec.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            accepted = "✓" if rec.get("accepted", 0) == 1 else "✗"
            
            print(f"{i}. [{timestamp}] {accepted}")
            print(f"   From: {rec.get('src_path', '')}")
            print(f"   To: {rec.get('dst_path', '')}")
            
            feedback = rec.get("feedback", "")
            if feedback:
                print(f"   Feedback: {feedback}")
            print()
    
    def run_interactive(self):
        """Run interactive monitor"""
        if not self.check_server():
            print("Error: Server is not running.")
            print("Please start the server first with: uvicorn server:app --reload")
            return
            
        while True:
            print("\n=== Evolution System Monitor ===")
            print("1. View current patterns")
            print("2. View evolution report")
            print("3. View recent recommendations")
            print("4. Trigger evolution process")
            print("5. Open evolution dashboard")
            print("0. Exit")
            
            choice = input("\nEnter choice (0-5): ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.display_patterns()
            elif choice == "2":
                self.display_report()
            elif choice == "3":
                self.display_recommendations()
            elif choice == "4":
                print("\nTriggering evolution process...")
                result = self.trigger_evolution()
                if result:
                    print(f"Evolution complete! {result.get('new_patterns_count', 0)} new patterns discovered.")
                else:
                    print("Evolution failed.")
            elif choice == "5":
                dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evolution_dashboard.html")
                print(f"\nOpening dashboard: file://{dashboard_path}")
                import webbrowser
                webbrowser.open(f"file://{dashboard_path}")
            else:
                print("Invalid choice. Please try again.")
                
            if choice in ["1", "2", "3", "4"]:
                input("\nPress Enter to continue...")

def main():
    parser = argparse.ArgumentParser(description="Evolution System Monitor")
    parser.add_argument("--patterns", action="store_true", help="Display current patterns")
    parser.add_argument("--report", action="store_true", help="Display evolution report")
    parser.add_argument("--recommendations", action="store_true", help="Display recent recommendations")
    parser.add_argument("--evolve", action="store_true", help="Trigger evolution process")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    monitor = EvolutionMonitor()
    
    # If no args specified, default to interactive mode
    if not any([args.patterns, args.report, args.recommendations, args.evolve, args.interactive]):
        args.interactive = True
    
    if args.patterns:
        monitor.display_patterns()
    
    if args.report:
        monitor.display_report()
    
    if args.recommendations:
        monitor.display_recommendations()
    
    if args.evolve:
        print("Triggering evolution process...")
        result = monitor.trigger_evolution()
        if result:
            print(f"Evolution complete! {result.get('new_patterns_count', 0)} new patterns discovered.")
        else:
            print("Evolution failed.")
    
    if args.interactive:
        monitor.run_interactive()

if __name__ == "__main__":
    main()
