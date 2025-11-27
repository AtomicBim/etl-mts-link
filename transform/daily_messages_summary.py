"""
Модуль для анализа сообщений из чатов за текущий день или за период.
Читает simplified JSON файлы из data/chats_archive и формирует сводку по сообщениям.
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


class DailyMessagesSummary:
    """Анализатор сообщений за день или период"""
    
    def __init__(self, chats_archive_dir: str = "data/chats_archive", days_back: int = 0):
        """
        Инициализация анализатора
        
        Args:
            chats_archive_dir: Путь к директории с архивом чатов
            days_back: Количество дней назад от сегодня для анализа (0 = только сегодня)
                      Например, days_back=3 означает анализ за последние 3 дня включая сегодня
        """
        self.chats_archive_dir = Path(chats_archive_dir)
        self.days_back = days_back
        self.today = datetime.now().date()
        
        # Вычислить диапазон дат
        if days_back > 0:
            self.start_date = self.today - timedelta(days=days_back)
        else:
            self.start_date = self.today
        self.end_date = self.today
    
    def _get_simplified_json_files(self) -> List[Path]:
        """
        Получить список всех simplified JSON файлов
        
        Returns:
            Список путей к файлам
        """
        pattern = "*_simplified.json"
        return sorted(self.chats_archive_dir.glob(pattern))
    
    def _read_chat_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Прочитать и распарсить JSON файл чата
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Словарь с данными чата
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _filter_messages_by_date_range(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Отфильтровать сообщения за указанный период
        
        Args:
            messages: Список всех сообщений
            
        Returns:
            Список сообщений за период
        """
        filtered_messages = []
        
        for message in messages:
            created_at = message.get('createdAt', '')
            if not created_at:
                continue
            
            # Формат даты: "2025-11-20 12:34:56"
            try:
                message_date = datetime.strptime(created_at[:10], "%Y-%m-%d").date()
                
                # Проверить, попадает ли дата в диапазон
                if self.start_date <= message_date <= self.end_date:
                    filtered_messages.append(message)
            except ValueError:
                # Пропустить сообщения с некорректной датой
                continue
        
        return filtered_messages
    
    def _format_message(self, message: Dict[str, Any]) -> Dict[str, str]:
        """
        Форматировать сообщение для вывода
        
        Args:
            message: Данные сообщения
            
        Returns:
            Отформатированное сообщение
        """
        return {
            "author": message.get("full_name", "Unknown"),
            "time": message.get("createdAt", ""),
            "text": message.get("text", "")
        }
    
    def analyze_chats(self) -> List[Dict[str, Any]]:
        """
        Проанализировать все чаты и вернуть сводку за указанный период
        
        Returns:
            Список чатов с сообщениями за период
        """
        summary = []
        
        json_files = self._get_simplified_json_files()
        print(f"Найдено {len(json_files)} simplified JSON файлов")
        
        for file_path in json_files:
            try:
                chat_data = self._read_chat_file(file_path)
                
                # Получить сообщения за период
                all_messages = chat_data.get('messages', [])
                filtered_messages = self._filter_messages_by_date_range(all_messages)
                
                # Пропустить чаты без сообщений за период
                if not filtered_messages:
                    continue
                
                # Отсортировать сообщения по времени
                filtered_messages.sort(key=lambda m: m.get('createdAt', ''))
                
                # Форматировать сообщения
                formatted_messages = [
                    self._format_message(msg) for msg in filtered_messages
                ]
                
                # Добавить в сводку
                chat_summary = {
                    "chat_name": chat_data.get("chat_name", "Unknown"),
                    "chat_id": chat_data.get("chat_id", ""),
                    "date_range": {
                        "start": self.start_date.strftime("%Y-%m-%d"),
                        "end": self.end_date.strftime("%Y-%m-%d")
                    },
                    "messages_count": len(formatted_messages),
                    "messages": formatted_messages
                }
                
                summary.append(chat_summary)
                
            except Exception as e:
                print(f"Ошибка обработки файла {file_path.name}: {e}")
                continue
        
        # Отсортировать чаты по количеству сообщений (больше сначала)
        summary.sort(key=lambda x: x['messages_count'], reverse=True)
        
        return summary
    
    def save_summary(self, output_file: str = None) -> str:
        """
        Проанализировать чаты и сохранить сводку в JSON файл
        
        Args:
            output_file: Путь для сохранения файла (если не указан, генерируется автоматически)
            
        Returns:
            Путь к сохраненному файлу
        """
        summary = self.analyze_chats()
        
        # Генерировать имя файла, если не указано
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.days_back > 0:
                output_file = f"data/messages_summary_{self.days_back}days_{timestamp}.json"
            else:
                output_file = f"data/daily_messages_summary_{timestamp}.json"
        
        # Создать директорию, если не существует
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохранить в JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        total_chats = len(summary)
        total_messages = sum(chat['messages_count'] for chat in summary)
        
        print(f"\n{'='*60}")
        if self.days_back > 0:
            print(f"Сводка за период: {self.start_date} - {self.end_date}")
            print(f"Количество дней: {self.days_back + 1}")
        else:
            print(f"Сводка за {self.today}")
        print(f"{'='*60}")
        print(f"Всего чатов с сообщениями: {total_chats}")
        print(f"Всего сообщений: {total_messages}")
        print(f"Результат сохранен в: {output_path}")
        print(f"{'='*60}\n")
        
        return str(output_path)


def main():
    """Главная функция для запуска анализа"""
    parser = argparse.ArgumentParser(
        description='Анализ сообщений из чатов за указанный период'
    )
    parser.add_argument(
        '--days-back',
        type=int,
        default=0,
        help='Количество дней назад от сегодня для анализа (0 = только сегодня, 14 = последние 14 дней + сегодня)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Путь для сохранения результата (если не указан, генерируется автоматически)'
    )
    
    args = parser.parse_args()
    
    analyzer = DailyMessagesSummary(days_back=args.days_back)
    output_file = analyzer.save_summary(output_file=args.output)
    
    print(f"Анализ завершен. Файл: {output_file}")


if __name__ == "__main__":
    main()

