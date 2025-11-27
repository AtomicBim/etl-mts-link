"""
Модуль для анализа активных пользователей по дням.
Показывает сколько пользователей написали хотя бы 1 сообщение в каждый день.
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict


class DailyActiveUsersAnalyzer:
    """Анализатор активных пользователей по дням"""
    
    def __init__(self, chats_archive_dir: str = "data/chats_archive", days_back: int = 0):
        """
        Инициализация анализатора
        
        Args:
            chats_archive_dir: Путь к директории с архивом чатов
            days_back: Количество дней назад от сегодня для анализа (0 = только сегодня)
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
        
        # Хранилище данных: {date: {user_id: count}}
        self.daily_users: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # Хранилище имен пользователей: {user_id: full_name}
        self.user_names: Dict[str, str] = {}
    
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
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка чтения {file_path.name}: {e}")
            return {}
    
    def _process_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Обработать сообщения и подсчитать активных пользователей по дням
        
        Args:
            messages: Список сообщений из чата
        """
        for message in messages:
            created_at = message.get('createdAt', '')
            if not created_at:
                continue
            
            try:
                # Формат даты: "2025-11-20 12:34:56"
                message_date = datetime.strptime(created_at[:10], "%Y-%m-%d").date()
                
                # Проверить, попадает ли дата в диапазон
                if self.start_date <= message_date <= self.end_date:
                    author_id = message.get('authorId', '')
                    full_name = message.get('full_name', 'Unknown User')
                    
                    if author_id:
                        date_str = message_date.strftime("%Y-%m-%d")
                        self.daily_users[date_str][author_id] += 1
                        
                        # Сохранить имя пользователя
                        if author_id not in self.user_names:
                            self.user_names[author_id] = full_name
                        
            except ValueError:
                # Пропустить сообщения с некорректной датой
                continue
    
    def analyze(self) -> Dict[str, Any]:
        """
        Проанализировать все чаты и подсчитать активных пользователей по дням
        
        Returns:
            Словарь с данными анализа
        """
        json_files = self._get_simplified_json_files()
        print(f"Найдено {len(json_files)} simplified JSON файлов")
        
        # Обработать все файлы
        for file_path in json_files:
            try:
                chat_data = self._read_chat_file(file_path)
                messages = chat_data.get('messages', [])
                if messages:
                    self._process_messages(messages)
            except Exception as e:
                print(f"Ошибка обработки {file_path.name}: {e}")
                continue
        
        print(f"Обработано дат: {len(self.daily_users)}")
        print(f"Уникальных пользователей: {len(self.user_names)}")
        
        return {
            'daily_users': dict(self.daily_users),
            'user_names': self.user_names,
            'date_range': {
                'start': self.start_date.strftime("%Y-%m-%d"),
                'end': self.end_date.strftime("%Y-%m-%d")
            }
        }
    
    def generate_report(self) -> List[Dict[str, Any]]:
        """
        Сгенерировать отчет по активным пользователям по дням
        
        Returns:
            Список записей для отчета
        """
        report_data = []
        
        # Создать список всех дат в диапазоне
        current_date = self.start_date
        all_dates = []
        while current_date <= self.end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Для каждой даты создать запись
        for date in all_dates:
            date_str = date.strftime("%Y-%m-%d")
            day_name = date.strftime("%A")  # Название дня недели
            
            users_on_date = self.daily_users.get(date_str, {})
            unique_users_count = len(users_on_date)
            total_messages = sum(users_on_date.values())
            
            report_data.append({
                'date': date_str,
                'day_of_week': day_name,
                'unique_active_users': unique_users_count,
                'total_messages': total_messages,
                'avg_messages_per_user': round(total_messages / unique_users_count, 2) if unique_users_count > 0 else 0
            })
        
        return report_data
    
    def generate_detailed_user_report(self) -> List[Dict[str, Any]]:
        """
        Сгенерировать детальный отчет по каждому пользователю
        
        Returns:
            Список записей с детализацией по пользователям
        """
        detailed_report = []
        
        # Для каждого пользователя посчитать активность по дням
        for user_id, full_name in self.user_names.items():
            # Собрать статистику по дням для этого пользователя
            days_active = 0
            total_messages = 0
            first_message_date = None
            last_message_date = None
            
            for date_str, users in self.daily_users.items():
                if user_id in users:
                    days_active += 1
                    msg_count = users[user_id]
                    total_messages += msg_count
                    
                    if first_message_date is None or date_str < first_message_date:
                        first_message_date = date_str
                    if last_message_date is None or date_str > last_message_date:
                        last_message_date = date_str
            
            if days_active > 0:
                detailed_report.append({
                    'user_id': user_id,
                    'full_name': full_name,
                    'days_active': days_active,
                    'total_messages': total_messages,
                    'avg_messages_per_day': round(total_messages / days_active, 2),
                    'first_message_date': first_message_date,
                    'last_message_date': last_message_date
                })
        
        # Отсортировать по количеству сообщений
        detailed_report.sort(key=lambda x: x['total_messages'], reverse=True)
        
        return detailed_report
    
    def save_to_csv(self, output_file: str = None) -> str:
        """
        Сохранить отчет в CSV файл
        
        Args:
            output_file: Путь для сохранения файла (если не указан, генерируется автоматически)
            
        Returns:
            Путь к сохраненному файлу
        """
        # Сначала выполнить анализ
        self.analyze()
        
        # Сгенерировать отчет
        report_data = self.generate_report()
        
        # Генерировать имя файла, если не указано
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.days_back > 0:
                output_file = f"data/daily_active_users_{self.days_back}days_{timestamp}.csv"
            else:
                output_file = f"data/daily_active_users_{timestamp}.csv"
        
        # Создать директорию, если не существует
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохранить в CSV
        fieldnames = ['date', 'day_of_week', 'unique_active_users', 'total_messages', 'avg_messages_per_user']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_data)
        
        # Вывести статистику
        total_days = len(report_data)
        total_messages = sum(r['total_messages'] for r in report_data)
        avg_users_per_day = sum(r['unique_active_users'] for r in report_data) / total_days if total_days > 0 else 0
        
        print(f"\n{'='*60}")
        if self.days_back > 0:
            print(f"Отчет по активным пользователям за период: {self.start_date} - {self.end_date}")
            print(f"Количество дней: {self.days_back + 1}")
        else:
            print(f"Отчет по активным пользователям за {self.today}")
        print(f"{'='*60}")
        print(f"Всего дней в отчете: {total_days}")
        print(f"Всего уникальных пользователей: {len(self.user_names)}")
        print(f"Среднее активных пользователей в день: {avg_users_per_day:.1f}")
        print(f"Всего сообщений за период: {total_messages}")
        print(f"Результат сохранен в: {output_path}")
        print(f"{'='*60}\n")
        
        return str(output_path)
    
    def save_detailed_to_csv(self, output_file: str = None) -> str:
        """
        Сохранить детальный отчет по пользователям в CSV файл
        
        Args:
            output_file: Путь для сохранения файла (если не указан, генерируется автоматически)
            
        Returns:
            Путь к сохраненному файлу
        """
        # Генерировать имя файла, если не указано
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.days_back > 0:
                output_file = f"data/daily_active_users_detailed_{self.days_back}days_{timestamp}.csv"
            else:
                output_file = f"data/daily_active_users_detailed_{timestamp}.csv"
        
        # Создать директорию, если не существует
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Сгенерировать детальный отчет
        detailed_report = self.generate_detailed_user_report()
        
        # Сохранить в CSV
        fieldnames = ['user_id', 'full_name', 'days_active', 'total_messages', 
                     'avg_messages_per_day', 'first_message_date', 'last_message_date']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(detailed_report)
        
        print(f"Детальный отчет сохранен в: {output_path}")
        print(f"Всего пользователей: {len(detailed_report)}")
        
        return str(output_path)


def main():
    """Главная функция для запуска анализа"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Анализ активных пользователей по дням')
    parser.add_argument('--days-back', '-d', type=int, default=0,
                       help='Количество дней назад для анализа (0 = только сегодня)')
    parser.add_argument('--output', '-o', help='Путь для сохранения основного отчета')
    parser.add_argument('--detailed', action='store_true',
                       help='Создать также детальный отчет по пользователям')
    parser.add_argument('--detailed-output', help='Путь для сохранения детального отчета')
    
    args = parser.parse_args()
    
    # Создать анализатор
    analyzer = DailyActiveUsersAnalyzer(days_back=args.days_back)
    
    # Сохранить основной отчет
    output_file = analyzer.save_to_csv(args.output)
    print(f"Основной отчет: {output_file}")
    
    # Сохранить детальный отчет, если указан флаг
    if args.detailed:
        detailed_file = analyzer.save_detailed_to_csv(args.detailed_output)
        print(f"Детальный отчет: {detailed_file}")


if __name__ == "__main__":
    main()

