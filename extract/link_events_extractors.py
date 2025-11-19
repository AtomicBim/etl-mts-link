import sys
import os
from typing import Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints, BaseExtractor


class OrganizationEventsExtractor(BaseExtractor):
    """Экстрактор для расписания мероприятий организации с обязательным параметром from"""

    def get_endpoint(self) -> str:
        return "/organization/events/schedule"

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
        for param in ['name', 'to', 'page', 'perPage']:
            if param in kwargs and kwargs[param]:
                params[param] = kwargs[param]

        # Обработка status[] как массива
        if 'status' in kwargs and kwargs['status']:
            if isinstance(kwargs['status'], list):
                for i, status in enumerate(kwargs['status']):
                    params[f'status[{i}]'] = status
            else:
                params['status[0]'] = kwargs['status']

        return params if params else None


@endpoint("/organization/events/schedule")
def organization_events_schedule():
    """Получить информацию о всех мероприятиях организации

    Обязательные параметры:
    - from: дата начала периода выборки (формат: yyyy-mm-dd+hh:mm:ss)

    Дополнительные параметры:
    - name: названия вебинара
    - status: статус вебинаров (ACTIVE, STOP, START)
    - to: дата окончания периода выборки
    - page: номер страницы выборки (по умолчанию: 1)
    - perPage: количество элементов на странице (10, 50, 100, 250)
    """
    pass


@endpoint("/organization/events/{eventID}")
def event_series_data():
    """Получить данные о шаблоне или серии мероприятий"""
    pass


class UserEventsExtractor(BaseExtractor):
    """Экстрактор для расписания мероприятий пользователя с обязательным параметром from"""

    def get_endpoint(self) -> str:
        return "/users/{userID}/events/schedule"

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
        for param in ['name', 'to', 'page', 'perPage']:
            if param in kwargs and kwargs[param]:
                params[param] = kwargs[param]

        # Обработка status[] как массива
        if 'status' in kwargs and kwargs['status']:
            if isinstance(kwargs['status'], list):
                for i, status in enumerate(kwargs['status']):
                    params[f'status[{i}]'] = status
            else:
                params['status[0]'] = kwargs['status']

        return params if params else None


@endpoint("/users/{userID}/events/schedule")
def user_events_schedule():
    """Получить информацию о мероприятиях, созданных конкретным сотрудником

    Обязательные параметры:
    - userID: идентификатор пользователя (в URL)
    - from: дата начала периода выборки (формат: yyyy-mm-dd+hh:mm:ss)

    Дополнительные параметры:
    - name: названия вебинара
    - status: статус вебинаров (ACTIVE, STOP, START)
    - to: дата окончания периода выборки
    - page: номер страницы выборки (по умолчанию: 1)
    - perPage: количество элементов на странице (10, 50, 100, 250)
    """
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


@endpoint("/eventsessions/{eventSessionId}/participations")
def event_session_participations():
    """Получить информацию об участниках конкретного мероприятия
    
    Обязательные параметры:
    - eventSessionId: идентификатор сессии мероприятия (в URL)
    
    Дополнительные параметры:
    - page: номер страницы выборки (по умолчанию: 1)
    - perPage: количество элементов на странице (10, 50, 100, 250)
    """
    pass


@endpoint("/eventsessions/{eventSessionId}/attention-control/checkpoints")
def event_attention_checkpoints():
    """Получить список контрольных точек присутствия на мероприятии
    
    Обязательные параметры:
    - eventSessionId: идентификатор сессии мероприятия (в URL)
    """
    pass


@endpoint("/eventsessions/{eventSessionId}/attention-control/interactions")
def event_attention_interactions():
    """Получить информацию о взаимодействиях участников (контроль присутствия)
    
    Обязательные параметры:
    - eventSessionId: идентификатор сессии мероприятия (в URL)
    
    Дополнительные параметры:
    - checkpointId: идентификатор контрольной точки
    """
    pass


@endpoint("/eventsessions/endless")
def endless_events_list():
    """Получить список постоянных встреч (endless events)
    
    Дополнительные параметры:
    - page: номер страницы выборки (по умолчанию: 1)
    - perPage: количество элементов на странице (10, 50, 100, 250)
    """
    pass


@endpoint("/eventsessions/endless/activities")
def endless_events_activities():
    """Получить активности в постоянных встречах
    
    Дополнительные параметры:
    - from: дата начала периода выборки (формат: yyyy-mm-dd+hh:mm:ss)
    - to: дата окончания периода выборки
    - page: номер страницы выборки (по умолчанию: 1)
    - perPage: количество элементов на странице (10, 50, 100, 250)
    """
    pass


@endpoint("/eventsessions/{eventSessionId}/recordings")
def event_session_recordings():
    """Получить список записей мероприятия
    
    Обязательные параметры:
    - eventSessionId: идентификатор сессии мероприятия (в URL)
    """
    pass


@endpoint("/users/{userId}/events/participations")
def user_events_participations():
    """Получить информацию об участии пользователя в мероприятиях
    
    Обязательные параметры:
    - userId: идентификатор пользователя (в URL)
    
    Дополнительные параметры:
    - from: дата начала периода выборки (формат: yyyy-mm-dd+hh:mm:ss)
    - to: дата окончания периода выборки
    - page: номер страницы выборки (по умолчанию: 1)
    - perPage: количество элементов на странице (10, 50, 100, 250)
    """
    pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run MTS-Link Events API extractors')
    parser.add_argument('extractor', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')

    for arg in ['eventSessionId', 'eventsessionID', 'userID', 'eventID', 'transcriptId', 'from_date', 'from', 'to', 'userId', 'eventId', 'name', 'status', 'page', 'perPage', 'cursor', 'checkpointId']:
        parser.add_argument(f'--{arg}', help=f'{arg} parameter')

    args = parser.parse_args()

    if args.list:
        endpoints = get_registered_endpoints()
        for name, path in endpoints.items():
            print(f"{name}: {path}")
        exit()

    kwargs = {k: v for k, v in vars(args).items() if v is not None and k != 'extractor' and k != 'list'}

    # Специальная обработка для endpoints с обязательными параметрами
    if args.extractor == 'organization_events_schedule':
        try:
            extractor = OrganizationEventsExtractor()
            data = extractor.extract(**kwargs)
            if data is not None:
                result = extractor.save_to_file(data)
                print(f"Result: {result}")
            else:
                print("Extraction failed")
        except ValueError as e:
            print(f"Error: {e}")
    elif args.extractor == 'user_events_schedule':
        try:
            extractor = UserEventsExtractor()
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