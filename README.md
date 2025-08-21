# ETL MTS Link - Экстракторы API данных

Этот проект представляет собой набор экстракторов для работы с API МТС Линк - корпоративной платформы для проведения видеоконференций, обучения и совместной работы.

## Описание проекта

Проект реализует паттерн ETL (Extract, Transform, Load) для извлечения данных из различных модулей МТС Линк через REST API. Все экстракторы организованы по функциональным модулям и поддерживают как командную строку, так и интерактивный режим работы.

### Архитектура

- **Базовые классы** (`abstractions/`):
  - `BaseExtractor` - базовый класс для всех экстракторов
  - `UniversalExtractor` - универсальный экстрактор для простых endpoints
  - `BaseExtractorCLI` - базовый класс для CLI интерфейсов
  - Система декораторов для регистрации endpoints
  - Унифицированная система логирования с цветовым выводом

- **Экстракторы** (`extract/`) - модули для извлечения данных из различных API endpoints
- **Конфигурация** (`config/`) - настройки API токенов и параметров подключения

## Структура проекта

```
etl-mts-link/
├── abstractions/          # Базовые классы и утилиты
│   ├── extract.py         # Базовые классы экстракторов
│   └── logging_config.py  # Настройка логирования
├── config/               # Конфигурационные файлы
│   └── tokens.json       # API токены и настройки
├── extract/              # Модули экстракторов
│   ├── link_addressbook_extractors.py    # Адресная книга и пользователи
│   ├── link_chats_extractors.py          # Чаты и курсы
│   ├── link_events_extractors.py         # Мероприятия и встречи
│   ├── link_files_extractors.py          # Файлы и записи
│   ├── link_organisation_extractors.py   # Организация и настройки
│   └── link_tests_extractors.py          # Тесты и голосования
└── README.md             # Данный файл
```

## Установка и настройка

### Требования
- Python 3.7+
- Библиотеки: `requests`, `python-dotenv`

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Настройка конфигурации
1. Создайте файл `config/tokens.json`:
```json
{
  "api_token": "ваш_api_токен_мтс_линк",
  "base_url": "https://api.mts-link.ru/v3"
}
```

2. Опционально создайте `.env` файл для настройки пути сохранения данных:
```bash
EXTRACTION_PATH=./extracted_data
```

## Экстракторы

### 1. Адресная книга и пользователи (`link_addressbook_extractors.py`)

Экстракторы для работы с контактами и информацией о пользователях организации.

**Доступные экстракторы:**

- **`contacts_search`** - Поиск по контактам в адресной книге
  ```bash
  python extract/link_addressbook_extractors.py contacts_search --query "поисковый запрос"
  ```

- **`organization_members`** - Список всех сотрудников организации
  ```bash
  python extract/link_addressbook_extractors.py organization_members
  ```

- **`contact_details`** - Детальная информация о конкретном контакте
  ```bash
  python extract/link_addressbook_extractors.py contact_details --contactsID 12345
  ```

- **`user_profile`** - Профиль текущего пользователя (требует OAuth)
  ```bash
  python extract/link_addressbook_extractors.py user_profile
  ```

### 2. Чаты и курсы (`link_chats_extractors.py`)

Экстракторы для работы с чатами МТС Линк и системой дистанционного обучения.

**Экстракторы чатов:**

- **`chats_organization_members`** - Пользователи организации в чатах
  ```bash
  python extract/link_chats_extractors.py chats_organization_members
  ```

- **`user_channels`** - Каналы конкретного пользователя
  ```bash
  python extract/link_chats_extractors.py user_channels --userId 74817491
  ```

- **`channel_messages`** - Сообщения из канала (с расширенными параметрами)
  ```bash
  python extract/link_chats_extractors.py channel_messages --chatId "channel-id" --limit 100
  ```

- **`channel_users`** - Участники канала
  ```bash
  python extract/link_chats_extractors.py channel_users --channelId "channel-id"
  ```

- **`channel_info`** - Информация о канале
  ```bash
  python extract/link_chats_extractors.py channel_info --channelId "channel-id"
  ```

**Экстракторы курсов:**

- **`organization_courses`** - Список всех курсов организации
- **`course_details`** - Детали конкретного курса
- **`courses_groups`** - Учебные группы курсов
- **`user_course_statistics`** - Статистика прохождения курсов пользователем

### 3. Мероприятия и встречи (`link_events_extractors.py`)

Самый обширный набор экстракторов для работы с видеоконференциями и мероприятиями.

**Основные экстракторы:**

- **`organization_events_schedule`** - Расписание всех мероприятий организации
- **`event_session_details`** - Детали конкретного мероприятия
  ```bash
  python extract/link_events_extractors.py event_session_details --eventsessionID 2282834298
  ```

- **`user_events_schedule`** - Мероприятия конкретного пользователя
  ```bash
  python extract/link_events_extractors.py user_events_schedule --userID 74817491
  ```

**Статистика и аналитика:**

- **`events_stats`** - Статистика мероприятий (требует обязательный параметр from)
  ```bash
  python extract/link_events_extractors.py events_stats --from "2025-01-01+00:00:00"
  ```

- **`users_stats`** - Статистика пользователей
- **`event_participants`** - Участники мероприятия
- **`event_series_stats`** - Статистика серии мероприятий

**Интерактивные данные:**

