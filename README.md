# ETL MTS Link - Экстракторы API данных

Набор экстракторов для извлечения данных из API МТС Линк - корпоративной платформы для видеоконференций, обучения и совместной работы.

## Установка

```bash
pip install -r requirements.txt
```

Создайте файл `config/tokens.json`:
```json
{
  "api_token": "ваш_api_токен_мтс_линк",
  "base_url": "https://api.mts-link.ru/v3"
}
```

## Экстракторы

### 1. События и мероприятия (`link_events_extractors.py`)

```bash
# Показать все доступные экстракторы
"venv/Scripts/python.exe" extract/link_events_extractors.py --list

# Основные экстракторы
"venv/Scripts/python.exe" extract/link_events_extractors.py organization_events_schedule
"venv/Scripts/python.exe" extract/link_events_extractors.py event_session_details --eventsessionID 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py user_events_schedule --userID 74817491
"venv/Scripts/python.exe" extract/link_events_extractors.py event_series_data --eventID 2293097334

# Статистика (обязательный параметр from)
"venv/Scripts/python.exe" extract/link_events_extractors.py events_stats --from "2025-01-01+00:00:00"
"venv/Scripts/python.exe" extract/link_events_extractors.py users_stats
"venv/Scripts/python.exe" extract/link_events_extractors.py visits_stats --userID 74817491

# Участники и взаимодействие
"venv/Scripts/python.exe" extract/link_events_extractors.py event_participants --eventsessionID 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py event_chat_messages --eventsessionID 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py event_questions --eventsessionID 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py attention_checkpoints --eventSessionId 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py attention_interactions --eventSessionId 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py raising_hands --eventSessionId 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py event_likes --eventSessionId 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py emoji_reactions --eventSessionId 2282834298

# Записи и файлы
"venv/Scripts/python.exe" extract/link_events_extractors.py transcript_list --eventSessionId 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py converted_records --eventSessionId 2282834298
"venv/Scripts/python.exe" extract/link_events_extractors.py online_records_list
"venv/Scripts/python.exe" extract/link_events_extractors.py stream_files_urls

# Постоянные встречи
"venv/Scripts/python.exe" extract/link_events_extractors.py endless_meetings_list
"venv/Scripts/python.exe" extract/link_events_extractors.py endless_meetings_activities
```

### 2. Чаты и курсы (`link_chats_extractors.py`)

```bash
# Показать все доступные экстракторы
"venv/Scripts/python.exe" extract/link_chats_extractors.py --list

# Пользователи и каналы
"venv/Scripts/python.exe" extract/link_chats_extractors.py chats_organization_members
"venv/Scripts/python.exe" extract/link_chats_extractors.py user_channels --userId 74817491
"venv/Scripts/python.exe" extract/link_chats_extractors.py channel_users --channelId "1f04c259-5854-6e4c-bba2-ca9a267b707c"
"venv/Scripts/python.exe" extract/link_chats_extractors.py channel_info --channelId "1f04c259-5854-6e4c-bba2-ca9a267b707c"

# Сообщения (лимит до 100 за запрос)
"venv/Scripts/python.exe" extract/link_chats_extractors.py channel_messages --chatId "1f04c259-5854-6e4c-bba2-ca9a267b707c" --limit 10
"venv/Scripts/python.exe" extract/link_chats_extractors.py channel_messages --chatId "1f04c259-5854-6e4c-bba2-ca9a267b707c" --viewerId "user456" --direction "Before" --limit 5

# Получение ВСЕХ сообщений без ограничений (специальный скрипт)
"venv/Scripts/python.exe" fetch_all_messages.py "1f04c259-5854-6e4c-bba2-ca9a267b707c"
"venv/Scripts/python.exe" fetch_all_messages.py "1f04c259-5854-6e4c-bba2-ca9a267b707c" --fromMessageId "1f050b8d-3ff0-62de-8f23-03bad8f244fa"

# Курсы
"venv/Scripts/python.exe" extract/link_chats_extractors.py organization_courses
"venv/Scripts/python.exe" extract/link_chats_extractors.py course_details --Courseid 123
"venv/Scripts/python.exe" extract/link_chats_extractors.py courses_groups
"venv/Scripts/python.exe" extract/link_chats_extractors.py user_course_statistics --userID 74817491
```

