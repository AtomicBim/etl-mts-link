"""
Примеры использования модуля daily_messages_summary
"""

import sys
import os

# Добавить корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transform.daily_messages_summary import DailyMessagesSummary
import json


def example_1_basic_usage():
    """Пример 1: Базовое использование - анализ и сохранение"""
    print("=" * 60)
    print("Пример 1: Базовое использование")
    print("=" * 60)
    
    analyzer = DailyMessagesSummary()
    output_file = analyzer.save_summary()
    
    print(f"\nФайл создан: {output_file}\n")


def example_2_get_data_without_saving():
    """Пример 2: Получение данных без сохранения в файл"""
    print("=" * 60)
    print("Пример 2: Анализ без сохранения")
    print("=" * 60)
    
    analyzer = DailyMessagesSummary()
    summary = analyzer.analyze_chats()
    
    print(f"\nНайдено чатов с сообщениями: {len(summary)}")
    
    if summary:
        print(f"\nСамый активный чат:")
        top_chat = summary[0]
        print(f"  Название: {top_chat['chat_name']}")
        print(f"  Сообщений: {top_chat['messages_count']}")
        
        print(f"\n  Первые 3 сообщения:")
        for i, msg in enumerate(top_chat['messages'][:3], 1):
            print(f"    {i}. [{msg['time']}] {msg['author']}: {msg['text'][:50]}...")
    print()


def example_2_1_analyze_multiple_days():
    """Пример 2.1: Анализ за несколько дней"""
    print("=" * 60)
    print("Пример 2.1: Анализ за последние 3 дня")
    print("=" * 60)
    
    # Анализ за последние 3 дня (включая сегодня)
    analyzer = DailyMessagesSummary(days_back=3)
    summary = analyzer.analyze_chats()
    
    print(f"\nПериод: {analyzer.start_date} - {analyzer.end_date}")
    print(f"Найдено чатов с сообщениями: {len(summary)}")
    
    if summary:
        total_messages = sum(chat['messages_count'] for chat in summary)
        print(f"Всего сообщений за период: {total_messages}")
        
        print(f"\nТоп-3 самых активных чата:")
        for i, chat in enumerate(summary[:3], 1):
            print(f"  {i}. {chat['chat_name']}: {chat['messages_count']} сообщений")
    print()


def example_3_custom_output_path():
    """Пример 3: Сохранение с пользовательским путем"""
    print("=" * 60)
    print("Пример 3: Сохранение с пользовательским путем")
    print("=" * 60)
    
    analyzer = DailyMessagesSummary()
    custom_path = "data/my_custom_summary.json"
    output_file = analyzer.save_summary(custom_path)
    
    print(f"\nФайл создан по пути: {output_file}\n")


def example_4_statistics():
    """Пример 4: Детальная статистика по чатам"""
    print("=" * 60)
    print("Пример 4: Детальная статистика")
    print("=" * 60)
    
    analyzer = DailyMessagesSummary()
    summary = analyzer.analyze_chats()
    
    if not summary:
        print("\nНет сообщений за сегодня")
        return
    
    total_messages = sum(chat['messages_count'] for chat in summary)
    avg_messages = total_messages / len(summary) if summary else 0
    
    print(f"\nОбщая статистика:")
    print(f"  Всего чатов: {len(summary)}")
    print(f"  Всего сообщений: {total_messages}")
    print(f"  Среднее сообщений на чат: {avg_messages:.1f}")
    
    print(f"\nТоп-5 самых активных чатов:")
    for i, chat in enumerate(summary[:5], 1):
        print(f"  {i}. {chat['chat_name']}: {chat['messages_count']} сообщений")
    
    # Статистика по авторам
    author_counts = {}
    for chat in summary:
        for msg in chat['messages']:
            author = msg['author']
            author_counts[author] = author_counts.get(author, 0) + 1
    
    print(f"\nТоп-5 самых активных авторов:")
    sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (author, count) in enumerate(sorted_authors[:5], 1):
        print(f"  {i}. {author}: {count} сообщений")
    
    print()


def example_5_filter_by_chat():
    """Пример 5: Поиск конкретного чата"""
    print("=" * 60)
    print("Пример 5: Поиск конкретного чата")
    print("=" * 60)
    
    analyzer = DailyMessagesSummary()
    summary = analyzer.analyze_chats()
    
    # Поиск чата по части названия
    search_term = "ИКП"
    found_chats = [chat for chat in summary if search_term.lower() in chat['chat_name'].lower()]
    
    print(f"\nНайдено чатов с '{search_term}': {len(found_chats)}")
    
    for chat in found_chats:
        print(f"\n  Чат: {chat['chat_name']}")
        print(f"  Сообщений: {chat['messages_count']}")
        if chat['messages']:
            print(f"  Последнее сообщение от: {chat['messages'][-1]['author']}")
            print(f"  Время: {chat['messages'][-1]['time']}")
    
    print()


def example_6_weekly_analysis():
    """Пример 6: Анализ за неделю"""
    print("=" * 60)
    print("Пример 6: Анализ за последние 7 дней")
    print("=" * 60)
    
    analyzer = DailyMessagesSummary(days_back=6)  # 6 дней назад + сегодня = 7 дней
    output_file = analyzer.save_summary()
    
    print(f"Недельная сводка сохранена в: {output_file}\n")


def main():
    """Запуск всех примеров"""
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ daily_messages_summary")
    print("=" * 60 + "\n")
    
    # Раскомментируйте нужные примеры:
    
    # example_1_basic_usage()
    example_2_get_data_without_saving()
    example_2_1_analyze_multiple_days()
    # example_3_custom_output_path()
    example_4_statistics()
    example_5_filter_by_chat()
    # example_6_weekly_analysis()
    
    print("=" * 60)
    print("Все примеры выполнены!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

