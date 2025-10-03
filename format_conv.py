#!/usr/bin/env python3
"""
Memory JSON Converter
Converts old format entries in memory.json to the new format.

Old format:
{
    "prompt": "user prompt",
    "response": "assistant response", 
    "timestamp": "datetime"
}

New format:
{
    "role": "user",
    "content": "user prompt",
    "timestamp": "datetime"
},
{
    "role": "assistant", 
    "content": "assistant response",
    "timestamp": "datetime"
}
"""

import json
import sys
import os
from datetime import datetime, timedelta
import argparse


def is_old_format(entry):
    """Check if an entry is in the old format."""
    return (isinstance(entry, dict) and 
            "prompt" in entry and 
            "response" in entry and 
            "timestamp" in entry and
            "role" not in entry)


def is_new_format(entry):
    """Check if an entry is in the new format."""
    return (isinstance(entry, dict) and 
            "role" in entry and 
            "content" in entry and 
            "timestamp" in entry)


def convert_entry(entry):
    """Convert a single old format entry to new format entries."""
    if not is_old_format(entry):
        return [entry]  # Return as-is if not old format
    
    timestamp = entry["timestamp"]
    
    # Create user entry
    user_entry = {
        "role": "user",
        "content": entry["prompt"],
        "timestamp": timestamp
    }
    
    # Create assistant entry (with same timestamp)
    assistant_entry = {
        "role": "assistant", 
        "content": entry["response"],
        "timestamp": timestamp
    }
    
    return [user_entry, assistant_entry]


def convert_memory_file(input_file, output_file=None, backup=True):
    """Convert memory.json file from old format to new format."""
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{input_file}': {e}")
        return False
    
    # Ensure data is a list
    if not isinstance(data, list):
        print(f"Error: Expected a list in '{input_file}', got {type(data).__name__}")
        return False
    
    # Create backup if requested
    if backup and output_file is None:
        backup_file = f"{input_file}.backup"
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Backup created: {backup_file}")
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
    
    # Convert entries
    converted_data = []
    old_format_count = 0
    new_format_count = 0
    
    for entry in data:
        if is_old_format(entry):
            old_format_count += 1
            converted_entries = convert_entry(entry)
            converted_data.extend(converted_entries)
        elif is_new_format(entry):
            new_format_count += 1
            converted_data.append(entry)
        else:
            print(f"Warning: Unrecognized entry format: {entry}")
            converted_data.append(entry)
    
    # Determine output file
    if output_file is None:
        output_file = input_file
    
    # Write the converted data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, indent=2, ensure_ascii=False)
        
        print(f"Conversion completed successfully!")
        print(f"- Converted {old_format_count} old format entries")
        print(f"- Preserved {new_format_count} new format entries")
        print(f"- Total entries in output: {len(converted_data)}")
        print(f"- Output written to: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert memory.json from old format to new format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python memory_converter.py memory.json
  python memory_converter.py memory.json -o converted_memory.json
  python memory_converter.py memory.json --no-backup
        """
    )
    
    parser.add_argument('input_file', 
                       help='Input JSON file to convert')
    parser.add_argument('-o', '--output', 
                       help='Output file (default: overwrite input file)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)
    
    success = convert_memory_file(
        args.input_file, 
        args.output, 
        backup=not args.no_backup
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()