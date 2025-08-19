# ETL MTS-Link

ETL система для извлечения данных из API МТС Линк с использованием декоратор-паттерна для определения endpoint'ов.

## Установка и настройка

### 1. Создание виртуального окружения

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # Linux/Mac
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка конфигурации

#### Токен API
Отредактируйте файл `config/tokens.json`:
```json
{
  "api_token": "your_mts_link_token_here",
  "base_url": "https://userapi.mts-link.ru/v3"
}
```

#### Путь для сохранения файлов
Настройте путь в файле `.env`:
```env
EXTRACTION_PATH=C:/Users/YourUser/YourFolder
```

## Использование

### Просмотр доступных экстракторов

```bash
python extract/link_events_extractors.py --list
```

### Запуск одного экстрактора

```bash
# Простые экстракторы (без параметров)
python extract/link_events_extractors.py organization_events_schedule

# Экстракторы с параметрами
python extract/link_events_extractors.py event_session_details --eventsessionID 123456
python extract/link_events_extractors.py user_events_schedule --userID 789012
```

### Запуск всех экстракторов

```bash
# Запускает только экстракторы, которые не требуют параметров
python extract/link_events_extractors.py --all
```

### Интерактивный режим

```bash
python extract/link_events_extractors.py
```

## Доступные экстракторы

### Экстракторы без параметров (можно запускать с --all):

| Название | Endpoint | Описание |
|----------|----------|----------|
| `organization_events_schedule` | `/organization/events/schedule` | Информация о всех мероприятиях организации |
| `endless_meetings_list` | `/eventsessions/endless` | Список всех постоянных встреч |
| `endless_meetings_activities` | `/eventsessions/endless/activities` | Данные об отдельных сессиях в постоянных встречах |
| `events_stats` | `/stats/events` | Агрегированная статистика по всем мероприятиям |
| `users_stats` | `/stats/users` | Данные по активности пользователей |
| `visits_stats` | `/stats/users/visits` | Общая статистика всех посещений |
| `online_records_list` | `/records` | Список всех онлайн-записей мероприятий |
| `stream_files_urls` | `/organization/eventsessions/streamFilesUrls` | URL-адреса видеопотоков спикеров |

### Экстракторы с параметрами:

| Название | Endpoint | Параметр | Описание |
|----------|----------|----------|----------|
| `event_session_details` | `/eventsessions/{eventsessionID}` | `--eventsessionID` | Детальная информация о мероприятии |
| `user_events_schedule` | `/users/{userID}/events/schedule` | `--userID` | Мероприятия конкретного сотрудника |
| `event_series_data` | `/organization/events/{eventID}` | `--eventID` | Данные о серии мероприятий |
| `event_session_notes` | `/eventsessions/{eventSessionId}/agendas` | `--eventSessionId` | Заметки и итоги мероприятия |
| `transcript_list` | `/eventsessions/{eventSessionId}/transcript/list` | `--eventSessionId` | Список текстовых расшифровок |
| `transcript_summary` | `/transcript/{transcriptId}` | `--transcriptId` | Саммаризация и текстовая расшифровка |
| `event_participants` | `/eventsessions/{eventsessionID}/participations` | `--eventsessionID` | Список участников мероприятия |
| `event_series_stats` | `/events/{eventID}/participations` | `--eventID` | Статистика по серии мероприятий |
| `conversion_status` | `/records/conversions/{conversionID}` | `--conversionID` | Статус конвертации записи |
| `converted_records` | `/eventsessions/{eventSessionId}/converted-records` | `--eventSessionId` | Сконвертированные записи |
| `event_chat_messages` | `/eventsessions/{eventsessionID}/chat` | `--eventsessionID` | История сообщений чата |
| `event_questions` | `/eventsessions/{eventsessionID}/questions` | `--eventsessionID` | Вопросы участников |
| `attention_checkpoints` | `/eventsessions/{eventSessionId}/attention-control/checkpoints` | `--eventSessionId` | Точки контроля внимания |
| `attention_interactions` | `/eventsessions/{eventSessionId}/attention-control/interactions` | `--eventSessionId` | Реакции на контроль внимания |
| `raising_hands` | `/eventsessions/{eventSessionId}/raising-hands` | `--eventSessionId` | Список поднятий рук |
| `event_likes` | `/eventsessions/{eventSessionId}/likes` | `--eventSessionId` | Реакции "огонек" |
| `emoji_reactions` | `/eventsessions/{eventSessionId}/emoji-reactions` | `--eventSessionId` | Реакции с эмодзи |

## Примеры использования

### 1. Получить расписание всех мероприятий
```bash
python extract/link_events_extractors.py organization_events_schedule
```

### 2. Получить детали конкретного мероприятия
```bash
python extract/link_events_extractors.py event_session_details --eventsessionID 2282834298
```

### 3. Получить статистику пользователей
```bash
python extract/link_events_extractors.py users_stats
```

### 4. Запустить все доступные экстракторы
```bash
python extract/link_events_extractors.py --all
```

## Результаты работы

Все извлеченные данные сохраняются в JSON-файлы в папку, указанную в переменной `EXTRACTION_PATH`. 

Формат имени файла: `_{endpoint_name}_{timestamp}.json`

Пример: `_organization_events_schedule_20250819_174715.json`

## Архитектура

### Структура проекта
```
etl-mts-link/
├── abstractions/
│   └── extract.py          # Базовый класс и декоратор
├── config/
│   └── tokens.json         # Конфигурация API
├── extract/
│   └── link_events_extractors.py  # Все экстракторы МТС Линк
├── .env                    # Переменные окружения
├── requirements.txt        # Зависимости Python
└── README.md              # Документация
```

### Как добавить новый экстрактор

1. Откройте файл `extract/link_events_extractors.py`
2. Добавьте новую функцию с декоратором `@endpoint`:

```python
@endpoint("/new/api/endpoint")
def new_extractor():
    """Описание нового экстрактора"""
    pass
```

3. Экстрактор автоматически появится в списке доступных

### Базовый класс

`BaseExtractor` в `abstractions/extract.py` обеспечивает:
- Загрузку конфигурации из `config/tokens.json`
- Аутентификацию через `x-auth-token` заголовок
- Выполнение HTTP-запросов с обработкой ошибок
- Автоматическое сохранение данных в JSON-файлы
- Загрузку пути сохранения из переменных окружения

## Требования

- Python 3.7+
- Зависимости из `requirements.txt`:
  - `requests` - для HTTP-запросов
  - `python-dotenv` - для работы с .env файлами
  - `pip-tools` - для управления зависимостями

## Лицензия

Этот проект предназначен для внутреннего использования.