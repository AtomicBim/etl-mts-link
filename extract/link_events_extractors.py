import sys
import os
from typing import Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints, BaseExtractor


@endpoint("/organization/events/schedule")
def organization_events_schedule():
    """Получить информацию о всех мероприятиях организации"""
    pass


@endpoint("/organization/events/{eventID}")
def event_series_data():
    """Получить данные о шаблоне или серии мероприятий"""
    pass


@endpoint("/users/{userID}/events/schedule")
def user_events_schedule():
    """Получить информацию о мероприятиях, созданных конкретным сотрудником"""
    pass


@endpoint("/eventsessions/{eventsessionID}")
def event_session_details():
    """Получить детальную информацию о конкретном мероприятии"""
    pass


@endpoint("/eventsessions/{eventSessionId}/transcript/list")
def transcript_list():
    """Получить список доступных текстовых расшифровок для мероприятия"""
    pass


@endpoint("/transcript/{transcriptId}")
def transcript_summary():
    """Получить готовую краткую сводку (саммари) и полную текстовую расшифровку"""
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

        if 'from_date' in kwargs:
            params['from'] = kwargs['from_date']
        elif 'from' in kwargs:
            params['from'] = kwargs['from']
        else:
            raise ValueError("Parameter 'from' (or 'from_date') is required. Format: yyyy-mm-dd+hh:mm:ss")

        if 'to' in kwargs and kwargs['to']:
            params['to'] = kwargs['to']
        if 'userId' in kwargs and kwargs['userId']:
            params['userId'] = kwargs['userId']
        if 'eventId' in kwargs and kwargs['eventId']:
            params['eventId'] = kwargs['eventId']

        return params if params else None


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


@endpoint("/records")
def online_records_list():
    """Получить список всех доступных онлайн-записей мероприятий"""
    pass


@endpoint("/eventsessions/{eventSessionId}/converted-records")
def converted_records():
    """Получить информацию о готовой MP4-записи мероприятия"""
    pass


@endpoint("/eventsessions/{eventsessionID}/chat")
def event_chat_messages():
    """Выгрузить всю историю сообщений из чата конкретного мероприятия"""
    pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run MTS-Link Events API extractors')
    parser.add_argument('extractor', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')

    for arg in ['eventSessionId', 'eventsessionID', 'userID', 'eventID', 'transcriptId', 'from_date', 'to', 'userId', 'eventId']:
        parser.add_argument(f'--{arg}', help=f'{arg} parameter')

    args = parser.parse_args()

    if args.list:
        endpoints = get_registered_endpoints()
        for name, path in endpoints.items():
            print(f"{name}: {path}")
        exit()

    kwargs = {k: v for k, v in vars(args).items() if v is not None and k != 'extractor' and k != 'list'}

    if args.extractor == 'events_stats':
        try:
            extractor = EventsStatsExtractor()
            data = extractor.extract(**kwargs)
            if data is not None:
                result = extractor.save_to_file(data)
                print(f"Result: {result}")
            else:
                print("Extraction failed")
        except ValueError as e:
            print(f"Error: {e}")
    else:
        result = run_extractor(args.extractor, **kwargs)
        print(f"Result: {result}")