### 3. Адресная книга (`link_addressbook_extractors.py`)

```bash
# Показать все доступные экстракторы
"venv/Scripts/python.exe" extract/link_addressbook_extractors.py --list

# Основные экстракторы
"venv/Scripts/python.exe" extract/link_addressbook_extractors.py organization_members
"venv/Scripts/python.exe" extract/link_addressbook_extractors.py contacts_search
"venv/Scripts/python.exe" extract/link_addressbook_extractors.py contact_details --contactsID 1341627
```

### 4. Файлы и записи (`link_files_extractors.py`)

```bash
# Показать все доступные экстракторы
"venv/Scripts/python.exe" extract/link_files_extractors.py --list

# Основные экстракторы
"venv/Scripts/python.exe" extract/link_files_extractors.py files_list
"venv/Scripts/python.exe" extract/link_files_extractors.py converted_records_list
"venv/Scripts/python.exe" extract/link_files_extractors.py file_details --fileID 578924551
"venv/Scripts/python.exe" extract/link_files_extractors.py file_details --fileID 578924551 --name "filename.png"

# Файлы событий
"venv/Scripts/python.exe" extract/link_files_extractors.py event_session_files --eventsessionsID 2282834298
"venv/Scripts/python.exe" extract/link_files_extractors.py event_series_files --eventsID 2293097334
```

### 5. Тесты (`link_tests_extractors.py`)

```bash
# Показать все доступные экстракторы
"venv/Scripts/python.exe" extract/link_tests_extractors.py --list

# Основные экстракторы
"venv/Scripts/python.exe" extract/link_tests_extractors.py tests_list
"venv/Scripts/python.exe" extract/link_tests_extractors.py test_info --testId 1439438553
"venv/Scripts/python.exe" extract/link_tests_extractors.py test_info --testId 1439438553 --testSessionId 646357
"venv/Scripts/python.exe" extract/link_tests_extractors.py user_tests_stats --userId 74817491
"venv/Scripts/python.exe" extract/link_tests_extractors.py test_results --testId 1439438553
"venv/Scripts/python.exe" extract/link_tests_extractors.py test_custom_answers --testId 1439438553
```

### 6. Организация (`link_organisation_extractors.py`)

```bash
# Показать все доступные экстракторы
"venv/Scripts/python.exe" extract/link_organisation_extractors.py --list

# Основные экстракторы
"venv/Scripts/python.exe" extract/link_organisation_extractors.py timezones_list
"venv/Scripts/python.exe" extract/link_organisation_extractors.py brandings_list
"venv/Scripts/python.exe" extract/link_organisation_extractors.py organization_groups
"venv/Scripts/python.exe" extract/link_organisation_extractors.py partner_applications
```

## Общие команды

```bash
# Показать список всех экстракторов в модуле
"venv/Scripts/python.exe" extract/link_events_extractors.py --list

# Запустить все экстракторы без параметров
"venv/Scripts/python.exe" extract/link_events_extractors.py --all

# Интерактивный режим
"venv/Scripts/python.exe" extract/link_events_extractors.py
```

## Трансформация данных

```bash
# Анализ активности каналов
"venv/Scripts/python.exe" transform/active_channels.py
"venv/Scripts/python.exe" transform/active_channels.py --output active_channels_report.csv
```

## Использование как модуль

```python
from abstractions.extract import run_extractor, UniversalExtractor

# Запуск экстрактора по имени
result = run_extractor('organization_events_schedule')

# Создание универсального экстрактора
extractor = UniversalExtractor('/organization/events/schedule')
data = extractor.extract()
filename = extractor.save_to_file(data)
```

## Особенности

- **Ограничение сообщений**: API ограничивает выдачу сообщений до 100 за запрос. Используйте `fetch_all_messages.py` для получения всех сообщений
- **Обязательные параметры**: Экстрактор `events_stats` требует параметр `from`
- **Автосохранение**: Все данные автоматически сохраняются в JSON файлы с временными метками
- **Цветное логирование**: Используется для удобного отслеживания процесса извлечения