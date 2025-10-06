# Документация MTS Link ETL

## Обзор
Эта ETL-система предоставляет инструменты для извлечения, преобразования и загрузки данных из API MTS Link. Она позволяет работать с чатами, мероприятиями и данными организации, подготавливая их для дальнейшего анализа.

## Быстрый старт
1.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Настройте окружение:** Создайте файл `.env` в корне проекта или экспортируйте переменные окружения:
    ```bash
    # Токен для доступа к API MTS Link
    API_TOKEN="your_api_token"
    # (Опционально) Путь для сохранения результатов. По умолчанию: ./data
    EXTRACTION_PATH="data/"
    ```
3.  **Выполните основной сценарий:**
    ```bash
    # Шаг 1: Собрать уникальные чаты организации
    python transform/unique_chats.py

    # Шаг 2: Проанализировать чаты (собрать статистику и архивы сообщений)
    python transform/chat_analyzer.py

    # Шаг 3: (Опционально) Упростить архивы чатов для удобства чтения
    # Сначала нужно выгрузить пользователей, чтобы обогатить данные именами
    python extract/link_chats_extractors.py chats_organization_members > data/users.json
    # Затем запустить обработчик
    python transform/json_processor.py data/chats_archive --directory --users-json data/users.json
    ```

## Структура проекта
```
├── abstractions/          # Базовые классы экстракторов
├── extract/               # Скрипты для извлечения данных из API
├── transform/             # Скрипты для преобразования данных
├── data/                  # Директория для сохранения результатов
│   ├── unique_chats_*.csv
│   ├── chat_analysis_*.csv
│   └── chats_archive/
├── config/                # Файлы конфигурации
├── load/                  # Утилиты загрузки данных
├── .gitignore
├── README.md
└── requirements.txt
```

## Модули извлечения (Extract)
Скрипты в папке `extract/` предназначены для прямого вызова конечных точек API MTS Link.

**Общие параметры:**
- `--list`: Показать все доступные конечные точки в файле.
- `--output`: Указать имя выходного файла.

### 1. Экстракторы чатов (`extract/link_chats_extractors.py`)
- `chats_organization_members`: Список всех пользователей организации в чатах.
  ```bash
  python extract/link_chats_extractors.py chats_organization_members --perPage 100
  ```
- `user_channels`: Список каналов для конкретного пользователя.
  ```bash
  python extract/link_chats_extractors.py user_channels --userId "user-id"
  ```
- `channel_messages`: Сообщения из указанного чата.
  ```bash
  python extract/link_chats_extractors.py channel_messages --chatId "chat-id" --limit 200
  ```
- `channel_users`: Список участников канала.
  ```bash
  python extract/link_chats_extractors.py channel_users --channelId "channel-id" --limit 1000
  ```
- `channel_info`: Информация о канале.
  ```bash
  python extract/link_chats_extractors.py channel_info --channelId "channel-id"
  ```

### 2. Экстракторы мероприятий (`extract/link_events_extractors.py`)
- `organization_events_schedule`: Расписание мероприятий организации.
  ```bash
  python extract/link_events_extractors.py organization_events_schedule --from "2024-01-01+00:00:00"
  ```
- `user_events_schedule`: Расписание мероприятий пользователя.
  ```bash
  python extract/link_events_extractors.py user_events_schedule --userID "user-id" --from "2024-01-01+00:00:00"
  ```
- `event_session_details`: Детали конкретной сессии мероприятия.
  ```bash
  python extract/link_events_extractors.py event_session_details --eventsessionID "session-123"
  ```
- `transcript_list`: Список текстовых расшифровок для мероприятия.
  ```bash
  python extract/link_events_extractors.py transcript_list --eventSessionId "session-123"
  ```
- `transcript_summary`: Краткая сводка и полная расшифровка.
  ```bash
  python extract/link_events_extractors.py transcript_summary --transcriptId "transcript-123"
  ```

### 3. Экстракторы организации (`extract/link_organisation_extractors.py`)
- `brandings_list`: Информация о брендинге.
- `organization_groups`: Список групп пользователей.
- `partner_applications`: Данные об OAuth-интеграциях.
- `timezones_list`: Список часовых поясов.
  ```bash
  python extract/link_organisation_extractors.py organization_groups
  ```

## Модули преобразования (Transform)
Скрипты в папке `transform/` выполняют более сложные сценарии, объединяя несколько вызовов API и обрабатывая данные.

