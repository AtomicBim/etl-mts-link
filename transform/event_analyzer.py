import sys
import os
import csv
import json
import glob
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import statistics

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import UniversalExtractor


class EventAnalyzer:
    """Analyzer for extracting detailed statistics from events/meetings"""

    def __init__(self, data_path: str = None):
        # Default to data directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = data_path or os.path.join(project_root, "data")

        # Event archive path
        self.archive_path = os.path.join(self.data_path, "events_archive")

        # Archive settings
        self.save_archives = True

        # Initialize extractors
        self.event_details_extractor = UniversalExtractor("/eventsessions/{eventsessionID}")
        self.event_participations_extractor = UniversalExtractor("/eventsessions/{eventSessionId}/participations")
        self.event_checkpoints_extractor = UniversalExtractor("/eventsessions/{eventSessionId}/attention-control/checkpoints")
        self.event_interactions_extractor = UniversalExtractor("/eventsessions/{eventSessionId}/attention-control/interactions")
        self.event_recordings_extractor = UniversalExtractor("/eventsessions/{eventSessionId}/recordings")
        self.transcript_list_extractor = UniversalExtractor("/eventsessions/{eventSessionId}/transcript/list")

        # Data storage
        self.events_data: List[Dict[str, Any]] = []
        self.analysis_results: List[Dict[str, Any]] = []

        # Progress tracking
        self.processed_count = 0
        self.total_count = 0

        # User mapping for full names
        self.user_mapping: Dict[str, str] = {}
        self._load_user_mapping()

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

    def load_unique_events(self, filename: str = None) -> bool:
        """Load unique events data from CSV file"""
        if filename:
            filepath = os.path.join(self.data_path, filename)
        else:
            # Find the most recent unique_events file
            pattern = os.path.join(self.data_path, "unique_events_*.csv")
            files = glob.glob(pattern)
            if not files:
                print("No unique events CSV files found in data directory")
                return False

            # Sort by modification time, get newest
            filepath = max(files, key=os.path.getmtime)
            print(f"Using most recent unique events file: {os.path.basename(filepath)}")

        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                self.events_data = list(reader)

            print(f"Loaded {len(self.events_data)} unique events for analysis")
            self.total_count = len(self.events_data)
            return True

        except Exception as e:
            print(f"Error loading unique events file: {e}")
            return False

    def get_event_details(self, event_session_id: str, viewer_id: str = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific event session"""
        try:
            print(f"  Fetching event details for {event_session_id}")
            
            params = {'eventsessionID': event_session_id}
            if viewer_id:
                params['viewerId'] = viewer_id
                print(f"    Using viewerId={viewer_id}")
            
            data = self.event_details_extractor.extract(**params)
            
            if data:
                print(f"    [OK] Event details retrieved")
                return data
            else:
                print(f"    [WARNING] No event details found")
                return None

        except Exception as e:
            print(f"    [ERROR] Failed to fetch event details: {e}")
            return None

    def get_event_participations(self, event_session_id: str, viewer_id: str = None) -> List[Dict[str, Any]]:
        """Get list of participants for an event with pagination"""
        try:
            print(f"  Fetching participations for event {event_session_id}")
            
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

    def get_event_attention_data(self, event_session_id: str, viewer_id: str = None) -> Dict[str, Any]:
        """Get attention control data (checkpoints and interactions)"""
        try:
            print(f"  Fetching attention control data for event {event_session_id}")
            
            # Get checkpoints
            params = {'eventSessionId': event_session_id}
            if viewer_id:
                params['viewerId'] = viewer_id
            
            checkpoints_data = self.event_checkpoints_extractor.extract(**params)
            checkpoints = self._extract_checkpoints_from_response(checkpoints_data)
            
            # Get interactions
            interactions_data = self.event_interactions_extractor.extract(**params)
            interactions = self._extract_interactions_from_response(interactions_data)
            
            print(f"    [OK] Checkpoints: {len(checkpoints)}, Interactions: {len(interactions)}")
            
            return {
                'checkpoints': checkpoints,
                'interactions': interactions,
                'checkpoint_count': len(checkpoints),
                'interaction_count': len(interactions)
            }

        except Exception as e:
            print(f"    [ERROR] Failed to fetch attention data: {e}")
            return {
                'checkpoints': [],
                'interactions': [],
                'checkpoint_count': 0,
                'interaction_count': 0
            }

    def get_event_recordings(self, event_session_id: str, viewer_id: str = None) -> List[Dict[str, Any]]:
        """Get list of recordings for an event"""
        try:
            print(f"  Fetching recordings for event {event_session_id}")
            
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

    def get_event_transcripts(self, event_session_id: str, viewer_id: str = None) -> List[Dict[str, Any]]:
        """Get list of transcripts for an event"""
        try:
            print(f"  Fetching transcripts for event {event_session_id}")
            
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
            # Try different possible structures
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

    def _extract_checkpoints_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract checkpoints from API response"""
        if not data:
            return []

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'data' in data:
                items = data['data']
                if isinstance(items, list):
                    return items
                elif isinstance(items, dict) and 'checkpoints' in items:
                    return items['checkpoints']
            elif 'checkpoints' in data:
                return data['checkpoints']

        return []

    def _extract_interactions_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract interactions from API response"""
        if not data:
            return []

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'data' in data:
                items = data['data']
                if isinstance(items, list):
                    return items
                elif isinstance(items, dict) and 'interactions' in items:
                    return items['interactions']
            elif 'interactions' in data:
                return data['interactions']

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

    def _calculate_duration_from_timestamps(self, start_time: str, end_time: str) -> int:
        """Calculate duration in minutes from timestamps"""
        try:
            if not start_time or not end_time:
                return 0
            
            # Parse timestamps (format: ISO 8601)
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration = (end_dt - start_dt).total_seconds() / 60
            return int(duration)
        except Exception:
            return 0

    def _calculate_participation_stats(self, participants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from participants data"""
        if not participants:
            return {
                'total_participants': 0,
                'unique_participants': 0,
                'average_duration_minutes': 0,
                'max_duration_minutes': 0,
                'min_duration_minutes': 0,
                'completed_count': 0,
                'in_progress_count': 0,
                'left_count': 0
            }

        # Extract unique participants
        unique_user_ids = set()
        durations = []
        status_counts = {
            'COMPLETED': 0,
            'IN_PROGRESS': 0,
            'LEFT': 0,
            'OTHER': 0
        }

        for participant in participants:
            # Track unique users
            user_id = participant.get('userId') or participant.get('participantId')
            if user_id:
                unique_user_ids.add(user_id)

            # Calculate duration if available
            join_time = participant.get('joinTime') or participant.get('startTime')
            leave_time = participant.get('leaveTime') or participant.get('endTime')
            
            if join_time and leave_time:
                duration = self._calculate_duration_from_timestamps(join_time, leave_time)
                if duration > 0:
                    durations.append(duration)

            # Count statuses
            status = participant.get('status', 'OTHER').upper()
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts['OTHER'] += 1

        return {
            'total_participants': len(participants),
            'unique_participants': len(unique_user_ids),
            'average_duration_minutes': int(statistics.mean(durations)) if durations else 0,
            'max_duration_minutes': max(durations) if durations else 0,
            'min_duration_minutes': min(durations) if durations else 0,
            'completed_count': status_counts['COMPLETED'],
            'in_progress_count': status_counts['IN_PROGRESS'],
            'left_count': status_counts['LEFT']
        }

    def analyze_event(self, event_data: Dict[str, Any], fetch_detailed_info: bool = True) -> Dict[str, Any]:
        """Analyze a single event and return comprehensive statistics"""
        event_session_id = event_data.get('event_session_id')
        event_name = event_data.get('name', 'Unknown')

        print(f"Analyzing event: {event_name} ({event_session_id})")

        result = {
            'event_session_id': event_session_id,
            'event_id': event_data.get('event_id', ''),
            'event_name': event_name,
            'event_type': event_data.get('event_type', ''),
            'status': event_data.get('status', ''),
            'start_time': event_data.get('start_time', ''),
            'end_time': event_data.get('end_time', ''),
            'scheduled_duration_minutes': event_data.get('duration_minutes', 0),
            'owner_id': event_data.get('owner_id', ''),
            'organization_id': event_data.get('organization_id', ''),
            'is_public': event_data.get('is_public', ''),
            'is_recurring': event_data.get('is_recurring', ''),
            'max_participants': event_data.get('max_participants', ''),
            'analysis_timestamp': datetime.now().isoformat()
        }

        if not fetch_detailed_info:
            result.update({
                'participants_count': 0,
                'unique_participants': 0,
                'recordings_count': 0,
                'transcripts_count': 0,
                'checkpoints_count': 0,
                'analysis_error': 'Detailed info fetch disabled'
            })
            return result

        try:
            # Get viewerId from event data for private/archived events access
            viewer_id = event_data.get('discovered_via_user_id') or event_data.get('owner_id')
            # Skip if viewer_id is 'unknown' or empty
            if viewer_id and viewer_id != 'unknown' and viewer_id.strip():
                print(f"  Using viewerId={viewer_id} for event access")
            else:
                viewer_id = None

            # Get event details
            event_details = self.get_event_details(event_session_id, viewer_id)

            # Get participants
            participants = self.get_event_participations(event_session_id, viewer_id)
            participation_stats = self._calculate_participation_stats(participants)

            # Get attention control data
            attention_data = self.get_event_attention_data(event_session_id, viewer_id)

            # Get recordings
            recordings = self.get_event_recordings(event_session_id, viewer_id)

            # Get transcripts
            transcripts = self.get_event_transcripts(event_session_id, viewer_id)

            # Update result with collected data
            result.update({
                'participants_count': participation_stats['total_participants'],
                'unique_participants': participation_stats['unique_participants'],
                'average_participant_duration_minutes': participation_stats['average_duration_minutes'],
                'max_participant_duration_minutes': participation_stats['max_duration_minutes'],
                'min_participant_duration_minutes': participation_stats['min_duration_minutes'],
                'completed_participants': participation_stats['completed_count'],
                'in_progress_participants': participation_stats['in_progress_count'],
                'left_participants': participation_stats['left_count'],
                'recordings_count': len(recordings),
                'transcripts_count': len(transcripts),
                'checkpoints_count': attention_data['checkpoint_count'],
                'interactions_count': attention_data['interaction_count'],
                'has_recordings': len(recordings) > 0,
                'has_transcripts': len(transcripts) > 0,
                'has_attention_control': attention_data['checkpoint_count'] > 0,
                'analysis_error': ''
            })

            # Save detailed archive
            if self.save_archives:
                archive_data = {
                    'event_info': event_data,
                    'event_details': event_details,
                    'participants': participants,
                    'attention_control': attention_data,
                    'recordings': recordings,
                    'transcripts': transcripts
                }
                self._save_event_archive(event_session_id, archive_data, event_name)

        except Exception as e:
            print(f"    [ERROR] Analysis failed: {e}")
            result['analysis_error'] = str(e)

        return result

    def analyze_all_events(self, limit: int = None, save_intermediate: bool = True, 
                          fetch_detailed_info: bool = True) -> None:
        """Analyze all loaded events"""
        if not self.events_data:
            print("No events data loaded. Call load_unique_events() first.")
            return

        print(f"Starting analysis of {len(self.events_data)} events...")

        # Apply limit if specified
        events_to_analyze = self.events_data[:limit] if limit else self.events_data

        self.analysis_results = []
        self.processed_count = 0

        for i, event_data in enumerate(events_to_analyze):
            self.processed_count += 1

            print(f"\nProgress: {self.processed_count}/{len(events_to_analyze)}")

            try:
                result = self.analyze_event(event_data, fetch_detailed_info)
                self.analysis_results.append(result)

                # Save intermediate results every 10 events
                if save_intermediate and self.processed_count % 10 == 0:
                    self._save_intermediate_results()

            except Exception as e:
                print(f"Error analyzing event {event_data.get('event_session_id', 'Unknown')}: {e}")
                # Add error record
                self.analysis_results.append({
                    'event_session_id': event_data.get('event_session_id', ''),
                    'event_name': event_data.get('name', ''),
                    'analysis_error': str(e),
                    'analysis_timestamp': datetime.now().isoformat()
                })

        # Clean up intermediate files after successful completion
        self._cleanup_intermediate_files()

        print(f"\nCompleted analysis of {len(self.analysis_results)} events")

        # Calculate statistics
        successful = len([r for r in self.analysis_results if not r.get('analysis_error')])
        print(f"Successful analyses: {successful}/{len(self.analysis_results)}")

    def _save_file_to_data_directory(self, filename: str, data: Any, file_format: str = 'json'):
        """Save file to local data directory"""
        local_path = os.path.join(self.data_path, filename)
        try:
            os.makedirs(self.data_path, exist_ok=True)
            if file_format == 'json':
                with open(local_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif file_format == 'csv':
                # For CSV, data should be [headers, results]
                headers, results = data
                with open(local_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                    writer.writeheader()
                    for result in results:
                        row = {header: result.get(header, '') for header in headers}
                        writer.writerow(row)
            return local_path
        except Exception as e:
            print(f"  Warning: Could not save to local directory: {e}")
            return None

    def _save_event_archive(self, event_session_id: str, archive_data: Dict[str, Any], event_name: str = "Unknown"):
        """Save complete event archive"""
        if not archive_data:
            return

        # Create filename based on event ID and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_event_id = event_session_id.replace('/', '_').replace('\\', '_')
        filename = f"event_{safe_event_id}_{timestamp}.json"

        # Create archive data structure
        full_archive = {
            'event_session_id': event_session_id,
            'event_name': event_name,
            'extraction_timestamp': datetime.now().isoformat(),
            **archive_data
        }

        # Save to archive
        saved_path = None
        try:
            os.makedirs(self.archive_path, exist_ok=True)
            archive_file_path = os.path.join(self.archive_path, filename)

            with open(archive_file_path, 'w', encoding='utf-8') as f:
                json.dump(full_archive, f, ensure_ascii=False, indent=2)

            saved_path = archive_file_path
            print(f"    Event archived")
        except Exception as e:
            print(f"    Warning: Could not save event archive: {e}")

        return saved_path

    def _save_intermediate_results(self):
        """Save intermediate results with fixed filename to avoid data loss"""
        filename = "event_analysis_intermediate_current.json"

        # Save intermediate results to archive directory (overwrite same file)
        try:
            os.makedirs(self.archive_path, exist_ok=True)
            filepath = os.path.join(self.archive_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'processed_count': self.processed_count,
                    'total_count': len(self.events_data) if hasattr(self, 'events_data') else 0,
                    'timestamp': datetime.now().isoformat(),
                    'results': self.analysis_results
                }, f, ensure_ascii=False, indent=2)
            print(f"  Updated intermediate results ({self.processed_count} events processed)")
        except Exception as e:
            print(f"  Warning: Could not save intermediate results: {e}")

    def _cleanup_intermediate_files(self):
        """Remove intermediate files after successful completion"""
        filename = "event_analysis_intermediate_current.json"

        # Remove from archive
        try:
            filepath = os.path.join(self.archive_path, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"  Cleaned up intermediate files")
        except Exception as e:
            print(f"  Warning: Could not remove intermediate file: {e}")

    def save_results_to_csv(self, filename: str = None) -> str:
        """Save analysis results to CSV file in both locations"""
        if not self.analysis_results:
            print("No analysis results to save")
            return None

        # Generate timestamp for new file
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not filename:
            filename = f"event_analysis_{current_timestamp}.csv"
        else:
            # If custom filename provided, still add timestamp if not present
            name, ext = os.path.splitext(filename)
            if not any(c.isdigit() for c in name):  # No timestamp in filename
                filename = f"{name}_{current_timestamp}{ext}"

        # Define CSV headers
        headers = [
            'event_session_id', 'event_id', 'event_name', 'event_type', 'status',
            'start_time', 'end_time', 'scheduled_duration_minutes',
            'owner_id', 'organization_id', 'is_public', 'is_recurring', 'max_participants',
            'participants_count', 'unique_participants',
            'average_participant_duration_minutes', 'max_participant_duration_minutes',
            'min_participant_duration_minutes', 'completed_participants',
            'in_progress_participants', 'left_participants',
            'recordings_count', 'transcripts_count', 'checkpoints_count', 'interactions_count',
            'has_recordings', 'has_transcripts', 'has_attention_control',
            'analysis_timestamp', 'analysis_error'
        ]

        # Prepare data for save
        csv_data = (headers, self.analysis_results)

        saved_path = self._save_file_to_data_directory(filename, csv_data, 'csv')

        if saved_path:
            print(f"Analysis results saved to: {saved_path}")
            print(f"Total analyzed events: {len(self.analysis_results)}")
            return saved_path
        else:
            print("Error saving analysis results")
            return None

    def save_results_to_json(self, filename: str = None) -> str:
        """Save analysis results to JSON file in both locations"""
        if not self.analysis_results:
            print("No analysis results to save")
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"event_analysis_{timestamp}.json"

        saved_path = self._save_file_to_data_directory(filename, self.analysis_results, 'json')

        if saved_path:
            print(f"Analysis results saved to: {saved_path}")
            print(f"Total analyzed events: {len(self.analysis_results)}")
            return saved_path
        else:
            print("Error saving analysis results to any location")
            return None

    def run_analysis(self, input_filename: str = None, output_filename: str = None,
                    limit: int = None, output_format: str = 'csv',
                    save_archives: bool = True, fetch_detailed_info: bool = True) -> str:
        """Run complete event analysis process"""
        print("Starting comprehensive event analysis...")

        # Set archive preference
        self.save_archives = save_archives

        # Load unique events data
        if not self.load_unique_events(input_filename):
            print("Failed to load unique events data")
            return None

        # Analyze all events
        self.analyze_all_events(limit=limit, fetch_detailed_info=fetch_detailed_info)

        if not self.analysis_results:
            print("No analysis results generated")
            return None

        # Save results
        if output_format.lower() == 'json':
            result_path = self.save_results_to_json(output_filename)
        else:
            result_path = self.save_results_to_csv(output_filename)

        return result_path

    def analyze_single_event(self, event_session_id: str, event_name: str = "Single Event",
                            output_filename: str = None, output_format: str = 'csv',
                            save_archives: bool = True) -> str:
        """Analyze a single event by ID"""
        print(f"Starting single event analysis for: {event_name} ({event_session_id})")

        # Set archive preference
        self.save_archives = save_archives

        # Create mock event data for single event
        event_data = {
            'event_session_id': event_session_id,
            'name': event_name,
            'event_type': 'unknown',
            'status': 'unknown',
            'owner_id': 'unknown',
            'organization_id': 'unknown'
        }

        try:
            # Analyze the single event
            result = self.analyze_event(event_data, fetch_detailed_info=True)
            self.analysis_results = [result]

            if not self.analysis_results:
                print("No analysis results generated")
                return None

            # Save results
            if output_format.lower() == 'json':
                return self.save_results_to_json(output_filename)
            else:
                return self.save_results_to_csv(output_filename)

        except Exception as e:
            print(f"Error analyzing single event: {e}")
            return None


def main():
    """Main function to run the event analyzer"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze unique events for detailed statistics')
    parser.add_argument('--input', '-i', help='Input unique events CSV filename')
    parser.add_argument('--output', '-o', help='Output analysis filename')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of events to analyze')
    parser.add_argument('--format', '-f', choices=['csv', 'json'], default='csv',
                       help='Output format (csv or json)')
    parser.add_argument('--no-archive', action='store_true',
                       help='Skip saving event archives (saves disk space)')
    parser.add_argument('--no-detailed-info', action='store_true',
                       help='Skip fetching detailed information (faster, less data)')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Test mode - analyze only first 3 events')
    parser.add_argument('--event-id', '-e', type=str,
                       help='Analyze specific event by session ID (bypasses CSV input)')
    parser.add_argument('--event-name', '-n', type=str, default='Single Event',
                       help='Name for single event analysis (default: Single Event)')

    args = parser.parse_args()

    # Set test mode limit
    if args.test:
        args.limit = args.limit or 3
        print(f"TEST MODE: Analyzing only first {args.limit} events")

    analyzer = EventAnalyzer()

    # Handle single event analysis
    if args.event_id:
        print(f"Analyzing single event: {args.event_id}")
        result_file = analyzer.analyze_single_event(
            event_session_id=args.event_id,
            event_name=args.event_name,
            output_filename=args.output,
            output_format=args.format,
            save_archives=not args.no_archive
        )
    else:
        result_file = analyzer.run_analysis(
            input_filename=args.input,
            output_filename=args.output,
            limit=args.limit,
            output_format=args.format,
            save_archives=not args.no_archive,
            fetch_detailed_info=not args.no_detailed_info
        )

    if result_file:
        print(f"\nEvent analysis completed successfully!")
        print(f"Results saved to: {result_file}")

        # Show summary statistics
        if analyzer.analysis_results:
            total_events = len(analyzer.analysis_results)
            successful_analyses = len([r for r in analyzer.analysis_results if not r.get('analysis_error')])

            print(f"\nSummary:")
            print(f"- Total events processed: {total_events}")
            print(f"- Successful analyses: {successful_analyses}")
            print(f"- Failed analyses: {total_events - successful_analyses}")
            
            # Calculate aggregate statistics
            if successful_analyses > 0:
                total_participants = sum(r.get('participants_count', 0) for r in analyzer.analysis_results)
                events_with_recordings = sum(1 for r in analyzer.analysis_results if r.get('has_recordings'))
                events_with_transcripts = sum(1 for r in analyzer.analysis_results if r.get('has_transcripts'))
                
                print(f"- Total participants across all events: {total_participants}")
                print(f"- Events with recordings: {events_with_recordings}")
                print(f"- Events with transcripts: {events_with_transcripts}")
    else:
        print("Event analysis failed")


if __name__ == "__main__":
    main()

