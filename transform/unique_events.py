import sys
import os
import csv
import glob
from typing import Set, Dict, List, Any, Optional
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract.link_events_extractors
from abstractions.extract import UniversalExtractor


class UniqueEventsTransformer:
    """Transformer for extracting and deduplicating unique events from organization"""

    # Configuration constants
    DEFAULT_TEST_USERS = 10
    USER_ID_KEYS = ['chatUserId', 'userId', 'id']
    EVENT_SESSION_ID_KEYS = ['eventSessionId', 'id', 'guid']

    def __init__(self, extraction_path: str = None):
        # Default to data directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_data_path = os.path.join(project_root, "data")

        if extraction_path:
            self.extraction_path = extraction_path
        else:
            # Always prefer the data directory over environment variable
            self.extraction_path = default_data_path
        
        self.unique_events: Set[str] = set()
        self.events_data: List[Dict[str, Any]] = []
        
        # Initialize extractors
        self.members_extractor = UniversalExtractor("/chats/organization/members")
        self.user_events_extractor = UniversalExtractor("/users/{userID}/events/schedule")
        self.org_events_extractor = UniversalExtractor("/organization/events/schedule")

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
                elif isinstance(items, dict) and 'eventSessions' in items:
                    result = items['eventSessions']
                elif isinstance(items, list):
                    result = items
                else:
                    result = []
            elif 'items' in data:
                result = data['items']
            elif 'eventSessions' in data:
                result = data['eventSessions']
            elif 'events' in data:
                result = data['events']
            else:
                result = [data] if data_type == "user events" else []

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

    def get_organization_members(self) -> List[Dict[str, Any]]:
        """Extract organization members using extractor"""
        print("Extracting organization members...")
        data = self.members_extractor.extract()
        return self._extract_items_from_response(data, "organization members")

    def get_organization_events(self, from_date: str, to_date: str = None, page: int = 1, per_page: int = 250) -> List[Dict[str, Any]]:
        """Get events for organization within date range"""
        print(f"Extracting organization events from {from_date}...")
        
        params = {
            'from': from_date,
            'page': page,
            'perPage': per_page
        }
        
        if to_date:
            params['to'] = to_date
        
        data = self.org_events_extractor.extract(**params)
        return self._extract_items_from_response(data, "organization events")

    def get_user_events(self, user_id: str, from_date: str, to_date: str = None) -> List[Dict[str, Any]]:
        """Get events for a specific user using extractor"""
        params = {
            'userID': user_id,
            'from': from_date
        }
        
        if to_date:
            params['to'] = to_date
        
        data = self.user_events_extractor.extract(**params)
        return self._extract_items_from_response(data, "user events")
    
    def _create_event_record(self, event: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """Create standardized event record from event data"""
        return {
            'event_session_id': self._extract_id_from_dict(event, self.EVENT_SESSION_ID_KEYS) or event.get('eventSessionId', ''),
            'event_id': event.get('eventId', ''),
            'name': event.get('name', ''),
            'description': event.get('description', ''),
            'status': event.get('status', ''),
            'start_time': event.get('startTime', '') or event.get('startsAt', ''),
            'end_time': event.get('endTime', '') or event.get('endsAt', ''),
            'duration_minutes': self._calculate_duration(event.get('startTime') or event.get('startsAt'), event.get('endTime') or event.get('endsAt')),
            'owner_id': event.get('ownerId', '') or event.get('createUserId', ''),
            'organization_id': event.get('organizationId', ''),
            'is_public': event.get('isPublic', ''),
            'is_recurring': event.get('isRecurring', False),
            'max_participants': event.get('maxParticipants', ''),
            'event_type': event.get('type', ''),
            'discovered_via_user_id': user_id or '',
            'extraction_timestamp': datetime.now().isoformat()
        }

    def _calculate_duration(self, start_time: str, end_time: str) -> int:
        """Calculate event duration in minutes from timestamps"""
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

    def collect_unique_events_from_users(self, from_date: str, to_date: str = None, 
                                        test_mode: bool = False, max_users: int = None) -> None:
        """Collect unique events by querying each user's schedule"""
        print("Starting unique events collection from users...")

        members = self.get_organization_members()
        if not members:
            print("No organization members found")
            return

        # Apply test mode limits
        if test_mode:
            max_users = max_users or self.DEFAULT_TEST_USERS
            members = members[:max_users]
            print(f"TEST MODE: Processing only first {len(members)} organization members...")
        else:
            print(f"Processing {len(members)} organization members...")

        processed_count = 0
        for member in members:
            user_id = self._extract_id_from_dict(member, self.USER_ID_KEYS)

            if not user_id:
                print(f"No user ID found in member data: {member}")
                continue

            processed_count += 1
            print(f"Processing user {processed_count}/{len(members)}: {user_id}")

            events = self.get_user_events(user_id, from_date, to_date)
            if not events:
                continue

            for event in events:
                event_session_id = self._extract_id_from_dict(event, self.EVENT_SESSION_ID_KEYS)

                if not event_session_id:
                    print(f"No event session ID found in event data: {event}")
                    continue

                if event_session_id not in self.unique_events:
                    self.unique_events.add(event_session_id)
                    event_data = self._create_event_record(event, user_id)
                    self.events_data.append(event_data)

        print(f"Collected {len(self.unique_events)} unique events")

    def collect_unique_events_from_organization(self, from_date: str, to_date: str = None,
                                               max_pages: int = 10) -> None:
        """Collect unique events by querying organization schedule (alternative method)"""
        print("Starting unique events collection from organization schedule...")

        page = 1
        per_page = 250
        
        while page <= max_pages:
            print(f"Fetching page {page}/{max_pages}...")
            
            events = self.get_organization_events(from_date, to_date, page, per_page)
            
            if not events:
                print(f"No more events found on page {page}")
                break

            for event in events:
                # Extract event sessions from nested structure
                event_sessions = event.get('eventSessions', [])
                
                # If no event sessions, treat the event itself as a session
                if not event_sessions:
                    event_sessions = [event]
                
                for session in event_sessions:
                    event_session_id = self._extract_id_from_dict(session, self.EVENT_SESSION_ID_KEYS)

                    if not event_session_id:
                        print(f"No event session ID found in session data: {session}")
                        continue

                    if event_session_id not in self.unique_events:
                        self.unique_events.add(event_session_id)
                        # Get owner from session or fall back to event createUserId
                        owner_id = session.get('createUserId', '') or event.get('createUserId', '')
                        # Merge session and event data, prioritizing session data
                        merged_data = {**event, **session, 'createUserId': owner_id}
                        event_data = self._create_event_record(merged_data)
                        self.events_data.append(event_data)
            
            # Check if there are more pages
            if len(events) < per_page:
                print(f"Received {len(events)} events (less than {per_page}), reached last page")
                break
            
            page += 1

        print(f"Collected {len(self.unique_events)} unique events")

    def _find_existing_files(self, base_filename: str) -> List[str]:
        """Find existing files with the same base name but different timestamps"""
        if not base_filename:
            return []

        # Extract base name without timestamp and extension
        if base_filename.startswith("unique_events_") and base_filename.endswith(".csv"):
            pattern = "unique_events_*.csv"
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
            if "unique_events_" in filename:
                try:
                    # Format: unique_events_YYYYMMDD_HHMMSS.csv
                    timestamp_part = filename.replace("unique_events_", "").replace(".csv", "")
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
        """Save unique events data to CSV file with timestamp-based overwrite protection"""
        if not self.events_data:
            print("No event data to save")
            return None

        # Generate timestamp for new file
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not filename:
            filename = f"unique_events_{current_timestamp}.csv"
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
        headers = list(self.events_data[0].keys()) if self.events_data else []

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.events_data)

            print(f"Unique events saved to: {filepath}")
            print(f"Total unique events: {len(self.events_data)}")
            return filepath

        except Exception as e:
            print(f"Error saving CSV file: {e}")
            return None


