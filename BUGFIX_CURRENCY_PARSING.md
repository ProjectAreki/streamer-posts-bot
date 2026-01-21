# Исправление парсинга валют (евро, доллар, фунт)

**Дата:** 2026-01-21  
**Проблема:** Парсер не распознавал русские названия валют ("евро", "доллар", "фунт") и использовал рубли (RUB) по умолчанию вместо правильной валюты.

## Описание проблемы

При вводе данных вида:
```
ник maxzayka
слот Possessed
выигрыш 10000.00 евро
ставка 0.20 евро
Х50000
```

Парсер не распознавал слово "евро" и использовал рубли (RUB) по умолчанию, что приводило к неправильному отображению валюты в сгенерированных постах:
- Вместо "0.20 €" → "0.2 ₽"
- Вместо "10 000 EUR" → "10 000 RUB"

## Исправленные файлы

### 1. `src/caption_parser.py` (строки 232-256)

**ДО:**
```python
# 1. Ищем USD (явное указание)
if re.search(r'(?:выигрыш|ставка|win|bet)[:\s]*[\d\s,.]+\s*(?:USD|\$)', caption, re.IGNORECASE):
    result.currency = 'USD'
# 2. Ищем EUR (явное указание)
elif re.search(r'(?:выигрыш|ставка|win|bet)[:\s]*[\d\s,.]+\s*(?:EUR|€)', caption, re.IGNORECASE):
    result.currency = 'EUR'
# 3. Ищем GBP (явное указание)
elif re.search(r'(?:выигрыш|ставка|win|bet)[:\s]*[\d\s,.]+\s*(?:GBP|£)', caption, re.IGNORECASE):
    result.currency = 'GBP'
```

**ПОСЛЕ:**
```python
# 1. Ищем USD (явное указание включая "доллар")
if re.search(r'(?:выигрыш|ставка|win|bet)[:\s]*[\d\s,.]+\s*(?:USD|\$|доллар)', caption, re.IGNORECASE):
    result.currency = 'USD'
# 2. Ищем EUR (явное указание включая "евро")
elif re.search(r'(?:выигрыш|ставка|win|bet)[:\s]*[\d\s,.]+\s*(?:EUR|€|евро)', caption, re.IGNORECASE):
    result.currency = 'EUR'
# 3. Ищем GBP (явное указание включая "фунт")
elif re.search(r'(?:выигрыш|ставка|win|bet)[:\s]*[\d\s,.]+\s*(?:GBP|£|фунт)', caption, re.IGNORECASE):
    result.currency = 'GBP'
```

Также добавлена проверка русских названий валют во вторичном поиске (строки 251-256):
```python
if re.search(r'\b(?:USD|доллар)\b', caption, re.IGNORECASE):
    result.currency = 'USD'
elif re.search(r'\b(?:EUR|евро)\b', caption, re.IGNORECASE):
    result.currency = 'EUR'
elif re.search(r'\b(?:GBP|фунт)\b', caption, re.IGNORECASE):
    result.currency = 'GBP'
```

### 2. `src/handlers/streamer_posts_handlers.py` (строки 1141-1149)

**ДО:**
```python
currency = "RUB"  # По умолчанию
text_upper = message.text.upper()
if 'USD' in text_upper or '$' in message.text:
    currency = "USD"
elif 'EUR' in text_upper or '€' in message.text:
    currency = "EUR"
elif 'GBP' in text_upper or '£' in message.text:
    currency = "GBP"
```

**ПОСЛЕ:**
```python
currency = "RUB"  # По умолчанию
text_upper = message.text.upper()
text_lower = message.text.lower()
if 'USD' in text_upper or '$' in message.text or 'доллар' in text_lower:
    currency = "USD"
elif 'EUR' in text_upper or '€' in message.text or 'евро' in text_lower:
    currency = "EUR"
elif 'GBP' in text_upper or '£' in message.text or 'фунт' in text_lower:
    currency = "GBP"
```

## Тестирование

Проведено тестирование парсера с различными форматами:

✅ **Тест 1: Русское слово "евро"**
```
ник maxzayka
слот Possessed
выигрыш 10000.00 евро
ставка 0.20 евро
Х50000
```
Результат: `currency = "EUR"` ✓

✅ **Тест 2: Русское слово "доллар"**
```
ник testuser
слот Gates of Olympus
выигрыш 5000.00 доллар
ставка 1.00 доллар
Х5000
```
Результат: `currency = "USD"` ✓

✅ **Тест 3: Символ €**
```
ник player123
слот Sweet Bonanza
выигрыш 10000.00 €
ставка 0.20 €
Х50000
```
Результат: `currency = "EUR"` ✓

✅ **Тест 4: Русское слово "рубл"**
```
ник ruuser
слот Book of Dead
выигрыш 100000.00 рубл
ставка 200 рубл
Х500
```
Результат: `currency = "RUB"` ✓

## Поддерживаемые форматы валют

Парсер теперь распознает следующие форматы:

| Валюта | Коды | Символы | Русские слова |
|--------|------|---------|---------------|
| Рубли | RUB | ₽ | руб, рубл, рублей |
| Доллары | USD | $ | доллар, долларов |
| Евро | EUR | € | евро |
| Фунты | GBP | £ | фунт, фунтов |

## Влияние на систему

Исправление затрагивает:
1. ✅ Парсинг caption (подписей к видео)
2. ✅ Ручной ввод данных через бота
3. ✅ Генерацию постов (правильная валюта используется в промптах)
4. ✅ Отображение валюты в финальных постах

## Статус

✅ **Исправлено и протестировано**

Все изменения внесены и проверены. Парсер теперь корректно определяет валюту из русских слов.
