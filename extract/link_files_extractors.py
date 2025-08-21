import sys
import os
from typing import Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints, BaseExtractor
from abstractions.logging_config import setup_logger

logger = setup_logger(__name__)


# MTS Link Files & Records Extractors - All file and record-related API endpoints

class FileDetailsExtractor(BaseExtractor):
    """Специализированный экстрактор для получения информации о файле с дополнительными параметрами"""
    
    def get_endpoint(self) -> str:
        return "/fileSystem/file/{fileID}"
    
    def get_url_params(self, **kwargs) -> Optional[Dict[str, Any]]:
        params = {}
        
        # Дополнительный параметр name
        if 'name' in kwargs and kwargs['name']:
            params['name'] = kwargs['name']
            
        return params if params else None
    
    def extract_and_save(self, filename: Optional[str] = None, **kwargs) -> Optional[str]:
        """Extract data and automatically save to file"""
        data = self.extract(**kwargs)
        if data is not None:
            return self.save_to_file(data, filename)
        return None


@endpoint("/fileSystem/file/{fileID}")
def file_details():
    """Получить информацию о конкретном файле из файлового менеджера
    
    Дополнительные параметры:
    - name: имя файла для дополнительной фильтрации
    """
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
    logger.info("Available MTS Link Files & Records extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        logger.info(f"  {name}: {path}")
        logger.info(f"    {description}")
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
    parser.add_argument('--name', help='File name for file_details endpoint')
    
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
    if args.name:
        kwargs['name'] = args.name
    
    if args.all:
        endpoints = get_registered_endpoints()
        no_param_endpoints = [name for name, path in endpoints.items() 
                             if '{' not in path]
        
        logger.info(f"Running {len(no_param_endpoints)} extractors (excluding parameterized ones)...")
        for extractor_name in no_param_endpoints:
            logger.info(f"\n--- Running {extractor_name} ---")
            result = run_extractor(extractor_name, **kwargs)
            if result:
                logger.success(f"{extractor_name} completed: {result}")
            else:
                logger.error(f"{extractor_name} failed")
        
        param_endpoints = [name for name, path in endpoints.items() 
                          if '{' in path]
        if param_endpoints:
            logger.warning(f"\nSkipped {len(param_endpoints)} parameterized endpoints:")
            for name in param_endpoints:
                logger.warning(f"  {name} (requires parameters)")
        
        return
    
    if args.extractor:
        # Special handling for file_details which requires custom extractor
        if args.extractor == 'file_details':
            try:
                extractor = FileDetailsExtractor()
                result = extractor.extract_and_save(**kwargs)
                if result:
                    logger.success(f"Extraction completed: {result}")
                else:
                    logger.error(f"Extraction failed")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
        else:
            result = run_extractor(args.extractor, **kwargs)
            if result:
                logger.success(f"Extraction completed: {result}")
            else:
                logger.error(f"Extraction failed")
        return
    
    endpoints = list_available_extractors()
    logger.info(f"\nEnter extractor name to run:")
    logger.info("Note: For parameterized endpoints, use command line arguments")
    logger.info("Examples:")
    logger.info("  python link_files_extractors.py file_details --fileID 123")
    logger.info("  python link_files_extractors.py event_session_files --eventsessionsID 456")
    logger.info("  python link_files_extractors.py download_converted_record --conversionId 789")
    
    while True:
        choice = input("> ").strip()
        
        if choice == 'quit' or choice == 'exit':
            break
        elif choice == 'all':
            no_param_endpoints = [name for name, path in endpoints.items() 
                                 if '{' not in path]
            for extractor_name in no_param_endpoints:
                logger.info(f"\n--- Running {extractor_name} ---")
                result = run_extractor(extractor_name)
                if result:
                    logger.success(f"{extractor_name} completed: {result}")
                else:
                    logger.error(f"{extractor_name} failed")
        elif choice in endpoints:
            # Special handling for file_details in interactive mode
            if choice == 'file_details':
                try:
                    extractor = FileDetailsExtractor()
                    result = extractor.extract_and_save(**kwargs)
                    if result:
                        logger.success(f"Extraction completed: {result}")
                    else:
                        logger.error(f"Extraction failed")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    logger.info("Note: file_details may require --fileID parameter. Use command line for parameters.")
            else:
                result = run_extractor(choice, **kwargs)
                if result:
                    logger.success(f"Extraction completed: {result}")
                else:
                    logger.error(f"Extraction failed")
        elif choice:
            logger.error(f"Unknown extractor: {choice}")
            logger.info("Available extractors: " + ", ".join(list(endpoints.keys())))


if __name__ == "__main__":
    main()