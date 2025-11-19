import sys
import os
import csv
import json
import glob
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import UniversalExtractor


class EndlessActivitiesAnalyzer:
    """Analyzer for extracting detailed statistics from endless activities (p2p calls, spontaneous meetings)"""

    def __init__(self, data_path: str = None):
        # Default to data directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = data_path or os.path.join(project_root, "data")

        # Archive paths for full activity data
        self.archive_path = os.path.join(self.data_path, "endless_activities_archive")

        # Archive settings
        self.save_archives = True

        # Initialize extractors
        self.event_details_extractor = UniversalExtractor("/eventsessions/{eventsessionID}")
        self.event_participations_extractor = UniversalExtractor("/eventsessions/{eventSessionId}/participations")
        self.event_recordings_extractor = UniversalExtractor("/eventsessions/{eventSessionId}/recordings")
        self.transcript_list_extractor = UniversalExtractor("/eventsessions/{eventSessionId}/transcript/list")
        self.endless_events_extractor = UniversalExtractor("/eventsessions/endless")

        # Data storage
        self.activities_data: List[Dict[str, Any]] = []
        self.analysis_results: List[Dict[str, Any]] = []

        # Progress tracking
        self.processed_count = 0
        self.total_count = 0

        # User mapping for full names
        self.user_mapping: Dict[str, str] = {}
        self._load_user_mapping()

        # Cache for endless events details
        self.endless_events_cache: Dict[str, Dict[str, Any]] = {}
        self._load_endless_events()

    def _load_user_mapping(self):
        """Load user mapping from organization_members CSV"""
        try:
            # Find the most recent organization_members file
            pattern = os.path.join(self.data_path, "organization_members_*.csv")
            files = glob.glob(pattern)
            if not files:
                print("Warning: No organization_members CSV files found. User names will show as 'Unknown User'")
                return

            # Sort by modification time, get newest
            filepath = max(files, key=os.path.getmtime)
            print(f"Loading user mapping from: {os.path.basename(filepath)}")

            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    user_id = row.get('chatUserId', '')
                    first_name = row.get('firstName', '')
                    last_name = row.get('lastName', '')

                    # Build full name from firstName and lastName
                    if first_name or last_name:
                        full_name = f"{first_name} {last_name}".strip()
                    else:
                        full_name = "Unknown User"

                    if user_id:
                        self.user_mapping[user_id] = full_name

            print(f"Loaded {len(self.user_mapping)} user mappings")

        except Exception as e:
            print(f"Warning: Could not load user mapping: {e}")
            print("User names will show as 'Unknown User'")

    def _load_endless_events(self):
        """Load endless events list for reference"""
        try:
            print("Loading endless events list...")
            
            page = 1
            per_page = 250
            max_pages = 10
            
            while page <= max_pages:
                data = self.endless_events_extractor.extract(page=page, perPage=per_page)
                
                if not data:
                    break
                
                events = self._extract_items_from_response(data, "endless events")
                
                if not events:
                    break
                
                for event in events:
                    event_id = event.get('id') or event.get('eventId', '')
                    if event_id:
                        self.endless_events_cache[str(event_id)] = event
                
                if len(events) < per_page:
                    break
                
                page += 1
            
            print(f"Loaded {len(self.endless_events_cache)} endless events to cache")

        except Exception as e:
            print(f"Warning: Could not load endless events: {e}")

    def _extract_items_from_response(self, data: Any, data_type: str) -> List[Dict[str, Any]]:
        """Extract items from API response"""
        if not data:
            return []

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            if 'data' in data:
                items = data['data']
                if isinstance(items, dict) and 'items' in items:
                    return items['items']
                elif isinstance(items, dict) and 'eventSessions' in items:
                    return items['eventSessions']
                elif isinstance(items, list):
                    return items
            elif 'items' in data:
                return data['items']
            elif 'eventSessions' in data:
                return data['eventSessions']

        return []

    def load_endless_activities(self, filename: str = None) -> bool:
        """Load endless activities data from CSV file"""
        if filename:
            filepath = os.path.join(self.data_path, filename)
        else:
            # Find the most recent endless_activities file
            pattern = os.path.join(self.data_path, "endless_activities_*.csv")
            files = glob.glob(pattern)
            if not files:
                print("No endless activities CSV files found in data directory")
                return False

            # Sort by modification time, get newest
            filepath = max(files, key=os.path.getmtime)
            print(f"Using most recent endless activities file: {os.path.basename(filepath)}")

        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                self.activities_data = list(reader)

            print(f"Loaded {len(self.activities_data)} endless activities for analysis")
            self.total_count = len(self.activities_data)
            return True

        except Exception as e:
            print(f"Error loading endless activities file: {e}")
            return False

    def get_activity_details(self, event_session_id: str, viewer_id: str = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific event session"""
        try:
            if not event_session_id or event_session_id == 'nan' or event_session_id == '':
                return None
                
            print(f"  Fetching activity details for {event_session_id}")
            
            params = {'eventsessionID': event_session_id}
            if viewer_id:
                params['viewerId'] = viewer_id
                print(f"    Using viewerId={viewer_id}")
            
            data = self.event_details_extractor.extract(**params)
            
            if data:
                print(f"    [OK] Activity details retrieved")
                return data
            else:
                print(f"    [WARNING] No activity details found")
                return None

        except Exception as e:
            print(f"    [ERROR] Failed to fetch activity details: {e}")
            return None

    def get_activity_participations(self, event_session_id: str, viewer_id: str = None) -> List[Dict[str, Any]]:
        """Get list of participants for an activity with pagination"""
        try:
            if not event_session_id or event_session_id == 'nan':
                return []
                
            print(f"  Fetching participations for activity {event_session_id}")
            
            all_participants = []
            page = 1
            per_page = 250
            max_pages = 20
            
            while page <= max_pages:
                print(f"    Fetching page {page}...")
                
                params = {
                    'eventSessionId': event_session_id,
                    'page': page,
                    'perPage': per_page
                }
                if viewer_id:
                    params['viewerId'] = viewer_id
                
                data = self.event_participations_extractor.extract(**params)
                
                if not data:
                    print(f"    No data returned on page {page}")
                    break
                
                participants = self._extract_participants_from_response(data)
                
                if not participants:
                    print(f"    No participants found on page {page}")
                    break
                
                all_participants.extend(participants)
                print(f"    Got {len(participants)} participants (total: {len(all_participants)})")
                
                # Check if there are more pages
                if len(participants) < per_page:
                    print(f"    Received {len(participants)} < {per_page}, reached last page")
                    break
                
                page += 1
            
            print(f"    [OK] Total participants: {len(all_participants)}")
            return all_participants

        except Exception as e:
            print(f"    [ERROR] Failed to fetch participations: {e}")
            return []

    def get_activity_recordings(self, event_session_id: str, viewer_id: str = None) -> List[Dict[str, Any]]:
        """Get list of recordings for an activity"""
        try:
            if not event_session_id or event_session_id == 'nan':
                return []
                
            print(f"  Fetching recordings for activity {event_session_id}")
            
            params = {'eventSessionId': event_session_id}
            if viewer_id:
                params['viewerId'] = viewer_id
            
            data = self.event_recordings_extractor.extract(**params)
            
            recordings = self._extract_recordings_from_response(data)
            print(f"    [OK] Found {len(recordings)} recordings")
            
            return recordings

        except Exception as e:
            print(f"    [ERROR] Failed to fetch recordings: {e}")
            return []

    def get_activity_transcripts(self, event_session_id: str, viewer_id: str = None) -> List[Dict[str, Any]]:
        """Get list of transcripts for an activity"""
        try:
            if not event_session_id or event_session_id == 'nan':
                return []
                
            print(f"  Fetching transcripts for activity {event_session_id}")
            
            params = {'eventSessionId': event_session_id}
            if viewer_id:
                params['viewerId'] = viewer_id
            
            data = self.transcript_list_extractor.extract(**params)
            
            transcripts = self._extract_transcripts_from_response(data)
            print(f"    [OK] Found {len(transcripts)} transcripts")
            
            return transcripts

        except Exception as e:
            print(f"    [ERROR] Failed to fetch transcripts: {e}")
            return []

    def _extract_participants_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract participants from API response"""
        if not data:
            return []

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'data' in data:
                items = data['data']
                if isinstance(items, list):
                    return items
                elif isinstance(items, dict) and 'items' in items:
                    return items['items']
                elif isinstance(items, dict) and 'participations' in items:
                    return items['participations']
            elif 'participations' in data:
                return data['participations']
            elif 'items' in data:
                return data['items']

        return []

    def _extract_recordings_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract recordings from API response"""
        if not data:
            return []

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'data' in data:
                items = data['data']
                if isinstance(items, list):
                    return items
                elif isinstance(items, dict) and 'recordings' in items:
                    return items['recordings']
            elif 'recordings' in data:
                return data['recordings']

        return []

    def _extract_transcripts_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract transcripts from API response"""
        if not data:
            return []

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'data' in data:
                items = data['data']
                if isinstance(items, list):
                    return items
                elif isinstance(items, dict) and 'transcripts' in items:
                    return items['transcripts']
            elif 'transcripts' in data:
                return data['transcripts']

        return []

    def analyze_activity(self, activity: Dict[str, Any], fetch_detailed_info: bool = True) -> Dict[str, Any]:
        """Analyze a single activity and gather all available statistics"""
        activity_id = activity.get('activity_id', 'unknown')
        event_session_id = activity.get('event_session_id', '')
        endless_event_id = activity.get('endless_event_id', '')
        
        self.processed_count += 1
        print(f"\n[{self.processed_count}/{self.total_count}] Analyzing activity: {activity_id}")
        print(f"  Event Session ID: {event_session_id or 'N/A'}")
        print(f"  Endless Event ID: {endless_event_id or 'N/A'}")
        
        # Initialize analysis result with basic info from CSV
        user_id = activity.get('user_id', '')
        # Try to get user_name from CSV first, then from mapping
        user_name = activity.get('user_name', '') or self.user_mapping.get(str(user_id), 'Unknown User')
        
        result = {
            'activity_id': activity_id,
            'event_session_id': event_session_id,
            'endless_event_id': endless_event_id,
            'user_id': user_id,
            'user_name': user_name if user_name else 'Unknown User',
            'activity_type': activity.get('activity_type', ''),
            'status': activity.get('status', ''),
            'start_time': activity.get('start_time', ''),
            'end_time': activity.get('end_time', ''),
            'duration_minutes': int(activity.get('duration_minutes', 0)) if activity.get('duration_minutes') else 0,
            'participants_count_csv': int(activity.get('participants_count', 0)) if activity.get('participants_count') else 0,
            'room_name': activity.get('room_name', ''),
            'is_recorded': activity.get('is_recorded', False),
        }
        
        # Get endless event details from cache
        if endless_event_id and str(endless_event_id) in self.endless_events_cache:
            endless_event = self.endless_events_cache[str(endless_event_id)]
            result['endless_event_name'] = endless_event.get('name', '')
            result['endless_event_owner_id'] = endless_event.get('ownerId', '')
        else:
            result['endless_event_name'] = ''
            result['endless_event_owner_id'] = ''
        
        # Initialize detailed stats
        result['participants_count_api'] = 0
        result['unique_participants'] = 0
        result['recordings_count'] = 0
        result['transcripts_count'] = 0
        result['has_transcript'] = False
        
        # Full data storage for archive
        full_activity_data = {
            'activity_info': activity,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Fetch detailed information if event_session_id is available and requested
        if fetch_detailed_info and event_session_id and event_session_id != 'nan':
            # Get viewerId for activity access (try from activity or endless event cache)
            viewer_id = activity.get('discovered_via_user_id')
            if not viewer_id and endless_event_id and str(endless_event_id) in self.endless_events_cache:
                endless_event = self.endless_events_cache[str(endless_event_id)]
                viewer_id = endless_event.get('ownerId')
            
            # Skip if viewer_id is 'unknown' or empty
            if viewer_id and viewer_id != 'unknown' and viewer_id.strip():
                print(f"  Using viewerId={viewer_id} for activity access")
            else:
                viewer_id = None
            
            # Get activity details
            activity_details = self.get_activity_details(event_session_id, viewer_id)
            if activity_details:
                full_activity_data['activity_details'] = activity_details
            
            # Get participants
            participants = self.get_activity_participations(event_session_id, viewer_id)
            if participants:
                result['participants_count_api'] = len(participants)
                
                # Count unique participants
                unique_user_ids = set()
                for p in participants:
                    user_id = p.get('userId') or p.get('chatUserId', '')
                    if user_id:
                        unique_user_ids.add(user_id)
                result['unique_participants'] = len(unique_user_ids)
                
                full_activity_data['participants'] = participants
                print(f"    Participants: {result['participants_count_api']} total, {result['unique_participants']} unique")
            
            # Get recordings
            recordings = self.get_activity_recordings(event_session_id, viewer_id)
            if recordings:
                result['recordings_count'] = len(recordings)
                full_activity_data['recordings'] = recordings
                print(f"    Recordings: {result['recordings_count']}")
            
            # Get transcripts
            transcripts = self.get_activity_transcripts(event_session_id, viewer_id)
            if transcripts:
                result['transcripts_count'] = len(transcripts)
                result['has_transcript'] = True
                full_activity_data['transcripts'] = transcripts
                print(f"    Transcripts: {result['transcripts_count']}")
        else:
            print(f"    Skipping detailed info fetch (no valid event_session_id or fetch disabled)")
        
        # Save full archive if enabled
        if self.save_archives:
            self._save_activity_archive(activity_id, full_activity_data)
        
        return result

    def _save_activity_archive(self, activity_id: str, data: Dict[str, Any]):
        """Save full activity data to JSON archive"""
        try:
            os.makedirs(self.archive_path, exist_ok=True)
            
            # Sanitize activity_id for filename
            safe_id = str(activity_id).replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = f"activity_{safe_id}.json"
            filepath = os.path.join(self.archive_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"    [ARCHIVE] Saved to: {filename}")

        except Exception as e:
            print(f"    [ERROR] Failed to save archive: {e}")

    def analyze_all_activities(self, limit: int = None, fetch_detailed_info: bool = True) -> List[Dict[str, Any]]:
        """Analyze all activities from loaded data"""
        if not self.activities_data:
            print("No activities data loaded. Call load_endless_activities() first.")
            return []
        
        activities_to_analyze = self.activities_data[:limit] if limit else self.activities_data
        self.total_count = len(activities_to_analyze)
        
        print(f"\n{'='*80}")
        print(f"Starting analysis of {self.total_count} endless activities")
        print(f"Detailed info fetch: {'ENABLED' if fetch_detailed_info else 'DISABLED'}")
        print(f"Save archives: {'ENABLED' if self.save_archives else 'DISABLED'}")
        print(f"{'='*80}\n")
        
        self.analysis_results = []
        
        for activity in activities_to_analyze:
            try:
                result = self.analyze_activity(activity, fetch_detailed_info)
                self.analysis_results.append(result)
            except Exception as e:
                print(f"\n[ERROR] Failed to analyze activity {activity.get('activity_id', 'unknown')}: {e}")
                continue
        
        print(f"\n{'='*80}")
        print(f"Analysis complete! Processed {len(self.analysis_results)}/{self.total_count} activities")
        print(f"{'='*80}\n")
        
        return self.analysis_results

    def save_analysis_results(self, filename: str = None, output_format: str = 'csv') -> str:
        """Save analysis results to file"""
        if not self.analysis_results:
            print("No analysis results to save")
            return None
        
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not filename:
            filename = f"endless_activities_analysis_{current_timestamp}"
        else:
            # Remove extension if provided
            filename = os.path.splitext(filename)[0]
        
        if output_format == 'csv':
            filepath = os.path.join(self.data_path, f"{filename}.csv")
            self._save_as_csv(filepath)
        elif output_format == 'json':
            filepath = os.path.join(self.data_path, f"{filename}.json")
            self._save_as_json(filepath)
        else:
            print(f"Unknown output format: {output_format}")
            return None
        
        return filepath

    def _save_as_csv(self, filepath: str):
        """Save results as CSV"""
        try:
            # Get all unique keys from all results
            all_keys = set()
            for result in self.analysis_results:
                all_keys.update(result.keys())
            
            fieldnames = sorted(list(all_keys))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.analysis_results)
            
            print(f"\nAnalysis results saved to: {filepath}")
            print(f"Total activities analyzed: {len(self.analysis_results)}")

        except Exception as e:
            print(f"Error saving CSV file: {e}")

    def _save_as_json(self, filepath: str):
        """Save results as JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.analysis_results, jsonfile, indent=2, ensure_ascii=False)
            
            print(f"\nAnalysis results saved to: {filepath}")
            print(f"Total activities analyzed: {len(self.analysis_results)}")

        except Exception as e:
            print(f"Error saving JSON file: {e}")


def main():
    """Main function to run the endless activities analyzer"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze endless activities from CSV file')
    parser.add_argument('--input', '-i', help='Input CSV filename (default: most recent endless_activities file)')
    parser.add_argument('--output', '-o', help='Output filename for analysis results')
    parser.add_argument('--activity-id', help='Analyze only one specific activity by its ID')
    parser.add_argument('--limit', type=int, help='Limit number of activities to analyze')
    parser.add_argument('--no-archive', action='store_true', help='Do not save full activity data archives')
    parser.add_argument('--no-detailed-info', action='store_true', help='Skip fetching detailed info (faster, less data)')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Output format (default: csv)')
    parser.add_argument('--test', action='store_true', help='Test mode - analyze only first 3 activities')

    args = parser.parse_args()

    analyzer = EndlessActivitiesAnalyzer()
    
    # Configure archive settings
    if args.no_archive:
        analyzer.save_archives = False
        print("Archive saving: DISABLED")
    
    # Load activities data
    if not analyzer.load_endless_activities(args.input):
        print("Failed to load endless activities data")
        return
    
    # Handle single activity analysis
    if args.activity_id:
        # Find the specific activity
        activity = next((a for a in analyzer.activities_data if a.get('activity_id') == args.activity_id), None)
        
        if not activity:
            print(f"Activity with ID '{args.activity_id}' not found in data")
            return
        
        analyzer.total_count = 1
        result = analyzer.analyze_activity(activity, fetch_detailed_info=not args.no_detailed_info)
        analyzer.analysis_results = [result]
    else:
        # Analyze all or limited activities
        limit = 3 if args.test else args.limit
        analyzer.analyze_all_activities(
            limit=limit,
            fetch_detailed_info=not args.no_detailed_info
        )
    
    # Save results
    if analyzer.analysis_results:
        output_file = analyzer.save_analysis_results(args.output, args.format)
        if output_file:
            print(f"\n[SUCCESS] Analysis completed successfully!")
            print(f"[RESULTS] {output_file}")
            if analyzer.save_archives:
                print(f"[ARCHIVES] {analyzer.archive_path}")
    else:
        print("No results to save")


if __name__ == "__main__":
    main()

