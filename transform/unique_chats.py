import sys
import os
import csv
import json
import glob
from typing import Set, Dict, List, Any, Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract.link_chats_extractors
from abstractions.extract import UniversalExtractor


class UniqueChatsTransformer:
    """Transformer for extracting and deduplicating unique chats from organization"""

    # Configuration constants
    DEFAULT_TEST_USERS = 10
    USER_ID_KEYS = ['chatUserId', 'userId', 'id']
    CHAT_ID_KEYS = ['chatId', 'id', 'guid']

    def __init__(self, extraction_path: str = None):
        # Default to data directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_data_path = os.path.join(project_root, "data")

        if extraction_path:
            self.extraction_path = extraction_path
        else:
            # Always prefer the data directory over environment variable
            self.extraction_path = default_data_path
        self.unique_chats: Set[str] = set()
        self.chats_data: List[Dict[str, Any]] = []
        self.members_extractor = UniversalExtractor("/chats/organization/members")
        self.channels_extractor = UniversalExtractor("/chats/channels/{userId}")
        
        # Mapping for user ID to human-readable name
        self.user_id_to_name: Dict[str, str] = {}
        
        # Mapping for organization ID to name
        self.org_id_to_name: Dict[str, str] = {}
        self._load_organization_mapping()

    def _load_organization_mapping(self) -> None:
        """Load organization ID to name mapping from JSON file"""
        mapping_file = os.path.join(self.extraction_path, "organizations_mapping.json")
        
        if not os.path.exists(mapping_file):
            print(f"Warning: Organization mapping file not found: {mapping_file}")
            print("Organization IDs will be used instead of names")
            return
        
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
            
            organizations = mapping_data.get('organizations', [])
            for org in organizations:
                org_id = org.get('organization_id')
                org_name = org.get('organization_name')
                if org_id and org_name:
                    self.org_id_to_name[org_id] = org_name
            
            if self.org_id_to_name:
                print(f"Loaded {len(self.org_id_to_name)} organization mappings")
            else:
                print("Warning: No organization mappings found in file")
        
        except Exception as e:
            print(f"Warning: Could not load organization mapping: {e}")

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
                elif isinstance(items, list):
                    result = items
                else:
                    result = []
            elif 'items' in data:
                result = data['items']
            elif 'channels' in data:
                result = data['channels']
            else:
                result = [data] if data_type == "user channels" else []

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
    
    def _get_user_display_name(self, member: Dict[str, Any]) -> str:
        """Extract full name (FIO) from member data"""
        # Try to get profile information
        profile = member.get('chatMemberProfile', {})
        
        if isinstance(profile, dict):
            # Priority: Full Name (firstName + lastName) > displayName > email > userId
            first_name = profile.get('firstName', '').strip()
            last_name = profile.get('lastName', '').strip()
            
            # Build full name (FIO)
            if first_name and last_name:
                return f"{last_name} {first_name}"  # Фамилия Имя
            elif first_name:
                return first_name
            elif last_name:
                return last_name
            
            # If no firstName/lastName, try displayName
            display_name = profile.get('displayName', '').strip()
            if display_name:
                return display_name
            
            # If no display name, try email
            email = profile.get('email', '').strip()
            if email:
                return email
        
        # Fallback to userId if no profile information
        user_id = self._extract_id_from_dict(member, self.USER_ID_KEYS)
        return user_id or 'Unknown User'
    
    def _build_user_mapping(self, members: List[Dict[str, Any]]) -> None:
        """Build mapping from user ID to human-readable name"""
        print("Building user ID to name mapping...")
        
        for member in members:
            user_id = self._extract_id_from_dict(member, self.USER_ID_KEYS)
            if user_id:
                display_name = self._get_user_display_name(member)
                self.user_id_to_name[user_id] = display_name
        
        print(f"Created mapping for {len(self.user_id_to_name)} users")

    def get_organization_members(self) -> List[Dict[str, Any]]:
        """Extract organization members using extractor with pagination support"""
        print("Extracting organization members...")
        
        all_members = []
        page = 1
        per_page = 100  # Use smaller page size for reliable pagination
        max_pages = 20  # Safety limit (100 * 20 = 2000 users max)
        
        while page <= max_pages:
            print(f"Fetching page {page} (perPage={per_page})...")
            data = self.members_extractor.extract(page=page, perPage=per_page)
            
            if not data:
                print(f"No data returned for page {page}")
                break
            
            members = self._extract_items_from_response(data, f"organization members (page {page})")
            
            if not members:
                # No more members to fetch
                print(f"No members found on page {page}, stopping pagination")
                break
            
            all_members.extend(members)
            print(f"  Collected {len(members)} members (total so far: {len(all_members)})")
            
            # Check if we got fewer records than requested (last page)
            if len(members) < per_page:
                print(f"Received {len(members)} members (less than {per_page}), this is the last page")
                break
            
            page += 1
        
        print(f"Total organization members fetched: {len(all_members)}")
        return all_members

    def get_user_channels(self, user_id: str) -> List[Dict[str, Any]]:
        """Get channels for a specific user using extractor"""
        data = self.channels_extractor.extract(userId=user_id)
        return self._extract_items_from_response(data, "user channels")
    
    def _create_chat_record(self, channel: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create standardized chat record from channel data"""
        # Get owner ID and convert to human-readable name
        owner_id = channel.get('ownerID', '')
        owner_name = self.user_id_to_name.get(owner_id, owner_id) if owner_id else ''
        
        # Get organization ID and convert to human-readable name
        org_id = channel.get('organizationId', '')
        org_name = self.org_id_to_name.get(org_id, org_id) if org_id else ''
        
        return {
            'chat_id': self._extract_id_from_dict(channel, self.CHAT_ID_KEYS),
            'name': channel.get('name', ''),
            'type': channel.get('type', ''),
            'is_public': channel.get('isPublic', ''),
            'is_read_only': channel.get('isReadOnly', ''),
            'owner_name': owner_name,
            'owner_id': owner_id,  # Keep original ID for reference
            'organization_name': org_name,
            'organization_id': org_id,
            'description': channel.get('description', ''),
            'is_notifiable': channel.get('isNotifiable', ''),
            'unread_message_count': channel.get('unreadMessageCount', ''),
            'started_webinar_event_id': channel.get('startedWebinarEventId', ''),
            'discovered_via_user_id': user_id,
            'extraction_timestamp': datetime.now().isoformat()
        }

    def _save_checkpoint(self, processed_users: int, total_users: int):
        """Save intermediate results as checkpoint"""
        checkpoint_file = os.path.join(self.extraction_path, "unique_chats_checkpoint.json")
        try:
            checkpoint_data = {
                'processed_users': processed_users,
                'total_users': total_users,
                'timestamp': datetime.now().isoformat(),
                'chats_data': self.chats_data
            }
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            print(f"  Checkpoint saved: {processed_users}/{total_users} users processed, {len(self.chats_data)} chats collected")
        except Exception as e:
            print(f"  Warning: Could not save checkpoint: {e}")

    def _load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load checkpoint if exists"""
        checkpoint_file = os.path.join(self.extraction_path, "unique_chats_checkpoint.json")
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load checkpoint: {e}")
        return None

    def _delete_checkpoint(self):
        """Delete checkpoint file after successful completion"""
        checkpoint_file = os.path.join(self.extraction_path, "unique_chats_checkpoint.json")
        try:
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
                print("Checkpoint file removed")
        except Exception as e:
            print(f"Warning: Could not remove checkpoint: {e}")

    def collect_unique_chats(self, test_mode: bool = False, max_users: int = None) -> None:
        """Main method to collect unique chats from all organization members"""
        print("Starting unique chats collection process...")

        members = self.get_organization_members()
        if not members:
            print("No organization members found")
            return

        # Build user ID to name mapping from all members
        self._build_user_mapping(members)

        # Apply test mode limits
        if test_mode:
            max_users = max_users or self.DEFAULT_TEST_USERS
            members = members[:max_users]
            print(f"TEST MODE: Processing only first {len(members)} organization members...")
        else:
            print(f"Processing {len(members)} organization members...")

        # Check for existing checkpoint
        checkpoint = self._load_checkpoint()
        if checkpoint:
            print(f"\n📁 Found checkpoint from {checkpoint['timestamp']}")
            print(f"   Previously processed: {checkpoint['processed_users']}/{checkpoint['total_users']} users")
            print(f"   Collected chats: {len(checkpoint['chats_data'])}")
            response = input("Continue from checkpoint? (y/n): ").strip().lower()
            if response == 'y':
                self.chats_data = checkpoint['chats_data']
                self.unique_chats = set(chat['chat_id'] for chat in self.chats_data)
                print(f"✅ Restored {len(self.chats_data)} chats from checkpoint\n")
            else:
                print("Starting fresh...\n")

        processed_count = 0
        for member in members:
            user_id = self._extract_id_from_dict(member, self.USER_ID_KEYS)

            if not user_id:
                print(f"No user ID found in member data: {member}")
                continue

            processed_count += 1
            print(f"Processing user {processed_count}/{len(members)}: {user_id}")

            try:
                channels = self.get_user_channels(user_id)
                if not channels:
                    continue

                for channel in channels:
                    chat_id = self._extract_id_from_dict(channel, self.CHAT_ID_KEYS)

                    if not chat_id:
                        print(f"No chat ID found in channel data: {channel}")
                        continue

                    if chat_id not in self.unique_chats:
                        self.unique_chats.add(chat_id)
                        chat_data = self._create_chat_record(channel, user_id)
                        self.chats_data.append(chat_data)

                # Save checkpoint every 10 users
                if processed_count % 10 == 0:
                    self._save_checkpoint(processed_count, len(members))

            except Exception as e:
                print(f"Error processing user {user_id}: {e}")
                # Save checkpoint on error
                self._save_checkpoint(processed_count, len(members))
                raise  # Re-raise to stop execution

        print(f"Collected {len(self.unique_chats)} unique chats")
        # Delete checkpoint on successful completion
        self._delete_checkpoint()

    def _find_existing_files(self, base_filename: str) -> List[str]:
        """Find existing files with the same base name but different timestamps"""
        if not base_filename:
            return []

        # Extract base name without timestamp and extension
        if base_filename.startswith("unique_chats_") and base_filename.endswith(".csv"):
            pattern = "unique_chats_*.csv"
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
            if "unique_chats_" in filename:
                try:
                    # Format: unique_chats_YYYYMMDD_HHMMSS.csv
                    timestamp_part = filename.replace("unique_chats_", "").replace(".csv", "")
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
        """Save unique chats data to CSV file with timestamp-based overwrite protection"""
        if not self.chats_data:
            print("No chat data to save")
            return None

        # Generate timestamp for new file
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not filename:
            filename = f"unique_chats_{current_timestamp}.csv"
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
        headers = list(self.chats_data[0].keys()) if self.chats_data else []

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.chats_data)

            print(f"Unique chats saved to: {filepath}")
            print(f"Total unique chats: {len(self.chats_data)}")
            return filepath

        except Exception as e:
            print(f"Error saving CSV file: {e}")
            return None
    
    def run(self, output_filename: str = None, test_mode: bool = False) -> str:
        """Run the complete unique chats extraction process"""
        print("Starting unique chats transformation...")

        self.collect_unique_chats(test_mode=test_mode)

        if not self.chats_data:
            print("No unique chats data to save")
            return None

        return self.save_to_csv(output_filename)


