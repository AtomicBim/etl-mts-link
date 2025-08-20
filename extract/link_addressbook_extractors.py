import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints


# MTS Link Addressbook & Users Extractors - All addressbook and user-related API endpoints

@endpoint("/contacts/{contactsID}")
def contact_details():
    """Получить детальную информацию о конкретном контакте из адресной книги"""
    pass


@endpoint("/contacts/search")
def contacts_search():
    """Осуществить поиск по контактам в адресной книге"""
    pass


@endpoint("/organization/members")
def organization_members():
    """Выгрузить список всех сотрудников, добавленных в аккаунт МТС Линк"""
    pass


@endpoint("/profile")
def user_profile():
    """Получить информацию о профиле пользователя, от имени которого выполняется запрос (OAuth)"""
    pass


def list_available_extractors():
    """List all available extractors"""
    endpoints = get_registered_endpoints()
    print("Available MTS Link Addressbook & Users extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        print(f"  {name}: {path}")
        print(f"    {description}")
    return endpoints


def main():
    """Main function to run extractors"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MTS-Link Addressbook & Users API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')
    parser.add_argument('--all', '-a', action='store_true', help='Run all extractors')
    
    # Addressbook-related parameters
    parser.add_argument('--contactsID', help='Contact ID for contact-specific endpoints')
    parser.add_argument('--query', help='Search query for contacts search')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_extractors()
        return
    
    kwargs = {}
    if args.contactsID:
        kwargs['contactsID'] = args.contactsID
    if args.query:
        kwargs['query'] = args.query
    
    if args.all:
        endpoints = get_registered_endpoints()
        no_param_endpoints = [name for name, path in endpoints.items() 
                             if '{' not in path]
        
        print(f"Running {len(no_param_endpoints)} extractors (excluding parameterized ones)...")
        for extractor_name in no_param_endpoints:
            print(f"\n--- Running {extractor_name} ---")
            result = run_extractor(extractor_name, **kwargs)
            if result:
                print(f"SUCCESS: {extractor_name} completed: {result}")
            else:
                print(f"FAILED: {extractor_name} failed")
        
        param_endpoints = [name for name, path in endpoints.items() 
                          if '{' in path]
        if param_endpoints:
            print(f"\nSkipped {len(param_endpoints)} parameterized endpoints:")
            for name in param_endpoints:
                print(f"  {name} (requires parameters)")
        
        return
    
    if args.extractor:
        result = run_extractor(args.extractor, **kwargs)
        if result:
            print(f"SUCCESS: Extraction completed: {result}")
        else:
            print(f"FAILED: Extraction failed")
        return
    
    endpoints = list_available_extractors()
    print(f"\nEnter extractor name to run:")
    print("Note: For parameterized endpoints, use command line arguments")
    print("Examples:")
    print("  python link_addressbook_extractors.py contact_details --contactsID 123")
    print("  python link_addressbook_extractors.py contacts_search --query 'search term'")
    
    while True:
        choice = input("> ").strip()
        
        if choice == 'quit' or choice == 'exit':
            break
        elif choice == 'all':
            no_param_endpoints = [name for name, path in endpoints.items() 
                                 if '{' not in path]
            for extractor_name in no_param_endpoints:
                print(f"\n--- Running {extractor_name} ---")
                result = run_extractor(extractor_name)
                if result:
                    print(f"SUCCESS: {extractor_name} completed: {result}")
                else:
                    print(f"FAILED: {extractor_name} failed")
        elif choice in endpoints:
            result = run_extractor(choice, **kwargs)
            if result:
                print(f"SUCCESS: Extraction completed: {result}")
            else:
                print(f"FAILED: Extraction failed")
        elif choice:
            print(f"Unknown extractor: {choice}")
            print("Available extractors:", list(endpoints.keys()))


if __name__ == "__main__":
    main()