# MTS Link ETL (Extract, Transform, Load)

Система для извлечения данных из MTS Link API - корпоративной платформы для проведения видеоконференций, вебинаров и управления обучением.

## Описание проекта

Этот проект представляет собой ETL-систему для работы с API MTS Link, позволяющую извлекать данные о:
- Мероприятиях и встречах
- Чатах и курсах
- Файлах и записях
- Пользователях и контактах
- Тестах и голосованиях
- Настройках организации

## Структура проекта

```
etl-mts-link/
├── abstractions/
│   └── extract.py          # Базовые классы для извлечения данных
├── config/
│   └── tokens.json         # Конфигурация API токенов
├── extract/                # Модули для извлечения данных
│   ├── link_addressbook_extractors.py
│   ├── link_chats_extractors.py
│   ├── link_events_extractors.py
│   ├── link_files_extractors.py
│   ├── link_organisation_extractors.py
│   └── link_tests_extractors.py
├── load/                   # Модули для загрузки данных
├── transform/              # Модули для трансформации данных
└── requirements.txt        # Зависимости проекта
```

## Установка и настройка

1. **Клонировать репозиторий:**
   ```bash
   git clone <repository-url>
   cd etl-mts-link
   ```

2. **Установить зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Настроить конфигурацию:**
   Отредактируйте файл `config/tokens.json`, указав свой API токен:
   ```json
   {
     "api_token": "your-mts-link-api-token",
     "base_url": "https://userapi.mts-link.ru/v3"
   }
   ```

## Использование

### Запуск extractors

Каждый модуль в папке `extract/` можно запускать независимо:

```bash
# Показать список доступных extractors
python extract/link_events_extractors.py --list

# Запустить конкретный extractor
python extract/link_events_extractors.py organization_events_schedule

# Запустить все extractors (без параметров)
python extract/link_events_extractors.py --all

# Запустить с параметрами
python extract/link_events_extractors.py event_session_details --eventsessionID 123456
```

### Общие параметры

- `--list` / `-l`: Показать список доступных extractors
- `--all` / `-a`: Запустить все extractors (исключая параметризованные)
- `--help`: Показать справку по использованию

## API Endpoints

### 1. Addressbook & Users (`link_addressbook_extractors.py`)

Работа с адресной книгой и пользователями:

| Extractor | Endpoint | Описание | Параметры |
|-----------|----------|----------|-----------|
| `contact_details` | `/contacts/{contactsID}` | Детальная информация о контакте | `--contactsID` |
| `contacts_search` | `/contacts/search` | Поиск по контактам | `--query` |
| `organization_members` | `/organization/members` | Список сотрудников организации | - |
| `user_profile` | `/profile` | Профиль текущего пользователя | - |

**Примеры использования:**
```bash
python extract/link_addressbook_extractors.py contact_details --contactsID 1341627
python extract/link_addressbook_extractors.py contacts_search --query "Иванов"
python extract/link_addressbook_extractors.py organization_members
```

### 2. Chats & Courses (`link_chats_extractors.py`)

Работа с чатами и курсами:

| Extractor | Endpoint | Описание | Параметры |
|-----------|----------|----------|-----------|
| `chats_organization_members` | `/chats/organization/members` | Пользователи организации в чатах | - |
| `user_channels` | `/chats/channels/{userId}` | Каналы пользователя | `--userId` |
| `channel_messages` | `/chats/channel/{chatId}/messages` | История сообщений канала | `--chatId` |
| `channel_info` | `/chats/channel/{channelId}` | Информация о канале | `--channelId` |
| `organization_courses` | `/organization/courses` | Курсы организации | - |
| `course_details` | `/courses/{Courseid}` | Детали курса | `--Courseid` |
| `courses_groups` | `/organization/courses/groups` | Учебные группы | - |
| `course_group_statistics` | `/courses/{courseID}/groups/{groupID}/statistics` | Статистика группы | `--courseID --groupID` |
| `course_group_info` | `/courses/{courseID}/groups/{groupID}` | Информация о группе | `--courseID --groupID` |
| `user_course_statistics` | `/organization/users/{userID}/statistics` | Статистика курсов пользователя | `--userID` |

**Примеры использования:**
```bash
python extract/link_chats_extractors.py user_channels --userId 74817491
python extract/link_chats_extractors.py channel_messages --chatId "1f04c259-5854-6e4c-bba2-ca9a267b707c"
python extract/link_chats_extractors.py course_details --Courseid 123
```

### 3. Events (`link_events_extractors.py`)

Работа с мероприятиями и встречами:

