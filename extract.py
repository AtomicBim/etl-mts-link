import requests
import json

# --- НАСТРОЙКИ ---
# Замените 'ВАШ_GUID_ТОКЕН' на ваш реальный токен доступа
API_TOKEN = "1b5e53723d479753b9742ca6e7b6e591"

# Базовый URL API МТС Линк. Убедитесь, что он верный для вашей интеграции.
BASE_URL = "https://api.mts-link.ru/v3"

# --- КОД ЗАПРОСА ---
def get_events_stats():
    """
    Выполняет GET-запрос к /stats/events для получения статистики по мероприятиям.
    """
    endpoint = "/organization/events/schedule"
    url = f"{BASE_URL}{endpoint}"

    # Заголовки запроса с вашим токеном для авторизации
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # (Опционально) Параметры запроса для фильтрации данных, например, по датам.
    # Раскомментируйте и настройте при необходимости.
    # params = {
    #     "dateFrom": "2025-01-01T00:00:00Z",
    #     "dateTo": "2025-01-31T23:59:59Z"
    # }

    print(f"Отправка запроса на: {url}")

    try:
        # Выполнение GET-запроса
        # response = requests.get(url, headers=headers, params=params) # с параметрами
        response = requests.get(url, headers=headers) # без параметров

        # Проверка, что запрос прошел успешно (код ответа 200)
        response.raise_for_status()

        # Получение данных в формате JSON
        data = response.json()
        print("✅ Запрос выполнен успешно!")
        
        # Красивый вывод JSON
        print(json.dumps(data, indent=4, ensure_ascii=False))
        return data

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP ошибка: {http_err}")
        print(f"Код ответа: {response.status_code}")
        print(f"Тело ответа: {response.text}")
    except requests.exceptions.RequestException as err:
        print(f"❌ Другая ошибка: {err}")
    
    return None

# --- ЗАПУСК ---
if __name__ == "__main__":
    get_events_stats()