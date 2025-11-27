# MTS Link ETL

ETL-система для извлечения и анализа данных из API MTS Link: чаты, мероприятия, спонтанные звонки.

## 🆕 Модули анализа

### 1. Анализ активных пользователей по дням

**Модуль:** `transform/daily_active_users.py`

Показывает сколько пользователей написали хотя бы 1 сообщение в каждый день.

```bash
# За сегодня
python transform/daily_active_users.py

# За последние 4 дня
python transform/daily_active_users.py --days-back 4

# За месяц с детальным отчетом по каждому пользователю
python transform/daily_active_users.py --days-back 30 --detailed
```

**Выходные файлы:**
- `daily_active_users_*.csv` - статистика по дням (дата, активные пользователи, сообщения)
- `daily_active_users_detailed_*.csv` - статистика по каждому пользователю (детальный режим)

**Пример результата:**
```csv
date,day_of_week,unique_active_users,total_messages,avg_messages_per_user
2025-11-17,Monday,63,388,6.16
2025-11-18,Tuesday,62,218,3.52
2025-11-19,Wednesday,53,298,5.62
2025-11-20,Thursday,32,102,3.19
```

### 2. Сводка сообщений за период

**Модуль:** `transform/daily_messages_summary.py`

Создает сводку по сообщениям из всех чатов за указанный период.

```bash
# За сегодня
python transform/daily_messages_summary.py

# За последние 3 дня
python transform/daily_messages_summary.py --days-back 3
```

**Выходной файл:** `messages_summary_*.json`

**Структура:**
```json
{
  "chat_name": "ИКП Внешний заказ",
  "chat_id": "...",
  "date_range": {"start": "2025-11-17", "end": "2025-11-20"},
  "messages_count": 61,
  "messages": [
    {
      "author": "Полина Сергеева",
      "time": "2025-11-20 10:44:32",
      "text": "Текст сообщения"
    }
  ]
}
```

### 3. Фильтрация по дате в chat_analyzer

**Обновлен:** `transform/chat_analyzer.py`

Теперь поддерживает аргумент `--days-back` для анализа только последних N дней:

```bash
# Анализировать чаты, но учитывать только сообщения за последние 7 дней
python transform/chat_analyzer.py --days-back 7

# Полезно для получения актуальной статистики без старых данных
python transform/chat_analyzer.py --limit 20 --days-back 30
```

---

## 📥 Полная выгрузка ВСЕХ данных

### Вариант 1: Максимально полная выгрузка (с архивами и участниками)

```bash
# 0. Маппинг организаций (первый раз или при добавлении новых организаций)
python utils/build_organizations_mapping.py

# 1. Справочник сотрудников (для имен пользователей)
python transform/organization_members.py

# 2. Чаты с полным анализом и архивами сообщений
python transform/unique_chats.py
python transform/chat_analyzer.py

# 3. Запланированные мероприятия за 90 дней
python transform/unique_events.py --last-days 90 --method organization --max-pages 100
python transform/event_analyzer.py

# 4. Спонтанные звонки (p2p) за 90 дней с полными данными
python transform/endless_activities.py --last-days 90
python transform/endless_activities_analyzer.py

# 5. Дневная активность (объединяет чаты + звонки)
python transform/daily_activity_analyzer.py
```

**Что получите:**
- ✅ Полные архивы чатов (`chats_archive/*.json`)
- ✅ Полные архивы мероприятий (`events_archive/*.json`)
- ✅ Полные архивы звонков с участниками (`endless_activities_archive/*.json`)
- ✅ CSV аналитика по всем данным
- ✅ Дневная активность со всеми метриками

---

### Вариант 2: Быстрая выгрузка (без архивов)

```bash
python transform/organization_members.py
python transform/unique_chats.py
python transform/chat_analyzer.py --no-archive
python transform/unique_events.py --last-days 30 --method organization --max-pages 100
python transform/endless_activities.py --last-days 30
python transform/event_analyzer.py --no-archive --no-detailed-info
python transform/endless_activities_analyzer.py --no-detailed-info --no-archive
python transform/daily_activity_analyzer.py
```

**Отличия:**
- ⚡ Быстрее (нет архивов JSON)
- ⚠️ Меньше данных об участниках созвонов
- ✅ Базовая аналитика сохраняется

---

## 🔧 Основные скрипты

