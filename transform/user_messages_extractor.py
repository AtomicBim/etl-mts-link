#!/usr/bin/env python3
"""
User Messages Extractor
Extracts all messages from a specific user across all their channels
"""
import sys
import os
import csv
import json
from typing import List, Dict, Any, Set
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import UniversalExtractor


class UserMessagesExtractor:
    """Extract all messages from a specific user across all channels"""
    
    def __init__(self, user_id: str, user_name: str = None, output_dir: str = None):
        self.user_id = user_id
        self.user_name = user_name or user_id
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = output_dir or os.path.join(project_root, "data")
        
        # Initialize extractors
        self.channels_extractor = UniversalExtractor("/chats/channels/{userId}")
        self.messages_extractor = UniversalExtractor("/chats/channel/{chatId}/messages")
        
        # User mapping for names
        self.user_mapping: Dict[str, str] = {}
        self._load_user_mapping()
        
        # Storage
        self.user_channels: List[Dict[str, Any]] = []
        self.user_messages: List[Dict[str, Any]] = []
        
    def _load_user_mapping(self):
        """Load user mapping from organization_members CSV"""
        import glob
        pattern = os.path.join(self.output_dir, "organization_members_*.csv")
        files = glob.glob(pattern)
        if files:
            filepath = max(files, key=os.path.getmtime)
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    uid = row.get('chatUserId', '')
                    name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
                    if uid and name:
                        self.user_mapping[uid] = name
    
    def _extract_items(self, data: Any) -> List[Dict[str, Any]]:
        """Extract items from API response"""
        if not data:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if 'data' in data:
                items = data['data']
                if isinstance(items, list):
                    return items
                if isinstance(items, dict) and 'items' in items:
                    return items['items']
            if 'items' in data:
                return data['items']
        return []
    
    def fetch_user_channels(self) -> List[Dict[str, Any]]:
        """Get all channels where user participates"""
        print(f"\nFetching channels for {self.user_name}...")
        data = self.channels_extractor.extract(userId=self.user_id)
        self.user_channels = self._extract_items(data)
        print(f"Found {len(self.user_channels)} channels")
        return self.user_channels
    
    def fetch_channel_messages(self, chat_id: str, chat_name: str, 
                               max_messages: int = 50000) -> List[Dict[str, Any]]:
        """Fetch all messages from a channel"""
        all_messages = []
        seen_ids: Set[str] = set()
        limit = 100
        from_message_id = None
        max_requests = max(1, max_messages // limit)
        
        for req_num in range(max_requests):
            params = {
                'chatId': chat_id,
                'limit': limit,
                'direction': 'Before',
                'viewerId': self.user_id
            }
            if from_message_id:
                params['fromMessageId'] = from_message_id
            
            data = self.messages_extractor.extract(**params)
            if not data:
                break
                
            messages = self._extract_items(data)
            if not messages:
                break
            
            # Deduplicate
            new_messages = []
            for msg in messages:
                msg_id = msg.get('id') or msg.get('messageId')
                if msg_id and msg_id not in seen_ids:
                    seen_ids.add(msg_id)
                    new_messages.append(msg)
            
            if not new_messages:
                break
                
            all_messages.extend(new_messages)
            
            if len(messages) < limit:
                break
                
            from_message_id = messages[-1].get('id') or messages[-1].get('messageId')
            if not from_message_id:
                break
        
        return all_messages
    
    def _timestamp_to_readable(self, ts_ms: int) -> str:
        try:
            return datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return ""
    
    def extract_user_messages(self, max_messages_per_channel: int = 50000) -> List[Dict[str, Any]]:
        """Extract all messages written by this user from all their channels"""
        if not self.user_channels:
            self.fetch_user_channels()
        
        print(f"\nExtracting messages from {len(self.user_channels)} channels...")
        print(f"Looking for messages from: {self.user_name} ({self.user_id})")
        
        self.user_messages = []
        
        for i, channel in enumerate(self.user_channels, 1):
            chat_id = channel.get('chatId') or channel.get('id')
            chat_name = channel.get('name', 'Unknown')
            
            print(f"\n[{i}/{len(self.user_channels)}] {chat_name}")
            
            if not chat_id:
                continue
            
            try:
                messages = self.fetch_channel_messages(chat_id, chat_name, max_messages_per_channel)
                print(f"  Total messages in channel: {len(messages)}")
                
                # Filter messages from this user
                user_msgs = [m for m in messages if m.get('authorId') == self.user_id]
                print(f"  Messages from {self.user_name}: {len(user_msgs)}")
                
                # Add channel info and simplify
                for msg in user_msgs:
                    self.user_messages.append({
                        'chat_name': chat_name,
                        'text': msg.get('text', ''),
                        'created_at': self._timestamp_to_readable(msg.get('createdAtMs', 0)),
                    })
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        print(f"\n{'='*50}")
        print(f"Total messages from {self.user_name}: {len(self.user_messages)}")
        
        return self.user_messages
    
    def save_to_csv(self, filename: str = None) -> str:
        """Save user messages to CSV"""
        if not self.user_messages:
            print("No messages to save")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self.user_name.replace(' ', '_').replace('/', '_')
            filename = f"messages_{safe_name}_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        fieldnames = ['chat_name', 'text', 'created_at']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.user_messages)
        
        print(f"\nSaved to: {filepath}")
        print(f"Total messages: {len(self.user_messages)}")
        return filepath
    
    def run(self, max_messages_per_channel: int = 50000) -> str:
        """Run extraction"""
        print(f"\n{'='*60}")
        print(f"User Messages Extractor")
        print(f"User: {self.user_name}")
        print(f"User ID: {self.user_id}")
        print(f"{'='*60}")
        
        self.fetch_user_channels()
        self.extract_user_messages(max_messages_per_channel)
        return self.save_to_csv()


def main():
    import argparse
    
    # Default: Сергеева Полина
    DEFAULT_USER_ID = "1ef8bfd6-cd52-6758-8876-a0423f4d30a4"
    DEFAULT_USER_NAME = "Сергеева Полина"
    
    parser = argparse.ArgumentParser(description='Extract all messages from a specific user')
    parser.add_argument('--user-id', '-u', default=DEFAULT_USER_ID, help='User ID')
    parser.add_argument('--user-name', '-n', default=DEFAULT_USER_NAME, help='User name')
    parser.add_argument('--max-messages', '-m', type=int, default=50000, help='Max messages per channel')
    
    args = parser.parse_args()
    
    extractor = UserMessagesExtractor(
        user_id=args.user_id,
        user_name=args.user_name
    )
    
    result = extractor.run(max_messages_per_channel=args.max_messages)
    
    if result:
        print(f"\nExtraction complete!")
    else:
        print("\nNo messages found")


if __name__ == "__main__":
    main()

