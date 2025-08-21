import sys
import os
import logging
from typing import Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints, BaseExtractor


# Configure colored logging
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[37m',      # White
        'SUCCESS': '\033[32m',   # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to the level name
        levelname = record.levelname
        if levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            record.levelname = colored_levelname
        
        return super().format(record)


# Add SUCCESS level
logging.SUCCESS = 25
logging.addLevelName(logging.SUCCESS, 'SUCCESS')

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.SUCCESS):
        self._log(logging.SUCCESS, message, args, **kwargs)

logging.Logger.success = success

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = ColoredFormatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)

# Add handler to logger
if not logger.handlers:
    logger.addHandler(console_handler)


# MTS Link Tests & Voting Extractors - All test and voting-related API endpoints

class TestInfoExtractor(BaseExtractor):
    """Специализированный экстрактор для получения информации о тесте с дополнительными параметрами"""
    
    def get_endpoint(self) -> str:
        return "/tests/{testId}"
    
    def get_url_params(self, **kwargs) -> Optional[Dict[str, Any]]:
        params = {}
        
        # Дополнительный параметр testSessionId
        if 'testSessionId' in kwargs and kwargs['testSessionId']:
            params['testSessionId'] = kwargs['testSessionId']
            
        return params if params else None
    
    def extract_and_save(self, filename: Optional[str] = None, **kwargs) -> Optional[str]:
        """Extract data and automatically save to file"""
        data = self.extract(**kwargs)
        if data is not None:
            return self.save_to_file(data, filename)
        return None


@endpoint("/tests/{testId}")
def test_info():
    """Получить детальную информацию о созданном тесте или голосовании
    
    Дополнительные параметры:
    - testSessionId: уникальный идентификатор результата теста для ограничения выборки
    """
    pass


@endpoint("/tests/{testId}/results")
def test_results():
    """Получить общие результаты прохождения теста всеми участниками"""
    pass


@endpoint("/users/{userId}/tests/stats")
def user_tests_stats():
    """Получить результаты всех тестов, пройденных конкретным участником"""
    pass


@endpoint("/tests/{testId}/customanswers")
def test_custom_answers():
    """Выгрузить текстовые ответы участников на открытые вопросы теста"""
    pass


@endpoint("/tests/list")
def tests_list():
    """Получить список тестов с информацией о времени их запуска"""
    pass


def list_available_extractors():
    """List all available extractors"""
    endpoints = get_registered_endpoints()
    logger.info("Available MTS Link Tests & Voting extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        logger.info(f"  {name}: {path}")
        logger.info(f"    {description}")
    return endpoints


def main():
    """Main function to run extractors"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MTS-Link Tests & Voting API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')
    parser.add_argument('--all', '-a', action='store_true', help='Run all extractors')
    
    # Tests-related parameters
    parser.add_argument('--testId', help='Test ID for test-specific endpoints')
    parser.add_argument('--userId', help='User ID for user-specific endpoints')
    parser.add_argument('--testSessionId', help='Test Session ID for limiting test_info results')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_extractors()
        return
    
    kwargs = {}
    if args.testId:
        kwargs['testId'] = args.testId
    if args.userId:
        kwargs['userId'] = args.userId
    if args.testSessionId:
        kwargs['testSessionId'] = args.testSessionId
    
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
        # Special handling for test_info which requires custom extractor
        if args.extractor == 'test_info':
            try:
                extractor = TestInfoExtractor()
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
    logger.info("  python link_tests_extractors.py test_info --testId 123")
    logger.info("  python link_tests_extractors.py user_tests_stats --userId 456")
    
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
            # Special handling for test_info in interactive mode
            if choice == 'test_info':
                try:
                    extractor = TestInfoExtractor()
                    result = extractor.extract_and_save(**kwargs)
                    if result:
                        logger.success(f"Extraction completed: {result}")
                    else:
                        logger.error(f"Extraction failed")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    logger.info("Note: test_info may require --testId parameter. Use command line for parameters.")
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