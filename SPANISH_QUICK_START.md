# 🎯 Быстрый старт - Испанский сценарий

## Что было сделано

✅ **Создано 2 новых файла:**
1. `src/ai_post_generator_es.py` - генератор на испанском
2. `src/handlers/spanish_posts_handlers.py` - обработчики на испанском

✅ **Обновлено 3 файла:**
1. `src/states/__init__.py` - добавлен SpanishPostsStates
2. `bot.py` - зарегистрирован испанский сценарий
3. Документация: `SPANISH_SCENARIO_IMPLEMENTATION.md`

## Как запустить

1. **Запустите бота:**
```bash
python bot.py
```

2. **Нажмите в меню:** `📹ES 100 posteos`

3. **Введите данные:**
   - 2 ссылки с бонусами
   - Выберите валюту: USD, EUR, CLP, MXN, ARS, COP
   - Загрузите видео или укажите канал
   - Загрузите картинки (опционально)

4. **Выберите AI модель** и запустите генерацию

## Ключевые отличия

| Параметр | Значение |
|----------|----------|
| 🌍 Язык | Español |
| 💰 Валюты | USD, EUR, CLP, MXN, ARS, COP, PEN, UYU |
| 🚫 Запрещено | Только "casino" |
| 👤 Стримеры | Необязательны (можно без) |
| 📝 Формат видео | `Slot_Bet_Win.mp4` |

## Формат имен видео файлов

**БЕЗ стримера (рекомендуется):**
```
Gates_of_Olympus_50USD_12500USD.mp4
Sweet_Bonanza_100EUR_25000EUR.mp4
```

**Со стримером (опционально):**
```
Pedro_Gates_of_Olympus_50_12500.mp4
```

## Поддерживаемые валюты

- 💵 **USD** - Dólares (Estados Unidos)
- 💶 **EUR** - Euros
- 🇨🇱 **CLP** - Pesos chilenos
- 🇲🇽 **MXN** - Pesos mexicanos
- 🇦🇷 **ARS** - Pesos argentinos
- 🇨🇴 **COP** - Pesos colombianos
- 🇵🇪 **PEN** - Soles peruanos
- 🇺🇾 **UYU** - Pesos uruguayos

## Пример поста

```
🔥 Victoria épica en Gates of Olympus

Un jugador arriesgó $50 y se llevó $12,500 
— ¡multiplicador x250! 💰

👉 https://site1.com
hasta 100 dólares y 100 giros gratis

👉 https://site2.com  
bono de bienvenida del 150%
```

## Что проверяет бот

✅ Текст на испанском (AI строго инструктирован)
✅ Обе ссылки присутствуют
❌ Слово "casino" (автоматически перегенерирует)

## Готово! 🎉

Испанский сценарий полностью интегрирован и готов к использованию.

---
📄 Полная документация: `SPANISH_SCENARIO_IMPLEMENTATION.md`
