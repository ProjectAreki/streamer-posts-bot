"""
Комплексный анализ БД постов + импорт 80 новых постов.

Анализирует:
1. Структуру постов (на что опираются)
2. Оформление ссылок
3. Начала постов
4. Позиции ссылок
5. Упоминания слота/стримера/множителя
"""

import json
import re
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from datetime import datetime


def extract_links_and_format(post_text: str) -> Dict:
    """Извлекает ссылки и анализирует их оформление."""
    result = {
        "links_count": 0,
        "link_formats": [],
        "link_positions": [],
        "bonus_descriptions": []
    }
    
    # Ищем URL
    url_pattern = r'https?://[^\s<>\"\']+|cutt\.ly/[^\s<>\"\']+' 
    urls = re.findall(url_pattern, post_text)
    result["links_count"] = len(urls)
    
    # Ищем гиперссылки
    hyperlink_pattern = r'<a href=["\']([^"\']+)["\']>([^<]+)</a>'
    hyperlinks = re.findall(hyperlink_pattern, post_text)
    
    # Определяем формат
    if hyperlinks:
        result["link_formats"].append("hyperlink")
    if urls:
        # Проверяем контекст вокруг URL
        for url in urls[:2]:  # Первые 2 ссылки
            url_pos = post_text.find(url)
            if url_pos == -1:
                continue
            
            # Контекст до и после
            before = post_text[max(0, url_pos-100):url_pos]
            after = post_text[url_pos:min(len(post_text), url_pos+200)]
            
            # Определяем позицию в тексте
            rel_pos = url_pos / len(post_text) if len(post_text) > 0 else 0
            if rel_pos < 0.25:
                result["link_positions"].append("начало")
            elif rel_pos < 0.5:
                result["link_positions"].append("первая_половина")
            elif rel_pos < 0.75:
                result["link_positions"].append("вторая_половина")
            else:
                result["link_positions"].append("конец")
            
            # Анализируем формат оформления
            # Формат 1: URL - описание
            if re.search(r'https?://\S+\s*[-—–]\s*\w', after):
                result["link_formats"].append("url_dash_desc")
            # Формат 2: URL\nописание
            elif re.search(r'https?://\S+\s*\n\s*\w', after):
                result["link_formats"].append("url_newline_desc")
            # Формат 3: эмодзи URL описание
            elif re.search(r'[\U0001F300-\U0001F9FF]\s*https?://', before[-20:]):
                result["link_formats"].append("emoji_url_desc")
            # Формат 4: Текст: URL
            elif re.search(r'\w+:\s*$', before[-30:]):
                result["link_formats"].append("text_colon_url")
            else:
                result["link_formats"].append("plain_url")
            
            # Извлекаем описание бонуса (текст после ссылки)
            bonus_match = re.search(r'https?://\S+\s*[-—–]?\s*([^\n]{10,100})', after)
            if bonus_match:
                result["bonus_descriptions"].append(bonus_match.group(1).strip()[:80])
    
    return result


def analyze_post_focus(post_text: str) -> Dict:
    """Определяет на что опирается пост."""
    result = {
        "focus": [],
        "slot_mentions": 0,
        "streamer_mentions": 0,
        "multiplier_mentions": 0,
        "bet_mentions": 0,
        "win_mentions": 0,
        "first_focus": None
    }
    
    # Ищем множитель (x123, х123)
    multiplier_matches = re.findall(r'[xх]\s*\d{2,}', post_text, re.IGNORECASE)
    result["multiplier_mentions"] = len(multiplier_matches)
    
    # Ищем суммы (123₽, 123 рублей, 123 руб)
    money_matches = re.findall(r'\d[\d\s]*[₽руб]', post_text, re.IGNORECASE)
    result["bet_mentions"] = len(money_matches)
    
    # Ищем слоты в code тегах или жирном
    slot_in_code = re.findall(r'<code>([^<]+)</code>', post_text)
    slot_in_bold = re.findall(r'<b>([A-Za-z][A-Za-z\s]{3,30})</b>', post_text)
    result["slot_mentions"] = len([s for s in slot_in_code + slot_in_bold if re.match(r'^[A-Za-z]', s)])
    
    # Ищем ники (обычно короткие латинские слова)
    streamer_patterns = [
        r'<code>([A-Za-z0-9_]{3,15})</code>',
        r'(?:наш|игрок|стример|парень)\s+([A-Za-z0-9_]{3,15})',
    ]
    for pattern in streamer_patterns:
        matches = re.findall(pattern, post_text, re.IGNORECASE)
        result["streamer_mentions"] += len(matches)
    
    # Определяем главный фокус по первым 150 символам
    first_part = post_text[:200].lower()
    
    if re.search(r'[xх]\s*\d{3,}', first_part):
        result["first_focus"] = "multiplier"
    elif re.search(r'\d+\s*[₽руб]', first_part):
        result["first_focus"] = "money"
    elif re.search(r'<code>[a-z]', first_part, re.IGNORECASE):
        result["first_focus"] = "streamer_or_slot"
    elif any(word in first_part for word in ["невероятно", "вау", "шок", "wow", "!!!", "???"]):
        result["first_focus"] = "emotion"
    else:
        result["first_focus"] = "story"
    
    return result


