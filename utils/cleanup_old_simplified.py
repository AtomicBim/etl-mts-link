#!/usr/bin/env python3
"""
Script to remove old simplified CSV files (keep only the latest ones)
"""
import os
import glob

# Get archive path (go up one directory from utils/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(project_root, "data")
archive_path = os.path.join(data_path, "chats_archive")

# Find all simplified CSV files
pattern = os.path.join(archive_path, "*_simplified.csv")
all_files = glob.glob(pattern)

print(f"Found {len(all_files)} simplified CSV files")

# Get the latest timestamp from filenames
if all_files:
    # Extract timestamps
    timestamps = []
    for filepath in all_files:
        filename = os.path.basename(filepath)
        # Extract timestamp part (YYYYMMDD_HHMMSS)
        parts = filename.split('_')
        if len(parts) >= 3:
            # Last two parts before .simplified.csv should be date and time
            try:
                timestamp = f"{parts[-3]}_{parts[-2]}"  # YYYYMMDD_HHMMSS
                timestamps.append((filepath, timestamp))
            except:
                pass

    if timestamps:
        # Find the latest timestamp
        latest_timestamp = max(ts[1] for ts in timestamps)
        print(f"Latest timestamp found: {latest_timestamp}")

        # Remove all files that don't have the latest timestamp
        removed_count = 0
        for filepath, timestamp in timestamps:
            if timestamp != latest_timestamp:
                try:
                    os.remove(filepath)
                    print(f"Removed: {os.path.basename(filepath)}")
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {filepath}: {e}")

        print(f"\nTotal removed: {removed_count} old files")
        print(f"Kept: {len(timestamps) - removed_count} files with latest timestamp")
    else:
        print("No valid timestamps found in filenames")
else:
    print("No simplified CSV files found")