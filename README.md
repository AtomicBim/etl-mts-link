# MTS Link ETL

ETL-система для извлечения и анализа данных из API MTS Link: чаты, мероприятия, спонтанные звонки.

## 🚀 Быстрый старт

### Установка
```bash
pip install -r requirements.txt
```

### Настройка
Создайте `.env` файл:
```bash
API_TOKEN="your_api_token"
EXTRACTION_PATH="data/"  # опционально
```

---

## 📥 Полная выгрузка ВСЕХ данных

### Вариант 1: Максимально полная выгрузка (с архивами и участниками)

```bash
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

---

## 📊 Детальное использование

### Чаты
```bash
# Полная выгрузка
python transform/unique_chats.py
python transform/chat_analyzer.py

# Без архивов (быстрее)
python transform/chat_analyzer.py --no-archive

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
└── daily_activity_*.csv                # Дневная активность (чаты + звонки)
```

**Пайплайны:**
```
unique_chats.py → chat_analyzer.py → chat_analysis_*.csv + chats_archive/*.json
unique_events.py → event_analyzer.py → event_analysis_*.csv + events_archive/*.json
endless_activities.py → endless_activities_analyzer.py → endless_activities_analysis_*.csv + endless_activities_archive/*.json

Итоговая аналитика: chats_archive/*.json + endless_activities_*.csv → daily_activity_analyzer.py → daily_activity_*.csv
```

---

## 🛡️ Защита от сбоев

**Автоповторы (все скрипты):**
- До 5 попыток при сетевых ошибах
- Экспоненциальная задержка: 1s → 2s → 4s → 8s → 16s
- Timeout 30 секунд

**Checkpoints (unique_chats.py):**
- Автосохранение каждые 10 пользователей
- Продолжение с последнего checkpoint при перезапуске

---

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
