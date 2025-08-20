# ETL MTS-Link

Comprehensive ETL system for extracting data from MTS Link API using decorator pattern for endpoint definitions. Supports multiple categories of data extraction including Events, Chats, Courses, Files, Tests, Organization settings, and User management.

## Quick Start

### 1. Installation

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configuration

Create `config/tokens.json`:
```json
{
  "api_token": "your_mts_link_token_here",
  "base_url": "https://userapi.mts-link.ru/v3"
}
```

Set extraction path in `.env`:
```env
EXTRACTION_PATH=C:/Users/YourUser/YourFolder
```

### 3. Usage Examples

```bash
# List available extractors
python extract/link_events_extractors.py --list

# Run single extractor
python extract/link_events_extractors.py organization_events_schedule

# Run with parameters
python extract/link_events_extractors.py event_session_details --eventsessionID 2282834298

# Run all non-parameterized extractors
python extract/link_events_extractors.py --all
```

## Available Extractors

### 1. Events & Meetings (`link_events_extractors.py`)

**Non-parameterized endpoints:**
| Extractor | Endpoint | Description |
|-----------|----------|-------------|
| `organization_events_schedule` | `/organization/events/schedule` | All organization events information |
| `endless_meetings_list` | `/eventsessions/endless` | List of permanent meetings |
| `endless_meetings_activities` | `/eventsessions/endless/activities` | Activities in permanent meetings |
| `users_stats` | `/stats/users` | User activity statistics |
| `online_records_list` | `/records` | List of online event records |
| `stream_files_urls` | `/organization/eventsessions/streamFilesUrls` | Speaker video stream URLs |

**Parameterized endpoints:**
| Extractor | Endpoint | Parameters | Description |
|-----------|----------|------------|-------------|
| `event_session_details` | `/eventsessions/{eventsessionID}` | `--eventsessionID` | Detailed event information |
| `user_events_schedule` | `/users/{userID}/events/schedule` | `--userID` | User's event schedule |
| `event_series_data` | `/organization/events/{eventID}` | `--eventID` | Event series data |
| `event_participants` | `/eventsessions/{eventsessionID}/participations` | `--eventsessionID` | Event participants list |
| `event_series_stats` | `/events/{eventID}/participations` | `--eventID` | Event series statistics |
| `visits_stats` | `/stats/users/visits/{userID}` | `--userID` | User visits statistics |
| `conversion_status` | `/records/conversions/{conversionID}` | `--conversionID` | Record conversion status |
| `converted_records` | `/eventsessions/{eventSessionId}/converted-records` | `--eventSessionId` | Converted records info |
| `event_session_notes` | `/eventsessions/{eventSessionId}/agendas` | `--eventSessionId` | Event notes and summaries |
| `transcript_list` | `/eventsessions/{eventSessionId}/transcript/list` | `--eventSessionId` | Available transcripts |
| `transcript_summary` | `/transcript/{transcriptId}` | `--transcriptId` | Transcript summary |
| `event_chat_messages` | `/eventsessions/{eventsessionID}/chat` | `--eventsessionID` | Event chat history |
| `event_questions` | `/eventsessions/{eventsessionID}/questions` | `--eventsessionID` | Participant questions |
| `attention_checkpoints` | `/eventsessions/{eventSessionId}/attention-control/checkpoints` | `--eventSessionId` | Attention control points |
| `attention_interactions` | `/eventsessions/{eventSessionId}/attention-control/interactions` | `--eventSessionId` | Attention control interactions |
| `raising_hands` | `/eventsessions/{eventSessionId}/raising-hands` | `--eventSessionId` | Hand raising events |
| `event_likes` | `/eventsessions/{eventSessionId}/likes` | `--eventSessionId` | Event likes/reactions |
| `emoji_reactions` | `/eventsessions/{eventSessionId}/emoji-reactions` | `--eventSessionId` | Emoji reactions |

### 2. Chats & Courses (`link_chats_extractors.py`)

**Working endpoints:**
| Extractor | Endpoint | Parameters | Description |
|-----------|----------|------------|-------------|
| `chats_teams` | `/chats/teams` | - | List of all teams (group chats) |
| `chats_organization_members` | `/chats/organization/members` | - | Chat users in organization |
| `organization_courses` | `/organization/courses` | - | All organization courses |
| `courses_groups` | `/organization/courses/groups` | - | All course groups |
| `course_details` | `/courses/{Courseid}` | `--Courseid` | Detailed course information |
| `course_group_statistics` | `/courses/{courseID}/groups/{groupID}/statistics` | `--courseID --groupID` | Course group statistics |
| `contact_user_info` | `/contacts/{contactID}/user` | `--contactID` | Student info by contact ID |
| `course_group_info` | `/courses/{courseID}/groups/{groupID}` | `--courseID --groupID` | Course group details |
| `user_course_statistics` | `/organization/users/{userID}/statistics` | `--userID` | User course statistics |

### 3. Address Book & Users (`link_addressbook_extractors.py`)

| Extractor | Endpoint | Parameters | Description |
|-----------|----------|------------|-------------|
| `contacts_search` | `/contacts/search` | `--query` (optional) | Search contacts |
| `organization_members` | `/organization/members` | - | All organization employees |
| `contact_details` | `/contacts/{contactsID}` | `--contactsID` | Detailed contact information |
| `user_profile` | `/profile` | - | Current user profile (OAuth) |

