"""
Daily Activity Analyzer - Анализ активности по дням

Анализирует:
- Сообщения в чатах (из chats_archive/*.json)
- Созвоны (из endless_activities_*.csv)

Выходной CSV содержит метрики по каждому дню:
- Дата
- Количество сообщений
- Средняя длина сообщения
- Количество уникальных отправителей
- Количество активных чатов
- Количество созвонов
- Средняя длительность созвона
- Количество участников созвонов
- Общая длительность созвонов в день
"""

import sys
import os
import json
import csv
import glob
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DailyActivityAnalyzer:
    """Analyzer for daily activity from chats and calls"""
    
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        self.chats_archive_path = os.path.join(data_path, "chats_archive")
        
        # Storage for daily metrics
        self.daily_messages = defaultdict(list)  # date -> list of message objects
        self.daily_calls = defaultdict(list)  # date -> list of call objects
        
    def extract_date_from_datetime(self, dt_string: str) -> str:
        """Extract date from datetime string"""
        try:
            # Try format: "2025-06-16 14:53:03"
            dt = datetime.strptime(dt_string.split('.')[0].split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                # Try ISO format: "2025-11-17T10:00:57+03:00"
                dt = datetime.fromisoformat(dt_string.replace('+', ' ').split()[0])
                return dt.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"Warning: Could not parse date '{dt_string}': {e}")
                return None
    
    def load_chat_messages(self):
        """Load all messages from chat archives"""
        print("\n" + "="*60)
        print("Loading chat messages...")
        print("="*60)
        
        # Find all simplified JSON files
        json_files = glob.glob(os.path.join(self.chats_archive_path, "*_simplified.json"))
        
        if not json_files:
            print(f"Warning: No simplified JSON files found in {self.chats_archive_path}")
            return
        
        print(f"Found {len(json_files)} chat archive files")
        
        total_messages = 0
        processed_files = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                chat_id = data.get('chat_id', 'unknown')
                chat_name = data.get('chat_name', 'Unknown Chat')
                messages = data.get('messages', [])
                
                for msg in messages:
                    created_at = msg.get('createdAt')
                    if not created_at:
                        continue
                    
                    date = self.extract_date_from_datetime(created_at)
                    if not date:
                        continue
                    
                    # Store message info
                    self.daily_messages[date].append({
                        'chat_id': chat_id,
                        'chat_name': chat_name,
                        'author_id': msg.get('authorId'),
                        'author_name': msg.get('full_name'),
                        'text': msg.get('text', ''),
                        'text_length': len(msg.get('text', ''))
                    })
                    total_messages += 1
                
                processed_files += 1
                
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
                continue
        
        print(f"\nProcessed {processed_files} files")
        print(f"Total messages loaded: {total_messages}")
        print(f"Date range: {len(self.daily_messages)} unique days")
    
    def load_calls_data(self):
        """Load calls data from endless_activities CSV"""
        print("\n" + "="*60)
        print("Loading calls data...")
        print("="*60)
        
        # Find endless_activities CSV files (include analysis files as fallback)
        all_csv_files = glob.glob(os.path.join(self.data_path, "endless_activities_*.csv"))
        
        # Prefer base files without 'analysis', but use analysis files if that's all we have
        base_csv_files = [f for f in all_csv_files if 'analysis' not in os.path.basename(f)]
        csv_files = base_csv_files if base_csv_files else all_csv_files
        
        if not csv_files:
            print(f"Warning: No endless_activities CSV files found in {self.data_path}")
            return
        
        # Get most recent file
        csv_file = max(csv_files, key=os.path.getmtime)
        print(f"Using: {os.path.basename(csv_file)}")
        
        total_calls = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Detect which participant count column exists
                first_row = None
                rows_to_process = []
                
                for row in reader:
                    if first_row is None:
                        first_row = row
                    rows_to_process.append(row)
                
                # Determine the correct column name for participants count
                participants_col = None
                if first_row:
                    if 'participants_count' in first_row:
                        participants_col = 'participants_count'
                    elif 'participants_count_csv' in first_row:
                        participants_col = 'participants_count_csv'
                    elif 'participants_count_api' in first_row:
                        participants_col = 'participants_count_api'
                
                if participants_col:
                    print(f"Using participants count column: {participants_col}")
                else:
                    print("Warning: No participants count column found, using 0")
                
                # Process all rows
                for row in rows_to_process:
                    start_time = row.get('start_time')
                    if not start_time:
                        continue
                    
                    date = self.extract_date_from_datetime(start_time)
                    if not date:
                        continue
                    
                    # Store call info
                    try:
                        duration = int(row.get('duration_minutes', 0) or 0)
                        participants = int(row.get(participants_col, 0) or 0) if participants_col else 0
                    except ValueError:
                        duration = 0
                        participants = 0
                    
                    self.daily_calls[date].append({
                        'activity_id': row.get('activity_id'),
                        'user_id': row.get('user_id'),
                        'user_name': row.get('user_name'),
                        'room_name': row.get('room_name'),
                        'duration_minutes': duration,
                        'participants_count': participants,
                        'endless_event_id': row.get('endless_event_id')
                    })
                    total_calls += 1
        
        except Exception as e:
            print(f"Error loading calls data: {e}")
            return
        
        print(f"Total calls loaded: {total_calls}")
        print(f"Date range: {len(self.daily_calls)} unique days")
    
    def calculate_daily_metrics(self) -> List[Dict]:
        """Calculate metrics for each day"""
        print("\n" + "="*60)
        print("Calculating daily metrics...")
        print("="*60)
        
        # Get all unique dates
        all_dates = set(self.daily_messages.keys()) | set(self.daily_calls.keys())
        
        if not all_dates:
            print("No data to analyze!")
            return []
        
        print(f"Analyzing {len(all_dates)} unique days")
        
        results = []
        
        for date in sorted(all_dates):
            messages = self.daily_messages.get(date, [])
            calls = self.daily_calls.get(date, [])
            
            # Messages metrics
            msg_count = len(messages)
            avg_msg_length = sum(m['text_length'] for m in messages) / msg_count if msg_count > 0 else 0
            unique_senders = len(set(m['author_id'] for m in messages if m['author_id']))
            active_chats = len(set(m['chat_id'] for m in messages if m['chat_id']))
            
            # Calls metrics
            calls_count = len(calls)
            avg_call_duration = sum(c['duration_minutes'] for c in calls) / calls_count if calls_count > 0 else 0
            total_call_duration = sum(c['duration_minutes'] for c in calls)
            # Note: Each row in endless_activities is one user's participation in a call
            unique_call_users = len(set(c['user_id'] for c in calls if c['user_id']))
            unique_call_rooms = len(set(c['endless_event_id'] for c in calls if c['endless_event_id']))
            total_call_participants = sum(c['participants_count'] for c in calls)
            
            results.append({
                'date': date,
                # Messages
                'messages_count': msg_count,
                'avg_message_length': round(avg_msg_length, 1),
                'unique_senders': unique_senders,
                'active_chats': active_chats,
                # Calls
                'calls_count': calls_count,
                'avg_call_duration_min': round(avg_call_duration, 1),
                'total_call_duration_min': total_call_duration,
                'unique_call_users': unique_call_users,
                'unique_call_rooms': unique_call_rooms,
                'total_call_participants': total_call_participants,
                # Combined
                'total_activity_events': msg_count + calls_count
            })
        
        return results
    
    def save_to_csv(self, results: List[Dict], output_file: str = None):
        """Save results to CSV"""
        if not results:
            print("No results to save!")
            return
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.data_path, f"daily_activity_{timestamp}.csv")
        
        print("\n" + "="*60)
        print("Saving results...")
        print("="*60)
        
        fieldnames = [
            'date',
            # Messages
            'messages_count',
            'avg_message_length',
            'unique_senders',
            'active_chats',
            # Calls
            'calls_count',
            'avg_call_duration_min',
            'total_call_duration_min',
            'unique_call_users',
            'unique_call_rooms',
            'total_call_participants',
            # Combined
            'total_activity_events'
        ]
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            print(f"[OK] Saved to: {output_file}")
            print(f"[OK] Total days: {len(results)}")
            print(f"[OK] Date range: {results[0]['date']} to {results[-1]['date']}")
            
            # Show summary statistics
            total_messages = sum(r['messages_count'] for r in results)
            total_calls = sum(r['calls_count'] for r in results)
            
            print(f"\n[SUMMARY]")
            print(f"  Total messages: {total_messages:,}")
            print(f"  Total calls: {total_calls:,}")
            print(f"  Avg messages/day: {total_messages / len(results):.1f}")
            print(f"  Avg calls/day: {total_calls / len(results):.1f}")
            
            return output_file
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return None
    
    def print_help_fields(self):
        """Print description of output fields"""
        print("\n" + "="*60)
        print("OUTPUT FIELDS DESCRIPTION")
        print("="*60)
        
        fields_info = {
            'date': 'Дата (YYYY-MM-DD)',
            'messages_count': 'Количество сообщений в день',
            'avg_message_length': 'Средняя длина сообщения (символов)',
            'unique_senders': 'Количество уникальных отправителей',
            'active_chats': 'Количество активных чатов',
            'calls_count': 'Количество созвонов в день (записи активностей)',
            'avg_call_duration_min': 'Средняя длительность созвона (минут)',
            'total_call_duration_min': 'Общая длительность всех созвонов (минут)',
            'unique_call_users': 'Количество уникальных пользователей в созвонах',
            'unique_call_rooms': 'Количество уникальных комнат/встреч',
            'total_call_participants': 'Общее количество участников во всех созвонах',
            'total_activity_events': 'Общее количество событий активности (сообщения + созвоны)'
        }
        
        for field, description in fields_info.items():
            print(f"  {field:30s} - {description}")
    
    def run(self, output_file: str = None):
        """Run the full analysis"""
        print("\n" + "="*60)
        print("DAILY ACTIVITY ANALYZER")
        print("="*60)
        
        # Load data
        self.load_chat_messages()
        self.load_calls_data()
        
        # Calculate metrics
        results = self.calculate_daily_metrics()
        
        # Save results
        if results:
            output_path = self.save_to_csv(results, output_file)
            return output_path
        else:
            print("\nNo data to analyze!")
            return None


def main():
    parser = argparse.ArgumentParser(
        description='Analyze daily activity from chats and calls',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python transform/daily_activity_analyzer.py
  python transform/daily_activity_analyzer.py --output my_analysis.csv
  python transform/daily_activity_analyzer.py --help-fields
        """
    )
    
    parser.add_argument('--data-path', default='data',
                        help='Path to data directory (default: data)')
    parser.add_argument('--output', '-o',
                        help='Output CSV file path')
    parser.add_argument('--help-fields', action='store_true',
                        help='Show description of output fields')
    
    args = parser.parse_args()
    
    analyzer = DailyActivityAnalyzer(data_path=args.data_path)
    
    if args.help_fields:
        analyzer.print_help_fields()
        return
    
    output_path = analyzer.run(output_file=args.output)
    
    if output_path:
        print("\n" + "="*60)
        print("[SUCCESS] Analysis complete!")
        print("="*60)


if __name__ == "__main__":
    main()

