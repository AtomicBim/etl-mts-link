import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints, BaseExtractor
from typing import Optional, Dict, Any


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


# MTS Link Events Extractors - All event-related API endpoints

@endpoint("/organization/events/schedule")
def organization_events_schedule():
    """Получить информацию о всех мероприятиях организации"""
    pass


@endpoint("/eventsessions/{eventsessionID}")
def event_session_details():
    """Получить детальную информацию о конкретном мероприятии"""
    pass


@endpoint("/users/{userID}/events/schedule")
def user_events_schedule():
    """Получить информацию о мероприятиях, созданных конкретным сотрудником"""
    pass


@endpoint("/organization/events/{eventID}")
def event_series_data():
    """Получить данные о шаблоне или серии мероприятий"""
    pass


@endpoint("/eventsessions/endless")
def endless_meetings_list():
    """Выгрузить список всех постоянных (бессрочных) встреч организации"""
    pass


@endpoint("/eventsessions/endless/activities")
def endless_meetings_activities():
    """Получить данные об отдельных сессиях в рамках постоянных встреч"""
    pass


@endpoint("/eventsessions/{eventSessionId}/transcript/list")
def transcript_list():
    """Получить список доступных текстовых расшифровок для мероприятия"""
    pass


@endpoint("/transcript/{transcriptId}")
def transcript_summary():
    """Получить готовую краткую сводку (саммари) и полную текстовую расшифровку"""
    pass


@endpoint("/eventsessions/{eventsessionID}/participations")
def event_participants():
    """Получить список всех зарегистрированных участников для конкретного мероприятия"""
    pass


@endpoint("/events/{eventID}/participations")
def event_series_stats():
    """Получить общую статистику посещаемости для всей серии мероприятий"""
    pass


class EventsStatsExtractor(BaseExtractor):
    """Специализированный экстрактор для статистики мероприятий с обязательными параметрами"""
    
    def get_endpoint(self) -> str:
        return "/stats/events"
    
    def get_url_params(self, **kwargs) -> Optional[Dict[str, Any]]:
        params = {}
        
        # Обязательный параметр from
        if 'from_date' in kwargs:
            params['from'] = kwargs['from_date']
        elif 'from' in kwargs:
            params['from'] = kwargs['from']
        else:
            raise ValueError("Parameter 'from' (or 'from_date') is required. Format: yyyy-mm-dd+hh:mm:ss")
        
        # Дополнительные параметры
        if 'to' in kwargs and kwargs['to']:
            params['to'] = kwargs['to']
        if 'userId' in kwargs and kwargs['userId']:
            params['userId'] = kwargs['userId']
        if 'eventId' in kwargs and kwargs['eventId']:
            params['eventId'] = kwargs['eventId']
            
        return params if params else None
    
    def extract_and_save(self, filename: Optional[str] = None, **kwargs) -> Optional[str]:
        """Extract data and automatically save to file"""
        data = self.extract(**kwargs)
        if data is not None:
            return self.save_to_file(data, filename)
        return None


@endpoint("/stats/events")
def events_stats():
    """Выгрузить статистику по мероприятиям
    
    Обязательные параметры:
    - from_date или from: дата начала периода (формат: yyyy-mm-dd+hh:mm:ss)
    
    Дополнительные параметры:
    - to: дата окончания периода (формат: yyyy-mm-dd+hh:mm:ss)
    - userId: ID сотрудника для ограничения выборки
    - eventId: ID конкретного мероприятия
    """
    pass


@endpoint("/stats/users")
def users_stats():
    """Получить данные по активности и посещениям конкретных пользователей"""
    pass


@endpoint("/stats/users/visits/{userID}")
def visits_stats():
    """Получить общую статистику всех посещений мероприятий для конкретного пользователя"""
    # UNAVAILABLE - 404 Error: No route found for "GET /userapi/stats/users/visits/{userID}"
    pass


@endpoint("/records")
def online_records_list():
    """Получить список всех доступных онлайн-записей мероприятий"""
    pass


@endpoint("/records/conversions/{conversionID}")
def conversion_status():
    """Узнать текущий статус конвертации записи в формат MP4"""
    pass


@endpoint("/eventsessions/{eventSessionId}/converted-records")
def converted_records():
    """Получить информацию о готовой MP4-записи мероприятия"""
    pass


@endpoint("/eventsessions/{eventsessionID}/chat")
def event_chat_messages():
    """Выгрузить всю историю сообщений из чата конкретного мероприятия"""
    pass


