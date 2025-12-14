# Установка Selenium для парсера Яндекс.Маркет

Selenium необходим для парсинга JavaScript-страниц Яндекс.Маркет. Без него парсер может не находить товары, так как контент загружается динамически.

## Шаг 1: Установка Python пакетов

Установите необходимые пакеты:

```bash
pip install selenium webdriver-manager
```

Или если используете requirements.txt:

```bash
pip install -r requirements.txt
```

## Шаг 2: Установка Google Chrome

Selenium использует Chrome для работы. Убедитесь, что Google Chrome установлен на вашей системе:

- **Windows**: Скачайте с [chrome.google.com](https://www.google.com/chrome/)
- **Linux**: 
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install -y google-chrome-stable
  
  # Или через snap
  sudo snap install chromium
  ```
- **macOS**: Скачайте с [chrome.google.com](https://www.google.com/chrome/) или используйте Homebrew:
  ```bash
  brew install --cask google-chrome
  ```

## Шаг 3: Настройка переменных окружения

Добавьте в файл `.env` в папке `python/`:

```env
USE_SELENIUM_FOR_PARSING=true
```

Или установите переменную окружения:

**Windows (PowerShell):**
```powershell
$env:USE_SELENIUM_FOR_PARSING="true"
```

**Windows (CMD):**
```cmd
set USE_SELENIUM_FOR_PARSING=true
```

**Linux/macOS:**
```bash
export USE_SELENIUM_FOR_PARSING=true
```

## Шаг 4: Проверка установки

После установки перезапустите сервер. В логах должно появиться:

```
✅ Яндекс.Маркет парсер инициализирован (с Selenium)
✅ Selenium WebDriver инициализирован (с автоматической установкой драйвера)
```

## Решение проблем

### Ошибка: "ChromeDriver not found"

**Решение 1**: Используйте webdriver-manager (рекомендуется)
```bash
pip install webdriver-manager
```

**Решение 2**: Установите ChromeDriver вручную
1. Скачайте ChromeDriver с [chromedriver.chromium.org](https://chromedriver.chromium.org/)
2. Убедитесь, что версия ChromeDriver соответствует версии Chrome
3. Добавьте ChromeDriver в PATH или поместите в папку проекта

### Ошибка: "Chrome binary not found"

Убедитесь, что Google Chrome установлен и доступен в PATH.

**Windows**: Chrome обычно устанавливается в `C:\Program Files\Google\Chrome\Application\chrome.exe`

**Linux**: Установите Chrome:
```bash
sudo apt-get install -y google-chrome-stable
```

### Ошибка: "selenium.common.exceptions.WebDriverException"

Проверьте:
1. Установлен ли Selenium: `pip show selenium`
2. Установлен ли Chrome
3. Совместимы ли версии Chrome и ChromeDriver

### Selenium работает медленно

Это нормально - Selenium запускает реальный браузер, что медленнее обычных HTTP-запросов. Для ускорения:
- Используйте headless режим (уже включен по умолчанию)
- Уменьшите таймауты ожидания элементов
- Используйте кэширование результатов

## Альтернативы

Если Selenium не работает, можно:
1. Использовать обычный парсинг (без Selenium) - но может не находить товары
2. Настроить Яндекс.Маркет Partner API (требует OAuth токен)
3. Использовать другие инструменты (Playwright, Puppeteer)

## Дополнительная информация

- [Документация Selenium](https://www.selenium.dev/documentation/)
- [WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager)
- [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads)

