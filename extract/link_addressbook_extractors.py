import sys
import os
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints
from abstractions.logging_config import setup_logger

logger = setup_logger(__name__)


# MTS Link Addressbook & Users Extractors - All addressbook and user-related API endpoints

@endpoint("/contacts/{contactsID}")
def contact_details(**kwargs):
    """Получить детальную информацию о конкретном контакте из адресной книги
    
    Параметры:
    - contactsID: ID контакта (обязательный)
    
    Возвращает информацию о контакте включая:
    - id: ID контакта
    - userId: ID пользователя
    - name: Фамилия
    - secondName: Имя
    - company: Компания
    - position: Должность
    - phoneMain: Основной телефон
    - email: Электронная почта
    - tags: Список тегов
    """
    from abstractions.extract import BaseExtractor
    
    class ContactDetailsExtractor(BaseExtractor):
        def get_endpoint(self):
            return "/contacts/{contactsID}"
    
    extractor = ContactDetailsExtractor()
    data = extractor.extract(**kwargs)
    
    if data:
        filename = extractor.save_to_file(data)
        return filename
    
    return None


@endpoint("/contacts/search")
def contacts_search():
    """Осуществить поиск по контактам в адресной книге"""
    pass


@endpoint("/organization/members")
def organization_members():
    """Выгрузить список всех сотрудников, добавленных в аккаунт МТС Линк"""
    from abstractions.extract import BaseExtractor
    
    class OrganizationMembersExtractor(BaseExtractor):
        def get_endpoint(self):
            return "/organization/members"
    
    extractor = OrganizationMembersExtractor()
    data = extractor.extract()
    
    if data:
        filename = extractor.save_to_file(data)
        return filename
    
    return None


def list_available_extractors():
    """List all available extractors"""
    endpoints = get_registered_endpoints()
    logger.info("Available MTS Link Addressbook & Users extractors:")
    for name, path in endpoints.items():
        func = globals().get(name)
        description = func.__doc__ if func and func.__doc__ else "No description"
        logger.info(f"  {name}: {path}")
        logger.info(f"    {description}")
    return endpoints


def main():
    """Main function to run extractors"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MTS-Link Addressbook & Users API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')
    parser.add_argument('--all', '-a', action='store_true', help='Run all extractors')
    
    # Addressbook-related parameters
    parser.add_argument('--contactsID', help='Contact ID for contact-specific endpoints')
    parser.add_argument('--query', help='Search query for contacts search')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_extractors()
        return
    
    kwargs = {}
    if args.contactsID:
        kwargs['contactsID'] = args.contactsID
    if args.query:
        kwargs['query'] = args.query
    
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
    logger.info("  python link_addressbook_extractors.py contact_details --contactsID 123")
    logger.info("  python link_addressbook_extractors.py contacts_search --query 'search term'")
    
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