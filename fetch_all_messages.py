#!/usr/bin/env python3
"""
Script to fetch all messages from a channel by implementing pagination
"""

import sys
import os
import json
import time
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from abstractions.extract import BaseExtractor
from abstractions.logging_config import setup_logger

logger = setup_logger(__name__)


class AllMessagesExtractor(BaseExtractor):
    """Extractor that fetches all messages from a channel using pagination"""
    
    def get_endpoint(self):
        return "/chats/channel/{chatId}/messages"
    
    def get_url_params(self, **kwargs):
        params = {}
        if 'viewerId' in kwargs:
            params['viewerId'] = kwargs['viewerId']
        if 'fromMessageId' in kwargs:
            params['fromMessageId'] = kwargs['fromMessageId']
        if 'parrentMessageId' in kwargs:
            params['parrentMessageId'] = kwargs['parrentMessageId']
        if 'direction' in kwargs:
            params['direction'] = kwargs['direction']
        if 'limit' in kwargs:
            params['limit'] = min(kwargs['limit'], 100)  # Enforce API limit
        else:
            params['limit'] = 100  # Use maximum allowed
        
        return params if params else None
    
    def fetch_all_messages(self, chat_id: str, **kwargs) -> List[Dict[Any, Any]]:
        """
        Fetch all messages from a channel using pagination
        
        Args:
            chat_id: Channel ID to fetch messages from
            **kwargs: Additional parameters (viewerId, direction, etc.)
        
        Returns:
            List of all messages
        """
        all_messages = []
        from_message_id = kwargs.get('fromMessageId')
        direction = kwargs.get('direction', 'Before')
        
        logger.info(f"Starting to fetch all messages from channel {chat_id}")
        
        page = 1
        while True:
            logger.info(f"Fetching page {page}...")
            
            # Prepare parameters for this request
            request_kwargs = kwargs.copy()
            request_kwargs['chatId'] = chat_id
            if from_message_id:
                request_kwargs['fromMessageId'] = from_message_id
            request_kwargs['limit'] = 100  # Maximum allowed
            
            # Fetch current page
            try:
                data = self.extract(**request_kwargs)
                if not data:
                    logger.info("No more data available")
                    break
                
                # Handle both direct array response and wrapped response
                if isinstance(data, list):
                    messages = data
                elif isinstance(data, dict) and 'data' in data:
                    if isinstance(data['data'], dict) and 'items' in data['data']:
                        messages = data['data']['items']
                    else:
                        messages = data['data']
                else:
                    logger.warning(f"Unexpected data format: {type(data)}")
                    break
                
                if not messages:
                    logger.info("No more messages available")
                    break
                
                logger.info(f"Fetched {len(messages)} messages on page {page}")
                all_messages.extend(messages)
                
                # If we got fewer than 100 messages, we've reached the end
                if len(messages) < 100:
                    logger.info("Reached the end (fewer than 100 messages returned)")
                    break
                
                # Get the last message ID for next iteration
                if direction == 'Before':
                    # When going backwards, use the oldest message as the next starting point
                    last_message = messages[-1]
                    from_message_id = last_message.get('id') or last_message.get('messageId')
                elif direction == 'After':
                    # When going forwards, use the newest message as the next starting point
                    first_message = messages[0]
                    from_message_id = first_message.get('id') or first_message.get('messageId')
                else:  # Around
                    logger.warning("'Around' direction doesn't support pagination well")
                    break
                
                if not from_message_id:
                    logger.warning("Could not find message ID for pagination")
                    break
                
                page += 1
                
                # Optional: Add a small delay to be nice to the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.success(f"Fetched {len(all_messages)} total messages across {page} pages")
        return all_messages


def fetch_all_messages_from_channel(chat_id: str, **kwargs) -> Optional[str]:
    """
    Fetch all messages from a channel and save to file
    
    Args:
        chat_id: Channel ID to fetch messages from
        **kwargs: Additional parameters
    
    Returns:
        Filename of saved data or None if failed
    """
    extractor = AllMessagesExtractor()
    all_messages = extractor.fetch_all_messages(chat_id, **kwargs)
    
    if all_messages:
        # Save all messages to file - use same format as channel_messages
        filename = extractor.save_to_file(all_messages)
        logger.info(f"Saved {len(all_messages)} messages to {filename}")
        return filename
    
    return None


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch all messages from a MTS-Link chat channel')
    parser.add_argument('chat_id', help='Channel ID to fetch messages from')
    parser.add_argument('--viewerId', help='Viewer ID for the request')
    parser.add_argument('--direction', help='Direction to paginate (Before, After)', 
                        choices=['Before', 'After'], default='Before')
    parser.add_argument('--fromMessageId', help='Starting message ID')
    parser.add_argument('--parrentMessageId', help='Parent message ID for discussions')
    
    args = parser.parse_args()
    
    kwargs = {}
    if args.viewerId:
        kwargs['viewerId'] = args.viewerId
    if args.direction:
        kwargs['direction'] = args.direction
    if args.fromMessageId:
        kwargs['fromMessageId'] = args.fromMessageId
    if args.parrentMessageId:
        kwargs['parrentMessageId'] = args.parrentMessageId
    
    logger.info(f"Fetching all messages from channel: {args.chat_id}")
    result = fetch_all_messages_from_channel(args.chat_id, **kwargs)
    
    if result:
        logger.success(f"All messages saved to: {result}")
        print(f"File saved: {result}")
    else:
        logger.error("Failed to fetch messages")
        sys.exit(1)


if __name__ == "__main__":
    main()