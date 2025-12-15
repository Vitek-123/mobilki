# ScanPrice 📱💰

Мобильное приложение для Android для поиска, сравнения цен и отслеживания товаров из различных интернет-магазинов, включая Яндекс.Маркет.

![Android](https://img.shields.io/badge/Android-API%2024%2B-brightgreen)
![Kotlin](https://img.shields.io/badge/Kotlin-1.9-blue)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121.1-009688)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Содержание

- [Описание](#описание)
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [База данных](#база-данных)
- [Технологический стек](#технологический-стек)
- [Установка и запуск](#установка-и-запуск)
- [Конфигурация](#конфигурация)
- [API Документация](#api-документация)
- [Разработка](#разработка)

## 📖 Описание

ScanPrice - это мобильное приложение, которое помогает пользователям находить лучшие цены на интересующие товары. Приложение собирает информацию о товарах из различных источников, включая локальную базу данных и Яндекс.Маркет, и предоставляет удобный интерфейс для сравнения цен.

## ✨ Возможности

- 🔍 **Поиск товаров** - поиск по базе данных и Яндекс.Маркет
- 💰 **Сравнение цен** - просмотр цен одного товара в разных магазинах
- ⭐ **Избранное** - сохранение интересных товаров (требуется авторизация)
- 📜 **История просмотров** - отслеживание просмотренных товаров
- 🔔 **Уведомления о ценах** - отслеживание изменений цен на товары
- 👤 **Профиль пользователя** - регистрация, авторизация, управление аккаунтом
- 🌙 **Темная тема** - поддержка светлой и темной темы
- 🌍 **Локализация** - поддержка русского и английского языков

## 🏗️ Архитектура

Система построена по архитектуре клиент-сервер с использованием REST API.

### Общая архитектура

```mermaid
graph TB
    subgraph "Client Layer"
        A[Android App<br/>Kotlin]
    end
    
    subgraph "API Layer"
        B[FastAPI Server<br/>Python]
        C[JWT Authentication]
    end
    
    subgraph "Business Logic"
        D[Product Service]
        E[External Data Service]
        F[Yandex Market Parser]
        G[Yandex Market OAuth API]
    end
    
    subgraph "Data Layer"
        H[(MySQL<br/>Database)]
        I[(Redis<br/>Cache)]
    end
    
    subgraph "External Services"
        J[Yandex Market<br/>Web]
    end
    
    A -->|HTTP/HTTPS| B
    B --> C
    B --> D
    B --> E
    E --> F
    E --> G
    E --> I
    D --> H
    F --> J
    G --> J
    
    style A fill:#3DDC84
    style B fill:#009688
    style H fill:#4479A1
    style I fill:#DC382D
    style J fill:#FC3F1D
```

### Детальная архитектура сервера

```mermaid
graph LR
    subgraph "FastAPI Application"
        A[Main Router]
        B[Auth Routes]
        C[Product Routes]
        D[User Routes]
    end
    
    subgraph "Services"
        E[Product Service]
        F[Price Service]
        G[External Data Service]
    end
    
    subgraph "Data Providers"
        H[Database Repository]
        I[Yandex Parser]
        J[Yandex OAuth API]
    end
    
    subgraph "Infrastructure"
        K[SQLAlchemy ORM]
        L[Redis Client]
        M[JWT Manager]
    end
    
    A --> B
    A --> C
    A --> D
    C --> E
    C --> F
    C --> G
    E --> H
    F --> H
    G --> I
    G --> J
    H --> K
    G --> L
    B --> M
    
    style A fill:#009688
    style K fill:#4479A1
    style L fill:#DC382D
```

## 💾 База данных

### ER-диаграмма

```mermaid
erDiagram
    User ||--o{ Favorite : has
    User ||--o{ ViewHistory : has
    User ||--o{ PriceAlert : has
    User ||--o{ ShoppingList : has
    User ||--o{ Comparison : has
    User ||--o{ Review : writes
    User ||--o{ PasswordResetToken : has
    User ||--o{ Subscription : has
    
    Product ||--o{ Listing : has
    Product ||--o{ ViewHistory : viewed_in
    Product ||--o{ PriceAlert : tracked_in
    Product ||--o{ ShoppingListItem : in
    Product ||--o{ ComparisonProduct : compared_in
    Product ||--o{ Review : reviewed_in
    
    Shop ||--o{ Listing : offers
    
    Listing ||--o{ Price : has
    
    ShoppingList ||--o{ ShoppingListItem : contains
    
    Comparison ||--o{ ComparisonProduct : contains
    
    User {
        int id_user PK
        string login UK
        string password
        string email UK
    }
    
    Product {
        int id_product PK
        string title
        string image
        decimal price
    }
    
    Shop {
        int id_shop PK
        string name
    }
    
    Listing {
        int id_listing PK
        int product_id FK
        int shop_id FK
        text url
    }
    
    Price {
        int id_price PK
        int listing_id FK
        decimal price
        timestamp scraped_at
    }
    
    Favorite {
        int id_favorite PK
        int user_id FK
        string title
        decimal price
        string shop
        string url_photo
        string url_site
        timestamp added_at
    }
    
    ViewHistory {
        int id_view PK
        int user_id FK
        int product_id FK
        timestamp viewed_at
    }
    
    PriceAlert {
        int id_alert PK
        int user_id FK
        int product_id FK
        decimal target_price
        int is_active
        timestamp created_at
    }
    
    ShoppingList {
        int id_list PK
        int user_id FK
        string name
        decimal budget
        timestamp created_at
    }
    
    ShoppingListItem {
        int id_item PK
        int list_id FK
        int product_id FK
        int quantity
        int is_purchased
        timestamp added_at
    }
    
    Comparison {
        int id_comparison PK
        int user_id FK
        string name
        timestamp created_at
    }
    
    ComparisonProduct {
        int id_comparison_product PK
        int comparison_id FK
        int product_id FK
        timestamp added_at
    }
    
    Review {
        int id_review PK
        int user_id FK
        int product_id FK
        int rating
        text comment
        timestamp created_at
        timestamp updated_at
    }
    
    PasswordResetToken {
        int id_token PK
        int user_id FK
        string token UK
        timestamp expires_at
        int used
        timestamp created_at
    }
    
    Subscription {
        int id_subscription PK
        int user_id FK
        int is_premium
        timestamp started_at
        timestamp expires_at
        timestamp created_at
    }
```

### Структура основных таблиц

#### Пользователи и аутентификация
- **User** - пользователи системы
- **PasswordResetToken** - токены для сброса пароля
- **Subscription** - подписки пользователей

#### Товары и магазины
- **Product** - товары
- **Shop** - магазины
- **Listing** - предложения товаров в магазинах (связь Product ↔ Shop)
- **Price** - история цен на предложения

#### Пользовательские данные
- **Favorite** - избранное
- **ViewHistory** - история просмотров
- **PriceAlert** - уведомления о ценах
- **ShoppingList** - списки покупок
- **ShoppingListItem** - элементы списков покупок
- **Comparison** - сравнения товаров
- **ComparisonProduct** - товары в сравнениях
- **Review** - отзывы на товары

## 🛠️ Технологический стек

### Frontend (Android)

- **Язык**: Kotlin
- **Минимальный SDK**: API 24 (Android 7.0)
- **Целевой SDK**: API 35
- **Архитектура**: MVVM (Model-View-ViewModel)
- **Основные библиотеки**:
  - Retrofit 2.9.0 - HTTP клиент
  - Gson 2.10.1 - JSON парсинг
  - Glide 4.16.0 - загрузка изображений
  - AndroidX Lifecycle - ViewModel, LiveData
  - Material Design Components

### Backend (Python)

- **Язык**: Python 3.12
- **Фреймворк**: FastAPI 0.121.1
- **База данных**: MySQL
- **ORM**: SQLAlchemy 2.0.23
- **Кэширование**: Redis 5.0+
- **Аутентификация**: JWT (python-jose)
- **Хеширование паролей**: bcrypt 5.0.0
- **Парсинг**: 
  - BeautifulSoup4 4.13.5
  - lxml 4.9.0
  - Selenium 4.0+ (для JavaScript-контента)

## 🚀 Установка и запуск

### Требования

- Python 3.12+
- MySQL 5.7+
- Redis 5.0+ (опционально)
- Android Studio Arctic Fox+ (для разработки Android)
- JDK 11+

### Backend

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd mobilki
```

2. Установите зависимости:
```bash
cd python
pip install -r requirements.txt
```

3. Настройте переменные окружения (см. раздел [Конфигурация](#конфигурация))

4. Запустите сервер:
```bash
python main.py
```

Сервер будет доступен по адресу: `http://localhost:8000`

### Frontend

1. Откройте проект в Android Studio

2. Синхронизируйте Gradle зависимости

3. Настройте базовый URL API в `RetrofitClient.kt`:
```kotlin
private const val BASE_URL = "http://your-server-ip:8000"
```

4. Запустите приложение на эмуляторе или физическом устройстве

## ⚙️ Конфигурация

Создайте файл `.env` в папке `python/` со следующим содержимым:

```env
# Обязательные настройки
SECRET_KEY=your-secret-key-min-32-characters-long
DATABASE_URL=mysql://user:password@localhost:3306/database_name

# Опциональные настройки
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_ENABLED=true
CACHE_TTL=10800

# JWT настройки
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Яндекс.Маркет
USE_SELENIUM_FOR_PARSING=false
YANDEX_OAUTH_TOKEN=your-oauth-token
YANDEX_MARKET_CAMPAIGN_ID=your-campaign-id
```

### Получение OAuth токена Яндекс.Маркет

Для работы с API Яндекс.Маркет необходимо получить OAuth токен:

1. Зарегистрируйте приложение в [Yandex OAuth](https://oauth.yandex.ru/)
2. Получите код авторизации
3. Обменяйте код на токен (см. `python/get_oauth_token.py`)

Подробнее: `python/HOW_TO_GET_AUTH_CODE.md`

## 📚 API Документация

После запуска сервера документация API доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Основные эндпоинты

#### Авторизация
- `POST /add_user` - Регистрация пользователя
- `POST /login` - Вход в систему
- `POST /forgot-password` - Запрос на восстановление пароля
- `POST /reset-password` - Сброс пароля

#### Товары
- `GET /products` - Список товаров (с поиском)
- `GET /products/{id}` - Детальная информация о товаре
- `GET /products/popular` - Популярные товары

#### Избранное (требуется авторизация)
- `POST /favorites` - Добавить в избранное
- `GET /favorites` - Список избранного
- `DELETE /favorites/{id}` - Удалить из избранного

#### История просмотров (требуется авторизация)
- `POST /user/view-history` - Добавить в историю
- `GET /user/view-history` - Получить историю
- `DELETE /user/view-history` - Очистить историю

#### Уведомления о ценах (требуется авторизация)
- `POST /user/price-alerts` - Создать уведомление
- `GET /user/price-alerts` - Список уведомлений
- `DELETE /user/price-alerts/{id}` - Удалить уведомление

## 🔧 Разработка

### Структура проекта

```
mobilki/
├── app/                          # Android приложение
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/example/test/
│   │   │   │   ├── Main.kt              # Главный экран
│   │   │   │   ├── ProductDetailActivity.kt
│   │   │   │   ├── ProfileActivity.kt
│   │   │   │   ├── FavoritesActivity.kt
│   │   │   │   ├── Auth.kt              # Авторизация
│   │   │   │   ├── Registration.kt
│   │   │   │   └── ...
│   │   │   └── res/                     # Ресурсы
│   │   └── test/
│   └── build.gradle.kts
│
├── python/                        # Backend сервер
│   ├── main.py                    # FastAPI приложение
│   ├── models.py                  # SQLAlchemy модели
│   ├── schemas.py                 # Pydantic схемы
│   ├── database.py                # Подключение к БД
│   ├── external_data_service.py   # Сервис внешних данных
│   ├── yandex_market_parser.py    # Парсер Яндекс.Маркет
│   ├── services/                  # Бизнес-логика
│   ├── repositories/              # Репозитории данных
│   └── requirements.txt
│
├── ТЗ.md                          # Техническое задание
└── README.md                      # Этот файл
```

### Миграции базы данных

Для создания таблиц используйте SQLAlchemy:

```python
from database import engine
from models import Base

Base.metadata.create_all(bind=engine)
```

Или используйте миграционные скрипты в `python/migrations/`

### Логирование

Логирование настроено на уровне DEBUG. Логи выводятся в консоль с форматом:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## 📝 Лицензия

MIT License

## 👥 Авторы

Разработано для проекта ScanPrice

## 🔗 Полезные ссылки

- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Документация Android](https://developer.android.com/)
- [Документация SQLAlchemy](https://docs.sqlalchemy.org/)
- [Yandex Market Partner API](https://yandex.ru/dev/market/partner-api/doc/ru/)

---

**Версия API**: 0.10.4
