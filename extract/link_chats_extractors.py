import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints


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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run MTS-Link Chats API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')

    for arg in ['channelId', 'chatId', 'userId', 'viewerId', 'fromMessageId', 'parrentMessageId', 'direction', 'limit']:
        parser.add_argument(f'--{arg}', help=f'{arg} parameter')

    args = parser.parse_args()

    if args.list:
        endpoints = get_registered_endpoints()
        for name, path in endpoints.items():
            print(f"{name}: {path}")
        exit()

    if not args.extractor:
        print("Error: extractor name is required")
        parser.print_help()
        exit(1)

    kwargs = {k: v for k, v in vars(args).items() if v is not None and k != 'extractor' and k != 'list'}
    result = run_extractor(args.extractor, **kwargs)
    print(f"Result: {result}")