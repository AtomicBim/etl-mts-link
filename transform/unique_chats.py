import sys
import os
import csv
from typing import Set, Dict, List, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract.link_chats_extractors
from abstractions.extract import UniversalExtractor


class UniqueChatsTransformer:
    def __init__(self):
        self.extraction_path = os.getenv("EXTRACTION_PATH", ".")
        self.unique_chats: Set[str] = set()
        self.chats_data: List[Dict[str, Any]] = []
        self.members_extractor = UniversalExtractor("/chats/organization/members")
        self.channels_extractor = UniversalExtractor("/chats/channels/{userId}")
        
    def get_organization_members(self) -> List[Dict[str, Any]]:
        """Extract organization members using extractor"""
        print("Extracting organization members...")

        data = self.members_extractor.extract()
        if data:
            if isinstance(data, dict) and 'data' in data:
                items = data['data'].get('items', [])
                print(f"Found {len(items)} organization members")
                return items
            elif isinstance(data, list):
                print(f"Found {len(data)} organization members")
                return data
            else:
                print(f"Unexpected data structure: {type(data)}")
                return []
        else:
            print("Failed to extract organization members")
            return []
    
    def get_user_channels(self, user_id: str) -> List[Dict[str, Any]]:
        """Get channels for a specific user using extractor"""
        data = self.channels_extractor.extract(userId=user_id)
        if data is None:
            return []

        if isinstance(data, dict):
            if 'data' in data:
                items = data['data']
                if isinstance(items, dict) and 'items' in items:
                    return items['items']
                elif isinstance(items, list):
                    return items
            elif 'items' in data:
                return data['items']
            elif 'channels' in data:
                return data['channels']
            else:
                return [data]
        elif isinstance(data, list):
            return data
        else:
            return []
    
    def collect_unique_chats(self, test_mode: bool = False, max_users: int = 10) -> None:
        """Main method to collect unique chats from all organization members"""
        print("Starting unique chats collection process...")

        members = self.get_organization_members()
        if not members:
            print("No organization members found")
            return

        if test_mode:
            members = members[:max_users]
            print(f"TEST MODE: Processing only first {len(members)} organization members...")
        else:
            print(f"Processing {len(members)} organization members...")

        processed_count = 0
        for member in members:
            user_id = member.get('chatUserId') or member.get('userId') or member.get('id')

            if not user_id:
                print(f"No user ID found in member data: {member}")
                continue

            processed_count += 1
            print(f"Processing user {processed_count}/{len(members)}: {user_id}")

            channels = self.get_user_channels(str(user_id))

            if not channels:
                continue

            for channel in channels:
                chat_id = channel.get('chatId') or channel.get('id') or channel.get('guid')

                if not chat_id:
                    print(f"No chat ID found in channel data: {channel}")
                    continue

                if chat_id not in self.unique_chats:
                    self.unique_chats.add(chat_id)

                    chat_data = {
                        'chat_id': chat_id,
                        'name': channel.get('name', ''),
                        'type': channel.get('type', ''),
                        'is_public': channel.get('isPublic', ''),
                        'is_read_only': channel.get('isReadOnly', ''),
                        'owner_id': channel.get('ownerID', ''),
                        'organization_id': channel.get('organizationId', ''),
                        'description': channel.get('description', ''),
                        'is_notifiable': channel.get('isNotifiable', ''),
                        'unread_message_count': channel.get('unreadMessageCount', ''),
                        'started_webinar_event_id': channel.get('startedWebinarEventId', ''),
                        'discovered_via_user_id': user_id,
                        'extraction_timestamp': datetime.now().isoformat()
                    }

                    self.chats_data.append(chat_data)

        print(f"Collected {len(self.unique_chats)} unique chats")
    
    def save_to_csv(self, filename: str = None) -> str:
        """Save unique chats data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unique_chats_{timestamp}.csv"
        
        filepath = os.path.join(self.extraction_path, filename)
        os.makedirs(self.extraction_path, exist_ok=True)
        
        # Define CSV headers
        headers = [
            'chat_id',
            'name', 
            'type',
            'is_public',
            'is_read_only',
            'owner_id',
            'organization_id',
            'description',
            'is_notifiable',
            'unread_message_count',
            'started_webinar_event_id',
            'discovered_via_user_id',
            'extraction_timestamp'
        ]
        
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
                       help='Test mode - process only first 10 users')
    parser.add_argument('--help-fields', action='store_true', 
                       help='Show description of CSV fields')
    
    args = parser.parse_args()
    
    if args.help_fields:
        print("\nCSV Fields Description:")
        print("- chat_id: Unique identifier of the chat/channel")
        print("- name: Name of the chat/channel")
        print("- type: Type of the chat (public, private, etc.)")
        print("- is_public: Whether the chat is public (true/false)")
        print("- is_read_only: Whether the chat is read-only (true/false)")
        print("- owner_id: ID of the chat owner")
        print("- organization_id: ID of the organization")
        print("- description: Chat description")
        print("- is_notifiable: Whether notifications are enabled")
        print("- unread_message_count: Number of unread messages")
        print("- started_webinar_event_id: ID of started webinar event if any")
        print("- discovered_via_user_id: User ID through which this chat was discovered")
        print("- extraction_timestamp: When this record was extracted")
        return
    
    transformer = UniqueChatsTransformer()
    result = transformer.run(args.output, test_mode=args.test)
    
    if result:
        print(f"Unique chats extraction completed successfully: {result}")
    else:
        print("Unique chats extraction failed")


if __name__ == "__main__":
    main()