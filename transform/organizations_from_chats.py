#!/usr/bin/env python3
"""
Organizations Extractor from Chats
Extracts unique organizations from chats data and saves to CSV
"""
import sys
import os
import csv
import glob
from typing import Dict, Set, List
from datetime import datetime
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class OrganizationsExtractor:
    """Extract unique organizations from chats data"""

    def __init__(self, data_path: str = None):
        # Default to data directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = data_path or os.path.join(project_root, "data")

        # Data storage
        self.organizations: Dict[str, Dict] = {}
        self.organization_chats: Dict[str, List[str]] = {}

    def _find_latest_unique_chats_csv(self) -> str:
        """Find the most recent unique_chats CSV file"""
        pattern = os.path.join(self.data_path, "unique_chats_*.csv")
        files = glob.glob(pattern)
        
        if not files:
            print(f"No unique_chats CSV files found in {self.data_path}")
            return None
        
        # Sort by modification time, get the latest
        latest_file = max(files, key=os.path.getmtime)
        print(f"Using chats file: {os.path.basename(latest_file)}")
        return latest_file

    def load_chats_data(self, chats_file: str = None) -> List[Dict]:
        """Load chats data from CSV"""
        if not chats_file:
            chats_file = self._find_latest_unique_chats_csv()
        
        if not chats_file or not os.path.exists(chats_file):
            print(f"Chats file not found: {chats_file}")
            return []

        chats_data = []
        try:
            with open(chats_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chats_data.append(row)
            
            print(f"Loaded {len(chats_data)} chats from CSV")
            return chats_data
        
        except Exception as e:
            print(f"Error reading chats file: {e}")
            return []

    def extract_organizations(self, chats_data: List[Dict]) -> None:
        """Extract unique organizations from chats data"""
        print("\nExtracting organizations from chats...")

        for chat in chats_data:
            org_id = chat.get('organization_id', '').strip()
            chat_id = chat.get('chat_id', '').strip()
            
            if not org_id:
                continue

            # Initialize organization entry if not exists
            if org_id not in self.organizations:
                self.organizations[org_id] = {
                    'organization_id': org_id,
                    'total_chats': 0,
                    'public_chats': 0,
                    'private_chats': 0,
                    'read_only_chats': 0,
                    'chat_types': Counter()
                }
                self.organization_chats[org_id] = []

            # Update organization statistics
            org = self.organizations[org_id]
            org['total_chats'] += 1

            # Track chat by ID
            if chat_id:
                self.organization_chats[org_id].append(chat_id)

            # Count by visibility
            is_public = str(chat.get('is_public', '')).lower()
            if is_public in ['true', '1', 'yes']:
                org['public_chats'] += 1
            else:
                org['private_chats'] += 1

            # Count read-only chats
            is_read_only = str(chat.get('is_read_only', '')).lower()
            if is_read_only in ['true', '1', 'yes']:
                org['read_only_chats'] += 1

            # Track chat types
            chat_type = chat.get('type', 'unknown').strip()
            if chat_type:
                org['chat_types'][chat_type] += 1

        print(f"Found {len(self.organizations)} unique organizations")

    def _prepare_export_data(self) -> List[Dict]:
        """Prepare organizations data for CSV export"""
        export_data = []

        for org_id, org in self.organizations.items():
            # Get most common chat types
            top_chat_types = org['chat_types'].most_common(3)
            chat_types_str = ', '.join([f"{ctype}({count})" for ctype, count in top_chat_types])

            export_data.append({
                'organization_id': org['organization_id'],
                'total_chats': org['total_chats'],
                'public_chats': org['public_chats'],
                'private_chats': org['private_chats'],
                'read_only_chats': org['read_only_chats'],
                'top_chat_types': chat_types_str,
                'extraction_timestamp': datetime.now().isoformat()
            })

        # Sort by total chats (descending)
        export_data.sort(key=lambda x: x['total_chats'], reverse=True)
        return export_data

    def save_to_csv(self, filename: str = None) -> str:
        """Save organizations data to CSV"""
        if not self.organizations:
            print("No organizations data to save")
            return None

        # Generate filename with timestamp
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"organizations_from_chats_{timestamp}.csv"

        filepath = os.path.join(self.data_path, filename)

        # Prepare data for export
        export_data = self._prepare_export_data()

        # Define CSV fieldnames
        fieldnames = [
            'organization_id',
            'total_chats',
            'public_chats',
            'private_chats',
            'read_only_chats',
            'top_chat_types',
            'extraction_timestamp'
        ]

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(export_data)

            print(f"\nOrganizations saved to: {filepath}")
            print(f"Total organizations: {len(export_data)}")
            
            # Show summary
            total_chats = sum(org['total_chats'] for org in export_data)
            print(f"Total chats across all organizations: {total_chats}")
            
            return filepath

        except Exception as e:
            print(f"Error saving CSV file: {e}")
            return None

    def run(self, chats_file: str = None, output_filename: str = None) -> str:
        """Run the complete extraction process"""
        print("Starting organizations extraction from chats...\n")

        # Load chats data
        chats_data = self.load_chats_data(chats_file)
        if not chats_data:
            print("No chats data available")
            return None

        # Extract organizations
        self.extract_organizations(chats_data)

        if not self.organizations:
            print("No organizations found")
            return None

        # Save to CSV
        return self.save_to_csv(output_filename)


def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract unique organizations from chats data'
    )
    parser.add_argument(
        '--chats-file', '-c',
        help='Path to unique_chats CSV file (default: latest in data/)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output CSV filename (default: organizations_from_chats_YYYYMMDD_HHMMSS.csv)'
    )
    parser.add_argument(
        '--data-dir', '-d',
        help='Data directory path (default: data/)'
    )

    args = parser.parse_args()

    # Create extractor
    extractor = OrganizationsExtractor(data_path=args.data_dir)

    # Run extraction
    try:
        result = extractor.run(
            chats_file=args.chats_file,
            output_filename=args.output
        )
        
        if result:
            print("\nExtraction completed successfully!")
            return True
        else:
            print("\nExtraction failed")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

