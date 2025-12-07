@echo off
echo ========================================
echo Исправление зависимостей для main.py
echo ========================================
echo.

echo [1/4] Переустановка pywin32...
pip uninstall pywin32 -y
pip install pywin32
echo.

echo [2/4] Запуск post-install скрипта pywin32...
python -m pywin32_postinstall -install
echo.

echo [3/4] Переустановка pydantic и pydantic_core...
pip uninstall pydantic pydantic_core -y
pip install pydantic==2.12.4 pydantic_core==2.41.5
echo.

echo [4/4] Проверка установки...
python -c "import pywin32; import pydantic; print('OK: Все зависимости установлены')"
echo.

echo ========================================
echo Готово! Теперь можно запустить main.py
echo ========================================
pause

