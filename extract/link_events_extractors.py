import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints


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


@endpoint("/eventsessions/{eventSessionId}/agendas")
def event_session_notes():
    """Выгрузить заметки и итоги, созданные во время мероприятия"""
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


# NOTE: This endpoint does not exist in the MTS Link API (returns 404)
# Tested alternatives: /organization/stats/events, /events/stats, etc. - all return 404
# @endpoint("/stats/events")
# def events_stats():
#     """Получить агрегированную статистику по всем мероприятиям"""
#     pass


@endpoint("/stats/users")
def users_stats():
    """Получить данные по активности и посещениям конкретных пользователей"""
    pass


@endpoint("/stats/users/visits/{userID}")
def visits_stats():
    """Получить общую статистику всех посещений мероприятий для конкретного пользователя"""
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
    print("Available MTS Link Events extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        print(f"  {name}: {path}")
        print(f"    {description}")
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
    print("Example: python link_events_extractors.py event_session_details --eventSessionId 123")
    
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