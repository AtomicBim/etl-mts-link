import sys
import os
import csv
import json
import glob
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import statistics

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import UniversalExtractor


class ChatAnalyzer:
    """Analyzer for extracting detailed statistics from unique chats"""

    def __init__(self, data_path: str = None, days_back: int = None):
        # Default to data directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = data_path or os.path.join(project_root, "data")

        # Chat archive path
        self.archive_path = os.path.join(self.data_path, "chats_archive")

        # Archive settings
        self.save_archives = True
        
        # Date filtering
        self.days_back = days_back
        if days_back is not None:
            self.end_date = datetime.now().date()
            self.start_date = self.end_date - timedelta(days=days_back)
            print(f"Filtering messages from {self.start_date} to {self.end_date}")
        else:
            self.start_date = None
            self.end_date = None

        # Initialize extractors
        self.channel_users_extractor = UniversalExtractor("/chats/channels/{channelId}/users")

        # Initialize multiple message extractors for fallback
        self.channel_messages_extractor = UniversalExtractor("/chats/channel/{chatId}/messages")
        self.channels_messages_extractor = UniversalExtractor("/chats/channels/{chatId}/messages")  # Fallback endpoint

        # Data storage
        self.chats_data: List[Dict[str, Any]] = []
        self.analysis_results: List[Dict[str, Any]] = []

        # Progress tracking
        self.processed_count = 0
        self.total_count = 0

        # User mapping for full names
        self.user_mapping: Dict[str, str] = {}
        self._load_user_mapping()

        # Organization mapping for organization names
        self.organization_mapping: Dict[str, str] = {}
        self._load_organization_mapping()

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

    def _load_organization_mapping(self):
        """Load organization mapping from organizations_mapping.json"""
        try:
            # Find the organizations_mapping.json file
            filepath = os.path.join(self.data_path, "organizations_mapping.json")
            
            if not os.path.exists(filepath):
                print("Warning: No organizations_mapping.json file found. Run build_organizations_mapping.py first.")
                print("Organization names will show as organization_id")
                return

            print(f"Loading organization mapping from: organizations_mapping.json")

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                organizations = data.get('organizations', [])
                
                for org in organizations:
                    org_id = org.get('organization_id', '')
                    org_name = org.get('organization_name', '')
                    
                    if org_id:
                        self.organization_mapping[org_id] = org_name or org_id

            print(f"Loaded {len(self.organization_mapping)} organization mappings")

        except Exception as e:
            print(f"Warning: Could not load organization mapping: {e}")
            print("Organization names will show as organization_id")

    def load_unique_chats(self, filename: str = None) -> bool:
        """Load unique chats data from CSV file"""
        if filename:
            filepath = os.path.join(self.data_path, filename)
        else:
            # Find the most recent unique_chats file
            pattern = os.path.join(self.data_path, "unique_chats_*.csv")
            files = glob.glob(pattern)
            if not files:
                print("No unique chats CSV files found in data directory")
                return False

            # Sort by modification time, get newest
            filepath = max(files, key=os.path.getmtime)
            print(f"Using most recent unique chats file: {os.path.basename(filepath)}")

        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                self.chats_data = list(reader)

            print(f"Loaded {len(self.chats_data)} unique chats for analysis")
            self.total_count = len(self.chats_data)
            return True

        except Exception as e:
            print(f"Error loading unique chats file: {e}")
            return False

    def get_chat_users_count(self, chat_id: str) -> int:
        """Get number of users in a chat using smart pagination"""
        try:
            print(f"  Fetching users for chat {chat_id}")

            # First try with high limit to see if API supports it
            print(f"    Trying single request with limit=2000")
            data = self.channel_users_extractor.extract(
                channelId=chat_id,
                limit=2000,
                offset=0
            )

            if data:
                users = self._extract_users_from_response(data)
                if users:
                    user_count = len(users)
                    print(f"    Got {user_count} users in single request")
                    # If we got less than 2000, we likely got all users
                    if user_count < 2000:
                        return user_count
                    else:
                        print(f"    Got full 2000 users, may be more - switching to pagination")
                        # Continue with pagination from offset 2000
                        return self._paginate_users_from_offset(chat_id, users, 2000)

            print(f"    Single request failed, using pagination with limit=100")
            # Fallback to pagination with limit=100
            return self._paginate_users_from_offset(chat_id, [], 0)

        except Exception as e:
            print(f"    Error fetching users for chat {chat_id}: {e}")
            return 0

    def _paginate_users_from_offset(self, chat_id: str, initial_users: List[Dict[str, Any]], start_offset: int) -> int:
        """Continue pagination from given offset with existing users"""
        all_users = initial_users.copy()
        seen_user_ids = set()

        # Track existing user IDs
        for user in all_users:
            user_id = user.get('userId') or user.get('id') or str(user)
            if user_id:
                seen_user_ids.add(user_id)

        offset = start_offset
        limit = 100
        iteration = 0

        print(f"    Starting pagination from offset {offset} with {len(all_users)} existing users")

        while True:  # No artificial limit - paginate until we get all users
            print(f"    Paginating: offset={offset}, limit={limit} (iteration {iteration + 1})")

            data = self.channel_users_extractor.extract(
                channelId=chat_id,
                limit=limit,
                offset=offset
            )

            # No data or empty response = end of data
            if not data:
                print(f"    No data returned - end of users")
                break

            users_batch = self._extract_users_from_response(data)
            if not users_batch:
                print(f"    No users in response - end of data")
                break

            # Filter new unique users
            new_users = []
            for user in users_batch:
                user_id = user.get('userId') or user.get('id') or str(user)
                if user_id and user_id not in seen_user_ids:
                    seen_user_ids.add(user_id)
                    new_users.append(user)

            print(f"    Batch: {len(users_batch)} total, {len(new_users)} new unique")

            # No new users = we've reached the end or are getting repeats
            if not new_users:
                print(f"    No new unique users found - stopping pagination")
                break

            all_users.extend(new_users)

            # Got less than requested limit = end of data
            if len(users_batch) < limit:
                print(f"    Received {len(users_batch)} < {limit} - end of data")
                break

            offset += limit
            iteration += 1

        final_count = len(all_users)
        if iteration > 0:
            print(f"  Completed: {final_count} total unique users (after {iteration} pagination requests)")
        else:
            print(f"  Completed: {final_count} total unique users")
        return final_count

    def get_chat_messages_stats(self, chat_id: str, max_messages: int = 50000, chat_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get message statistics for a chat with fallback endpoints"""

        # Try different message extractors in order
        extractors_to_try = [
            (self.channel_messages_extractor, "/chats/channel/{chatId}/messages"),
            (self.channels_messages_extractor, "/chats/channels/{chatId}/messages")
        ]

        last_error = None

        for extractor, endpoint_desc in extractors_to_try:
            try:
                print(f"  Fetching messages for chat {chat_id} using {endpoint_desc}")
                result = self._fetch_messages_with_extractor(extractor, chat_id, max_messages, chat_info)

                if result.get('message_count', 0) > 0 or not result.get('error'):
                    print(f"  [OK] Successfully fetched messages using {endpoint_desc}")
                    return result

            except Exception as e:
                error_msg = str(e)
                print(f"    [ERROR] Failed with {endpoint_desc}: {error_msg}")
                last_error = error_msg

                # Don't try fallback if it's a 403 (permission denied) - likely same for all endpoints
                if "403" in error_msg:
                    print(f"    -> Access denied - skipping other endpoints")
                    break

                continue

        # All extractors failed
        print(f"    [ERROR] All message endpoints failed for chat {chat_id}")
        return self._create_error_result(last_error or "All endpoints failed", chat_id)

    def _extract_messages_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract messages from API response"""
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
            elif 'messages' in data:
                return data['messages']
            elif 'items' in data:
                return data['items']

        return []

    def _extract_users_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract users from API response"""
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
            elif 'users' in data:
                return data['users'] if isinstance(data['users'], list) else []
            elif 'items' in data:
                return data['items'] if isinstance(data['items'], list) else []

        return []

    def _format_extractor_error(self, extractor, chat_id: str) -> str:
        """Build a descriptive error message based on extractor state"""
        endpoint = getattr(extractor, 'endpoint_path', None)
        if endpoint is None and hasattr(extractor, 'get_endpoint'):
            try:
                endpoint = extractor.get_endpoint()
            except Exception:
                endpoint = 'unknown_endpoint'
        endpoint = endpoint or 'unknown_endpoint'

        status = getattr(extractor, 'last_response_status', None)
        error_text = getattr(extractor, 'last_error', '') or 'Unknown error'
        response_body = getattr(extractor, 'last_response_body', '')

        if response_body:
            response_body = response_body.strip()
            if len(response_body) > 500:
                response_body = response_body[:500] + "...[truncated]"

        parts = [f"Endpoint {endpoint}", f"chat {chat_id}"]
        if status:
            parts.append(f"status {status}")
        message = f"{' | '.join(parts)}: {error_text}"

        if response_body:
            message = f"{message} | Response body: {response_body}"

        return message

    def _fetch_messages_with_extractor(self, extractor, chat_id: str, max_messages: int, chat_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fetch messages using a specific extractor with cursor-based pagination"""
        all_messages = []
        seen_message_ids = set()  # Track unique message IDs to prevent duplicates
        limit = 100  # Messages per request
        from_message_id = None
        max_requests = max(1, max_messages // limit)  # Calculate based on desired max messages, minimum 1
        request_count = 0
        
        # Get viewerId from chat_info for private channels
        viewer_id = None
        if chat_info:
            # Try to use discovered_via_user_id (user who can access this chat)
            viewer_id = chat_info.get('discovered_via_user_id') or chat_info.get('owner_id')
            # Skip if viewer_id is 'unknown' or empty (not a valid UUID)
            if viewer_id and viewer_id != 'unknown' and viewer_id.strip():
                print(f"    Using viewerId={viewer_id} for private channel access")
            else:
                viewer_id = None

        while request_count < max_requests:
            params = {
                'chatId': chat_id,
                'limit': limit,
                'direction': 'Before'
            }
            
            # Add viewerId for private channels access
            if viewer_id:
                params['viewerId'] = viewer_id
                
            if from_message_id:
                params['fromMessageId'] = from_message_id

            data = extractor.extract(**params)

            if data is None:
                error_msg = self._format_extractor_error(extractor, chat_id)
                print(f"    [ERROR] {error_msg}")
                raise RuntimeError(error_msg)

            if not data:
                print(f"    No data returned - end of messages")
                break

            # Extract messages from response
            messages = self._extract_messages_from_response(data)
            if not messages:
                break

            # Filter out duplicate messages (in case API returns overlapping results)
            new_messages = []
            for message in messages:
                msg_id = message.get('id') or message.get('messageId')
                if msg_id and msg_id not in seen_message_ids:
                    seen_message_ids.add(msg_id)
                    new_messages.append(message)

            # If no new messages, we've reached the end or getting duplicates
            if not new_messages:
                print(f"    No new unique messages - stopping pagination")
                break

            all_messages.extend(new_messages)
            print(f"    Fetched {len(messages)} messages ({len(new_messages)} new, total: {len(all_messages)}, request #{request_count + 1})")

            # Get the oldest message ID for next request (use last message from original batch)
            if len(messages) < limit:
                # Reached the end of chat history
                print(f"    Received {len(messages)} < {limit} messages, reached end of chat history")
                break

            from_message_id = messages[-1].get('id') or messages[-1].get('messageId')
            if not from_message_id:
                print(f"    No message ID found for pagination, stopping")
                break

            request_count += 1

        # Check if we hit the limit
        if request_count >= max_requests:
            print(f"    WARNING: Reached maximum request limit ({max_requests} requests = {max_messages} messages)")
            print(f"    Chat may have more messages than analyzed ({len(all_messages)} messages collected)")
        else:
            print(f"    [OK] Collected all {len(all_messages)} messages from chat")

        # Save chat archive before analysis
        if self.save_archives:
            self._save_chat_archive(chat_id, all_messages, chat_info)

        # Analyze messages
        return self._analyze_messages(all_messages)

    def _create_error_result(self, error_msg: str, chat_id: str) -> Dict[str, Any]:
        """Create standardized error result"""
        # Classify error types for better understanding
        if "404" in error_msg and "Channel not found" in error_msg:
            print(f"    -> Chat messages not accessible (404 - Channel not found)")
            print(f"    -> Tried both /chats/channel/{chat_id}/messages and /chats/channels/{chat_id}/messages")
            print(f"    -> This may indicate: restricted access, archived chat, or different permissions")
            error_type = '404_channel_not_found'
        elif "403" in error_msg:
            print(f"    -> Access denied to chat messages (403)")
            print(f"    -> User may not have permission to read messages in this chat")
            error_type = '403_access_denied'
        elif "500" in error_msg:
            print(f"    -> Server error when fetching messages (500)")
            print(f"    -> Temporary server issue or internal API problem")
            error_type = '500_server_error'
        else:
            print(f"    -> Other error: {error_msg}")
            error_type = 'other'

        return {
            'message_count': 0,
            'average_message_length': 0,
            'unique_senders': 0,
            'error': error_msg,
            'error_type': error_type
        }

    def _filter_messages_by_date(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter messages by date range if days_back is set"""
        if self.start_date is None or self.end_date is None:
            return messages
        
        filtered_messages = []
        for message in messages:
            # Try to extract date from createdAtMs
            created_at_ms = message.get('createdAtMs')
            if created_at_ms:
                try:
                    timestamp_sec = created_at_ms / 1000
                    msg_date = datetime.fromtimestamp(timestamp_sec).date()
                    
                    if self.start_date <= msg_date <= self.end_date:
                        filtered_messages.append(message)
                except (ValueError, OSError, OverflowError):
                    # Invalid timestamp, skip
                    continue
        
        return filtered_messages
    
    def _analyze_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze list of messages and return statistics"""
        # Filter by date if needed
        messages = self._filter_messages_by_date(messages)
        
        if not messages:
            return {
                'message_count': 0,
                'average_message_length': 0,
                'unique_senders': 0
            }

        message_lengths = []
        unique_senders = set()

        for message in messages:
            # Extract message text
            text = message.get('text') or message.get('content') or message.get('message', '')
            if isinstance(text, str):
                message_lengths.append(len(text))

            # Extract sender info - check all possible fields
            sender = None
            if 'senderId' in message and message['senderId']:
                sender = message['senderId']
            elif 'userId' in message and message['userId']:
                sender = message['userId']
            elif 'authorId' in message and message['authorId']:
                sender = message['authorId']
            elif 'author' in message and isinstance(message['author'], dict) and 'id' in message['author']:
                sender = message['author']['id']

            if sender:
                unique_senders.add(str(sender))

        # Calculate average message length
        avg_length = statistics.mean(message_lengths) if message_lengths else 0

        return {
            'message_count': len(messages),
            'average_message_length': round(avg_length, 2),
            'unique_senders': len(unique_senders)
        }

    def analyze_chat(self, chat_data: Dict[str, Any], max_messages: int = 50000) -> Dict[str, Any]:
        """Analyze a single chat and return comprehensive statistics"""
        chat_id = chat_data.get('chat_id')
        chat_name = chat_data.get('name', 'Unknown')

        print(f"Analyzing chat: {chat_name} ({chat_id})")

        # Get user count
        users_count = self.get_chat_users_count(chat_id)

        # Get message statistics (passing chat info for archiving)
        message_stats = self.get_chat_messages_stats(chat_id, max_messages, chat_data)

        # Get organization name from mapping
        organization_id = chat_data.get('organization_id', '')
        organization_name = self.organization_mapping.get(organization_id, organization_id)

        # Combine all data
        result = {
            'chat_id': chat_id,
            'chat_name': chat_name,
            'chat_type': chat_data.get('type', ''),
            'is_public': chat_data.get('is_public', ''),
            'organization_id': organization_id,
            'organization_name': organization_name,
            'discovered_via_user_id': chat_data.get('discovered_via_user_id', ''),
            'users_count': users_count,
            'message_count': message_stats['message_count'],
            'average_message_length': message_stats['average_message_length'],
            'unique_message_senders': message_stats.get('unique_senders', 0),
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_error': message_stats.get('error', '')
        }

        return result

    def analyze_all_chats(self, limit: int = None, save_intermediate: bool = True, max_messages_per_chat: int = 50000) -> None:
        """Analyze all loaded chats"""
        if not self.chats_data:
            print("No chats data loaded. Call load_unique_chats() first.")
            return

        print(f"Starting analysis of {len(self.chats_data)} chats...")

        # Apply limit if specified
        chats_to_analyze = self.chats_data[:limit] if limit else self.chats_data

        self.analysis_results = []
        self.processed_count = 0

        for i, chat_data in enumerate(chats_to_analyze):
            self.processed_count += 1

            print(f"\nProgress: {self.processed_count}/{len(chats_to_analyze)}")

            try:
                result = self.analyze_chat(chat_data, max_messages_per_chat)
                self.analysis_results.append(result)

                # Save intermediate results every 10 chats
                if save_intermediate and self.processed_count % 10 == 0:
                    self._save_intermediate_results()

            except Exception as e:
                print(f"Error analyzing chat {chat_data.get('chat_id', 'Unknown')}: {e}")
                # Add error record
                self.analysis_results.append({
                    'chat_id': chat_data.get('chat_id', ''),
                    'chat_name': chat_data.get('name', ''),
                    'analysis_error': str(e),
                    'analysis_timestamp': datetime.now().isoformat()
                })

        # Clean up intermediate files after successful completion
        self._cleanup_intermediate_files()

        # Calculate error statistics
        error_stats = self._calculate_error_statistics()

        print(f"\nCompleted analysis of {len(self.analysis_results)} chats")
        if error_stats['total_errors'] > 0:
            print(f"\nError Summary:")
            print(f"  Total chats with errors: {error_stats['total_errors']}")
            print(f"  Success rate: {error_stats['success_rate']:.1f}%")
            print(f"  404 'Channel not found' errors: {error_stats['404_channel_not_found']}")
            print(f"  403 'Access denied' errors: {error_stats['403_access_denied']}")
            print(f"  500 'Server error' errors: {error_stats['500_server_error']}")
            print(f"  Other errors: {error_stats['other']}")

            if error_stats['404_channel_not_found'] > 0:
                print(f"\n  Analysis of 404 errors:")
                print(f"  - These chats have user data accessible but messages are restricted")
                print(f"  - Tried both endpoint variants: /chats/channel/{{id}}/messages and /chats/channels/{{id}}/messages")
                print(f"  - Possible causes: archived chats, permission restrictions, or API inconsistencies")

            if error_stats['403_access_denied'] > 0:
                print(f"\n  Analysis of 403 errors:")
                print(f"  - User lacks permission to read messages in these chats")
                print(f"  - These chats may be private or require special access")
        else:
            print("All chats processed successfully!")

    def _calculate_error_statistics(self) -> Dict[str, Any]:
        """Calculate error statistics from analysis results"""
        total_chats = len(self.analysis_results)
        error_counts = {
            '404_channel_not_found': 0,
            '403_access_denied': 0,
            '500_server_error': 0,
            'other': 0
        }

        for result in self.analysis_results:
            error_type = result.get('error_type')
            if error_type in error_counts:
                error_counts[error_type] += 1
            elif 'error' in result or 'analysis_error' in result:
                error_counts['other'] += 1

        total_errors = sum(error_counts.values())
        success_rate = ((total_chats - total_errors) / total_chats * 100) if total_chats > 0 else 0

        return {
            'total_errors': total_errors,
            'success_rate': success_rate,
            **error_counts
        }

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

    def _timestamp_to_human_readable(self, timestamp_ms: int) -> str:
        """Convert timestamp in milliseconds to human readable format"""
        try:
            timestamp_sec = timestamp_ms / 1000
            dt = datetime.fromtimestamp(timestamp_sec)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError, OverflowError):
            return f"invalid_timestamp_{timestamp_ms}"

    def _simplify_message(self, message: Dict[str, Any], chat_id: str = None, chat_name: str = None, 
                         organization_id: str = None, organization_name: str = None) -> Dict[str, Any]:
        """Simplify a single message by keeping only essential fields"""
        simplified = {}

        if chat_id:
            simplified["chat_id"] = chat_id
        if chat_name:
            simplified["chat_name"] = chat_name
        if organization_id:
            simplified["organization_id"] = organization_id
        if organization_name:
            simplified["organization_name"] = organization_name

        # Extract author info with user mapping
        author_id = message.get("authorId")
        if author_id:
            simplified["authorId"] = author_id
            # Look up full name from user mapping
            simplified["full_name"] = self.user_mapping.get(author_id, "Unknown User")

        # Keep text
        if "text" in message:
            simplified["text"] = message["text"]

        # Convert createdAtMs to human readable time
        if "createdAtMs" in message and message["createdAtMs"] is not None:
            simplified["createdAt"] = self._timestamp_to_human_readable(message["createdAtMs"])

        return simplified

    def _process_and_save_simplified(self, chat_id: str, messages: List[Dict[str, Any]], chat_info: Dict[str, Any] = None):
        """Process messages and save simplified JSON and CSV versions"""
        if not messages:
            return

        chat_name = chat_info.get('name', 'Unknown Chat') if chat_info else 'Unknown Chat'
        
        # Get organization info
        organization_id = chat_info.get('organization_id', '') if chat_info else ''
        organization_name = self.organization_mapping.get(organization_id, organization_id) if organization_id else ''
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_chat_id = chat_id.replace('/', '_').replace('\\', '_')

        # Simplify messages with organization info
        simplified_messages = [
            self._simplify_message(msg, chat_id, chat_name, organization_id, organization_name) 
            for msg in messages
        ]

        # Create simplified data structure
        simplified_data = {
            "chat_id": chat_id,
            "chat_name": chat_name,
            "extraction_timestamp": datetime.now().isoformat(),
            "original_total_messages": len(messages),
            "simplified_messages_count": len(simplified_messages),
            "processing_timestamp": datetime.now().isoformat(),
            "messages": simplified_messages
        }

        # Save simplified JSON to archive
        simplified_json_filename = f"chat_{safe_chat_id}_{timestamp}_simplified.json"
        
        try:
            os.makedirs(self.archive_path, exist_ok=True)
            json_path = os.path.join(self.archive_path, simplified_json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(simplified_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"    Warning: Could not save simplified JSON: {e}")

        # Save simplified CSV to archive
        simplified_csv_filename = f"chat_{safe_chat_id}_{timestamp}_simplified.csv"
        fieldnames = ['chat_id', 'chat_name', 'organization_id', 'organization_name', 'authorId', 'full_name', 'text', 'createdAt']

        try:
            os.makedirs(self.archive_path, exist_ok=True)
            csv_path = os.path.join(self.archive_path, simplified_csv_filename)
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for message in simplified_messages:
                    row = {field: message.get(field, '') for field in fieldnames}
                    writer.writerow(row)
        except Exception as e:
            print(f"    Warning: Could not save simplified CSV: {e}")

        print(f"    Simplified files saved (JSON + CSV)")

    def _save_chat_archive(self, chat_id: str, messages: List[Dict[str, Any]], chat_info: Dict[str, Any] = None):
        """Save complete chat archive plus simplified versions"""
        if not messages:
            return

        # Create filename based on chat ID and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_chat_id = chat_id.replace('/', '_').replace('\\', '_')
        filename = f"chat_{safe_chat_id}_{timestamp}.json"

        # Create archive data structure
        archive_data = {
            'chat_id': chat_id,
            'extraction_timestamp': datetime.now().isoformat(),
            'total_messages': len(messages),
            'chat_info': chat_info or {},
            'messages': messages
        }

        # Save to archive
        saved_path = None
        try:
            os.makedirs(self.archive_path, exist_ok=True)
            archive_file_path = os.path.join(self.archive_path, filename)

            with open(archive_file_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2)

            saved_path = archive_file_path
            print(f"    Chat archived ({len(messages)} messages)")
        except Exception as e:
            print(f"    Warning: Could not save chat archive: {e}")

        # Save simplified versions (JSON + CSV)
        self._process_and_save_simplified(chat_id, messages, chat_info)

        return saved_path

    def _save_intermediate_results(self):
        """Save intermediate results with fixed filename to avoid data loss"""
        filename = "chat_analysis_intermediate_current.json"

        # Save intermediate results to archive directory (overwrite same file)
        try:
            os.makedirs(self.archive_path, exist_ok=True)
            filepath = os.path.join(self.archive_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'processed_count': self.processed_count,
                    'total_count': len(self.chats_data) if hasattr(self, 'chats_data') else 0,
                    'timestamp': datetime.now().isoformat(),
                    'results': self.analysis_results
                }, f, ensure_ascii=False, indent=2)
            print(f"  Updated intermediate results ({self.processed_count} chats processed)")
        except Exception as e:
            print(f"  Warning: Could not save intermediate results: {e}")

    def _cleanup_intermediate_files(self):
        """Remove intermediate files after successful completion"""
        filename = "chat_analysis_intermediate_current.json"

        # Remove from archive
        try:
            filepath = os.path.join(self.archive_path, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"  Cleaned up intermediate files")
        except Exception as e:
            print(f"  Warning: Could not remove intermediate file: {e}")

        # Also clean up old timestamped intermediate files (from previous versions)
        self._cleanup_old_intermediate_files()

    def _cleanup_old_intermediate_files(self):
        """Remove old timestamped intermediate files from previous versions"""
        import glob

        # Clean up old intermediate files
        try:
            pattern = os.path.join(self.archive_path, "chat_analysis_intermediate_*.json")
            old_files = glob.glob(pattern)
            for file_path in old_files:
                if "_current.json" not in file_path:  # Don't remove the current file
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
        except Exception:
            pass

    def _find_existing_analysis_files(self, base_filename: str) -> List[str]:
        """Find existing analysis files with the same base name but different timestamps"""
        if not base_filename:
            return []

        # Extract base name without timestamp and extension
        if base_filename.startswith("chat_analysis_") and base_filename.endswith(".csv"):
            pattern = "chat_analysis_*.csv"
        else:
            name_without_ext = os.path.splitext(base_filename)[0]
            pattern = f"{name_without_ext}*.csv"

        pattern_path = os.path.join(self.data_path, pattern)
        existing_files = glob.glob(pattern_path)
        return existing_files

    def _should_overwrite_analysis(self, existing_files: List[str], new_timestamp: str) -> Optional[str]:
        """Check if we should overwrite existing analysis files based on timestamp"""
        if not existing_files:
            return None

        files_to_remove = []
        for file_path in existing_files:
            filename = os.path.basename(file_path)

            # Extract timestamp from filename
            if "chat_analysis_" in filename:
                try:
                    # Format: chat_analysis_YYYYMMDD_HHMMSS.csv
                    timestamp_part = filename.replace("chat_analysis_", "").replace(".csv", "")
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

    def save_results_to_csv(self, filename: str = None) -> str:
        """Save analysis results to CSV file in both locations with timestamp-based overwrite protection"""
        if not self.analysis_results:
            print("No analysis results to save")
            return None

        # Generate timestamp for new file
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not filename:
            filename = f"chat_analysis_{current_timestamp}.csv"
        else:
            # If custom filename provided, still add timestamp if not present
            name, ext = os.path.splitext(filename)
            if not any(c.isdigit() for c in name):  # No timestamp in filename
                filename = f"{name}_{current_timestamp}{ext}"

        # Check for existing files and handle overwrite (only for local data folder)
        existing_files = self._find_existing_analysis_files(filename)
        existing_file = self._should_overwrite_analysis(existing_files, current_timestamp)

        if existing_file:
            print(f"Skipping save - newer file already exists: {os.path.basename(existing_file)}")
            return existing_file

        # Define CSV headers
        headers = [
            'chat_id', 'chat_name', 'chat_type', 'is_public', 'organization_id', 'organization_name',
            'discovered_via_user_id', 'users_count', 'message_count',
            'average_message_length', 'unique_message_senders',
            'analysis_timestamp', 'analysis_error'
        ]

        # Prepare data for dual save
        csv_data = (headers, self.analysis_results)

        saved_path = self._save_file_to_data_directory(filename, csv_data, 'csv')

        if saved_path:
            print(f"Analysis results saved to: {saved_path}")
            print(f"Total analyzed chats: {len(self.analysis_results)}")
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
            filename = f"chat_analysis_{timestamp}.json"

        saved_path = self._save_file_to_data_directory(filename, self.analysis_results, 'json')

        if saved_path:
            print(f"Analysis results saved to: {saved_path}")
            print(f"Total analyzed chats: {len(self.analysis_results)}")
            return saved_path
        else:
            print("Error saving analysis results")
            return None

    def _merge_analysis_with_messages(self) -> str:
        """Merge chat messages with chat_id and chat_name only"""
        if not self.analysis_results:
            return None

        print("\nCreating combined messages file...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chats_with_messages_{timestamp}.csv"
        filepath = os.path.join(self.data_path, filename)

        # Find all simplified CSV files
        simplified_csvs = glob.glob(os.path.join(self.archive_path, "*_simplified.csv"))
        print(f"  Found {len(simplified_csvs)} simplified chat CSV files")

        if not simplified_csvs:
            print("  No simplified CSV files found")
            return None

        # Merge data (only selected fields)
        merged_rows = []
        for csv_file in simplified_csvs:
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Keep only essential fields
                        merged_row = {
                            'chat_id': row.get('chat_id', ''),
                            'chat_name': row.get('chat_name', ''),
                            'organization_id': row.get('organization_id', ''),
                            'organization_name': row.get('organization_name', ''),
                            'authorId': row.get('authorId', ''),
                            'full_name': row.get('full_name', ''),
                            'text': row.get('text', ''),
                            'createdAt': row.get('createdAt', '')
                        }
                        merged_rows.append(merged_row)
            except Exception as e:
                print(f"  Warning: Could not process {os.path.basename(csv_file)}: {e}")

        if not merged_rows:
            print("  No rows to save")
            return None

        # Save merged CSV
        try:
            fieldnames = ['chat_id', 'chat_name', 'organization_id', 'organization_name', 'authorId', 'full_name', 'text', 'createdAt']

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(merged_rows)

            print(f"  Combined messages file saved to: {filepath}")
            print(f"  Total rows: {len(merged_rows)}")
            return filepath
        except Exception as e:
            print(f"  Error saving combined file: {e}")
            return None

    def run_analysis(self, input_filename: str = None, output_filename: str = None,
                    limit: int = None, output_format: str = 'csv', max_messages_per_chat: int = 50000,
                    save_archives: bool = True) -> str:
        """Run complete chat analysis process"""
        print("Starting comprehensive chat analysis...")

        # Set archive preference
        self.save_archives = save_archives

        # Load unique chats data
        if not self.load_unique_chats(input_filename):
            print("Failed to load unique chats data")
            return None

        # Analyze all chats
        self.analyze_all_chats(limit=limit, max_messages_per_chat=max_messages_per_chat)

        if not self.analysis_results:
            print("No analysis results generated")
            return None

        # Save main results
        if output_format.lower() == 'json':
            result_path = self.save_results_to_json(output_filename)
        else:
            result_path = self.save_results_to_csv(output_filename)

        # Create additional reports
        if save_archives:  # Only create merged report if archives were saved
            self._merge_analysis_with_messages()

        return result_path

    def analyze_single_chat(self, chat_id: str, chat_name: str = "Single Chat",
                           output_filename: str = None, output_format: str = 'csv',
                           max_messages: int = 50000, save_archives: bool = True,
                           viewer_id: str = None) -> str:
        """Analyze a single chat by ID
        
        Args:
            chat_id: Channel/chat ID to analyze
            chat_name: Name of the channel (for reporting)
            output_filename: Custom output filename
            output_format: Output format ('csv' or 'json')
            max_messages: Maximum messages to extract
            save_archives: Whether to save message archives
            viewer_id: User ID to access private channels (optional)
        """
        print(f"Starting single chat analysis for: {chat_name} ({chat_id})")

        # Set archive preference
        self.save_archives = save_archives

        # Create mock chat data for single chat
        chat_data = {
            'chat_id': chat_id,
            'name': chat_name,
            'type': 'unknown',
            'is_public': 'unknown',
            'organization_id': 'unknown',
            'discovered_via_user_id': viewer_id if viewer_id else 'unknown'
        }

        try:
            # Analyze the single chat
            result = self.analyze_chat(chat_data, max_messages)
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
            print(f"Error analyzing single chat: {e}")
            return None


def main():
    """Main function to run the chat analyzer"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze unique chats for detailed statistics')
    parser.add_argument('--input', '-i', help='Input unique chats CSV filename')
    parser.add_argument('--output', '-o', help='Output analysis filename')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of chats to analyze')
    parser.add_argument('--max-messages', '-m', type=int, default=50000,
                       help='Maximum messages to analyze per chat (default: 50000)')
    parser.add_argument('--format', '-f', choices=['csv', 'json'], default='csv',
                       help='Output format (csv or json)')
    parser.add_argument('--no-archive', action='store_true',
                       help='Skip saving chat archives (saves disk space)')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Test mode - analyze only first 3 chats')
    parser.add_argument('--chat-id', '-c', type=str,
                       help='Analyze specific chat by ID (bypasses CSV input)')
    parser.add_argument('--chat-name', '-n', type=str, default='Single Chat',
                       help='Name for single chat analysis (default: Single Chat)')
    parser.add_argument('--viewer-id', '-v', type=str,
                       help='Viewer ID for accessing private channels (required for some private chats)')
    parser.add_argument('--days-back', '-d', type=int,
                       help='Filter messages to only include last N days (e.g., --days-back 7 for last week)')

    args = parser.parse_args()

    # Set test mode limit
    if args.test:
        args.limit = args.limit or 3
        print(f"TEST MODE: Analyzing only first {args.limit} chats")

    analyzer = ChatAnalyzer(days_back=args.days_back)

    # Handle single chat analysis
    if args.chat_id:
        print(f"Analyzing single chat: {args.chat_id}")
        if args.viewer_id:
            print(f"Using viewer ID: {args.viewer_id}")
        result_file = analyzer.analyze_single_chat(
            chat_id=args.chat_id,
            chat_name=args.chat_name,
            output_filename=args.output,
            output_format=args.format,
            max_messages=args.max_messages,
            save_archives=not args.no_archive,
            viewer_id=args.viewer_id
        )
    else:
        result_file = analyzer.run_analysis(
            input_filename=args.input,
            output_filename=args.output,
            limit=args.limit,
            output_format=args.format,
            max_messages_per_chat=args.max_messages,
            save_archives=not args.no_archive
        )

    if result_file:
        print(f"\nChat analysis completed successfully!")
        print(f"Results saved to: {result_file}")

        # Show summary statistics
        if analyzer.analysis_results:
            total_chats = len(analyzer.analysis_results)
            successful_analyses = len([r for r in analyzer.analysis_results if not r.get('analysis_error')])

            print(f"\nSummary:")
            print(f"- Total chats processed: {total_chats}")
            print(f"- Successful analyses: {successful_analyses}")
            print(f"- Failed analyses: {total_chats - successful_analyses}")
    else:
        print("Chat analysis failed")


if __name__ == "__main__":
    main()