def main():
    """Main function to run the unique events transformer"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract unique events from organization')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--from-date', '-f',
                       help='Start date for events (format: YYYY-MM-DD+HH:MM:SS or YYYY-MM-DD)')
    parser.add_argument('--to-date', '-t',
                       help='End date for events (format: YYYY-MM-DD+HH:MM:SS or YYYY-MM-DD)')
    parser.add_argument('--method', '-m', choices=['users', 'organization'], default='organization',
                       help='Collection method: users (query each user) or organization (query org schedule)')
    parser.add_argument('--test', action='store_true',
                       help=f'Test mode - process only first {UniqueEventsTransformer.DEFAULT_TEST_USERS} users (only for users method)')
    parser.add_argument('--max-users', type=int, help='Maximum number of users to process in test mode')
    parser.add_argument('--max-pages', type=int, default=10,
                       help='Maximum pages to fetch for organization method (default: 10)')
    parser.add_argument('--help-fields', action='store_true',
                       help='Show description of CSV fields')
    parser.add_argument('--last-days', type=int,
                       help='Shortcut: extract events from last N days (overrides --from-date)')

    args = parser.parse_args()

    if args.help_fields:
        print("\nCSV Fields Description:")
        fields_description = {
            "event_session_id": "Unique identifier of the event session",
            "event_id": "ID of the parent event (for recurring events)",
            "name": "Name of the event",
            "description": "Event description",
            "status": "Event status (ACTIVE, START, STOP, etc.)",
            "start_time": "Event start timestamp",
            "end_time": "Event end timestamp",
            "duration_minutes": "Calculated event duration in minutes",
            "owner_id": "ID of the event owner/creator",
            "organization_id": "ID of the organization",
            "is_public": "Whether the event is public",
            "is_recurring": "Whether this is a recurring event",
            "max_participants": "Maximum number of participants allowed",
            "event_type": "Type of event",
            "discovered_via_user_id": "User ID through which this event was discovered (users method only)",
            "extraction_timestamp": "When this record was extracted"
        }

        for field, description in fields_description.items():
            print(f"- {field}: {description}")
        return

    # Validate that either --from-date or --last-days is provided
    if not args.from_date and not args.last_days:
        parser.error("Either --from-date/-f or --last-days must be specified")

    transformer = UniqueEventsTransformer()

    # Calculate from_date
    if args.last_days:
        from_datetime = datetime.now() - timedelta(days=args.last_days)
        from_date = from_datetime.strftime("%Y-%m-%d+00:00:00")
        print(f"Using calculated from_date (last {args.last_days} days): {from_date}")
    else:
        from_date = args.from_date
        # Add time if not provided
        if '+' not in from_date and ' ' not in from_date:
            from_date = f"{from_date}+00:00:00"

    to_date = args.to_date
    if to_date and '+' not in to_date and ' ' not in to_date:
        to_date = f"{to_date}+23:59:59"

    # Choose collection method
    if args.method == 'users':
        max_users = args.max_users if args.test and args.max_users else None
        transformer.collect_unique_events_from_users(from_date, to_date, 
                                                    test_mode=args.test, max_users=max_users)
    else:
        transformer.collect_unique_events_from_organization(from_date, to_date, 
                                                           max_pages=args.max_pages)

    if transformer.events_data:
        result = transformer.save_to_csv(args.output)
        if result:
            print(f"\nUnique events extraction completed successfully: {result}")
        else:
            print("Failed to save results")
    else:
        print("No unique events found")


if __name__ == "__main__":
    main()

