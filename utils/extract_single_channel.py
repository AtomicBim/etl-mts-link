#!/usr/bin/env python3
"""
Script to extract messages from a single channel with simplified output
"""
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import UniversalExtractor


def load_organization_mapping(data_path="data"):
    """Load organization mapping from JSON file"""
    filepath = os.path.join(data_path, "organizations_mapping.json")
    mapping = {}
    
    if not os.path.exists(filepath):
        print(f"Warning: organizations_mapping.json not found in {data_path}")
        print("Organization IDs will be used instead of names")
        return mapping
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for org in data.get('organizations', []):
                org_id = org.get('organization_id')
                org_name = org.get('organization_name')
                if org_id and org_name:
                    mapping[org_id] = org_name
        
        if mapping:
            print(f"Loaded {len(mapping)} organization mappings")
    except Exception as e:
        print(f"Warning: Could not load organization mapping: {e}")
    
    return mapping


def timestamp_to_human_readable(timestamp_ms):
    """Convert timestamp in milliseconds to human readable format"""
    try:
        timestamp_sec = timestamp_ms / 1000
        dt = datetime.fromtimestamp(timestamp_sec)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, OverflowError):
        return f"invalid_timestamp_{timestamp_ms}"


def simplify_message(message, chat_id=None, chat_name=None, 
                    organization_id=None, organization_name=None):
    """Simplify a single message"""
    simplified = {}
    
    if chat_id:
        simplified["chat_id"] = chat_id
    if chat_name:
        simplified["chat_name"] = chat_name
    if organization_id:
        simplified["organization_id"] = organization_id
    if organization_name:
        simplified["organization_name"] = organization_name
    
    # Extract author info
    author_id = message.get("authorId")
    if author_id:
        simplified["authorId"] = author_id
    
    # Keep text
    if "text" in message:
        simplified["text"] = message["text"]
    
    # Convert createdAtMs to human readable time
    if "createdAtMs" in message and message["createdAtMs"] is not None:
        simplified["createdAt"] = timestamp_to_human_readable(message["createdAtMs"])
    
    return simplified


def extract_messages_from_response(data):
    """Extract messages from API response"""
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
        elif 'messages' in data:
            return data['messages']
        elif 'items' in data:
            return data['items']
    
    return []


