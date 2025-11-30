# Быстрое исправление кодировки ошибок

## Проблема
Ошибки отображаются как кракозябры (например: `   譥`) вместо нормального текста.

## Быстрое решение (3 шага)

### Шаг 1: Установите кодировку в PowerShell
Выполните в терминале Cursor/VS Code:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### Шаг 2: Перезапустите Gradle daemon
```powershell
cd C:\mobilki
.\gradlew.bat --stop
```

### Шаг 3: Запустите сборку заново
```powershell
.\gradlew.bat assembleDebug
```

## Для постоянного решения

### Вариант А: Постоянная настройка PowerShell профиля

1. Откройте профиль PowerShell:
   ```powershell
   notepad $PROFILE
   ```

2. Если файл не существует, создайте его:
   ```powershell
   New-Item -Path $PROFILE -Type File -Force
   notepad $PROFILE
   ```

3. Добавьте в файл:
   ```powershell
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   [Console]::InputEncoding = [System.Text.Encoding]::UTF8
   chcp 65001 | Out-Null
   ```

4. Перезапустите PowerShell

### Вариант Б: Используйте Gradle напрямую (рекомендуется)

Вместо Code Runner используйте Gradle напрямую в терминале:

```powershell
cd C:\mobilki
.\gradlew.bat assembleDebug
```

## Язык ошибок

**Английский** (по умолчанию): уже настроен в `gradle.properties`

**Русский**: измените в `gradle.properties`:
```
systemProp.user.language=ru
systemProp.user.country=RU
```

## Что уже настроено в проекте

✅ `gradle.properties` - кодировка UTF-8, английский язык  
✅ `.vscode/settings.json` - настройки терминала  
✅ `app/build.gradle.kts` - кодировка компиляции UTF-8  

## Важно

⚠️ **Code Runner не подходит для Android проектов!**  
Используйте Gradle напрямую через терминал:
- `.\gradlew.bat assembleDebug` - сборка
- `.\gradlew.bat installDebug` - установка на устройство

Подробная инструкция: см. `ENCODING_FIX.md`

