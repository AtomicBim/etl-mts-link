import sys
import os
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints
from abstractions.logging_config import setup_logger

logger = setup_logger(__name__)


@endpoint("/chats/organization/members")
def chats_organization_members():
    """Получить список всех пользователей организации, использующих Чаты"""
    pass


@endpoint("/chats/channels/{userId}")
def user_channels():
    """Получить список каналов из Линк Чатов для определенного пользователя"""
    pass


@endpoint("/chats/channel/{chatId}/messages")
def channel_messages():
    """Чтение сообщений из Линк Чатов
    
    Дополнительные параметры:
    - viewerId: ИД пользователя
    - fromMessageId: UUID сообщения, начиная с которого выводятся последующие
    - parrentMessageId: идентификатор родительского сообщения (обсуждения)
    - direction: Направление поиска от fromMessageId (Before, After, Around). По умолчанию - Before
    - limit: лимит сообщений
    """
    pass


@endpoint("/chats/channels/{channelId}/users")
def channel_users():
    """Получение списка участников канала LinkChat
    
    Поля ответа:
    - userId: идентификатор пользователя
    - role: роль пользователя
    - status: статус пользователя
    """
    pass


@endpoint("/chats/channel/{channelId}")
def channel_info():
    """Получить информацию о канале в Линк Чатах
    
    Поля ответа:
    - chatId: идентификатор чата
    - organizationId: идентификатор организации
    - name: название чата
    - isPublic: true/false чат публичный или нет
    - isReadOnly: true/false чат только для чтения или нет
    - ownerID: идентификатор владельца чата
    - type: тип чата
    - unreadMessageCount: количество непрочитанных сообщений
    - lastMessage: последнее сообщение
    - firstUnreadMessage: последнее не прочитанное сообщение
    - startedWebinarEventId: идентификатор начатой встречи
    - description: описание чата
    - isNotifiable: true/false включены ли оповещения
    """
    pass


# МТС Линк Курсы (MTS Link Courses)

@endpoint("/organization/courses")
def organization_courses():
    """Получить список всех курсов, созданных в организации"""
    pass


@endpoint("/courses/{Courseid}")
def course_details():
    """Получить данные о конкретном курсе
    
    Позволяет получить название, статус, список групп курса и их настройки.
    {CourseID} можно получить запросом GET /organization/courses/groups.
    
    Поля ответа:
    - id: идентификатор курса
    - name: имя курса
    - owner: идентификатор сотрудника организации, создавшего курс
    - isPublish: состояние публикации курса
    - isPreModerationEnabled: необходима ли предварительная модерация участников
    - groups: идентификатор группы
    - trajectory: траектория курса закрытая или открытая
    - passingScore: минимальный проходной балл
    - certSetting: параметр выдачи сертификата (нет/автоматически/вручную)
    - visibilityStatus: видимость курса (всем/только приглашенным)
    - additionalFields: дополнительные поля курса (массив параметров)
    - locale: язык курса
    """
    pass


@endpoint("/contacts/{contactID}/user")
def contact_user_info():
    """Получить информацию о студенте по его ID в адресной книге"""
    pass


@endpoint("/organization/users/{userID}/statistics")
def user_course_statistics():
    """Получить статистику прохождения курсов конкретным пользователем"""
    pass


