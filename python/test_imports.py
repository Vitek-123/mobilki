#!/usr/bin/env python
"""Тестовый скрипт для проверки всех зависимостей"""
import sys

def test_imports():
    errors = []
    
    print("Проверка зависимостей...")
    print("-" * 50)
    
    # Основные зависимости
    try:
        import fastapi
        print("✅ FastAPI")
    except Exception as e:
        errors.append(f"❌ FastAPI: {e}")
        print(f"❌ FastAPI: {e}")
    
    try:
        import pydantic
        print("✅ Pydantic")
    except Exception as e:
        errors.append(f"❌ Pydantic: {e}")
        print(f"❌ Pydantic: {e}")
    
    try:
        import pydantic_core
        print("✅ Pydantic Core")
    except Exception as e:
        errors.append(f"❌ Pydantic Core: {e}")
        print(f"❌ Pydantic Core: {e}")
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy")
    except Exception as e:
        errors.append(f"❌ SQLAlchemy: {e}")
        print(f"❌ SQLAlchemy: {e}")
    
    try:
        import redis
        print("✅ Redis")
    except Exception as e:
        print(f"⚠️  Redis: {e} (опционально)")
    
    try:
        import selenium
        print("✅ Selenium")
    except Exception as e:
        print(f"⚠️  Selenium: {e} (опционально)")
    
    # pywin32 (только для Windows)
    try:
        import win32api
        print("✅ pywin32")
    except Exception as e:
        print(f"⚠️  pywin32: {e} (опционально, только для Windows)")
    
    print("-" * 50)
    
    if errors:
        print(f"\n❌ Найдено {len(errors)} ошибок:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ Все основные зависимости установлены!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)