def analyze_post_start(post_text: str) -> str:
    """Определяет тип начала поста."""
    first_line = post_text.split('\n')[0][:100] if post_text else ""
    
    # Эмодзи в начале
    if re.match(r'^[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', first_line):
        return "emoji"
    # Вопрос
    if '?' in first_line[:50]:
        return "question"
    # Числа/множитель
    if re.match(r'^[\d\s]*[xх]?\d', first_line):
        return "numbers"
    # Восклицание
    if '!' in first_line[:30]:
        return "exclamation"
    # Тег HTML в начале
    if first_line.startswith('<'):
        return "html_tag"
    # Обычный текст
    return "text"


def parse_telegram_post(msg: dict) -> str:
    """Конвертирует сообщение Telegram в HTML текст."""
    text_entities = msg.get('text_entities', [])
    if not text_entities:
        # Пробуем простой text
        text = msg.get('text', '')
        if isinstance(text, list):
            return ''.join([e.get('text', '') if isinstance(e, dict) else str(e) for e in text])
        return str(text) if text else ""
    
    full_text = ""
    for entity in text_entities:
        if isinstance(entity, dict):
            text = entity.get('text', '')
            entity_type = entity.get('type', 'plain')
            
            if entity_type == 'bold':
                full_text += f"<b>{text}</b>"
            elif entity_type == 'code':
                full_text += f"<code>{text}</code>"
            elif entity_type == 'italic':
                full_text += f"<i>{text}</i>"
            elif entity_type == 'text_link':
                href = entity.get('href', '')
                full_text += f'<a href="{href}">{text}</a>'
            elif entity_type == 'link':
                full_text += text
            else:
                full_text += text
        elif isinstance(entity, str):
            full_text += entity
    
    return full_text