def list_available_extractors():
    """List all available extractors"""
    endpoints = get_registered_endpoints()
    logger.info("Available MTS Link Chats & Courses extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        logger.info(f"  {name}: {path}")
        logger.info(f"    {description}")
    return endpoints


def main():
    """Main function to run extractors"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MTS-Link Chats & Courses API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')
    parser.add_argument('--all', '-a', action='store_true', help='Run all extractors')
    
    # Chat-related parameters
    parser.add_argument('--channelId', help='Channel ID for channel-specific endpoints')
    parser.add_argument('--chatId', help='Chat ID for chat-specific endpoints')
    parser.add_argument('--userId', help='User ID for user-specific endpoints')
    
    # Channel messages parameters
    parser.add_argument('--viewerId', help='Viewer ID for channel messages')
    parser.add_argument('--fromMessageId', help='UUID of message to start from')
    parser.add_argument('--parrentMessageId', help='Parent message ID for discussions')
    parser.add_argument('--direction', help='Search direction (Before, After, Around)', 
                        choices=['Before', 'After', 'Around'])
    parser.add_argument('--limit', type=int, help='Message limit')
    
    # Course-related parameters
    parser.add_argument('--courseId', help='Course ID for course-specific endpoints')
    parser.add_argument('--Courseid', help='Course ID (alternative parameter name)')
    parser.add_argument('--courseID', help='Course ID (alternative parameter name)')
    parser.add_argument('--groupID', help='Group ID for group-specific endpoints')
    parser.add_argument('--contactID', help='Contact ID for contact-specific endpoints')
    parser.add_argument('--userID', help='User ID (alternative parameter name)')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_extractors()
        return
    
    kwargs = {}
    if args.channelId:
        kwargs['channelId'] = args.channelId
    if args.chatId:
        kwargs['chatId'] = args.chatId
    if args.userId:
        kwargs['userId'] = args.userId
    
    # Channel messages parameters
    if args.viewerId:
        kwargs['viewerId'] = args.viewerId
    if args.fromMessageId:
        kwargs['fromMessageId'] = args.fromMessageId
    if args.parrentMessageId:
        kwargs['parrentMessageId'] = args.parrentMessageId
    if args.direction:
        kwargs['direction'] = args.direction
    if args.limit:
        kwargs['limit'] = args.limit
    if args.courseId:
        kwargs['courseId'] = args.courseId
    if args.Courseid:
        kwargs['Courseid'] = args.Courseid
    if args.courseID:
        kwargs['courseID'] = args.courseID
    if args.groupID:
        kwargs['groupID'] = args.groupID
    if args.contactID:
        kwargs['contactID'] = args.contactID
    if args.userID:
        kwargs['userID'] = args.userID
    
    if args.all:
        endpoints = get_registered_endpoints()
        no_param_endpoints = [name for name, path in endpoints.items() 
                             if '{' not in path]
        
        logger.info(f"Running {len(no_param_endpoints)} extractors (excluding parameterized ones)...")
        for extractor_name in no_param_endpoints:
            logger.info(f"\n--- Running {extractor_name} ---")
            result = run_extractor(extractor_name, **kwargs)
            if result:
                logger.success(f"{extractor_name} completed: {result}")
            else:
                logger.error(f"{extractor_name} failed")
        
        param_endpoints = [name for name, path in endpoints.items() 
                          if '{' in path]
        if param_endpoints:
            logger.warning(f"\nSkipped {len(param_endpoints)} parameterized endpoints:")
            for name in param_endpoints:
                logger.warning(f"  {name} (requires parameters)")
        
        return
    
    if args.extractor:
        result = run_extractor(args.extractor, **kwargs)
        if result:
            logger.success(f"Extraction completed: {result}")
        else:
            logger.error(f"Extraction failed")
        return
    
    endpoints = list_available_extractors()
    logger.info(f"\nEnter extractor name to run:")
    logger.info("Note: For parameterized endpoints, use command line arguments")
    logger.info("Examples:")
    logger.info("  python link_chats_extractors.py channel_info --channelId 123")
    logger.info("  python link_chats_extractors.py course_details --Courseid 456")
    
    while True:
        choice = input("> ").strip()
        
        if choice == 'quit' or choice == 'exit':
            break
        elif choice == 'all':
            no_param_endpoints = [name for name, path in endpoints.items() 
                                 if '{' not in path]
            for extractor_name in no_param_endpoints:
                logger.info(f"\n--- Running {extractor_name} ---")
                result = run_extractor(extractor_name)
                if result:
                    logger.success(f"{extractor_name} completed: {result}")
                else:
                    logger.error(f"{extractor_name} failed")
        elif choice in endpoints:
            result = run_extractor(choice, **kwargs)
            if result:
                logger.success(f"Extraction completed: {result}")
            else:
                logger.error(f"Extraction failed")
        elif choice:
            logger.error(f"Unknown extractor: {choice}")
            logger.info("Available extractors: " + ", ".join(list(endpoints.keys())))


if __name__ == "__main__":
    main()