import sys
import os
import csv
import requests
import json
import urllib3
import ssl
from typing import Set, Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import extractors to register them
import extract.link_chats_extractors

from abstractions.extract import run_extractor
from abstractions.logging_config import setup_logger

logger = setup_logger(__name__)


class UniqueChatsTransformer:
    def __init__(self):
        self.extraction_path = os.getenv("EXTRACTION_PATH", ".")
        self.unique_chats: Set[str] = set()
        self.chats_data: List[Dict[str, Any]] = []
        
        # Load API config
        self.config = self._load_config()
        self.base_url = self.config.get("base_url", "https://userapi.mts-link.ru/v3")
        self.api_token = self.config.get("api_token")
        
    def _load_config(self, config_path: str = "config/tokens.json") -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            return {}
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-auth-token": self.api_token,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def _make_api_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make direct API request"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                logger.debug(f"No data found for {endpoint}")
            else:
                logger.error(f"API request failed for {endpoint}: HTTP {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None
        
    def get_organization_members(self) -> List[Dict[str, Any]]:
        """Extract organization members using direct API call"""
        logger.info("Extracting organization members...")
        
        # Make direct API call
        data = self._make_api_request("/chats/organization/members")
        if data:
            # Handle the nested structure: {"data": {"items": [...], "total": N}}
            if isinstance(data, dict) and 'data' in data:
                items = data['data'].get('items', [])
                logger.info(f"Found {len(items)} organization members")
                return items
            elif isinstance(data, list):
                logger.info(f"Found {len(data)} organization members (direct list)")
                return data
            else:
                logger.warning(f"Unexpected data structure: {type(data)}")
                return []
        else:
            logger.error("Failed to extract organization members")
            return []
    
    def get_user_channels(self, user_id: str) -> List[Dict[str, Any]]:
        """Get channels for a specific user using direct API call"""
        logger.debug(f"Getting channels for user {user_id}")
        
        # Make direct API call
        data = self._make_api_request(f"/chats/channels/{user_id}")
        if data is None:
            return []  # API call failed, return empty list
            
        if data:
            # Handle various response structures
            if isinstance(data, dict):
                # Could be {"data": {"items": [...]}} or {"channels": [...]} or similar
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
                    # If it's a dict but not the expected structure, might be the channels directly
                    logger.debug(f"User {user_id} channels data keys: {list(data.keys())}")
                    return [data]  # Treat the whole response as a single channel
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected channels data structure for user {user_id}: {type(data)}")
                return []
        else:
            logger.warning(f"Failed to extract channels for user {user_id}")
            return []
    
    def collect_unique_chats(self, test_mode: bool = False, max_users: int = 10) -> None:
        """Main method to collect unique chats from all organization members"""
        logger.info("Starting unique chats collection process...")
        
        # Get all organization members
        members = self.get_organization_members()
        if not members:
            logger.error("No organization members found")
            return
        
        if test_mode:
            members = members[:max_users]
            logger.info(f"TEST MODE: Processing only first {len(members)} organization members...")
        else:
            logger.info(f"Processing {len(members)} organization members...")
        
        processed_count = 0
        for member in members:
            # Extract user ID - adjust field name based on API response structure
            user_id = member.get('chatUserId') or member.get('userId') or member.get('id')
            
            if not user_id:
                logger.warning(f"No user ID found in member data: {member}")
                continue
            
            processed_count += 1
            logger.info(f"Processing user {processed_count}/{len(members)}: {user_id}")
            
            # Get channels for this user
            channels = self.get_user_channels(str(user_id))
            
            if not channels:
                continue  # Skip users with no channels
            
            for channel in channels:
                # Extract chat GUID - adjust field name based on API response structure
                chat_id = channel.get('chatId') or channel.get('id') or channel.get('guid')
                
                if not chat_id:
                    logger.warning(f"No chat ID found in channel data: {channel}")
                    continue
                
                # Add to unique set and collect chat data if it's new
                if chat_id not in self.unique_chats:
                    self.unique_chats.add(chat_id)
                    
                    # Prepare chat data for CSV
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
                    logger.debug(f"Added unique chat: {chat_id} - {channel.get('name', 'Unnamed')}")
        
        logger.info(f"Collected {len(self.unique_chats)} unique chats")
    
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
            
            logger.success(f"Unique chats saved to: {filepath}")
            logger.info(f"Total unique chats: {len(self.chats_data)}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")
            return None
    
    def run(self, output_filename: str = None, test_mode: bool = False) -> str:
        """Run the complete unique chats extraction process"""
        logger.info("Starting unique chats transformation...")
        
        self.collect_unique_chats(test_mode=test_mode)
        
        if not self.chats_data:
            logger.warning("No unique chats data to save")
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