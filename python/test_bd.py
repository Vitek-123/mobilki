from sqlalchemy import create_engine, text

# Ваш код подключения
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/project_mobilki_aviasales"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

def test_connection():
    try:
        # Пробуем подключиться и выполнить простой запрос
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Подключение успешно! База данных отвечает.")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

# Проверяем
test_connection()