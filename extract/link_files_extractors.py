import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints


# MTS Link Files & Records Extractors - All file and record-related API endpoints

@endpoint("/fileSystem/file/{fileID}")
def file_details():
    """Получить информацию о конкретном файле из файлового менеджера"""
    pass


@endpoint("/fileSystem/files")
def files_list():
    """Получить полный список файлов из файлового менеджера"""
    pass


@endpoint("/eventsessions/{eventsessionsID}/files")
def event_session_files():
    """Получить список файлов, прикрепленных к конкретному мероприятию"""
    pass


@endpoint("/events/{eventsID}/files")
def event_series_files():
    """Получить список файлов, прикрепленных к серии мероприятий"""
    pass


@endpoint("/fileSystem/files/converted-record")
def converted_records_list():
    """Получить список всех готовых MP4-записей в организации"""
    pass


@endpoint("/fileSystem/file/{conversionId}")
def download_converted_record():
    """Получить файл MP4-записи по ID ее конвертации"""
    pass


def list_available_extractors():
    """List all available extractors"""
    endpoints = get_registered_endpoints()
    print("Available MTS Link Files & Records extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        print(f"  {name}: {path}")
        print(f"    {description}")
    return endpoints


def main():
    """Main function to run extractors"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MTS-Link Files & Records API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')
    parser.add_argument('--all', '-a', action='store_true', help='Run all extractors')
    
    # Files-related parameters
    parser.add_argument('--fileID', help='File ID for file-specific endpoints')
    parser.add_argument('--eventsessionsID', help='Event session ID for event session files')
    parser.add_argument('--eventsID', help='Event series ID for event series files')
    parser.add_argument('--conversionId', help='Conversion ID for MP4 record download')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_extractors()
        return
    
    kwargs = {}
    if args.fileID:
        kwargs['fileID'] = args.fileID
    if args.eventsessionsID:
        kwargs['eventsessionsID'] = args.eventsessionsID
    if args.eventsID:
        kwargs['eventsID'] = args.eventsID
    if args.conversionId:
        kwargs['conversionId'] = args.conversionId
    
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
    print("  python link_files_extractors.py file_details --fileID 123")
    print("  python link_files_extractors.py event_session_files --eventsessionsID 456")
    print("  python link_files_extractors.py download_converted_record --conversionId 789")
    
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