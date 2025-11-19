import sys
import os
import csv
import glob
from typing import Set, Dict, List, Any, Optional
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract.link_events_extractors
from abstractions.extract import UniversalExtractor


class EndlessActivitiesTransformer:
    """Transformer for extracting and deduplicating activities from endless events (permanent meetings)"""

    # Configuration constants
    ACTIVITY_ID_KEYS = ['id', 'activityId', 'guid']
    EVENT_SESSION_ID_KEYS = ['eventSessionId', 'sessionId', 'id']
    USER_ID_KEYS = ['userId', 'id']

    def __init__(self, extraction_path: str = None):
        # Default to data directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_data_path = os.path.join(project_root, "data")

        if extraction_path:
            self.extraction_path = extraction_path
        else:
            self.extraction_path = default_data_path
        
        self.unique_activities: Set[str] = set()
        self.activities_data: List[Dict[str, Any]] = []
        
        # Initialize extractors
        self.endless_activities_extractor = UniversalExtractor("/eventsessions/endless/activities")
        self.endless_events_extractor = UniversalExtractor("/eventsessions/endless")

    def _extract_items_from_response(self, data: Any, data_type: str) -> List[Dict[str, Any]]:
        """Extract items from API response with unified logic"""
        if not data:
            print(f"Failed to extract {data_type}")
            return []

        if isinstance(data, list):
            print(f"Found {len(data)} {data_type}")
            return data

        if isinstance(data, dict):
            # Try different possible structures
            if 'data' in data:
                items = data['data']
                if isinstance(items, dict) and 'items' in items:
                    result = items['items']
                elif isinstance(items, dict) and 'activities' in items:
                    result = items['activities']
                elif isinstance(items, dict) and 'eventSessions' in items:
                    result = items['eventSessions']
                elif isinstance(items, list):
                    result = items
                else:
                    result = []
            elif 'items' in data:
                result = data['items']
            elif 'activities' in data:
                result = data['activities']
            elif 'eventSessions' in data:
                result = data['eventSessions']
            else:
                result = []

            print(f"Found {len(result)} {data_type}")
            return result

        print(f"Unexpected data structure for {data_type}: {type(data)}")
        return []

    def _extract_id_from_dict(self, data: Dict[str, Any], id_keys: List[str]) -> str:
        """Extract ID from dictionary using multiple possible keys"""
        for key in id_keys:
            if key in data and data[key]:
                return str(data[key])
        return None

    def get_endless_activities(self, from_date: str = None, to_date: str = None, 
                               page: int = 1, per_page: int = 250) -> List[Dict[str, Any]]:
        """Get activities from endless events within date range"""
        params = {
            'page': page,
            'perPage': per_page
        }
        
        if from_date:
            params['from'] = from_date
            print(f"Extracting endless activities from {from_date}...")
        else:
            print("Extracting endless activities (no date filter)...")
        
        if to_date:
            params['to'] = to_date
        
        data = self.endless_activities_extractor.extract(**params)
        return self._extract_items_from_response(data, "endless activities")

    def get_endless_events(self, page: int = 1, per_page: int = 250) -> List[Dict[str, Any]]:
        """Get list of endless events"""
        print(f"Extracting endless events list (page {page})...")
        
        params = {
            'page': page,
            'perPage': per_page
        }
        
        data = self.endless_events_extractor.extract(**params)
        return self._extract_items_from_response(data, "endless events")
    
    def _create_activity_record(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized activity record from activity data"""
        # Extract basic info
        activity_id = self._extract_id_from_dict(activity, self.ACTIVITY_ID_KEYS) or activity.get('id', '')
        
        # Try to extract start/end times from different possible fields
        start_time = activity.get('startTime') or activity.get('startedAt') or activity.get('createdAt', '')
        end_time = activity.get('endTime') or activity.get('finishedAt') or activity.get('endedAt', '')
        
        # Extract event session info (nested structure)
        event_session = activity.get('eventSession', {})
        endless_event_id = event_session.get('id', '')
        room_name = event_session.get('name', '') or activity.get('roomName', '') or activity.get('name', '')
        
        # Extract user_id and name from eventSession.createdBy (room owner)
        created_by = event_session.get('createdBy', {})
        user_id = created_by.get('id', '') or activity.get('userId', '')
        
        # Build user name from createdBy
        if created_by:
            first_name = created_by.get('name', '')
            last_name = created_by.get('secondName', '')
            patr_name = created_by.get('patrName', '')
            user_name = f"{first_name} {last_name}".strip() if first_name or last_name else ''
        else:
            user_name = ''
        
        # Get participants info
        participants = activity.get('participants', [])
        participants_count = len(participants) if participants else activity.get('participantsCount', 0)
        
        return {
            'activity_id': activity_id,
            'event_session_id': activity.get('eventSessionId', ''),
            'endless_event_id': endless_event_id,
            'user_id': user_id,
            'user_name': user_name,
            'activity_type': activity.get('type') or activity.get('activityType', ''),
            'status': activity.get('status', ''),
            'start_time': start_time,
            'end_time': end_time,
            'duration_minutes': self._calculate_duration(start_time, end_time),
            'participants_count': participants_count,
            'room_name': room_name,
            'is_recorded': activity.get('isRecorded', False),
            'extraction_timestamp': datetime.now().isoformat()
        }

    def _calculate_duration(self, start_time: str, end_time: str) -> int:
        """Calculate duration in minutes from timestamps"""
        try:
            if not start_time or not end_time:
                return 0
            
            # Parse timestamps (format: ISO 8601)
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration = (end_dt - start_dt).total_seconds() / 60
            return int(duration)
        except Exception as e:
            print(f"    Warning: Could not calculate duration: {e}")
            return 0

    def collect_endless_activities(self, from_date: str = None, to_date: str = None,
                                   max_pages: int = 100) -> None:
        """Collect unique activities from endless events with pagination"""
        print("Starting endless activities collection...")

        page = 1
        per_page = 250
        
        while page <= max_pages:
            print(f"Fetching page {page}/{max_pages}...")
            
            activities = self.get_endless_activities(from_date, to_date, page, per_page)
            
            if not activities:
                print(f"No more activities found on page {page}")
                break

            for activity in activities:
                activity_id = self._extract_id_from_dict(activity, self.ACTIVITY_ID_KEYS)

                if not activity_id:
                    # If no ID found, create composite key from available data
                    event_session_id = activity.get('eventSessionId', '')
                    start_time = activity.get('startTime') or activity.get('startedAt', '')
                    user_id = activity.get('userId', '')
                    activity_id = f"{event_session_id}_{user_id}_{start_time}"
                    
                    if not event_session_id and not start_time:
                        print(f"Skipping activity without identifiable data: {activity}")
                        continue

                if activity_id not in self.unique_activities:
                    self.unique_activities.add(activity_id)
                    activity_data = self._create_activity_record(activity)
                    self.activities_data.append(activity_data)
            
            # Check if there are more pages
            if len(activities) < per_page:
                print(f"Received {len(activities)} activities (less than {per_page}), reached last page")
                break
            
            page += 1

        print(f"Collected {len(self.unique_activities)} unique activities")

    def _find_existing_files(self, base_filename: str) -> List[str]:
        """Find existing files with the same base name but different timestamps"""
        if not base_filename:
            return []

        # Extract base name without timestamp and extension
        if base_filename.startswith("endless_activities_") and base_filename.endswith(".csv"):
            pattern = "endless_activities_*.csv"
        else:
            name_without_ext = os.path.splitext(base_filename)[0]
            pattern = f"{name_without_ext}*.csv"

        pattern_path = os.path.join(self.extraction_path, pattern)
        existing_files = glob.glob(pattern_path)
        return existing_files

    def _should_overwrite(self, existing_files: List[str], new_timestamp: str) -> Optional[str]:
        """Check if we should overwrite existing files based on timestamp"""
        if not existing_files:
            return None

        files_to_remove = []
        for file_path in existing_files:
            filename = os.path.basename(file_path)

            # Extract timestamp from filename
            if "endless_activities_" in filename:
                try:
                    # Format: endless_activities_YYYYMMDD_HHMMSS.csv
                    timestamp_part = filename.replace("endless_activities_", "").replace(".csv", "")
                    if len(timestamp_part) == 15 and "_" in timestamp_part:  # YYYYMMDD_HHMMSS
                        existing_datetime = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                        new_datetime = datetime.strptime(new_timestamp, "%Y%m%d_%H%M%S")

                        if new_datetime > existing_datetime:
                            files_to_remove.append(file_path)
                            print(f"Found older file to replace: {filename}")
                        else:
                            print(f"Newer file already exists: {filename}")
                            return file_path  # Don't overwrite newer file
                except ValueError:
                    # If timestamp parsing fails, keep the file
                    continue

        # Remove older files
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"Removed older file: {os.path.basename(file_path)}")
            except OSError as e:
                print(f"Warning: Could not remove {file_path}: {e}")

        return None

    def save_to_csv(self, filename: str = None) -> str:
        """Save endless activities data to CSV file with timestamp-based overwrite protection"""
        if not self.activities_data:
            print("No activity data to save")
            return None

        # Generate timestamp for new file
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not filename:
            filename = f"endless_activities_{current_timestamp}.csv"
        else:
            # If custom filename provided, still add timestamp if not present
            name, ext = os.path.splitext(filename)
            if not any(c.isdigit() for c in name):  # No timestamp in filename
                filename = f"{name}_{current_timestamp}{ext}"

        # Ensure data directory exists
        os.makedirs(self.extraction_path, exist_ok=True)

        # Check for existing files and handle overwrite
        existing_files = self._find_existing_files(filename)
        existing_file = self._should_overwrite(existing_files, current_timestamp)

        if existing_file:
            print(f"Skipping save - newer file already exists: {os.path.basename(existing_file)}")
            return existing_file

        filepath = os.path.join(self.extraction_path, filename)

        # Get headers from first record to ensure all fields are included
        headers = list(self.activities_data[0].keys()) if self.activities_data else []

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.activities_data)

            print(f"Endless activities saved to: {filepath}")
            print(f"Total unique activities: {len(self.activities_data)}")
            return filepath

        except Exception as e:
            print(f"Error saving CSV file: {e}")
            return None


def main():
    """Main function to run the endless activities transformer"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract activities from endless events (permanent meetings, p2p calls)')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--from-date', '-f',
                       help='Start date for activities (format: YYYY-MM-DD+HH:MM:SS or YYYY-MM-DD)')
    parser.add_argument('--to-date', '-t',
                       help='End date for activities (format: YYYY-MM-DD+HH:MM:SS or YYYY-MM-DD)')
    parser.add_argument('--max-pages', type=int, default=100,
                       help='Maximum pages to fetch (default: 100)')
    parser.add_argument('--help-fields', action='store_true',
                       help='Show description of CSV fields')
    parser.add_argument('--last-days', type=int,
                       help='Shortcut: extract activities from last N days (overrides --from-date)')

    args = parser.parse_args()

    if args.help_fields:
        print("\nCSV Fields Description:")
        fields_description = {
            "activity_id": "Unique identifier of the activity",
            "event_session_id": "ID of the event session",
            "endless_event_id": "ID of the parent endless event (permanent meeting)",
            "user_id": "ID of the user who initiated/participated",
            "activity_type": "Type of activity",
            "status": "Activity status",
            "start_time": "Activity start timestamp",
            "end_time": "Activity end timestamp",
            "duration_minutes": "Calculated activity duration in minutes",
            "participants_count": "Number of participants",
            "room_name": "Name of the meeting room/session",
            "is_recorded": "Whether the activity was recorded",
            "extraction_timestamp": "When this record was extracted"
        }

        for field, description in fields_description.items():
            print(f"- {field}: {description}")
        return

    transformer = EndlessActivitiesTransformer()

    # Calculate from_date
    from_date = None
    if args.last_days:
        from_datetime = datetime.now() - timedelta(days=args.last_days)
        from_date = from_datetime.strftime("%Y-%m-%d+00:00:00")
        print(f"Using calculated from_date (last {args.last_days} days): {from_date}")
    elif args.from_date:
        from_date = args.from_date
        # Add time if not provided
        if '+' not in from_date and ' ' not in from_date:
            from_date = f"{from_date}+00:00:00"

    to_date = args.to_date
    if to_date and '+' not in to_date and ' ' not in to_date:
        to_date = f"{to_date}+23:59:59"

    # Collect activities
    transformer.collect_endless_activities(from_date, to_date, max_pages=args.max_pages)

    if transformer.activities_data:
        result = transformer.save_to_csv(args.output)
        if result:
            print(f"\nEndless activities extraction completed successfully: {result}")
        else:
            print("Failed to save results")
    else:
        print("No activities found")


if __name__ == "__main__":
    main()

