"""
Анализатор зависимости постов от названия слота.

Цель: Понять как посты используют название слота и как можно уменьшить эту зависимость.
"""

import json
import re
from typing import List, Dict
from collections import Counter


def extract_slot_from_post(post_text: str) -> str:
    """Извлекает название слота из поста (обычно в <b> или <code> тегах)."""
    # Паттерны для поиска слота
    patterns = [
        r'<b>([^<]+?)</b>',  # в жирном
        r'<code>([^<]+?)</code>',  # в моноширинном
        r'слот[:\s]+([A-Za-z0-9\s]+)',  # после слова "слот"
        r'игр[аеу][:\s]+([A-Za-z0-9\s]+)',  # после "игра/игре"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, post_text, re.IGNORECASE)
        if matches:
            # Ищем то что похоже на название слота (с заглавными буквами)
            for match in matches:
                if any(c.isupper() for c in match) and len(match) > 3:
                    return match.strip()
    return ""


def analyze_slot_mention_position(post_text: str, slot_name: str) -> Dict:
    """Анализирует где и как упоминается слот в посте."""
    if not slot_name:
        return {"found": False}
    
    # Ищем первое упоминание
    slot_pattern = re.escape(slot_name)
    match = re.search(slot_pattern, post_text, re.IGNORECASE)
    
    if not match:
        return {"found": False}
    
    position = match.start()
    total_length = len(post_text)
    relative_position = position / total_length
    
    # Определяем часть поста
    if relative_position < 0.2:
        section = "начало"
    elif relative_position < 0.5:
        section = "первая_треть"
    elif relative_position < 0.8:
        section = "середина"
    else:
        section = "конец"
    
    # Считаем сколько раз упоминается
    mentions_count = len(re.findall(slot_pattern, post_text, re.IGNORECASE))
    
    # Проверяем контекст упоминания (что до и после)
    context_before = post_text[max(0, position-50):position]
    context_after = post_text[position:min(len(post_text), position+50)]
    
    return {
        "found": True,
        "position": position,
        "relative_position": f"{relative_position:.1%}",
        "section": section,
        "mentions_count": mentions_count,
        "context_before": context_before[-30:] if len(context_before) > 30 else context_before,
        "context_after": context_after[:30] if len(context_after) > 30 else context_after
    }


def analyze_post_structure(post_text: str) -> Dict:
    """Анализирует структуру поста."""
    lines = post_text.split('\n')
    
    # Первая строка (обычно хук)
    first_line = lines[0] if lines else ""
    
    # Проверяем начало
    starts_with_emoji = bool(re.match(r'^[\U0001F300-\U0001F9FF]', first_line))
    starts_with_question = first_line.strip().startswith('?') or '?' in first_line[:50]
    starts_with_exclamation = '!' in first_line[:30]
    
    # Проверяем наличие элементов
    has_bold = '<b>' in post_text
    has_code = '<code>' in post_text
    has_italic = '<i>' in post_text
    
    return {
        "total_length": len(post_text),
        "lines_count": len([l for l in lines if l.strip()]),
        "first_line": first_line[:100],
        "starts_with_emoji": starts_with_emoji,
        "starts_with_question": starts_with_question,
        "starts_with_exclamation": starts_with_exclamation,
        "has_bold": has_bold,
        "has_code": has_code,
        "has_italic": has_italic
    }


def main():
    # Будем писать в файл вместо консоли (проблема с эмодзи в Windows)
    output_file = open('slot_dependency_analysis.txt', 'w', encoding='utf-8')
    
    def log(text=""):
        output_file.write(text + "\n")
        output_file.flush()  # Сразу записываем в файл
    
    log("="*70)
    log("АНАЛИЗ ЗАВИСИМОСТИ ПОСТОВ ОТ НАЗВАНИЯ СЛОТА")
    log("="*70)
    
    # Загружаем текущие посты
    log("\n1. Загружаем текущую базу my_posts.json...")
    try:
        with open('data/my_posts.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            current_posts = [p['text'] for p in data.get('posts', [])[:50]]  # Берём первые 50 для анализа
        log(f"   Загружено {len(current_posts)} постов для анализа")
    except Exception as e:
        log(f"   Ошибка: {e}")
        current_posts = []
    
    # Загружаем новые посты из Telegram
    log("\n2. Загружаем новые посты из result.json...")
    try:
        with open(r'c:\Users\smike\Downloads\Telegram Desktop\ChatExport_2026-01-21\result.json', 'r', encoding='utf-8') as f:
            telegram_data = json.load(f)
            
        # Извлекаем текст из text_entities
        new_posts = []
        for msg in telegram_data.get('messages', []):
            if msg.get('type') != 'message':
                continue
            
            text_entities = msg.get('text_entities', [])
            if not text_entities:
                continue
            
            # Собираем текст из entities
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
                    else:
                        full_text += text
                elif isinstance(entity, str):
                    full_text += entity
            
            if len(full_text) > 100:  # Только содержательные посты
                new_posts.append(full_text)
        
        log(f"   Загружено {len(new_posts)} новых постов")
    except Exception as e:
        log(f"   Ошибка: {e}")
        new_posts = []
    
    # Анализируем текущие посты
    log("\n" + "="*70)
    log("АНАЛИЗ ТЕКУЩИХ ПОСТОВ (my_posts.json)")
    log("="*70)
    
    slot_positions = []
    slot_sections = []
    slot_mentions = []
    post_starts = []
    
    for i, post in enumerate(current_posts[:10], 1):  # Детальный анализ первых 10
        slot = extract_slot_from_post(post)
        structure = analyze_post_structure(post)
        
        if slot:
            mention_info = analyze_slot_mention_position(post, slot)
            if mention_info['found']:
                slot_positions.append(mention_info['relative_position'])
                slot_sections.append(mention_info['section'])
                slot_mentions.append(mention_info['mentions_count'])
                
                log(f"\n--- Пост #{i} ---")
                log(f"Слот: {slot}")
                log(f"Позиция: {mention_info['section']} ({mention_info['relative_position']})")
                log(f"Упоминаний: {mention_info['mentions_count']}")
                log(f"Контекст: ...{mention_info['context_before']}[{slot}]{mention_info['context_after']}...")
                log(f"Первая строка: {structure['first_line']}")
        
        # Анализируем начало
        if structure['starts_with_emoji']:
            post_starts.append("emoji")
        elif structure['starts_with_question']:
            post_starts.append("question")
        elif structure['starts_with_exclamation']:
            post_starts.append("exclamation")
        else:
            post_starts.append("text")
    
    # Анализируем новые посты
    log("\n" + "="*70)
    log("АНАЛИЗ НОВЫХ ПОСТОВ (result.json)")
    log("="*70)
    
    new_slot_positions = []
    new_slot_sections = []
    new_slot_mentions = []
    new_post_starts = []
    
    for i, post in enumerate(new_posts[:10], 1):  # Детальный анализ первых 10
        slot = extract_slot_from_post(post)
        structure = analyze_post_structure(post)
        
        if slot:
            mention_info = analyze_slot_mention_position(post, slot)
            if mention_info['found']:
                new_slot_positions.append(mention_info['relative_position'])
                new_slot_sections.append(mention_info['section'])
                new_slot_mentions.append(mention_info['mentions_count'])
                
                log(f"\n--- Новый пост #{i} ---")
                log(f"Слот: {slot}")
                log(f"Позиция: {mention_info['section']} ({mention_info['relative_position']})")
                log(f"Упоминаний: {mention_info['mentions_count']}")
                log(f"Первая строка: {structure['first_line']}")
        
        if structure['starts_with_emoji']:
            new_post_starts.append("emoji")
        elif structure['starts_with_question']:
            new_post_starts.append("question")
        elif structure['starts_with_exclamation']:
            new_post_starts.append("exclamation")
        else:
            new_post_starts.append("text")
    
    # Статистика
    log("\n" + "="*70)
    log("СТАТИСТИКА")
    log("="*70)
    
    log("\nТЕКУЩИЕ ПОСТЫ:")
    if slot_sections:
        log(f"  Позиции слота: {Counter(slot_sections).most_common()}")
        log(f"  Среднее упоминаний: {sum(slot_mentions)/len(slot_mentions):.1f}")
    log(f"  Начало постов: {Counter(post_starts).most_common()}")
    
    log("\nНОВЫЕ ПОСТЫ:")
    if new_slot_sections:
        log(f"  Позиции слота: {Counter(new_slot_sections).most_common()}")
        log(f"  Среднее упоминаний: {sum(new_slot_mentions)/len(new_slot_mentions):.1f}")
    log(f"  Начало постов: {Counter(new_post_starts).most_common()}")
    
    log("\n" + "="*70)
    log("РЕКОМЕНДАЦИИ")
    log("="*70)
    log("""
Для уменьшения зависимости от слота нужно:

1. НАЧИНАТЬ С УНИВЕРСАЛЬНОГО ХУКА (не связанного со слотом):
   ✓ Эмоции: "Это просто невероятно!", "Не могу молчать!"
   ✓ Вопросы: "Когда удача улыбается?", "Как превратить 100р в 100к?"
   ✓ Истории: "Вчера случилось нечто...", "Один игрок..."
   
2. СЛОТ - КАК ДЕТАЛЬ, НЕ ОСНОВА:
   ✓ Упоминать 1 раз в середине: "...и случилось это в [слот]..."
   ✓ Можно вообще без названия: "один из автоматов", "эта игра"
   
3. ФОКУС НА ИСТОРИИ/ЭМОЦИИ/ЦИФРАХ:
   ✓ "x2000 - такой множитель увидишь не каждый день"
   ✓ "Ставка 100р → Выигрыш 200к - магия? Нет, математика удачи!"
   
4. ТЕМАТИЧЕСКАЯ ИНТЕРПРЕТАЦИЯ (если слот тематический):
   ✓ Gates of Olympus → боги, Олимп, божественные выигрыши
   ✓ Sugar Rush → сладость победы, конфетный дождь
   НО не делать пост ТОЛЬКО об этом!
""")
    
    log("\n==> Анализ сохранен в slot_dependency_analysis.txt")
    output_file.close()
    print("OK: Analysis saved to slot_dependency_analysis.txt")


if __name__ == "__main__":
    main()
