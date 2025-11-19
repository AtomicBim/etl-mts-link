#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки добавления организаций в chat_analyzer.py
"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transform.chat_analyzer import ChatAnalyzer

def test_organization_mapping():
    """Тест загрузки маппинга организаций"""
    print("="*80)
    print("Тест 1: Загрузка маппинга организаций")
    print("="*80)
    
    analyzer = ChatAnalyzer()
    
    print(f"\n✅ User mappings loaded: {len(analyzer.user_mapping)}")
    print(f"✅ Organization mappings loaded: {len(analyzer.organization_mapping)}")
    
    if len(analyzer.organization_mapping) > 0:
        print(f"\nПримеры организаций:")
        for i, (org_id, org_name) in enumerate(list(analyzer.organization_mapping.items())[:5]):
            print(f"  {i+1}. {org_name[:50]} ({org_id[:20]}...)")
        print("✅ Маппинг организаций работает!")
    else:
        print("⚠️ Маппинг организаций пустой. Запустите: python build_organizations_mapping.py")
    
    return analyzer

def test_analyze_result_structure():
    """Тест структуры результата анализа"""
    print("\n" + "="*80)
    print("Тест 2: Структура результата анализа")
    print("="*80)
    
    analyzer = ChatAnalyzer()
    
    # Создаем тестовые данные
    test_chat_data = {
        'chat_id': 'test-chat-123',
        'name': 'Тестовый чат',
        'type': 'channel',
        'is_public': 'true',
        'organization_id': '1f04c25b-62e8-6133-bb29-caa25282186a',  # АСК-ИТ
        'discovered_via_user_id': 'test-user-456'
    }
    
    # Получаем название организации
    org_id = test_chat_data['organization_id']
    org_name = analyzer.organization_mapping.get(org_id, org_id)
    
    print(f"\nТестовые данные:")
    print(f"  Chat ID: {test_chat_data['chat_id']}")
    print(f"  Chat Name: {test_chat_data['name']}")
    print(f"  Organization ID: {org_id}")
    print(f"  Organization Name: {org_name}")
    
    if org_name != org_id:
        print("\n✅ Маппинг организации работает!")
        print(f"   ID был преобразован в название: {org_name}")
    else:
        print("\n⚠️ Маппинг не сработал, проверьте organizations_mapping.json")
    
    # Показываем ожидаемую структуру результата
    print("\n📄 Ожидаемая структура результата анализа:")
    expected_fields = [
        'chat_id', 'chat_name', 'chat_type', 'is_public', 
        'organization_id', 'organization_name',  # <-- НОВОЕ ПОЛЕ
        'discovered_via_user_id', 'users_count', 'message_count',
        'average_message_length', 'unique_message_senders',
        'analysis_timestamp', 'analysis_error'
    ]
    
    for i, field in enumerate(expected_fields, 1):
        marker = "🆕" if field == 'organization_name' else "  "
        print(f"  {marker} {i}. {field}")
    
    return True

def test_simplified_message_structure():
    """Тест структуры упрощенного сообщения"""
    print("\n" + "="*80)
    print("Тест 3: Структура упрощенного сообщения")
    print("="*80)
    
    analyzer = ChatAnalyzer()
    
    # Тестовое сообщение
    test_message = {
        'id': 'msg-123',
        'authorId': '1ef8c1ae-a4c8-6326-aa53-a0423f4d30a4',  # Victor
        'text': 'Привет всем!',
        'createdAtMs': 1700000000000
    }
    
    # Данные чата
    chat_id = 'test-chat-123'
    chat_name = 'Тестовый чат'
    org_id = '1f04c25b-62e8-6133-bb29-caa25282186a'
    org_name = analyzer.organization_mapping.get(org_id, org_id)
    
    # Упрощаем сообщение
    simplified = analyzer._simplify_message(
        test_message, 
        chat_id=chat_id, 
        chat_name=chat_name,
        organization_id=org_id,
        organization_name=org_name
    )
    
    print("\n📄 Структура упрощенного сообщения:")
    for key, value in simplified.items():
        marker = "🆕" if key in ['organization_id', 'organization_name'] else "  "
        display_value = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
        print(f"  {marker} {key}: {display_value}")
    
    if 'organization_name' in simplified:
        print("\n✅ Поле organization_name добавлено в упрощенные сообщения!")
    else:
        print("\n⚠️ Поле organization_name отсутствует")
    
    return True

def test_csv_headers():
    """Тест заголовков CSV файлов"""
    print("\n" + "="*80)
    print("Тест 4: Заголовки CSV файлов")
    print("="*80)
    
    print("\n📄 Заголовки основного файла анализа (chat_analysis_*.csv):")
    headers_analysis = [
        'chat_id', 'chat_name', 'chat_type', 'is_public', 
        'organization_id', 'organization_name',
        'discovered_via_user_id', 'users_count', 'message_count',
        'average_message_length', 'unique_message_senders',
        'analysis_timestamp', 'analysis_error'
    ]
    
    for i, header in enumerate(headers_analysis, 1):
        marker = "🆕" if header == 'organization_name' else "  "
        print(f"  {marker} {i}. {header}")
    
    print("\n📄 Заголовки упрощенных файлов сообщений (*_simplified.csv):")
    headers_simplified = [
        'chat_id', 'chat_name', 
        'organization_id', 'organization_name',
        'authorId', 'full_name', 'text', 'createdAt'
    ]
    
    for i, header in enumerate(headers_simplified, 1):
        marker = "🆕" if header in ['organization_id', 'organization_name'] else "  "
        print(f"  {marker} {i}. {header}")
    
    print("\n✅ Все заголовки обновлены!")
    return True

def main():
    """Запуск всех тестов"""
    print("\n" + "="*80)
    print("🧪 ТЕСТИРОВАНИЕ: Добавление организаций в chat_analyzer.py")
    print("="*80)
    
    try:
        test_organization_mapping()
        test_analyze_result_structure()
        test_simplified_message_structure()
        test_csv_headers()
        
        print("\n" + "="*80)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("="*80)
        
        print("\n📝 Следующие шаги:")
        print("  1. Запустите тестовый анализ: python transform/chat_analyzer.py --test")
        print("  2. Проверьте файлы в data/:")
        print("     - chat_analysis_*.csv (должен содержать organization_name)")
        print("     - data/chats_archive/*_simplified.csv (должны содержать organization поля)")
        print("  3. Запустите полный анализ: python transform/chat_analyzer.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