- **`event_chat_messages`** - История чата мероприятия
- **`event_questions`** - Вопросы от участников
- **`attention_checkpoints`** - Точки контроля внимания
- **`attention_interactions`** - Реакции на контроль внимания
- **`raising_hands`** - "Поднятые руки" участников
- **`event_likes`** - Реакции "огонек"
- **`emoji_reactions`** - Эмодзи реакции

**Записи и файлы:**

- **`transcript_list`** - Список расшифровок
- **`converted_records`** - MP4 записи мероприятий
- **`stream_files_urls`** - URL видеопотоков

### 4. Файлы и записи (`link_files_extractors.py`)

Экстракторы для работы с файловой системой МТС Линк.

- **`files_list`** - Полный список файлов организации
- **`file_details`** - Детали конкретного файла
  ```bash
  python extract/link_files_extractors.py file_details --fileID 578924551 --name "filename.png"
  ```

- **`event_session_files`** - Файлы, прикрепленные к мероприятию
- **`event_series_files`** - Файлы серии мероприятий
- **`converted_records_list`** - Список MP4 записей

### 5. Организация и настройки (`link_organisation_extractors.py`)

Экстракторы для административных данных организации.

- **`brandings_list`** - Брендинги организации
- **`organization_groups`** - Группы пользователей
- **`partner_applications`** - Интеграции через OAuth
- **`timezones_list`** - Доступные часовые пояса

### 6. Тесты и голосования (`link_tests_extractors.py`)

Экстракторы для системы тестирования и опросов.

- **`tests_list`** - Список всех тестов
- **`test_info`** - Детали конкретного теста
  ```bash
  python extract/link_tests_extractors.py test_info --testId 1439438553 --testSessionId 646357
  ```

- **`test_results`** - Результаты теста
- **`user_tests_stats`** - Статистика тестов пользователя
- **`test_custom_answers`** - Текстовые ответы на открытые вопросы

## Использование

### Командная строка

Каждый экстрактор поддерживает стандартные команды:

```bash
# Показать список доступных экстракторов
python extract/link_events_extractors.py --list

# Запустить все экстракторы без параметров
python extract/link_events_extractors.py --all

# Запустить конкретный экстрактор
python extract/link_events_extractors.py organization_events_schedule

# Запустить с параметрами
python extract/link_events_extractors.py event_session_details --eventsessionID 12345
```

### Интерактивный режим

Запуск без параметров открывает интерактивный режим:

```bash
python extract/link_events_extractors.py

# В интерактивном режиме доступны команды:
# - имя экстрактора для его запуска
# - 'all' для запуска всех экстракторов
# - 'quit' или 'exit' для выхода
```

### Программный интерфейс

```python
from abstractions.extract import run_extractor, UniversalExtractor

# Запуск экстрактора по имени
result = run_extractor('organization_events_schedule')

# Создание универсального экстрактора
extractor = UniversalExtractor('/organization/events/schedule')
data = extractor.extract()
filename = extractor.save_to_file(data)
```

## Особенности реализации

### Система регистрации endpoints

Используется декоратор `@endpoint()` для автоматической регистрации API точек:

```python
@endpoint("/organization/events/schedule")
def organization_events_schedule():
    """Получить информацию о всех мероприятиях организации"""
    pass
```

### Специализированные экстракторы

Некоторые endpoints требуют специальной обработки параметров и реализованы как отдельные классы:

- `EventsStatsExtractor` - для статистики с обязательным параметром `from`
- `FileDetailsExtractor` - для файлов с дополнительными параметрами
- `TestInfoExtractor` - для тестов с опциональными параметрами

### Обработка ошибок

Все экстракторы включают обработку следующих ошибок:
- HTTP ошибки (401, 403, 404, etc.)
- Ошибки сети и таймауты
- Ошибки парсинга JSON
- Недоступные endpoints (помечены как UNAVAILABLE в комментариях)

### Сохранение данных

- Автоматическое создание имен файлов с временными метками
- Сохранение в JSON формате с правильной кодировкой UTF-8
- Структурированное логирование процесса извлечения

## Конфигурация токенов

Файл `config/tokens.json` должен содержать:

```json
{
  "api_token": "ваш_api_токен",
  "base_url": "https://api.mts-link.ru/v3"
}
```

API токен можно получить в административной панели МТС Линк в разделе интеграций.

## Логирование

Проект использует цветное логирование с уровнями:
- **INFO** (белый) - общая информация
- **SUCCESS** (зеленый) - успешные операции  
- **WARNING** (желтый) - предупреждения
- **ERROR** (красный) - ошибки
- **DEBUG** (голубой) - отладочная информация

## Примеры использования

### Массовое извлечение данных о мероприятиях
```bash
# Получить все мероприятия
python extract/link_events_extractors.py organization_events_schedule

# Получить статистику за период
python extract/link_events_extractors.py events_stats --from "2024-01-01+00:00:00" --to "2024-12-31+23:59:59"

# Получить участников конкретного мероприятия
python extract/link_events_extractors.py event_participants --eventsessionID 2282834298
```

### Анализ чатовой активности
```bash
# Получить всех пользователей чатов
python extract/link_chats_extractors.py chats_organization_members

# Получить сообщения из конкретного канала
python extract/link_chats_extractors.py channel_messages --chatId "channel-uuid" --limit 1000
```

### Аудит файлов и записей
```bash
# Получить все файлы организации
python extract/link_files_extractors.py files_list

# Получить все готовые MP4 записи
python extract/link_files_extractors.py converted_records_list
```

Этот проект предоставляет полный инструментарий для извлечения и анализа данных из всех модулей МТС Линк, обеспечивая гибкость использования и высокую надежность извлечения данных.