| Extractor | Endpoint | Описание | Параметры |
|-----------|----------|----------|-----------|
| `organization_events_schedule` | `/organization/events/schedule` | Расписание мероприятий организации | - |
| `event_session_details` | `/eventsessions/{eventsessionID}` | Детали конкретного мероприятия | `--eventsessionID` |
| `user_events_schedule` | `/users/{userID}/events/schedule` | Мероприятия пользователя | `--userID` |
| `event_series_data` | `/organization/events/{eventID}` | Данные серии мероприятий | `--eventID` |
| `endless_meetings_list` | `/eventsessions/endless` | Постоянные встречи | - |
| `endless_meetings_activities` | `/eventsessions/endless/activities` | Активности постоянных встреч | - |
| `event_session_notes` | `/eventsessions/{eventSessionId}/agendas` | Заметки мероприятия | `--eventSessionId` |
| `transcript_list` | `/eventsessions/{eventSessionId}/transcript/list` | Список расшифровок | `--eventSessionId` |
| `event_participants` | `/eventsessions/{eventsessionID}/participations` | Участники мероприятия | `--eventsessionID` |
| `event_series_stats` | `/events/{eventID}/participations` | Статистика серии мероприятий | `--eventID` |
| `users_stats` | `/stats/users` | Статистика пользователей | - |
| `visits_stats` | `/stats/users/visits/{userID}` | Статистика посещений | `--userID` |
| `online_records_list` | `/records` | Список записей | - |
| `converted_records` | `/eventsessions/{eventSessionId}/converted-records` | MP4-записи мероприятия | `--eventSessionId` |
| `event_chat_messages` | `/eventsessions/{eventsessionID}/chat` | Сообщения чата мероприятия | `--eventsessionID` |
| `event_questions` | `/eventsessions/{eventsessionID}/questions` | Вопросы мероприятия | `--eventsessionID` |
| `attention_checkpoints` | `/eventsessions/{eventSessionId}/attention-control/checkpoints` | Точки контроля внимания | `--eventSessionId` |
| `stream_files_urls` | `/organization/eventsessions/streamFilesUrls` | URL видеопотоков | - |

**Примеры использования:**
```bash
python extract/link_events_extractors.py event_session_details --eventsessionID 2282834298
python extract/link_events_extractors.py user_events_schedule --userID 74817491
python extract/link_events_extractors.py event_participants --eventsessionID 2282834298
```

### 4. Files & Records (`link_files_extractors.py`)

Работа с файлами и записями:

| Extractor | Endpoint | Описание | Параметры |
|-----------|----------|----------|-----------|
| `file_details` | `/fileSystem/file/{fileID}` | Информация о файле | `--fileID` |
| `files_list` | `/fileSystem/files` | Список файлов | - |
| `event_session_files` | `/eventsessions/{eventsessionsID}/files` | Файлы мероприятия | `--eventsessionsID` |
| `event_series_files` | `/events/{eventsID}/files` | Файлы серии мероприятий | `--eventsID` |
| `converted_records_list` | `/fileSystem/files/converted-record` | Список MP4-записей | - |
| `download_converted_record` | `/fileSystem/file/{conversionId}` | Скачать MP4-запись | `--conversionId` |

**Примеры использования:**
```bash
python extract/link_files_extractors.py file_details --fileID 123
python extract/link_files_extractors.py event_session_files --eventsessionsID 2282834298
```

### 5. Organisation & Settings (`link_organisation_extractors.py`)

Работа с настройками организации:

| Extractor | Endpoint | Описание | Параметры |
|-----------|----------|----------|-----------|
| `brandings_list` | `/brandings` | Темы оформления | - |
| `organization_groups` | `/organization-groups` | Группы пользователей | - |
| `partner_applications` | `/partner-applications` | OAuth интеграции | - |
| `timezones_list` | `/timezones` | Часовые пояса | - |

**Примеры использования:**
```bash
python extract/link_organisation_extractors.py brandings_list
python extract/link_organisation_extractors.py organization_groups
```

### 6. Tests & Voting (`link_tests_extractors.py`)

Работа с тестами и голосованиями:

| Extractor | Endpoint | Описание | Параметры |
|-----------|----------|----------|-----------|
| `test_info` | `/tests/{testId}` | Информация о тесте | `--testId` |
| `test_results` | `/tests/{testId}/results` | Результаты теста | `--testId` |
| `user_tests_stats` | `/users/{userId}/tests/stats` | Статистика тестов пользователя | `--userId` |
| `test_custom_answers` | `/tests/{testId}/customanswers` | Текстовые ответы теста | `--testId` |
| `tests_list` | `/tests/list` | Список тестов | - |

**Примеры использования:**
```bash
python extract/link_tests_extractors.py test_info --testId 123
python extract/link_tests_extractors.py user_tests_stats --userId 74817491
```

## Архитектура

### BaseExtractor

Базовый класс для всех extractors, предоставляющий:
- Загрузку конфигурации из `config/tokens.json`
- Формирование HTTP-заголовков с авторизацией
- Выполнение HTTP-запросов к MTS Link API
- Обработку ошибок и логирование
- Сохранение данных в JSON файлы

### Decorator @endpoint

Декоратор для регистрации endpoint'ов, позволяющий:
- Автоматическую регистрацию endpoint'ов
- Динамический запуск extractors по имени
- Поддержку параметризованных URL

### Особенности реализации

- **SSL Отключение**: Проект отключает проверку SSL сертификатов для работы с корпоративной сетью
- **Параметризация**: Поддержка path-параметров в URL (например, `{userID}`, `{eventID}`)
- **Автосохранение**: Данные автоматически сохраняются в JSON файлы с timestamp
- **Интерактивный режим**: Возможность запуска в интерактивном режиме для выбора extractors

## Выходные данные

Все данные сохраняются в JSON файлы с именованием:
```
{endpoint_name}_{timestamp}.json
```

Например: `organization_events_schedule_20231220_143022.json`

## Безопасность

⚠️ **Важно**: Файл `config/tokens.json` содержит API токен и не должен коммититься в репозиторий. Добавьте его в `.gitignore`.

## Требования

- Python 3.7+
- requests>=2.31.0
- python-dotenv>=1.0.0
- pip-tools>=7.3.0

## Лицензия

Проект предназначен для внутреннего использования с MTS Link API.