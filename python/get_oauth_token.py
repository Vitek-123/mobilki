"""
Скрипт для получения OAuth токена для Яндекс.Маркет API
Документация: https://yandex.ru/dev/market/partner-api/doc/ru/
"""
import os
import webbrowser
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

load_dotenv()

# Порт для локального сервера
PORT = 8080

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик OAuth callback"""
    
    def do_GET(self):
        """Обработка GET запроса с кодом авторизации"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if 'code' in query_params:
            auth_code = query_params['code'][0]
            self.server.auth_code = auth_code
            
            # Отправляем HTML ответ
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Авторизация успешна</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        text-align: center;
                    }
                    h1 { color: #4CAF50; }
                    p { color: #666; font-size: 16px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Авторизация успешна!</h1>
                    <p>Код авторизации получен.</p>
                    <p>Вы можете закрыть это окно.</p>
                </div>
            </body>
            </html>
            """
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        else:
            # Ошибка
            error = query_params.get('error', ['Неизвестная ошибка'])[0]
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Ошибка авторизации</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        text-align: center;
                    }}
                    h1 {{ color: #f44336; }}
                    p {{ color: #666; font-size: 16px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Ошибка авторизации</h1>
                    <p>{error}</p>
                </div>
            </body>
            </html>
            """
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Отключаем логирование запросов"""
        pass


def get_oauth_token_interactive(client_id: str, client_secret: str) -> str:
    """Интерактивное получение OAuth токена"""
    print("\n" + "=" * 80)
    print("Интерактивное получение OAuth токена")
    print("=" * 80)
    
    # Формируем URL авторизации
    auth_url = (
        f"https://oauth.yandex.ru/authorize?"
        f"response_type=code&"
        f"client_id={client_id}"
    )
    
    print(f"\nШаг 1: Открываю браузер для авторизации...")
    print(f"URL: {auth_url}\n")
    
    # Открываем браузер
    webbrowser.open(auth_url)
    
    # Запускаем локальный сервер для получения callback
    print("Шаг 2: Ожидаю код авторизации...")
    print("После авторизации в браузере код будет получен автоматически.\n")
    
    with socketserver.TCPServer(("", PORT), OAuthCallbackHandler) as httpd:
        httpd.timeout = 300  # 5 минут таймаут
        httpd.handle_request()
        
        if hasattr(httpd, 'auth_code'):
            auth_code = httpd.auth_code
            print(f"✅ Код авторизации получен: {auth_code[:20]}...")
        else:
            print("❌ Код авторизации не получен. Попробуйте ручной способ.")
            return None
    
    # Обмениваем код на токен
    print("\nШаг 3: Обмениваю код на токен...")
    token_url = "https://oauth.yandex.ru/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if access_token:
            print(f"✅ Токен успешно получен!")
            return access_token
        else:
            print(f"❌ Ошибка: токен не найден в ответе")
            print(f"Ответ: {token_data}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при получении токена: {e}")
        return None


def get_oauth_token_manual(client_id: str, client_secret: str) -> str:
    """Ручное получение OAuth токена"""
    print("\n" + "=" * 80)
    print("Ручное получение OAuth токена")
    print("=" * 80)
    
    # Формируем URL авторизации
    auth_url = (
        f"https://oauth.yandex.ru/authorize?"
        f"response_type=code&"
        f"client_id={client_id}"
    )
    
    print(f"\nШаг 1: Откройте эту ссылку в браузере:")
    print(f"{auth_url}\n")
    
    print("Шаг 2: Авторизуйтесь и разрешите доступ")
    print("Шаг 3: После авторизации вас перенаправит на страницу с кодом")
    print("Шаг 4: Скопируйте код из параметра 'code' в URL\n")
    
    auth_code = input("Вставьте код авторизации: ").strip()
    
    if not auth_code:
        print("❌ Код не введен")
        return None
    
    # Обмениваем код на токен
    print("\nОбмен кода на токен...")
    token_url = "https://oauth.yandex.ru/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if access_token:
            print("✅ Токен успешно получен!")
            return access_token
        else:
            print(f"❌ Ошибка: токен не найден в ответе")
            print(f"Ответ: {token_data}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при получении токена: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Ответ сервера: {e.response.text}")
        return None


def save_token_to_env(token: str):
    """Сохранение токена в .env файл"""
    env_file = ".env"
    
    # Читаем существующий .env
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Обновляем токен
    env_vars['YANDEX_OAUTH_TOKEN'] = token
    
    # Записываем обратно
    with open(env_file, 'w', encoding='utf-8') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ Токен сохранен в {env_file}")


def main():
    """Основная функция"""
    print("=" * 80)
    print("Получение OAuth токена для Яндекс.Маркет API")
    print("=" * 80)
    print("\nПеред началом:")
    print("1. Создайте приложение на https://oauth.yandex.ru/")
    print("2. Получите Client ID и Client Secret")
    print("3. Настройте права доступа: market:partner-api")
    print("4. Укажите redirect URI (для интерактивного способа): http://localhost:8080")
    print()
    
    # Получаем Client ID и Client Secret
    client_id = input("Введите Client ID: ").strip()
    if not client_id:
        print("❌ Client ID не введен")
        return
    
    client_secret = input("Введите Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret не введен")
        return
    
    # Выбираем способ получения токена
    print("\nВыберите способ получения токена:")
    print("1. Интерактивный (автоматически откроет браузер)")
    print("2. Ручной (скопируете код вручную)")
    
    choice = input("Ваш выбор (1 или 2): ").strip()
    
    if choice == "1":
        token = get_oauth_token_interactive(client_id, client_secret)
    elif choice == "2":
        token = get_oauth_token_manual(client_id, client_secret)
    else:
        print("❌ Неверный выбор")
        return
    
    if not token:
        print("\n❌ Не удалось получить токен")
        return
    
    # Показываем токен
    print("\n" + "=" * 80)
    print("✅ ТОКЕН УСПЕШНО ПОЛУЧЕН!")
    print("=" * 80)
    print(f"\nAccess Token: {token[:30]}...")
    
    # Показываем срок действия
    try:
        response = requests.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {token}"},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Токен валиден")
    except:
        pass
    
    # Предлагаем сохранить в .env
    save = input("\nСохранить токен в .env файл? (да/нет): ").strip().lower()
    if save in ("да", "yes", "y", "д"):
        save_token_to_env(token)
        print("\n" + "=" * 80)
        print("Следующие шаги:")
        print("=" * 80)
        print("1. Токен сохранен в .env файл")
        print("2. Перезапустите сервер")
        print("3. Проверьте работу API")
    else:
        print("\nДобавьте в .env файл:")
        print(f"YANDEX_OAUTH_TOKEN={token}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

