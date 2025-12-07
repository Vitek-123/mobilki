@echo off
echo ========================================
echo Исправление pydantic_core
echo ========================================
echo.

echo [1/3] Переустановка pydantic_core...
pip uninstall pydantic_core -y
pip install pydantic_core==2.41.5 --force-reinstall --no-cache-dir
echo.

echo [2/3] Проверка pydantic...
python -c "import pydantic; print('✅ pydantic OK')"
echo.

echo [3/3] Проверка FastAPI...
python -c "from fastapi import FastAPI; print('✅ FastAPI OK')"
echo.

echo ========================================
echo Готово! Теперь можно запустить main.py
echo ========================================
pause

