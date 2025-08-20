import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints


# MTS Link Chats & Courses Extractors - All chat and course-related API endpoints

# МТС Линк Чаты (MTS Link Chats)

@endpoint("/chats/teams")
def chats_teams():
    """Получить список всех команд (групповых чатов)"""
    pass


# NOTE: This endpoint does not exist in the MTS Link API (returns 404)
# Tested with sample channelId parameter - no route found
# @endpoint("/chats/channels/{channelId}/users")
# def channel_users():
#     """Выгрузить список всех пользователей в конкретном канале"""
#     pass


# NOTE: This endpoint does not exist in the MTS Link API (returns 404)
# Tested with sample channelId parameter - no route found
# @endpoint("/chats/channel/{channelId}")
# def channel_info():
#     """Получить детальную информацию о конкретном канале в Чатах"""
#     pass


# NOTE: This endpoint does not exist in the MTS Link API (returns 404)
# Tested with sample userId parameter - no route found
# @endpoint("/chats/channels/{userId}")
# def user_channels():
#     """Получить список каналов, в которых состоит определенный пользователь"""
#     pass


# NOTE: This endpoint does not exist in the MTS Link API (returns 404)
# Tested with sample chatId parameter - no route found
# @endpoint("/chats/channel/{chatId}/messages")
# def channel_messages():
#     """Выгрузить историю сообщений из указанного канала"""
#     pass


@endpoint("/chats/organization/members")
def chats_organization_members():
    """Получить список всех пользователей организации, использующих Чаты"""
    pass


# МТС Линк Курсы (MTS Link Courses)

@endpoint("/organization/courses")
def organization_courses():
    """Получить список всех курсов, созданных в организации"""
    pass


@endpoint("/courses/{Courseid}")
def course_details():
    """Получить детальную информацию по одному курсу"""
    pass


@endpoint("/organization/courses/groups")
def courses_groups():
    """Выгрузить список всех учебных групп, созданных в рамках курсов"""
    pass


@endpoint("/courses/{courseID}/groups/{groupID}/statistics")
def course_group_statistics():
    """Получить агрегированную статистику по успеваемости и активности группы"""
    pass


@endpoint("/contacts/{contactID}/user")
def contact_user_info():
    """Получить информацию о студенте по его ID в адресной книге"""
    pass


@endpoint("/courses/{courseID}/groups/{groupID}")
def course_group_info():
    """Получить детальную информацию о конкретной учебной группе"""
    pass


@endpoint("/organization/users/{userID}/statistics")
def user_course_statistics():
    """Получить статистику прохождения курсов конкретным пользователем"""
    pass


def list_available_extractors():
    """List all available extractors"""
    endpoints = get_registered_endpoints()
    print("Available MTS Link Chats & Courses extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        print(f"  {name}: {path}")
        print(f"    {description}")
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
        
        print(f"Running {len(no_param_endpoints)} extractors (excluding parameterized ones)...")
        for extractor_name in no_param_endpoints:
            print(f"\n--- Running {extractor_name} ---")
            result = run_extractor(extractor_name, **kwargs)
            if result:
                print(f"SUCCESS: {extractor_name} completed: {result}")
            else:
                print(f"FAILED: {extractor_name} failed")
        
        param_endpoints = [name for name, path in endpoints.items() 
                          if '{' in path]
        if param_endpoints:
            print(f"\nSkipped {len(param_endpoints)} parameterized endpoints:")
            for name in param_endpoints:
                print(f"  {name} (requires parameters)")
        
        return
    
    if args.extractor:
        result = run_extractor(args.extractor, **kwargs)
        if result:
            print(f"SUCCESS: Extraction completed: {result}")
        else:
            print(f"FAILED: Extraction failed")
        return
    
    endpoints = list_available_extractors()
    print(f"\nEnter extractor name to run:")
    print("Note: For parameterized endpoints, use command line arguments")
    print("Examples:")
    print("  python link_chats_extractors.py channel_info --channelId 123")
    print("  python link_chats_extractors.py course_details --Courseid 456")
    
    while True:
        choice = input("> ").strip()
        
        if choice == 'quit' or choice == 'exit':
            break
        elif choice == 'all':
            no_param_endpoints = [name for name, path in endpoints.items() 
                                 if '{' not in path]
            for extractor_name in no_param_endpoints:
                print(f"\n--- Running {extractor_name} ---")
                result = run_extractor(extractor_name)
                if result:
                    print(f"SUCCESS: {extractor_name} completed: {result}")
                else:
                    print(f"FAILED: {extractor_name} failed")
        elif choice in endpoints:
            result = run_extractor(choice, **kwargs)
            if result:
                print(f"SUCCESS: Extraction completed: {result}")
            else:
                print(f"FAILED: Extraction failed")
        elif choice:
            print(f"Unknown extractor: {choice}")
            print("Available extractors:", list(endpoints.keys()))


if __name__ == "__main__":
    main()