### 1. Сборщик уникальных чатов (`transform/unique_chats.py`)
Собирает информацию о чатах от всех пользователей организации, дедуплицирует её и сохраняет в CSV-файл.
- `--output`: Имя выходного файла.
- `--test`: Запустить в тестовом режиме на ограниченном числе пользователей.
- `--max-users`: Указать максимальное количество пользователей для обработки.
- `--help-fields`: Показать описание полей в итоговом CSV.
```bash
# Полная выгрузка
python transform/unique_chats.py

# Тестовый запуск для 5 пользователей
python transform/unique_chats.py --test --max-users 5
```

### 2. Анализатор чатов (`transform/chat_analyzer.py`)
Анализирует чаты из файла, созданного `unique_chats.py`. Для каждого чата собирает статистику (кол-во пользователей, сообщений) и сохраняет полный архив сообщений в JSON.
- `--input`: Указать входной CSV-файл (по умолчанию берется последний созданный).
- `--output`: Имя выходного файла для статистики.
- `--chat-id`: Проанализировать только один чат по его ID.
- `--chat-name`: Указать имя чата при анализе одного чата.
- `--max-messages`: Максимальное количество сообщений для выгрузки из одного чата.
- `--limit`: Ограничить количество чатов для анализа.
- `--no-archive`: Не сохранять полные архивы сообщений.
- `--format`: Формат вывода статистики (`csv` или `json`).
- `--test`: Запустить в тестовом режиме на 3 чатах.
```bash
# Анализ всех чатов из последнего файла unique_chats
python transform/chat_analyzer.py

# Анализ одного чата с выгрузкой до 5000 сообщений
python transform/chat_analyzer.py --chat-id "chat-id" --max-messages 5000
```

### 3. Обработчик архивов чатов (`transform/json_processor.py`)
Упрощает JSON-архивы сообщений, созданные `chat_analyzer.py`. Оставляет только ключевые поля, заменяет ID авторов на полные имена и сохраняет результат в JSON и CSV.
- `input_path`: Путь к файлу или папке для обработки.
- `--directory`: Указывает, что `input_path` — это папка.
- `--pattern`: Шаблон для поиска файлов в папке (например, `"chat_*.json"`).
- `--users-json`: Путь к `users.json` файлу для обогащения данных именами пользователей.
- `--output-filename`: Имя выходного файла (для одиночного файла).
- `--output-dir`: Папка для сохранения результатов (для пакетной обработки).
- `--csv-only`: Сохранить результат только в формате CSV.
```bash
# Обработка одного файла с добавлением имен
python transform/json_processor.py data/chats_archive/chat_..._simplified.json --users-json data/users.json

# Пакетная обработка всех архивов в папке
python transform/json_processor.py data/chats_archive --directory --users-json data/users.json
```

### 4. Обработчик данных о сотрудниках (`transform/organization_members.py`)
Собирает, обрабатывает и сохраняет данные о сотрудниках организации, включая их активность, роли и контактную информацию.
- `--output`: Имя выходного файла.
- `--format`: Формат вывода (`csv` или `json`).
- `--mode`: Режим выгрузки (`full` или `active`). `full` выгружает всех, `active` — только активных.
- `--fields`: Список полей для включения в отчет (например, `fullName,email,status`).
- `--add-org-groups`: Включить информацию о группах, в которых состоит пользователь.
```bash
# Выгрузить всех активных пользователей в CSV
python transform/organization_members.py --mode active

# Выгрузить всех пользователей с указанными полями и группами в JSON
python transform/organization_members.py --mode full --fields "fullName,email,role" --add-org-groups --format json
```

## Рекомендуемый рабочий процесс
1.  **Сбор данных о сотрудниках.** Полезно для дальнейшего обогащения данных.
    ```bash
    python transform/organization_members.py --output members.csv
    ```
2.  **Поиск уникальных чатов.** Основа для дальнейшего анализа.
    ```bash
    python transform/unique_chats.py
    ```
3.  **Анализ чатов.** Сбор статистики и архивов. Используйте последний созданный файл `unique_chats_*.csv`.
    ```bash
    # Быстрый анализ без сохранения архивов
    python transform/chat_analyzer.py --no-archive

    # Полный анализ с выгрузкой до 10000 сообщений на чат
    python transform/chat_analyzer.py --max-messages 10000
    ```
4.  **Упрощение архивов.** (Опционально) Делает архивы легче и удобнее для ручного просмотра.
    ```bash
    # Сначала получаем актуальный список пользователей
    python extract/link_chats_extractors.py chats_organization_members > data/users.json
    # Затем обрабатываем все архивы
    python transform/json_processor.py data/chats_archive --directory --users-json data/users.json
    ```

## Зависимости
Для работы скриптов необходим Python 3.7+ и зависимости, перечисленные в `requirements.txt`.
```bash
pip install -r requirements.txt
```
Основные зависимости: `requests`, `python-dotenv`.
