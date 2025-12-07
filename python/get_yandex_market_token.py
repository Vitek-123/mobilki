"""
Скрипт для получения OAuth токена Яндекс.Маркет
"""
import requests
import webbrowser
import os
from urllib.parse import urlencode, parse_qs, urlparse
from dotenv import load_dotenv

load_dotenv()

# Данные из вашего приложения (можно загрузить из .env или использовать напрямую)
CLIENT_ID = os.getenv("YANDEX_MARKET_CLIENT_ID", "5c11d50c52304b16b6c07fbb6b5382d8")
CLIENT_SECRET = os.getenv("YANDEX_MARKET_CLIENT_SECRET", "63f8b8c7e1d74543affdab9cde21c14b")
REDIRECT_URI = os.getenv("YANDEX_MARKET_REDIRECT_URI", "https://oauth.yandex.ru/verification_code")

def get_authorization_url(use_scope=True):
    """Получение URL для авторизации"""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI
    }
    
    # Пробуем разные варианты scope
    if use_scope:
        # Вариант 1: Без scope (базовые права приложения)
        # Не добавляем scope - используем права, указанные при создании приложения
        pass
    else:
        # Вариант 2: Явно не указываем scope
        pass
    
    url = "https://oauth.yandex.ru/authorize?" + urlencode(params)
    return url

def get_token(authorization_code):
    """Обмен кода авторизации на токен"""
    url = "https://oauth.yandex.ru/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Ошибка получения токена: {response.status_code}")
        print(f"Ответ: {response.text}")
        return None

def main():
    print("=" * 60)
    print("Получение OAuth токена для Яндекс.Маркет")
    print("=" * 60)
    print()
    
    # Шаг 1: Получаем URL для авторизации (без scope)
    print("Шаг 1: Авторизация")
    print("Пробуем получить токен БЕЗ указания scope")
    print("(используем права, указанные при создании приложения)")
    print()
    
    auth_url = get_authorization_url(use_scope=False)
    print(f"URL для авторизации:")
    print(auth_url)
    print()
    print("Открываю браузер...")
    
    # Открываем браузер
    try:
        webbrowser.open(auth_url)
    except:
        print("Не удалось открыть браузер автоматически")
        print("Скопируйте URL выше и откройте вручную")
    
    print()
    print("=" * 60)
    print("Инструкция:")
    print("=" * 60)
    print("1. В браузере авторизуйтесь в Яндекс")
    print("2. Разрешите доступ приложению")
    print("3. После авторизации вас перенаправит на страницу с кодом")
    print("4. Скопируйте код из адресной строки (параметр 'code')")
    print("   Или скопируйте весь URL и вставьте сюда")
    print()
    print("Пример URL:")
    print("https://oauth.yandex.ru/verification_code?code=1234567890abcdef")
    print()
    
    # Шаг 2: Получаем код от пользователя
    user_input = input("Вставьте URL или код авторизации: ").strip()
    
    # Извлекаем код из URL или используем как есть
    if user_input.startswith("http"):
        # Парсим URL
        parsed = urlparse(user_input)
        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]
    else:
        code = user_input
    
    if not code:
        print("❌ Код не найден. Попробуйте еще раз.")
        return
    
    print()
    print("Шаг 2: Получение токена...")
    
    # Шаг 3: Обмениваем код на токен
    token = get_token(code)
    
    if token:
        print()
        print("=" * 60)
        print("✅ Токен успешно получен!")
        print("=" * 60)
        print()
        print("Ваш OAuth токен:")
        print(token)
        print()
        print("⚠️ ВАЖНО: Сохраните этот токен в безопасном месте!")
        print()
        print("Добавьте в файл .env:")
        print(f"YANDEX_MARKET_OAUTH_TOKEN={token}")
        print()
        
        # Предлагаем сохранить в .env
        save = input("Сохранить токен в .env файл? (y/n): ").strip().lower()
        if save == 'y':
            try:
                with open('.env', 'a', encoding='utf-8') as f:
                    f.write(f"\n# Яндекс.Маркет OAuth токен\n")
                    f.write(f"YANDEX_MARKET_OAUTH_TOKEN={token}\n")
                print("✅ Токен сохранен в .env файл")
            except Exception as e:
                print(f"❌ Ошибка сохранения: {e}")
                print("Сохраните токен вручную в .env файл")
    else:
        print("❌ Не удалось получить токен")

if __name__ == "__main__":
    main()

