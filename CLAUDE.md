# Streamer Posts Bot — Инструкции для AI

## Проект

Telegram бот для генерации уникальных постов про выигрыши в слотах.
4 языковых сценария: русский, испанский, итальянский, французский.
Каждый сценарий: 80 видео-постов + 20 постов с картинками.

## Стек

- Python 3.9+, aiogram 3.x, telethon 1.34+
- OpenRouter API (15+ AI моделей через openai SDK)
- asyncio, FSM (aiogram.fsm)

## Ключевые файлы

| Файл | Описание |
|------|----------|
| `bot.py` | Главный файл, запуск бота |
| `src/ai_post_generator.py` | AI генератор постов (русский) — ЭТАЛОН |
| `src/ai_post_generator_es.py` | AI генератор (испанский) |
| `src/ai_post_generator_it.py` | AI генератор (итальянский) |
| `src/ai_post_generator_fr.py` | AI генератор (французский) |
| `src/handlers/streamer_posts_handlers.py` | FSM обработчики (русский) |
| `src/handlers/spanish_posts_handlers.py` | FSM обработчики (испанский) |
| `src/handlers/french_posts_handlers.py` | FSM обработчики (французский) |
| `src/handlers/image_posts_handlers.py` | Обработчики для картинок |
| `src/bonus_generator.py` | Генератор вариаций бонусов |
| `src/chat_scanner.py` | Telethon клиент для каналов |
| `src/config_manager.py` | Управление конфигурацией |
| `data/number_formats_curated.json` | 80 шаблонов блоков цифр (русский) |
| `data/number_formats_italian.json` | 80 шаблонов блоков цифр (итальянский) |
| `data/number_formats_french.json` | 80 шаблонов блоков цифр (французский) |

## Сервер и деплой

### Быстрый деплой (одна команда)

```bash
ssh -i ~/.ssh/digitalocean_streamer root@142.93.227.232 "cd /root/streamer-posts-bot && git pull origin main && systemctl restart streamer-posts-bot.service"
```

### Параметры сервера

- **IP**: 142.93.227.232
- **User**: root
- **SSH ключ**: ~/.ssh/digitalocean_streamer
- **Путь проекта**: /root/streamer-posts-bot
- **Systemd сервис**: streamer-posts-bot.service
- **Git remote**: origin, ветка main
- **ОС**: Ubuntu 22.04 (DigitalOcean Droplet, 2GB RAM)

### Стандартный workflow: правка → коммит → деплой

```bash
# 1. Внести правки в код
# 2. Коммит и пуш
git add -A && git commit -m "описание" && git push

# 3. Деплой на сервер
ssh -i ~/.ssh/digitalocean_streamer root@142.93.227.232 "cd /root/streamer-posts-bot && git pull origin main && systemctl restart streamer-posts-bot.service"
```

### Проверка после деплоя

```bash
# Статус сервиса
ssh -i ~/.ssh/digitalocean_streamer root@142.93.227.232 "systemctl status streamer-posts-bot.service --no-pager"

# Последние логи
ssh -i ~/.ssh/digitalocean_streamer root@142.93.227.232 "tail -100 /root/streamer-posts-bot/logs/bot.log"

# Только ошибки
ssh -i ~/.ssh/digitalocean_streamer root@142.93.227.232 "grep -i error /root/streamer-posts-bot/logs/bot.log | tail -20"

# Проверка что все посты сгенерировались
ssh -i ~/.ssh/digitalocean_streamer root@142.93.227.232 "grep '✅ Пост #' /root/streamer-posts-bot/logs/bot.log | tail -20"

# Проверка обрезки длинных постов
ssh -i ~/.ssh/digitalocean_streamer root@142.93.227.232 "grep '✂️' /root/streamer-posts-bot/logs/bot.log | tail -10"
```

## Критические правила

### Языки

- Русский сценарий → весь AI-контент на русском
- Испанский сценарий → весь AI-контент на испанском (без ¡ и ¿ в итальянском!)
- Итальянский сценарий → весь AI-контент строго на итальянском
- Французский сценарий → весь AI-контент строго на французском
- **ВАЖНО**: никакие русские/испанские/итальянские слова НЕ должны просачиваться в другие генераторы
- UI бота (кнопки, сообщения пользователю) — всегда на русском

### Telegram лимиты

- Caption для медиа: максимум **1024 символа**
- Генератор целится в 600-900 символов
- Retry-логика: допустимый диапазон 500-1000
- Жёсткий trim при >1020 символов → `_smart_trim_text(text, 1000)`
- Ссылки и описания бонусов НИКОГДА не обрезаются

### Итальянский сценарий (ai_post_generator_it.py)

- Только 1 ссылка и 1 бонус (в отличие от русского — 2 ссылки)
- Стримеров НЕТ в данных — только Puntata/Vincita/Slot
- Валюта: EUR (не RUB)
- "euro" не склоняется (всегда "euro", не "euros")
- `_filter_non_russian` НЕ используется

### Французский сценарий (ai_post_generator_fr.py)

- Только 1 ссылка и 1 бонус (как в итальянском)
- Стримеров НЕТ в данных — только Mise/Gain/Slot
- Валюта: EUR (euro → euros во французском)
- AI-пул описаний бонусов (портировано из русского сценария)
- Стратегии размещения ссылок — ссылка "бегает" по тексту (6 позиций)
- 20 категорий форматов ссылок с французскими CTA
- `_filter_non_russian` НЕ используется

### Архитектура для новых языков

При добавлении нового языка:
1. Скопировать `ai_post_generator_es.py` → `ai_post_generator_XX.py`
2. Скопировать `spanish_posts_handlers.py` → `XX_posts_handlers.py`
3. Создать `data/number_formats_XX.json` (80 шаблонов)
4. Перевести ВСЕ промпты, water_phrases, length_notes
5. Зарегистрировать роутер в `bot.py`

## Частые проблемы

| Проблема | Причина | Решение |
|----------|---------|---------|
| "caption is too long" | Пост > 1024 символов | Проверить retry-логику и `_smart_trim_text` |
| Бот зависает на N/80 | Ошибки публикации | Проверить логи: `grep ERROR logs/bot.log` |
| JSON parsing error | AI вернул невалидный JSON | `repair_json` и `try_fix_truncated` в генераторе |
| Английские фразы в тексте | AI игнорирует промпт | Проверка `english_phrases` + регенерация |
| Ссылка пропала | AI не включил URL | Проверка `url1_present` → регенерация |

## Конфигурация

Обязательные переменные в `.env`:
- `TELEGRAM_BOT_TOKEN` — от @BotFather
- `TELEGRAM_API_ID` — с my.telegram.org
- `TELEGRAM_API_HASH` — с my.telegram.org
- `OPENROUTER_API_KEY` — sk-or-v1-...

## Git правила

- `.env`, `*.session`, `logs/*.log` — НИКОГДА не коммитить
- `CLAUDE.md` — коммитится (не содержит секретов)
- Коммиты на русском языке
- Формат: `fix: описание` / `feat: описание` / `refactor: описание`
