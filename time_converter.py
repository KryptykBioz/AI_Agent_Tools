#!/usr/bin/env python3
"""
Memory JSON Timestamp Converter
Converts timestamp properties in memory.json from ISO format to readable format.
"""

import json
import re
from datetime import datetime
from pathlib import Path
import sys


def is_iso_timestamp(timestamp_str):
    """Check if timestamp is in ISO format (e.g., 2025-05-11T21:49:50.973606)"""
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$'
    return bool(re.match(iso_pattern, timestamp_str))


def convert_iso_to_readable(iso_timestamp):
    """Convert ISO timestamp to readable format"""
    try:
        # Parse the ISO timestamp
        if '.' in iso_timestamp:
            dt = datetime.fromisoformat(iso_timestamp)
        else:
            dt = datetime.fromisoformat(iso_timestamp)
        
        # Format as: Sunday, June 01, 2025 at 07:20 AM UTC
        formatted = dt.strftime("%A, %B %d, %Y at %I:%M %p UTC")
        return formatted
    except ValueError as e:
        print(f"Error parsing timestamp '{iso_timestamp}': {e}")
        return iso_timestamp  # Return original if parsing fails


def process_memory_file(file_path):
    """Process the memory.json file and convert timestamps"""
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("Error: memory.json should contain a list of message objects")
            return False
        
        converted_count = 0
        
        # Process each message entry
        for entry in data:
            if isinstance(entry, dict) and 'timestamp' in entry:
                timestamp = entry['timestamp']
                
                # Only convert if it's in ISO format
                if is_iso_timestamp(timestamp):
                    converted_timestamp = convert_iso_to_readable(timestamp)
                    entry['timestamp'] = converted_timestamp
                    converted_count += 1
                    print(f"Converted: {timestamp} -> {converted_timestamp}")
        
        # Write back to file with pretty formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nConversion complete!")
        print(f"Total entries processed: {len(data)}")
        print(f"Timestamps converted: {converted_count}")
        print(f"File saved: {file_path}")
        
        return True
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main function"""
    # Default file path
    file_path = "memory.json"
    
    # Allow custom file path as command line argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    print(f"Memory JSON Timestamp Converter")
    print(f"Processing file: {file_path}")
    print("-" * 50)
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' does not exist")
        print(f"Usage: python {sys.argv[0]} [path_to_memory.json]")
        sys.exit(1)
    
    # Create backup
    backup_path = f"{file_path}.backup"
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"Backup created: {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup - {e}")
    
    # Process the file
    success = process_memory_file(file_path)
    
    if success:
        print(f"\n✅ Successfully converted timestamps in {file_path}")
    else:
        print(f"\n❌ Failed to process {file_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()