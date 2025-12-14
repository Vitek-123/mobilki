"""
Скрипт для обмена кода авторизации на OAuth токен
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def exchange_code_for_token(auth_code: str, client_id: str, client_secret: str) -> str:
    """Обмен кода авторизации на токен"""
    print("=" * 80)
    print("Обмен кода авторизации на OAuth токен")
    print("=" * 80)
    
    token_url = "https://oauth.yandex.ru/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    print(f"\nКод авторизации: {auth_code[:20]}...")
    print("Отправляю запрос на обмен...\n")
    
    try:
        response = requests.post(token_url, data=data, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                print("✅ Токен успешно получен!")
                print(f"\nAccess Token: {access_token[:50]}...")
                
                # Показываем информацию о токене
                expires_in = token_data.get("expires_in", "не указан")
                print(f"Срок действия: {expires_in} секунд")
                
                return access_token
            else:
                print("❌ Ошибка: токен не найден в ответе")
                print(f"Ответ: {token_data}")
                return None
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при получении токена: {e}")
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
    
    print(f"\n✅ Токен сохранен в {env_file}")


def main():
    """Основная функция"""
    print("=" * 80)
    print("Обмен кода авторизации на OAuth токен")
    print("=" * 80)
    print("\nУ вас есть код авторизации, который нужно обменять на токен.\n")
    
    # Получаем код авторизации
    auth_code = input("Введите код авторизации: ").strip()
    if not auth_code:
        print("❌ Код не введен")
        return
    
    # Получаем Client ID и Client Secret
    client_id = input("Введите Client ID: ").strip()
    if not client_id:
        print("❌ Client ID не введен")
        return
    
    client_secret = input("Введите Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret не введен")
        return
    
    # Обмениваем код на токен
    token = exchange_code_for_token(auth_code, client_id, client_secret)
    
    if not token:
        print("\n❌ Не удалось получить токен")
        return
    
    # Предлагаем сохранить в .env
    print("\n" + "=" * 80)
    save = input("Сохранить токен в .env файл? (да/нет): ").strip().lower()
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

