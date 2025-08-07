#!/usr/bin/env python3
"""
MCP Server Integration Test
This script tests the MCP server's basic functionality.
"""
import os
import sys
import json
import time
import requests
from typing import Dict, Any

def test_mcp_server(base_url: str = "http://localhost:8080") -> bool:
    """Test basic MCP server functionality."""
    test_endpoints = [
        "/health",
        "/api/status",
        "/api/features"
    ]
    
    print("🔍 Testing MCP Server Endpoints:")
    print("=" * 50)
    
    all_tests_passed = True
    
    for endpoint in test_endpoints:
        try:
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            response = requests.get(url, timeout=5)
            status = "✓" if response.status_code == 200 else "✗"
            color = "\033[92m" if status == "✓" else "\033[91m"
            print(f"{color}{status} {endpoint} (Status: {response.status_code})\033[0m")
            
            if response.status_code != 200:
                all_tests_passed = False
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"\033[91m✗ {endpoint} - Error: {str(e)}\033[0m")
            all_tests_passed = False
    
    return all_tests_passed

def main() -> None:
    print("🚀 Starting MCP Server Integration Tests")
    print("=" * 50)
    
    # Test server connectivity
    if test_mcp_server():
        print("\n✅ All MCP server tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some MCP server tests failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
