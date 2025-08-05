#!/usr/bin/env python3
"""
Cache Monitor - Production tool for managing and debugging cache issues
Usage: python cache_monitor.py [command] [batch_name]
Commands: info, clear-batch, clear-all, test-batch
"""

import sys
from app.services.api_service import ApiService

def main():
    if len(sys.argv) < 2:
        print("Usage: python cache_monitor.py [command] [batch_name]")
        print("Commands:")
        print("  info                    - Show cache information")
        print("  clear-batch [batch]     - Clear cache for specific batch")
        print("  clear-all               - Clear all cache")
        print("  test-batch [batch]      - Test fresh query for batch")
        return
    
    command = sys.argv[1]
    api = ApiService()
    
    if command == "info":
        info = api.get_cache_info()
        print("=== Cache Information ===")
        print(f"Cache file: {info['cache_file']}")
        print(f"Cache exists: {info['cache_exists']}")
        print(f"Last fetch: {info['last_fetch_time']}")
        print(f"Cache valid: {info['is_valid']}")
        print("\nCached batches:")
        for batch_info in info['cached_batches']:
            status = "✅" if batch_info['student_count'] > 0 else "⚠️"
            print(f"  {status} {batch_info['batch']}: {batch_info['student_count']} students")
    
    elif command == "clear-batch":
        if len(sys.argv) < 3:
            print("Error: Please specify batch name")
            return
        batch = sys.argv[2]
        api.clear_cache_for_batch(batch)
    
    elif command == "clear-all":
        api.clear_all_cache()
    
    elif command == "test-batch":
        if len(sys.argv) < 3:
            print("Error: Please specify batch name")
            return
        batch = sys.argv[2]
        print(f"=== Testing fresh query for {batch} ===")
        try:
            result = api.get_students_by_batch(batch)
            student_count = len(result.get('students', []))
            print(f"Result: {student_count} students")
            if student_count > 0:
                print(f"First student: {result['students'][0].get('name', 'N/A')}")
        except Exception as e:
            print(f"Error: {e}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main() 