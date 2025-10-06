#!/usr/bin/env python3
"""
Organization Members Extractor
Extracts all organization members from MTS Link Chats and saves to CSV
"""
import sys
import os
import csv
from typing import List, Dict, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import UniversalExtractor


class OrganizationMembersExtractor:
    """Extractor for organization members from MTS Link Chats"""

    def __init__(self, output_dir: str = None):
        # Default to data directory in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = output_dir or os.path.join(project_root, "data")

        # Initialize extractor
        self.extractor = UniversalExtractor("/chats/organization/members")

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Data storage
        self.members_data: List[Dict[str, Any]] = []

    def _extract_members_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """Extract members from API response"""
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
            elif 'items' in data:
                return data['items']
            elif 'members' in data:
                return data['members']

        return []

    def fetch_all_members(self) -> List[Dict[str, Any]]:
        """Fetch all organization members with pagination"""
        print("Fetching organization members...")

        all_members = []
        page = 1
        per_page = 100  # Default pagination size
        max_pages = 100  # Safety limit

        while page <= max_pages:
            print(f"  Fetching page {page}...")

            # Make API request with pagination
            data = self.extractor.extract(page=page, perPage=per_page)

            if not data:
                print(f"  No data returned on page {page}")
                break

            # Extract members from response
            members = self._extract_members_from_response(data)

            if not members:
                print(f"  No members found on page {page}, stopping pagination")
                break

            all_members.extend(members)
            print(f"  Found {len(members)} members (total: {len(all_members)})")

            # If we got fewer members than per_page, we've reached the end
            if len(members) < per_page:
                print(f"  Received {len(members)} < {per_page} members, reached end of list")
                break

            page += 1

        print(f"\nTotal members fetched: {len(all_members)}")
        return all_members

    def _flatten_member_data(self, member: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested member data structure for CSV export"""
        flattened = {}

        # Top-level fields
        flattened['chatUserId'] = member.get('chatUserId', '')
        flattened['organizationId'] = member.get('organizationId', '')
        flattened['role'] = member.get('role', '')
        flattened['status'] = member.get('status', '')

        # Extract profile information
        profile = member.get('chatMemberProfile', {})
        if isinstance(profile, dict):
            flattened['firstName'] = profile.get('firstName', '')
            flattened['lastName'] = profile.get('lastName', '')
            flattened['displayName'] = profile.get('displayName', '')
            flattened['email'] = profile.get('email', '')
            flattened['phone'] = profile.get('phone', '')
            flattened['avatarUrl'] = profile.get('avatarUrl', '')
            flattened['position'] = profile.get('position', '')
            flattened['department'] = profile.get('department', '')

        return flattened

    def save_to_csv(self, members: List[Dict[str, Any]], filename: str = None) -> str:
        """Save members data to CSV file"""
        if not members:
            print("No members data to save")
            return None

        # Generate filename with timestamp
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"organization_members_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        # Flatten all member data
        flattened_members = [self._flatten_member_data(member) for member in members]

        # Define CSV fieldnames in logical order
        fieldnames = [
            'chatUserId',
            'organizationId',
            'firstName',
            'lastName',
            'displayName',
            'email',
            'phone',
            'role',
            'status',
            'position',
            'department',
            'avatarUrl'
        ]

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header
                writer.writeheader()

                # Write members
                for member in flattened_members:
                    # Ensure all fields exist (fill missing with empty string)
                    row = {field: member.get(field, '') for field in fieldnames}
                    writer.writerow(row)

            print(f"\nOrganization members saved to: {filepath}")
            print(f"Total members saved: {len(flattened_members)}")
            return filepath

        except Exception as e:
            print(f"Error saving CSV file: {e}")
            return None

    def run(self, output_filename: str = None) -> str:
        """Run the complete extraction and save process"""
        print("Starting organization members extraction...\n")

        # Fetch all members
        members = self.fetch_all_members()

        if not members:
            print("No members found")
            return None

        # Save to CSV
        filepath = self.save_to_csv(members, output_filename)

        if filepath:
            print("\nExtraction completed successfully!")
        else:
            print("\nExtraction failed")

        return filepath


def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract organization members from MTS Link Chats'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output CSV filename (default: organization_members_YYYYMMDD_HHMMSS.csv)'
    )
    parser.add_argument(
        '--output-dir', '-d',
        help='Output directory (default: data/)'
    )

    args = parser.parse_args()

    # Create extractor
    extractor = OrganizationMembersExtractor(output_dir=args.output_dir)

    # Run extraction
    try:
        result = extractor.run(output_filename=args.output)
        return result is not None
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)