def main():
    """Main function to run the unique chats transformer"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract unique chats from organization members')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--test', '-t', action='store_true',
                       help=f'Test mode - process only first {UniqueChatsTransformer.DEFAULT_TEST_USERS} users')
    parser.add_argument('--max-users', type=int, help='Maximum number of users to process in test mode')
    parser.add_argument('--help-fields', action='store_true',
                       help='Show description of CSV fields')

    args = parser.parse_args()

    if args.help_fields:
        print("\nCSV Fields Description:")
        fields_description = {
            "chat_id": "Unique identifier of the chat/channel",
            "name": "Name of the chat/channel",
            "type": "Type of the chat (public, private, etc.)",
            "is_public": "Whether the chat is public (true/false)",
            "is_read_only": "Whether the chat is read-only (true/false)",
            "owner_name": "Full name (FIO) of the chat owner (Last Name + First Name, or displayName, or email)",
            "owner_id": "ID of the chat owner (for reference)",
            "organization_name": "Human-readable name of the organization (from teams)",
            "organization_id": "ID of the organization",
            "description": "Chat description",
            "is_notifiable": "Whether notifications are enabled",
            "unread_message_count": "Number of unread messages",
            "started_webinar_event_id": "ID of started webinar event if any",
            "discovered_via_user_id": "User ID through which this chat was discovered",
            "extraction_timestamp": "When this record was extracted"
        }

        for field, description in fields_description.items():
            print(f"- {field}: {description}")
        return

    transformer = UniqueChatsTransformer()

    # Set max_users if provided
    max_users = args.max_users if args.test and args.max_users else None

    transformer.collect_unique_chats(test_mode=args.test, max_users=max_users)

    if transformer.chats_data:
        result = transformer.save_to_csv(args.output)
        if result:
            print(f"Unique chats extraction completed successfully: {result}")
        else:
            print("Failed to save results")
    else:
        print("No unique chats found")


if __name__ == "__main__":
    main()