### 4. Files & Records (`link_files_extractors.py`)

| Extractor | Endpoint | Parameters | Description |
|-----------|----------|------------|-------------|
| `files_list` | `/fileSystem/files` | - | All files from file manager |
| `converted_records_list` | `/fileSystem/files/converted-record` | - | All ready MP4 records |
| `file_details` | `/fileSystem/file/{fileID}` | `--fileID` | File information by ID |
| `event_session_files` | `/eventsessions/{eventsessionsID}/files` | `--eventsessionsID` | Files attached to event session |
| `event_series_files` | `/events/{eventsID}/files` | `--eventsID` | Files attached to event series |
| `download_converted_record` | `/fileSystem/file/{conversionId}` | `--conversionId` | Download MP4 record |

### 5. Tests & Voting (`link_tests_extractors.py`)

| Extractor | Endpoint | Parameters | Description |
|-----------|----------|------------|-------------|
| `tests_list` | `/tests/list` | - | List of tests with launch times |
| `test_info` | `/tests/{testId}` | `--testId` | Detailed test information |
| `test_results` | `/tests/{testId}/results` | `--testId` | Test results from all participants |
| `user_tests_stats` | `/users/{userId}/tests/stats` | `--userId` | User's test results |
| `test_custom_answers` | `/tests/{testId}/customanswers` | `--testId` | Text answers to open questions |

### 6. Organization & Settings (`link_organisation_extractors.py`)

| Extractor | Endpoint | Parameters | Description |
|-----------|----------|------------|-------------|
| `brandings_list` | `/brandings` | - | Available branding themes |
| `organization_groups` | `/organization-groups` | - | Organization user groups |
| `partner_applications` | `/partner-applications` | - | OAuth integrations |
| `timezones_list` | `/timezones` | - | Supported timezones |

## Usage Examples

### Basic Usage
```bash
# Events
python extract/link_events_extractors.py organization_events_schedule
python extract/link_events_extractors.py event_session_details --eventsessionID 2282834298

# Chats & Courses
python extract/link_chats_extractors.py chats_teams
python extract/link_chats_extractors.py user_course_statistics --userID 74817491

# Files
python extract/link_files_extractors.py files_list
python extract/link_files_extractors.py event_session_files --eventsessionsID 2282834298

# Tests
python extract/link_tests_extractors.py tests_list
python extract/link_tests_extractors.py user_tests_stats --userId 74817491

# Organization
python extract/link_organisation_extractors.py timezones_list
```

### Batch Operations
```bash
# Run all non-parameterized extractors in each category
python extract/link_events_extractors.py --all
python extract/link_chats_extractors.py --all
python extract/link_files_extractors.py --all
python extract/link_tests_extractors.py --all
python extract/link_organisation_extractors.py --all
```

### Interactive Mode
```bash
python extract/link_events_extractors.py
> organization_events_schedule
> quit
```

## Output Format

Data is saved to JSON files in the configured `EXTRACTION_PATH`:
- Format: `_{endpoint_name}_{timestamp}.json`
- Example: `_organization_events_schedule_20250820_123456.json`

## Architecture

### Project Structure
```
etl-mts-link/
├── abstractions/
│   └── extract.py              # Base extractor class and decorator
├── config/
│   └── tokens.json             # API configuration
├── extract/
│   ├── link_events_extractors.py      # Events & meetings
│   ├── link_chats_extractors.py       # Chats & courses
│   ├── link_addressbook_extractors.py # Contacts & users
│   ├── link_files_extractors.py       # Files & records
│   ├── link_tests_extractors.py       # Tests & voting
│   └── link_organisation_extractors.py # Organization settings
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── README.md                   # This documentation
```

### Adding New Extractors

1. Choose appropriate extractor file or create new one
2. Add function with `@endpoint` decorator:

```python
@endpoint("/new/api/endpoint")
def new_extractor():
    """Description of new extractor"""
    pass
```

3. For parameterized endpoints:
```python
@endpoint("/new/api/{paramName}")
def parameterized_extractor():
    """Description with parameter"""
    pass
```

4. Add parameter handling in `main()` function if needed

### Features

- **Decorator-based endpoint registration** - Simple `@endpoint` decorator
- **Automatic parameter injection** - URL parameters from command line
- **Error handling** - HTTP errors with detailed responses
- **Batch execution** - Run all compatible extractors at once
- **Interactive mode** - Choose extractors interactively
- **Configurable output** - Customizable file paths and formats
- **Authentication** - Token-based API authentication

## Error Handling

The system handles various error scenarios:
- **404 errors** - Non-existent endpoints are commented out with explanations
- **403 errors** - Permission/authentication issues are logged
- **Invalid parameters** - Missing or incorrect parameter values
- **Network issues** - Connection timeouts and network errors

## Requirements

- Python 3.7+
- Dependencies: `requests`, `python-dotenv`
- MTS Link API access token
- Network access to MTS Link API

## Notes

Some endpoints require:
- Valid entity IDs (events, users, files, etc.)
- Specific permissions or OAuth authentication
- Organization membership or role-based access

Commented-out endpoints in the code represent non-functional API routes that were tested and found to return 404 errors.