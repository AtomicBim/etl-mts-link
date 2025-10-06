#!/usr/bin/env python3
"""
Script to recreate chats_with_messages CSV from simplified files
"""
import os
import csv
import glob
from datetime import datetime

# Paths
data_path = os.path.join(os.path.dirname(__file__), "data")
archive_path = os.path.join(data_path, "chats_archive")

# Find all simplified CSV files
pattern = os.path.join(archive_path, "*_simplified.csv")
simplified_csvs = glob.glob(pattern)
print(f"Found {len(simplified_csvs)} simplified chat CSV files")

if not simplified_csvs:
    print("No simplified CSV files found")
    exit(1)

# Merge data (only selected fields)
merged_rows = []
for csv_file in simplified_csvs:
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Keep only essential fields
                merged_row = {
                    'chat_id': row.get('chat_id', ''),
                    'chat_name': row.get('chat_name', ''),
                    'authorId': row.get('authorId', ''),
                    'full_name': row.get('full_name', ''),
                    'text': row.get('text', ''),
                    'createdAt': row.get('createdAt', '')
                }
                merged_rows.append(merged_row)
    except Exception as e:
        print(f"Warning: Could not process {os.path.basename(csv_file)}: {e}")

if not merged_rows:
    print("No rows to save")
    exit(1)

# Save merged CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"chats_with_messages_{timestamp}.csv"
filepath = os.path.join(data_path, filename)

try:
    fieldnames = ['chat_id', 'chat_name', 'authorId', 'full_name', 'text', 'createdAt']

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_rows)

    print(f"Combined messages file saved to: {filepath}")
    print(f"Total rows: {len(merged_rows)}")
except Exception as e:
    print(f"Error saving combined file: {e}")
    exit(1)