# 📦 Установка зависимостей

## Быстрая установка

```bash
cd python
pip install -r requirements.txt
```

## Для Windows (PowerShell)

```powershell
cd C:\mobilki\python
python -m pip install -r requirements.txt
```

## Для Windows (CMD)

```cmd
cd C:\mobilki\python
pip install -r requirements.txt
```

## Обновление pip перед установкой

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Установка с очисткой кэша (если есть проблемы)

```bash
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

## Проверка установки

После установки проверьте, что все пакеты установлены:

```bash
pip list
```

Или проверьте конкретные пакеты:

```bash
python -c "import fastapi; print('FastAPI OK')"
python -c "import pydantic; print('Pydantic OK')"
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "import redis; print('Redis OK')"
python -c "import selenium; print('Selenium OK')"
```

## Использование виртуального окружения (рекомендуется)

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows PowerShell)
venv\Scripts\Activate.ps1

# Активировать (Windows CMD)
venv\Scripts\activate.bat

# Установить зависимости
pip install -r requirements.txt
```

## Основные зависимости проекта

- **FastAPI** - веб-фреймворк
- **Pydantic** - валидация данных
- **SQLAlchemy** - ORM для работы с БД
- **PyMySQL** - драйвер MySQL
- **Redis** - кэширование
- **Selenium** - парсинг с JavaScript
- **BeautifulSoup4** - парсинг HTML
- **Requests** - HTTP запросы
- **Uvicorn** - ASGI сервер

