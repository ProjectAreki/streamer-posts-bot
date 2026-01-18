# 🐛 Bug Fix Report #2 - Telethon Client Not Initialized

## Проблема
```
❌ Telethon клиент не инициализирован
Please enter your phone (or bot token): EOF when reading a line
'NoneType' object has no attribute 'get_entity'
```

## Причина
`TelethonClientManager` в `src/telethon_manager.py` использовал **интерактивную авторизацию**:
```python
await client.start()  # ❌ Требует ввода телефона
```

Это вызывало ошибку в неинтерактивном режиме (systemd service).

## Решение

### Коммит: `4eda8bc`
**Файл:** `src/telethon_manager.py`

**Изменение 1:** Неинтерактивная авторизация (строка 119)

```python
# Было:
await client.start()

# Стало:
# Подключаемся без интерактивной авторизации
await client.connect()

# Проверяем авторизацию
if not await client.is_user_authorized():
    self.logger.warning(
        f"Telethon аккаунт #{idx} не авторизован", 
        session=session_name
    )
    await client.disconnect()
    continue
```

**Изменение 2:** Путь к сессии (строка 42-64)

```python
def _select_session_name(self) -> str:
    candidates = []
    # Проверяем сессию нового бота
    candidates.append("data/streamer_bot")  # ⭐ Добавлен приоритет
    # Из известных ранее
    candidates.extend([
        "chat_scanner_session",
        "content_extractor_session",
        "working_bot_session",
    ])
    for name in candidates:
        session_file = Path(f"{name}.session")
        if session_file.exists():
            self.logger.info("Используем существующую Telethon сессию", session=str(session_file))
            return name
    # Фолбэк
    return "data/streamer_bot"  # ⭐ Изменен дефолт
```

## Результат

### До исправления:
```
Please enter your phone (or bot token): 
ERROR | Ошибка инициализации Telethon общего клиента | error=EOF when reading a line
WARNING | Не удалось получить название канала: 'NoneType' object has no attribute 'get_entity'
```

### После исправления:
```
✅ Бот инициализирован
🚀 Запуск бота...
✅ Telethon клиент запущен
✅ Используем существующую Telethon сессию | session=data/streamer_bot.session
```

## Проверка

```bash
ssh root@142.93.227.232 "systemctl status streamer-posts-bot.service"
```

**Результат:**
```
● streamer-posts-bot.service - Streamer Posts Bot (Standalone)
     Active: active (running)
   Main PID: 4115497
     Memory: 108.3M
```

**Ошибок:** 0  
**Telethon:** ✅ Инициализирован  
**Сессия:** ✅ data/streamer_bot.session

## Связанные исправления

Это второе исправление после:
1. **Bug Fix #1** (коммит `994da5c`): Исправлен импорт `ConfigManager`
2. **Bug Fix #2** (коммит `4eda8bc`): Исправлена инициализация Telethon

## Деплой

1. ✅ Исправлена логика авторизации
2. ✅ Добавлен путь к сессии `data/`
3. ✅ Коммит в GitHub
4. ✅ Pull на сервере
5. ✅ Перезапуск сервиса
6. ✅ Проверка логов
7. ✅ Бот работает без ошибок

## Время исправления

**Обнаружено:** 2026-01-17 21:10  
**Исправлено:** 2026-01-17 21:11  
**Время:** ~1 минута

---

**Статус:** ✅ Исправлено и развернуто  
**Коммит:** 4eda8bc  
**Файл:** src/telethon_manager.py  
**Бот:** ✅ Готов к работе
