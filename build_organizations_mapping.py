#!/usr/bin/env python3
"""
Build organizations mapping from Chats Teams API
"""
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from abstractions.extract import UniversalExtractor

def main():
    print("Building organizations mapping from Chats Teams...\n")
    
    # Extract teams data
    extractor = UniversalExtractor("/chats/teams")
    data = extractor.extract()
    
    if not data:
        print("Error: Could not fetch teams data")
        return False
    
    # Extract teams from response
    teams = []
    if isinstance(data, dict):
        if 'data' in data:
            data_obj = data['data']
            if isinstance(data_obj, dict) and 'items' in data_obj:
                teams = data_obj['items']
            elif isinstance(data_obj, list):
                teams = data_obj
        elif 'items' in data:
            teams = data['items']
    elif isinstance(data, list):
        teams = data
    
    if not teams:
        print("Error: No teams found in response")
        return False
    
    print(f"Found {len(teams)} teams/organizations\n")
    
    # Build mapping
    organizations = []
    for team in teams:
        team_id = team.get('id', '')
        team_name = team.get('name', '')
        team_code = team.get('code', '')
        team_description = team.get('description', '')
        
        if team_id and team_name:
            organizations.append({
                "organization_id": team_id,
                "organization_name": team_name,
                "code": team_code,
                "description": team_description,
                "created_at": datetime.now().strftime("%Y-%m-%d")
            })
            print(f"  {team_name} ({team_code}) - ID: {team_id}")
    
    # Save mapping
    mapping_data = {
        "organizations": organizations,
        "total": len(organizations),
        "created_at": datetime.now().isoformat(),
        "source": "/chats/teams API endpoint",
        "comment": "Mapping of organization_id to organization_name from MTS Link Chats Teams"
    }
    
    output_file = "data/organizations_mapping.json"
    os.makedirs("data", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"Organizations mapping saved to: {output_file}")
    print(f"Total organizations: {len(organizations)}")
    print('='*80)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

