# Исправление проблемы с кодировкой ошибок

## Проблема
Ошибки компиляции отображаются в виде кракозябр (например: `   譥`) вместо нормального текста на русском или английском.

## Решение

### 1. Настройки в проекте (уже применены)

В файле `gradle.properties` добавлены настройки:
- `org.gradle.console=plain` - простой вывод без цветов
- `systemProp.file.encoding=UTF-8` - кодировка файлов UTF-8
- `systemProp.console.encoding=UTF-8` - кодировка консоли UTF-8
- `systemProp.user.language=en` - язык ошибок английский

### 2. Настройка PowerShell (для текущей сессии)

Выполните в PowerShell:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### 3. Постоянная настройка PowerShell

Откройте профиль PowerShell:
```powershell
notepad $PROFILE
```

Добавьте строки:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
```

Если файл не существует, создайте его:
```powershell
New-Item -Path $PROFILE -Type File -Force
notepad $PROFILE
```

### 4. Настройка VS Code/Cursor

1. Откройте настройки: `Ctrl + ,`
2. Найдите "encoding"
3. Установите "Files: Encoding" = `utf8`
4. Включите "Files: Auto Guess Encoding"

### 5. Для Code Runner расширения

**Важно**: Code Runner не подходит для Android проектов. Используйте Gradle напрямую:

```powershell
# Вместо запуска через Code Runner используйте:
.\gradlew.bat assembleDebug

# Или для запуска приложения:
.\gradlew.bat installDebug
```

### 6. Альтернатива: использовать Gradle через терминал

Откройте встроенный терминал в Cursor/VS Code (`Ctrl + ``) и выполните:

```powershell
# Сначала установите кодировку
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# Затем запустите сборку
cd C:\mobilki
.\gradlew.bat assembleDebug
```

### 7. Язык ошибок

По умолчанию теперь установлен английский язык (`user.language=en`). 

Для русского языка измените в `gradle.properties`:
```
systemProp.user.language=ru
systemProp.user.country=RU
```

**Примечание**: Некоторые сообщения об ошибках могут остаться на английском, так как они зависят от компилятора Kotlin.

## Проверка

После применения настроек перезапустите:
1. Cursor/VS Code
2. Gradle daemon (если запущен):
   ```powershell
   .\gradlew.bat --stop
   ```

Затем запустите сборку заново - ошибки должны отображаться корректно.