| Скрипт | Назначение | Выход |
|--------|-----------|-------|
| `organization_members.py` | Справочник сотрудников | `organization_members_*.csv` |
| `unique_chats.py` | Сбор всех чатов | `unique_chats_*.csv` |
| `chat_analyzer.py` | Анализ чатов + архивы | `chat_analysis_*.csv`, `chats_archive/*.json` |
| `unique_events.py` | Запланированные мероприятия | `unique_events_*.csv` |
| `event_analyzer.py` | Анализ мероприятий + архивы | `event_analysis_*.csv`, `events_archive/*.json` |
| `endless_activities.py` | Спонтанные звонки (p2p) | `endless_activities_*.csv` |
| `endless_activities_analyzer.py` | Анализ звонков + архивы | `endless_activities_analysis_*.csv`, `endless_activities_archive/*.json` |
| `daily_activity_analyzer.py` | Дневная активность | `daily_activity_*.csv` |
| **`daily_active_users.py`** 🆕 | **Активные пользователи по дням** | `daily_active_users_*.csv` |
| **`daily_messages_summary.py`** 🆕 | **Сводка сообщений за период** | `messages_summary_*.json` |

---

## 📊 Детальное использование

### Чаты
```bash
# Полная выгрузка
python transform/unique_chats.py
python transform/chat_analyzer.py

# Без архивов (быстрее)
python transform/chat_analyzer.py --no-archive

# 🆕 Анализ только за последние 7 дней
python transform/chat_analyzer.py --days-back 7

# Тест на 5 пользователях
python transform/unique_chats.py --test --max-users 5

# Один чат
python transform/chat_analyzer.py --chat-id "CHAT_ID"

# Описание полей
python transform/unique_chats.py --help-fields
```

---

### Мероприятия (запланированные)
```bash
# Рекомендуемый способ
python transform/unique_events.py --last-days 30 --method organization --max-pages 100
python transform/event_analyzer.py

# Быстрый анализ без архивов
python transform/event_analyzer.py --no-archive --no-detailed-info

# За конкретный период
python transform/unique_events.py --from-date "2024-01-01" --to-date "2024-12-31" --max-pages 100

# Описание полей
python transform/unique_events.py --help-fields
```

**Параметры:**
- `--last-days N` - события за последние N дней
- `--method organization` - быстрая выгрузка по организации (рекомендуется)
- `--max-pages N` - лимит страниц пагинации (100+ для полной выгрузки)

---

### Звонки (спонтанные p2p)
```bash
# Полная выгрузка с участниками и архивами
python transform/endless_activities.py --last-days 90
python transform/endless_activities_analyzer.py

# Быстрая выгрузка (без участников)
python transform/endless_activities_analyzer.py --no-detailed-info --no-archive

# За конкретный период
python transform/endless_activities.py --from-date "2024-01-01" --to-date "2024-12-31"

# Описание полей
python transform/endless_activities.py --help-fields
```

**Что собирает:**
- Activity ID, User ID, User Name
- Время начала/конца, длительность
- Название комнаты, количество участников
- Endless Event ID (постоянная комната)

**⚠️ Важно:**
- БЕЗ `--no-detailed-info` → загружает полные данные об участниках
- С `--no-detailed-info` → быстрее, но без деталей участников

---

### Дневная активность
```bash
# Полный анализ
python transform/daily_activity_analyzer.py

# С указанием выходного файла
python transform/daily_activity_analyzer.py -o my_report.csv

# Описание полей
python transform/daily_activity_analyzer.py --help-fields
```

**Анализирует:**
- Сообщения в чатах (из `chats_archive/*.json`)
- Созвоны (из `endless_activities_*.csv` или `endless_activities_analysis_*.csv`)

**Выходные метрики по дням:**
- Количество сообщений, средняя длина
- Уникальные отправители, активные чаты
- Количество созвонов, средняя/общая длительность
- Уникальные пользователи в звонках
- Уникальные комнаты/встречи

> **📝 Примечание:** `total_call_participants` будет заполнен только если `endless_activities_analysis_*.csv` был создан **БЕЗ** флага `--no-detailed-info`

---

### Сотрудники
```bash
# Активные пользователи
python transform/organization_members.py --mode active

# Полная выгрузка с группами
python transform/organization_members.py --mode full --add-org-groups
```

---

## 📁 Структура проекта

```
etl-mts-link/
├── abstractions/          # Базовые классы (UniversalExtractor)
├── extract/              # Низкоуровневые вызовы API
├── transform/            # Основные ETL скрипты
├── utils/                # 🆕 Вспомогательные утилиты
├── examples/             # Примеры использования модулей
├── data/                 # Выходные данные (создается автоматически)
├── config/               # Конфигурация (tokens.json)
├── .env                  # API токен и настройки
├── requirements.txt      # Зависимости Python
└── README.md            # Эта документация
```

## 📁 Структура выходных данных

