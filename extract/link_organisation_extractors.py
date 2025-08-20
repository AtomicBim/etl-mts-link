import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints


# MTS Link Organisation & Settings Extractors - All organization and settings-related API endpoints

@endpoint("/brandings")
def brandings_list():
    """Получить список доступных тем оформления для мероприятий"""
    pass


@endpoint("/organization-groups")
def organization_groups():
    """Выгрузить список созданных в организации групп пользователей"""
    pass


@endpoint("/partner-applications")
def partner_applications():
    """Получить данные об интеграциях, подключенных к организации через OAuth"""
    pass


@endpoint("/timezones")
def timezones_list():
    """Получить справочный список всех доступных часовых поясов"""
    pass


def list_available_extractors():
    """List all available extractors"""
    endpoints = get_registered_endpoints()
    print("Available MTS Link Organisation & Settings extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        print(f"  {name}: {path}")
        print(f"    {description}")
    return endpoints


def main():
    """Main function to run extractors"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MTS-Link Organisation & Settings API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')
    parser.add_argument('--all', '-a', action='store_true', help='Run all extractors')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_extractors()
        return
    
    endpoints = get_registered_endpoints()
    
    if args.all:
        print(f"Running {len(endpoints)} extractors...")
        for extractor_name in endpoints:
            print(f"\n--- Running {extractor_name} ---")
            result = run_extractor(extractor_name)
            if result:
                print(f"SUCCESS: {extractor_name} completed: {result}")
            else:
                print(f"FAILED: {extractor_name} failed")
        return
    
    if args.extractor:
        result = run_extractor(args.extractor)
        if result:
            print(f"SUCCESS: Extraction completed: {result}")
        else:
            print(f"FAILED: Extraction failed")
        return
    
    list_available_extractors()
    print(f"\nEnter extractor name to run:")
    print("Examples:")
    print("  python link_organisation_extractors.py brandings_list")
    print("  python link_organisation_extractors.py organization_groups")
    
    while True:
        choice = input("> ").strip()
        
        if choice == 'quit' or choice == 'exit':
            break
        elif choice == 'all':
            for extractor_name in endpoints:
                print(f"\n--- Running {extractor_name} ---")
                result = run_extractor(extractor_name)
                if result:
                    print(f"SUCCESS: {extractor_name} completed: {result}")
                else:
                    print(f"FAILED: {extractor_name} failed")
        elif choice in endpoints:
            result = run_extractor(choice)
            if result:
                print(f"SUCCESS: Extraction completed: {result}")
            else:
                print(f"FAILED: Extraction failed")
        elif choice:
            print(f"Unknown extractor: {choice}")
            print("Available extractors:", list(endpoints.keys()))


if __name__ == "__main__":
    main()