@endpoint("/eventsessions/{eventsessionID}/questions")
def event_questions():
    """Выгрузить все вопросы, заданные участниками через специальный модуль"""
    pass


@endpoint("/eventsessions/{eventSessionId}/attention-control/checkpoints")
def attention_checkpoints():
    """Получить информацию о точках контроля внимания, показанных участникам"""
    pass


@endpoint("/eventsessions/{eventSessionId}/attention-control/interactions")
def attention_interactions():
    """Получить данные о реакциях участников на чекпоинты контроля внимания"""
    pass


@endpoint("/eventsessions/{eventSessionId}/raising-hands")
def raising_hands():
    """Получить список участников, которые "поднимали руку" во время сессии"""
    pass


@endpoint("/eventsessions/{eventSessionId}/likes")
def event_likes():
    """Получить данные по реакциям "огонек", отправленным участниками"""
    pass


@endpoint("/eventsessions/{eventSessionId}/emoji-reactions")
def emoji_reactions():
    """Получить список всех реакций с эмодзи, отправленных во время сессии"""
    pass


@endpoint("/organization/eventsessions/streamFilesUrls")
def stream_files_urls():
    """Получить URL-адреса видеопотоков спикеров"""
    pass


def list_available_extractors():
    """List all available extractors"""
    endpoints = get_registered_endpoints()
    logger.info("Available MTS Link Events extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        logger.info(f"  {name}: {path}")
        logger.info(f"    {description}")
    return endpoints


def main():
    """Main function to run extractors"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MTS-Link Events API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')
    parser.add_argument('--all', '-a', action='store_true', help='Run all extractors')
    
    parser.add_argument('--eventSessionId', help='Event Session ID for parameterized endpoints')
    parser.add_argument('--eventsessionID', help='Event Session ID (alternative parameter name)')
    parser.add_argument('--userID', help='User ID for user-specific endpoints')
    parser.add_argument('--eventID', help='Event ID for event-specific endpoints')
    parser.add_argument('--transcriptId', help='Transcript ID for transcript endpoints')
    parser.add_argument('--conversionID', help='Conversion ID for conversion status')
    
    # Parameters for events_stats
    parser.add_argument('--from', '--from_date', dest='from_date', help='Start date for events_stats (format: yyyy-mm-dd+hh:mm:ss)')
    parser.add_argument('--to', help='End date for events_stats (format: yyyy-mm-dd+hh:mm:ss)')
    parser.add_argument('--userId', help='User ID to filter events_stats by specific user')
    parser.add_argument('--eventId', help='Event ID to filter events_stats by specific event')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_extractors()
        return
    
    kwargs = {}
    if args.eventSessionId:
        kwargs['eventSessionId'] = args.eventSessionId
    if args.eventsessionID:
        kwargs['eventsessionID'] = args.eventsessionID
    if args.userID:
        kwargs['userID'] = args.userID
    if args.eventID:
        kwargs['eventID'] = args.eventID
    if args.transcriptId:
        kwargs['transcriptId'] = args.transcriptId
    if args.conversionID:
        kwargs['conversionID'] = args.conversionID
    
    # Parameters for events_stats
    if args.from_date:
        kwargs['from_date'] = args.from_date
    if args.to:
        kwargs['to'] = args.to
    if args.userId:
        kwargs['userId'] = args.userId
    if args.eventId:
        kwargs['eventId'] = args.eventId
    
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
        # Special handling for events_stats which requires custom extractor
        if args.extractor == 'events_stats':
            try:
                extractor = EventsStatsExtractor()
                result = extractor.extract_and_save(**kwargs)
                if result:
                    logger.success(f"Extraction completed: {result}")
                else:
                    logger.error(f"Extraction failed")
            except ValueError as e:
                logger.error(f"{e}")
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
    logger.info("  python link_events_extractors.py event_session_details --eventSessionId 123")
    logger.info("  python link_events_extractors.py events_stats --from 2023-01-01+00:00:00 --to 2023-12-31+23:59:59")
    
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
            # Special handling for events_stats in interactive mode
            if choice == 'events_stats':
                try:
                    extractor = EventsStatsExtractor()
                    result = extractor.extract_and_save(**kwargs)
                    if result:
                        logger.success(f"Extraction completed: {result}")
                    else:
                        logger.error(f"Extraction failed")
                except ValueError as e:
                    logger.error(f"{e}")
                    logger.info("Note: events_stats requires --from parameter. Use command line for parameters.")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
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