def fetch_channel_messages(channel_id, chat_name="Unknown", viewer_id=None, max_messages=50000):
    """Fetch all messages from a channel"""
    print(f"\n{'='*60}")
    print(f"Fetching messages for channel: {channel_id}")
    print(f"Channel name: {chat_name}")
    print(f"{'='*60}\n")
    
    # Try different endpoints
    endpoints_to_try = [
        "/chats/channel/{chatId}/messages",
        "/chats/channels/{chatId}/messages"
    ]
    
    all_messages = []
    seen_message_ids = set()
    
    for endpoint in endpoints_to_try:
        print(f"\nTrying endpoint: {endpoint}")
        extractor = UniversalExtractor(endpoint)
        
        limit = 100
        from_message_id = None
        max_requests = max(1, max_messages // limit)
        request_count = 0
        success = False
        
        try:
            while request_count < max_requests:
                params = {
                    'chatId': channel_id,
                    'limit': limit,
                    'direction': 'Before'
                }
                
                # Add viewerId if provided
                if viewer_id:
                    params['viewerId'] = viewer_id
                
                if from_message_id:
                    params['fromMessageId'] = from_message_id
                
                print(f"  Request #{request_count + 1}, params: {params}")
                data = extractor.extract(**params)
                
                if data is None:
                    print(f"  Failed to fetch data")
                    break
                
                if not data:
                    print(f"  No data returned - end of messages")
                    break
                
                # Extract messages
                messages = extract_messages_from_response(data)
                if not messages:
                    print(f"  No messages in response")
                    break
                
                # Filter duplicates
                new_messages = []
                for message in messages:
                    msg_id = message.get('id') or message.get('messageId')
                    if msg_id and msg_id not in seen_message_ids:
                        seen_message_ids.add(msg_id)
                        new_messages.append(message)
                
                if not new_messages:
                    print(f"  No new unique messages - stopping pagination")
                    break
                
                all_messages.extend(new_messages)
                print(f"  Fetched {len(messages)} messages ({len(new_messages)} new, total: {len(all_messages)})")
                
                # Check if we reached the end
                if len(messages) < limit:
                    print(f"  Received {len(messages)} < {limit} messages, reached end")
                    success = True
                    break
                
                # Get next message ID for pagination
                from_message_id = messages[-1].get('id') or messages[-1].get('messageId')
                if not from_message_id:
                    print(f"  No message ID for pagination, stopping")
                    break
                
                request_count += 1
                success = True
            
            if success and all_messages:
                print(f"\n[OK] Successfully fetched {len(all_messages)} messages using {endpoint}")
                break
            
        except Exception as e:
            print(f"  Error with {endpoint}: {e}")
            continue
    
    if not all_messages:
        print(f"\n[ERROR] Failed to fetch messages from all endpoints")
        return None
    
    return all_messages


def save_simplified_json(channel_id, chat_name, messages, output_dir="data",
                        organization_id=None, organization_name=None):
    """Save simplified JSON with messages"""
    if not messages:
        print("No messages to save")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_chat_id = channel_id.replace('/', '_').replace('\\', '_')
    
    # Simplify messages
    simplified_messages = [
        simplify_message(
            msg, channel_id, chat_name, 
            organization_id, organization_name
        ) 
        for msg in messages
    ]
    
    # Create simplified data structure
    simplified_data = {
        "chat_id": channel_id,
        "chat_name": chat_name,
        "organization_id": organization_id or "",
        "organization_name": organization_name or "",
        "extraction_timestamp": datetime.now().isoformat(),
        "total_messages": len(messages),
        "messages": simplified_messages
    }
    
    # Save JSON
    filename = f"chat_{safe_chat_id}_{timestamp}_simplified.json"
    filepath = os.path.join(output_dir, filename)
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(simplified_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"[OK] Saved simplified JSON:")
    print(f"  File: {filepath}")
    print(f"  Total messages: {len(simplified_messages)}")
    if organization_name:
        print(f"  Organization: {organization_name}")
    print(f"{'='*60}")
    
    return filepath


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract messages from a single channel')
    parser.add_argument('--channel-id', required=True, help='Channel ID to extract')
    parser.add_argument('--channel-name', default='Unknown Channel', help='Channel name (optional)')
    parser.add_argument('--viewer-id', help='Viewer ID (optional, may help with private channels)')
    parser.add_argument('--max-messages', type=int, default=50000, help='Maximum messages to extract')
    parser.add_argument('--output-dir', default='data', help='Output directory')
    parser.add_argument('--organization-id', help='Organization ID (optional)')
    
    args = parser.parse_args()
    
    # Load organization mapping
    org_mapping = load_organization_mapping(args.output_dir)
    
    # Get organization name if ID provided
    organization_id = args.organization_id
    organization_name = None
    
    if organization_id and org_mapping:
        organization_name = org_mapping.get(organization_id, organization_id)
        print(f"Organization: {organization_name}")
    elif organization_id:
        organization_name = organization_id
        print(f"Organization ID: {organization_id} (no mapping found)")
    
    # Fetch messages
    messages = fetch_channel_messages(
        channel_id=args.channel_id,
        chat_name=args.channel_name,
        viewer_id=args.viewer_id,
        max_messages=args.max_messages
    )
    
    if not messages:
        print("\n[ERROR] Failed to fetch messages")
        return 1
    
    # Save simplified JSON
    output_file = save_simplified_json(
        channel_id=args.channel_id,
        chat_name=args.channel_name,
        messages=messages,
        output_dir=args.output_dir,
        organization_id=organization_id,
        organization_name=organization_name
    )
    
    if output_file:
        print(f"\n[SUCCESS] Simplified JSON saved to: {output_file}")
        return 0
    else:
        print("\n[ERROR] Failed to save output file")
        return 1


if __name__ == "__main__":
    sys.exit(main())

