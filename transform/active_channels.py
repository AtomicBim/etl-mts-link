import sys
import os
import pandas as pd
from typing import Set, Dict, Any, List
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import UniversalExtractor
from abstractions.logging_config import setup_logger
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger(__name__)


class ActiveChannelsTransformer:
    def __init__(self, config_path: str = "config/tokens.json"):
        self.extraction_path = os.getenv("EXTRACTION_PATH", ".")
        self.config_path = config_path
        
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all organization members who use channels"""
        logger.info("Getting all organization members using channels...")
        
        extractor = UniversalExtractor("/channels/organization/members", self.config_path)
        data = extractor.extract()
        
        if not data:
            logger.error("Failed to get organization members")
            return []
        
        # Extract users from the response - handle nested structure
        if 'items' in data:
            users = data['items']
        elif 'data' in data:
            data_content = data['data']
            if isinstance(data_content, dict) and 'items' in data_content:
                users = data_content['items']
            elif isinstance(data_content, list):
                users = data_content
            else:
                users = [data_content] if data_content else []
        else:
            users = []
        
        logger.info(f"Found {len(users)} users")
        return users
    
    def get_user_channels(self, user_id: str) -> List[Dict[str, Any]]:
        """Get channels for a specific user"""
        logger.info(f"Getting channels for user {user_id}...")
        
        extractor = UniversalExtractor("/channels/channels/{userId}", self.config_path)
        data = extractor.extract(userId=user_id)
        
        if not data:
            logger.warning(f"Failed to get channels for user {user_id}")
            return []
        
        # Extract channels from the response - handle nested structure like users
        if 'data' in data and isinstance(data['data'], dict) and 'items' in data['data']:
            channels = data['data']['items']
        elif 'data' in data and isinstance(data['data'], list):
            channels = data['data']
        elif 'items' in data:
            channels = data['items']
        else:
            channels = []
        
        logger.info(f"Found {len(channels)} channels for user {user_id}")
        return channels
    
    def collect_unique_channels(self) -> pd.DataFrame:
        """Collect all unique channels from all users and convert to DataFrame"""
        logger.info("Starting collection of unique channels...")
        
        # Get all users
        users = self.get_all_users()
        
        if not users:
            logger.error("No users found, cannot proceed")
            return pd.DataFrame()
        
        # Collect all channels from all users
        all_channels = {}  # Use dict to automatically handle uniqueness
        
        # Process all users
        logger.info(f"Processing all {len(users)} users...")
        
        for user in users:
            # Use chatUserId for the channels endpoint (UUID format required)
            user_id = user.get('chatUserId')
            if not user_id:
                # Log the user info for debugging
                display_name = user.get('chatMemberProfile', {}).get('displayName', 'Unknown')
                logger.debug(f"Skipping user {display_name} - no chatUserId found")
                continue
                
            user_id_str = str(user_id)
            
            try:
                channels = self.get_user_channels(user_id_str)
                
                for channel in channels:
                    chat_id = channel.get('chatId') or channel.get('id') or channel.get('channelId')
                    if chat_id:
                        chat_id_str = str(chat_id)
                        # Store unique chat info
                        if chat_id_str not in all_channels:
                            all_channels[chat_id_str] = {
                                'chat_id': chat_id_str,
                                'name': channel.get('name', ''),
                                'type': channel.get('type', ''),
                                'is_public': channel.get('isPublic', False),
                                'is_readonly': channel.get('isReadOnly', False),
                                'owner_id': channel.get('ownerID', ''),
                                'organization_id': channel.get('organizationId', ''),
                                'description': channel.get('description', ''),
                                'is_notifiable': channel.get('isNotifiable', True),
                                'unread_count': channel.get('unreadMessageCount', 0)
                            }
                            
            except Exception as e:
                logger.error(f"Error processing user {user_id_str}: {e}")
                continue
        
        logger.info(f"Found {len(all_channels)} unique channels across all users")
        
        # Convert to DataFrame
        if all_channels:
            df = pd.DataFrame(list(all_channels.values()))
            logger.info(f"Created DataFrame with shape: {df.shape}")
            return df
        else:
            logger.warning("No channels found")
            return pd.DataFrame()
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """Save DataFrame to CSV file"""
        if df.empty:
            logger.error("DataFrame is empty, nothing to save")
            return ""
        
        if not filename:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"active_channels_{timestamp}.csv"
        
        filepath = os.path.join(self.extraction_path, filename)
        os.makedirs(self.extraction_path, exist_ok=True)
        
        try:
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.success(f"Active channels data saved to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")
            return ""
    
    def run(self, output_filename: str = None) -> str:
        """Run the complete active channels transformation"""
        logger.info("Starting active channels transformation...")
        
        # Collect unique channels
        df = self.collect_unique_channels()
        
        if df.empty:
            logger.error("No data to process")
            return ""
        
        # Save to CSV
        filepath = self.save_to_csv(df, output_filename)
        
        if filepath:
            logger.success("Active channels transformation completed successfully!")
            logger.info(f"Summary:")
            logger.info(f"  - Total unique channels: {len(df)}")
            logger.info(f"  - Output file: {filepath}")
            
            # Show sample of data
            logger.info("Sample data:")
            print(df.head().to_string(index=False))
        
        return filepath


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract and transform active channels data')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--config', '-c', default='config/tokens.json', help='Config file path')
    
    args = parser.parse_args()
    
    transformer = ActiveChannelsTransformer(args.config)
    result = transformer.run(args.output)
    
    if result:
        logger.success(f"Transformation completed: {result}")
    else:
        logger.error("Transformation failed")


if __name__ == "__main__":
    main()