```
data/
├── organization_members_*.csv          # Справочник сотрудников
│
├── unique_chats_*.csv                  # Список чатов
├── chat_analysis_*.csv                 # Аналитика по чатам
├── chats_with_messages_*.csv           # Чаты с количеством сообщений
├── chats_archive/*.json                # Полные архивы сообщений
│
├── unique_events_*.csv                 # Список мероприятий
├── event_analysis_*.csv                # Аналитика по мероприятиям
├── events_archive/*.json               # Полные архивы мероприятий
│
├── endless_activities_*.csv            # Список звонков
├── endless_activities_analysis_*.csv   # Аналитика по звонкам
├── endless_activities_archive/*.json   # Полные архивы звонков
│
├── daily_activity_*.csv                # Дневная активность (чаты + звонки)
│
├── daily_active_users_*.csv            # 🆕 Активные пользователи по дням
├── daily_active_users_detailed_*.csv   # 🆕 Детальная статистика по пользователям
└── messages_summary_*.json             # 🆕 Сводка сообщений за период
```

**Пайплайны:**
```
unique_chats.py → chat_analyzer.py → chat_analysis_*.csv + chats_archive/*.json
unique_events.py → event_analyzer.py → event_analysis_*.csv + events_archive/*.json
endless_activities.py → endless_activities_analyzer.py → endless_activities_analysis_*.csv + endless_activities_archive/*.json

Итоговая аналитика: chats_archive/*.json + endless_activities_*.csv → daily_activity_analyzer.py → daily_activity_*.csv
```

## 💡 Полезные команды

**Тестовые режимы:**
```bash
python transform/unique_chats.py --test --max-users 5
python transform/chat_analyzer.py --test
python transform/event_analyzer.py --test
python transform/endless_activities_analyzer.py --test
```

**Описание полей:**
```bash
python transform/unique_chats.py --help-fields
python transform/unique_events.py --help-fields
python transform/endless_activities.py --help-fields
python transform/daily_activity_analyzer.py --help-fields
```

---

## 🔍 Важные отличия

### Два типа мероприятий

| Критерий | Запланированные | Спонтанные (p2p) |
|----------|----------------|------------------|
| **Скрипт сбора** | `unique_events.py` | `endless_activities.py` |
| **Скрипт анализа** | `event_analyzer.py` | `endless_activities_analyzer.py` |
| **Что собирает** | Вебинары, конференции | P2P звонки, быстрые встречи |
| **Имена пользователей** | Из `organization_members.csv` | Уже в CSV (из API) |

---

### Полная vs Быстрая выгрузка

| Параметр | Полная выгрузка | Быстрая выгрузка |
|----------|----------------|------------------|
| `--no-archive` | НЕ используется | Используется |
| `--no-detailed-info` | НЕ используется | Используется |
| **Архивы JSON** | ✅ Сохраняются | ❌ Не сохраняются |
| **Участники созвонов** | ✅ Полные данные | ⚠️ Базовые данные |
| **Скорость** | Медленнее | Быстрее |
| **Размер данных** | Большой | Маленький |

---

## 🛠️ Утилиты (utils/)

Вспомогательные скрипты для обслуживания системы.

### 1. Маппинг организаций
```bash
# Создать маппинг ID организаций → названия
python utils/build_organizations_mapping.py

# Создает: data/organizations_mapping.json
# Используется: chat_analyzer.py, daily_active_users.py
```

**Когда запускать:**
- После первой установки
- При добавлении новых организаций
- Если скрипты показывают organization_id вместо названий

### 2. Очистка старых файлов
```bash
# Удалить старые simplified CSV из chats_archive
python utils/cleanup_old_simplified.py

# Оставляет только файлы с последней датой
# Освобождает место на диске
```

**Когда запускать:**
- После повторного запуска chat_analyzer.py
- Для освобождения места

### 3. Извлечение одного канала
```bash
# Извлечь сообщения из одного чата
python utils/extract_single_channel.py \
  --channel-id "CHANNEL_ID" \
  --channel-name "Название"

# С организацией
python utils/extract_single_channel.py \
  --channel-id "CHANNEL_ID" \
  --organization-id "ORG_ID"

# Для приватного канала
python utils/extract_single_channel.py \
  --channel-id "CHANNEL_ID" \
  --viewer-id "USER_ID"
```

**Когда использовать:**
- Тестирование доступа к каналу
- Быстрое извлечение одного чата
- Отладка проблем с конкретным каналом

**Подробнее:** `utils/README.md`

---

## 🌐 Прямой доступ к API (extract/)

Низкоуровневые вызовы API без обработки:

```bash
# Чаты
python extract/link_chats_extractors.py chats_organization_members
python extract/link_chats_extractors.py chats_teams
python extract/link_chats_extractors.py channel_messages --chatId "ID" --limit 200
python extract/link_chats_extractors.py --list

# Мероприятия
python extract/link_events_extractors.py organization_events_schedule --from "2024-01-01+00:00:00"
python extract/link_events_extractors.py event_session_participations --eventSessionId "ID"
python extract/link_events_extractors.py endless_events_activities --from "2024-01-01+00:00:00"
python extract/link_events_extractors.py --list

# Организация
python extract/link_organisation_extractors.py organization_groups
python extract/link_organisation_extractors.py --list