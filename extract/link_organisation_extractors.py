import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abstractions.extract import endpoint, run_extractor, get_registered_endpoints


@endpoint("/brandings")
def brandings_list():
    """Получить информацию о брендингах организации"""
    pass


@endpoint("/organization-groups")
def organization_groups():
    """Выгрузить список созданных в организации групп пользователей"""
    pass


@endpoint("/partner-applications")
def partner_applications():
    """Получить данные об интеграциях, подключенных к организации через OAuth

    Дополнительные параметры:
    - approval: фильтр разрешенных приложений (all, approved, rejected)
    """
    pass


@endpoint("/timezones")
def timezones_list():
    """Получить список доступных часовых поясов"""
    pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run MTS-Link Organisation & Settings API extractors')
    parser.add_argument('extractor', nargs='?', help='Name of the extractor to run')
    parser.add_argument('--list', '-l', action='store_true', help='List available extractors')

    for arg in ['approval']:
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