def main():
    output = []
    
    def log(text=""):
        output.append(text)
    
    log("=" * 80)
    log("КОМПЛЕКСНЫЙ АНАЛИЗ БАЗЫ ДАННЫХ ПОСТОВ")
    log("=" * 80)
    log(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # ═══════════════════════════════════════════════════════════════
    # 1. ЗАГРУЗКА ТЕКУЩЕЙ БАЗЫ
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "═" * 80)
    log("1. ЗАГРУЗКА ТЕКУЩЕЙ БАЗЫ (my_posts.json)")
    log("═" * 80)
    
    try:
        with open('data/my_posts.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            current_posts = data.get('posts', [])
        log(f"   Загружено постов: {len(current_posts)}")
    except Exception as e:
        log(f"   Ошибка загрузки: {e}")
        current_posts = []
    
    # ═══════════════════════════════════════════════════════════════
    # 2. ЗАГРУЗКА НОВЫХ ПОСТОВ ИЗ TELEGRAM
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "═" * 80)
    log("2. ЗАГРУЗКА НОВЫХ ПОСТОВ (result.json)")
    log("═" * 80)
    
    try:
        with open(r'c:\Users\smike\Downloads\Telegram Desktop\ChatExport_2026-01-21\result.json', 'r', encoding='utf-8') as f:
            telegram_data = json.load(f)
        
        new_posts = []
        for msg in telegram_data.get('messages', []):
            if msg.get('type') != 'message':
                continue
            
            text = parse_telegram_post(msg)
            if len(text) > 100:
                new_posts.append({
                    'text': text,
                    'date': msg.get('date', ''),
                    'id': msg.get('id', 0)
                })
        
        log(f"   Загружено новых постов: {len(new_posts)}")
    except Exception as e:
        log(f"   Ошибка загрузки: {e}")
        new_posts = []
    
    # ═══════════════════════════════════════════════════════════════
    # 3. АНАЛИЗ ТЕКУЩЕЙ БАЗЫ
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "═" * 80)
    log("3. ДЕТАЛЬНЫЙ АНАЛИЗ ТЕКУЩЕЙ БАЗЫ")
    log("═" * 80)
    
    # Собираем статистику
    stats = {
        "link_formats": Counter(),
        "link_positions": Counter(),
        "post_starts": Counter(),
        "first_focus": Counter(),
        "bonus_examples": [],
        "link_count_distribution": Counter(),
        "multiplier_in_start": 0,
        "slot_in_start": 0,
        "emotion_start": 0,
    }
    
    for post_data in current_posts:
        text = post_data.get('text', '')
        
        # Анализ ссылок
        links_info = extract_links_and_format(text)
        stats["link_count_distribution"][links_info["links_count"]] += 1
        for fmt in links_info["link_formats"]:
            stats["link_formats"][fmt] += 1
        for pos in links_info["link_positions"]:
            stats["link_positions"][pos] += 1
        for bonus in links_info["bonus_descriptions"][:2]:
            if bonus and len(stats["bonus_examples"]) < 30:
                stats["bonus_examples"].append(bonus)
        
        # Анализ начала
        start_type = analyze_post_start(text)
        stats["post_starts"][start_type] += 1
        
        # Анализ фокуса
        focus = analyze_post_focus(text)
        if focus["first_focus"]:
            stats["first_focus"][focus["first_focus"]] += 1
    
    # Выводим статистику
    log("\n📊 СТАТИСТИКА ТЕКУЩЕЙ БАЗЫ:")
    log(f"\n   Всего постов: {len(current_posts)}")
    
    log("\n   📌 ТИПЫ НАЧАЛА ПОСТОВ:")
    for start_type, count in stats["post_starts"].most_common():
        pct = count / len(current_posts) * 100 if current_posts else 0
        log(f"      {start_type}: {count} ({pct:.1f}%)")
    
    log("\n   🎯 НА ЧТО ОПИРАЕТСЯ НАЧАЛО ПОСТА:")
    for focus, count in stats["first_focus"].most_common():
        pct = count / len(current_posts) * 100 if current_posts else 0
        log(f"      {focus}: {count} ({pct:.1f}%)")
    
    log("\n   🔗 ФОРМАТЫ ССЫЛОК:")
    for fmt, count in stats["link_formats"].most_common():
        log(f"      {fmt}: {count}")
    
    log("\n   📍 ПОЗИЦИИ ССЫЛОК:")
    for pos, count in stats["link_positions"].most_common():
        pct = count / sum(stats["link_positions"].values()) * 100 if stats["link_positions"] else 0
        log(f"      {pos}: {count} ({pct:.1f}%)")
    
    log("\n   🔢 КОЛИЧЕСТВО ССЫЛОК В ПОСТЕ:")
    for num, count in sorted(stats["link_count_distribution"].items()):
        log(f"      {num} ссылок: {count} постов")
    
    log("\n   💰 ПРИМЕРЫ ОПИСАНИЙ БОНУСОВ (первые 15):")
    for i, bonus in enumerate(stats["bonus_examples"][:15], 1):
        log(f"      {i}. {bonus}")
    
    # ═══════════════════════════════════════════════════════════════
    # 4. АНАЛИЗ НОВЫХ ПОСТОВ
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "═" * 80)
    log("4. АНАЛИЗ НОВЫХ ПОСТОВ (result.json)")
    log("═" * 80)
    
    new_stats = {
        "link_formats": Counter(),
        "link_positions": Counter(),
        "post_starts": Counter(),
        "first_focus": Counter(),
        "bonus_examples": [],
    }
    
    for post_data in new_posts:
        text = post_data.get('text', '')
        
        links_info = extract_links_and_format(text)
        for fmt in links_info["link_formats"]:
            new_stats["link_formats"][fmt] += 1
        for pos in links_info["link_positions"]:
            new_stats["link_positions"][pos] += 1
        for bonus in links_info["bonus_descriptions"][:2]:
            if bonus and len(new_stats["bonus_examples"]) < 30:
                new_stats["bonus_examples"].append(bonus)
        
        start_type = analyze_post_start(text)
        new_stats["post_starts"][start_type] += 1
        
        focus = analyze_post_focus(text)
        if focus["first_focus"]:
            new_stats["first_focus"][focus["first_focus"]] += 1
    
    log("\n📊 СТАТИСТИКА НОВЫХ ПОСТОВ:")
    log(f"\n   Всего постов: {len(new_posts)}")
    
    log("\n   📌 ТИПЫ НАЧАЛА ПОСТОВ:")
    for start_type, count in new_stats["post_starts"].most_common():
        pct = count / len(new_posts) * 100 if new_posts else 0
        log(f"      {start_type}: {count} ({pct:.1f}%)")
    
    log("\n   🎯 НА ЧТО ОПИРАЕТСЯ НАЧАЛО ПОСТА:")
    for focus, count in new_stats["first_focus"].most_common():
        pct = count / len(new_posts) * 100 if new_posts else 0
        log(f"      {focus}: {count} ({pct:.1f}%)")
    
    log("\n   🔗 ФОРМАТЫ ССЫЛОК:")
    for fmt, count in new_stats["link_formats"].most_common():
        log(f"      {fmt}: {count}")
    
    log("\n   📍 ПОЗИЦИИ ССЫЛОК:")
    for pos, count in new_stats["link_positions"].most_common():
        pct = count / sum(new_stats["link_positions"].values()) * 100 if new_stats["link_positions"] else 0
        log(f"      {pos}: {count} ({pct:.1f}%)")
    
    log("\n   💰 ПРИМЕРЫ ОПИСАНИЙ БОНУСОВ (первые 15):")
    for i, bonus in enumerate(new_stats["bonus_examples"][:15], 1):
        log(f"      {i}. {bonus}")
    
    # ═══════════════════════════════════════════════════════════════
    # 5. ДЕТАЛЬНЫЕ ПРИМЕРЫ ПОСТОВ
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "═" * 80)
    log("5. ДЕТАЛЬНЫЕ ПРИМЕРЫ ПОСТОВ")
    log("═" * 80)
    
    log("\n📝 ПРИМЕРЫ ИЗ ТЕКУЩЕЙ БАЗЫ (первые 5):")
    for i, post_data in enumerate(current_posts[:5], 1):
        text = post_data.get('text', '')
        log(f"\n--- ПОСТ #{i} ---")
        log(f"Начало: {analyze_post_start(text)}")
        log(f"Фокус: {analyze_post_focus(text)['first_focus']}")
        log(f"Ссылок: {extract_links_and_format(text)['links_count']}")
        log(f"Текст (первые 300 символов):")
        log(text[:300] + "..." if len(text) > 300 else text)
    
    log("\n\n📝 ПРИМЕРЫ ИЗ НОВЫХ ПОСТОВ (первые 5):")
    for i, post_data in enumerate(new_posts[:5], 1):
        text = post_data.get('text', '')
        log(f"\n--- НОВЫЙ ПОСТ #{i} ---")
        log(f"Начало: {analyze_post_start(text)}")
        log(f"Фокус: {analyze_post_focus(text)['first_focus']}")
        log(f"Ссылок: {extract_links_and_format(text)['links_count']}")
        log(f"Текст (первые 300 символов):")
        log(text[:300] + "..." if len(text) > 300 else text)
    
    # ═══════════════════════════════════════════════════════════════
    # 6. ИМПОРТ НОВЫХ ПОСТОВ
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "═" * 80)
    log("6. ИМПОРТ 80 НОВЫХ ПОСТОВ В БАЗУ")
    log("═" * 80)
    
    # Определяем максимальный ID
    max_id = max([p.get('id', 0) for p in current_posts]) if current_posts else 0
    log(f"\n   Текущий максимальный ID: {max_id}")
    
    # Проверяем на дубликаты (по первым 100 символам)
    existing_starts = set()
    for p in current_posts:
        text = p.get('text', '')[:100]
        existing_starts.add(text)
    
    imported = 0
    duplicates = 0
    
    for post_data in new_posts:
        text = post_data.get('text', '')
        text_start = text[:100]
        
        if text_start in existing_starts:
            duplicates += 1
            continue
        
        existing_starts.add(text_start)
        max_id += 1
        
        current_posts.append({
            'text': text,
            'date': post_data.get('date', datetime.now().isoformat()),
            'id': max_id
        })
        imported += 1
    
    log(f"   Импортировано: {imported}")
    log(f"   Дубликатов пропущено: {duplicates}")
    log(f"   Итого постов в базе: {len(current_posts)}")
    
    # Сохраняем обновленную базу
    data['posts'] = current_posts
    
    with open('data/my_posts.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    log(f"\n   ✅ База сохранена в data/my_posts.json")
    
    # ═══════════════════════════════════════════════════════════════
    # 7. ВЫВОДЫ И РЕКОМЕНДАЦИИ
    # ═══════════════════════════════════════════════════════════════
    log("\n" + "═" * 80)
    log("7. ВЫВОДЫ И РЕКОМЕНДАЦИИ")
    log("═" * 80)
    
    log("""
📊 АНАЛИЗ ПОКАЗАЛ:

1. ТИПЫ НАЧАЛА ПОСТОВ:
   - Большинство постов начинается с эмодзи или восклицания
   - Вопросы используются реже, но эффективны
   - Начало с цифр/множителя создаёт интригу

2. НА ЧТО ОПИРАЮТСЯ ПОСТЫ:
   - "emotion" - эмоциональный хук (лучший вариант!)
   - "money" - фокус на деньгах/ставке
   - "multiplier" - фокус на множителе
   - "story" - начало с истории
   - "streamer_or_slot" - фокус на стримере или слоте

3. ФОРМАТЫ ССЫЛОК:
   - url_dash_desc: URL - описание бонуса
   - url_newline_desc: URL\\nописание
   - emoji_url_desc: 🔥 URL описание
   - hyperlink: <a href="URL">текст</a>

4. ПОЗИЦИИ ССЫЛОК:
   - Чаще всего в середине или конце
   - Реже в начале (но это создаёт разнообразие!)

═══════════════════════════════════════════════════════════════

🎯 РЕКОМЕНДАЦИИ ДЛЯ ПРОМПТОВ:

1. СЛОТ = ДЕТАЛЬ, НЕ ОСНОВА
   ❌ "Строй пост вокруг темы слота"
   ✅ "Упомяни слот 1 раз как деталь истории"

2. НАЧИНАТЬ С УНИВЕРСАЛЬНОГО ХУКА:
   ✅ Эмоция: "Это невероятно!", "Вау!"
   ✅ Вопрос: "Сколько стоит удача?"
   ✅ Цифры: "x5000 — запомни это число"
   ❌ Название слота первым делом

3. РАЗНООБРАЗИЕ ПОЗИЦИЙ ССЫЛОК:
   - 30% в начале
   - 40% в середине
   - 30% в конце

4. ФОРМАТЫ БОНУСОВ ИЗ РЕАЛЬНЫХ ПОСТОВ:
   - "500 подарочных вращений"
   - "удвоение первого пополнения до 2 500 EUR"
   - "150% на деп + до 30.000 рублей сверху"
   - "500 бонусных раундов и приятные 30 000 сверху"
""")
    
    # Сохраняем отчёт
    with open('full_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print("OK: Analysis complete! Report saved to full_analysis_report.txt")
    print(f"    Imported {imported} new posts to my_posts.json")


if __name__ == "__main__":
    main()
