import json
import re
from collections import Counter

with open('data/my_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

posts = data.get('posts', [])

output = []
output.append("="*100)
output.append("ГЛУБОКИЙ АНАЛИЗ 500 ПОСТОВ ИЗ БАЗЫ ДАННЫХ")
output.append("="*100)
output.append(f"\nВсего постов: {len(posts)}")
output.append("")

# ========================================
# 1. АНАЛИЗ: НА ЧТО ОПИРАЕТСЯ ПОСТ?
# ========================================

output.append("\n" + "="*100)
output.append("1. НА ЧТО ОПИРАЕТСЯ КАЖДЫЙ ПОСТ? (ГЛАВНЫЙ ФОКУС)")
output.append("="*100)

categories = {
    'slot_focus': 0,      # Пост про слот (слот - главный герой)
    'streamer_focus': 0,  # Пост про стримера (его действия/эмоции)
    'win_focus': 0,       # Пост про выигрыш (цифры/результат)
    'story_focus': 0,     # Пост-история (повествование)
    'mixed': 0,           # Смешанный фокус
}

# Паттерны для определения фокуса
slot_focus_patterns = [
    r'^[А-ЯA-Z][\w\s]+ (—|–) ',  # "Starlight Princess — ..."
    r'слот[е]? [\w\s]+ (решил|устроил|выдал|подарил)',  # "Слот решил..."
    r'механизм [\w\s]+ (решил|устроил)',  # "Механизм слота..."
    r'^(Vampy|Starlight|Zeus|Gates|Donut|Viking|Das|Sweet)',  # Начало с названия слота
]

streamer_focus_patterns = [
    r'(Manik|Dencho|Buratino|стример)',  # Упоминание стримера в начале
    r'(крутанул|запустил|зашёл|решил попробовать|поставил)',  # Действия стримера
    r'(его|ему|он) ',  # Местоимения про стримера
]

win_focus_patterns = [
    r'^\d+[\s₽руб]',  # Начало с цифр
    r'выигр[а-я]+ \d+',
    r'(занос|победа|успех) ',
]

for i, post in enumerate(posts):
    text = post.get('text', '')
    first_100 = text[:100].lower()
    
    slot_score = sum(1 for p in slot_focus_patterns if re.search(p, text[:150], re.IGNORECASE))
    streamer_score = sum(1 for p in streamer_focus_patterns if re.search(p, first_100, re.IGNORECASE))
    win_score = sum(1 for p in win_focus_patterns if re.search(p, first_100, re.IGNORECASE))
    
    if slot_score > streamer_score and slot_score > win_score:
        categories['slot_focus'] += 1
    elif streamer_score > slot_score and streamer_score > win_score:
        categories['streamer_focus'] += 1
    elif win_score > 0:
        categories['win_focus'] += 1
    elif slot_score > 0 and streamer_score > 0:
        categories['mixed'] += 1
    else:
        categories['story_focus'] += 1

output.append("\nРаспределение по фокусу:")
for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    pct = count / len(posts) * 100
    output.append(f"  {cat:20} : {count:4} постов ({pct:5.1f}%)")

# ========================================
# 2. ПОЗИЦИЯ СЛОТА В ПОСТЕ
# ========================================

output.append("\n" + "="*100)
output.append("2. ГДЕ УПОМИНАЕТСЯ СЛОТ В ПОСТЕ?")
output.append("="*100)

slot_positions = {
    'beginning': 0,  # В первых 100 символах
    'middle': 0,     # В середине
    'end': 0,        # В конце
    'not_mentioned': 0,  # Вообще не упоминается явно
}

for post in posts:
    text = post.get('text', '')
    
    # Ищем упоминание слота (название в верхнем регистре или слово "слот")
    slot_matches = list(re.finditer(r'([A-Z][a-z]+ [A-Z][a-z]+|слот[а-я]*)', text))
    
    if not slot_matches:
        slot_positions['not_mentioned'] += 1
    else:
        first_match_pos = slot_matches[0].start()
        text_length = len(text)
        
        if first_match_pos < 100:
            slot_positions['beginning'] += 1
        elif first_match_pos > text_length - 100:
            slot_positions['end'] += 1
        else:
            slot_positions['middle'] += 1

output.append("\nПозиция первого упоминания слота:")
for pos, count in sorted(slot_positions.items(), key=lambda x: x[1], reverse=True):
    pct = count / len(posts) * 100
    output.append(f"  {pos:20} : {count:4} ({pct:5.1f}%)")

# ========================================
# 3. НАЧАЛО ПОСТА (ПЕРВЫЕ СЛОВА)
# ========================================

output.append("\n" + "="*100)
output.append("3. КАК НАЧИНАЮТСЯ ПОСТЫ? (ПЕРВЫЕ 5 СЛОВ)")
output.append("="*100)

beginnings = []
for post in posts:
    text = post.get('text', '')
    # Убираем HTML теги
    clean_text = re.sub(r'<[^>]+>', '', text)
    words = clean_text.split()[:5]
    if words:
        beginning = ' '.join(words)
        beginnings.append(beginning)

beginning_counter = Counter(beginnings)
output.append("\nТоп-20 начал постов:")
for beginning, count in beginning_counter.most_common(20):
    output.append(f"  {count:3}x : {beginning[:80]}")

# ========================================
# 4. СТРУКТУРА ПОСТОВ
# ========================================

output.append("\n" + "="*100)
output.append("4. СТРУКТУРА ПОСТОВ")
output.append("="*100)

# Длина постов
lengths = [len(post.get('text', '')) for post in posts]
avg_length = sum(lengths) / len(lengths)
min_length = min(lengths)
max_length = max(lengths)

output.append(f"\nДлина постов:")
output.append(f"  Средняя: {avg_length:.0f} символов")
output.append(f"  Минимум: {min_length} символов")
output.append(f"  Максимум: {max_length} символов")

# Количество абзацев
paragraphs = [text.count('\n') + 1 for text in [p.get('text', '') for p in posts]]
avg_paragraphs = sum(paragraphs) / len(paragraphs)

output.append(f"\nСредднее количество абзацев: {avg_paragraphs:.1f}")

# Использование эмодзи
emoji_count = sum(1 for p in posts if re.search(r'[\U0001F300-\U0001F9FF]', p.get('text', '')))
output.append(f"\nПостов с эмодзи: {emoji_count} ({emoji_count/len(posts)*100:.1f}%)")

# ========================================
# 5. УПОМИНАНИЕ СТРИМЕРА
# ========================================

output.append("\n" + "="*100)
output.append("5. УПОМИНАНИЕ СТРИМЕРА")
output.append("="*100)

streamer_names = ['Manik', 'Dencho', 'Buratino', 'стример']
posts_with_streamer = 0

for post in posts:
    text = post.get('text', '')
    if any(name.lower() in text.lower() for name in streamer_names):
        posts_with_streamer += 1

output.append(f"\nПостов с упоминанием стримера: {posts_with_streamer} ({posts_with_streamer/len(posts)*100:.1f}%)")

# ========================================
# 6. ПРИМЕРЫ ПОСТОВ РАЗНЫХ ТИПОВ
# ========================================

output.append("\n" + "="*100)
output.append("6. ПРИМЕРЫ ПОСТОВ РАЗНЫХ ТИПОВ")
output.append("="*100)

# Находим примеры
examples = {
    'slot_first': [],
    'streamer_first': [],
    'win_first': [],
}

for post in posts[:100]:  # Первые 100 для быстроты
    text = post.get('text', '')
    first_50 = text[:50]
    
    if re.match(r'^[A-Z][a-z]+ [A-Z]', first_50):
        if len(examples['slot_first']) < 3:
            examples['slot_first'].append(text[:200])
    elif re.search(r'^(Manik|Dencho|стример|Он|Парень)', first_50, re.IGNORECASE):
        if len(examples['streamer_first']) < 3:
            examples['streamer_first'].append(text[:200])
    elif re.match(r'^\d+', first_50):
        if len(examples['win_first']) < 3:
            examples['win_first'].append(text[:200])

output.append("\nПРИМЕР 1: Посты, начинающиеся со СЛОТА:")
for i, ex in enumerate(examples['slot_first'], 1):
    clean = re.sub(r'<[^>]+>', '', ex)
    output.append(f"\n  {i}. {clean}...")

output.append("\n\nПРИМЕР 2: Посты, начинающиеся со СТРИМЕРА:")
for i, ex in enumerate(examples['streamer_first'], 1):
    clean = re.sub(r'<[^>]+>', '', ex)
    output.append(f"\n  {i}. {clean}...")

output.append("\n\nПРИМЕР 3: Посты, начинающиеся с ВЫИГРЫША:")
for i, ex in enumerate(examples['win_first'], 1):
    clean = re.sub(r'<[^>]+>', '', ex)
    output.append(f"\n  {i}. {clean}...")

# ========================================
# ВЫВОД И РЕКОМЕНДАЦИИ
# ========================================

output.append("\n\n" + "="*100)
output.append("ВЫВОДЫ И РЕКОМЕНДАЦИИ")
output.append("="*100)

output.append(f"""
ОСНОВНЫЕ НАХОДКИ:

1. ГЛАВНЫЙ ФОКУС ПОСТОВ:
   - Посты про СТРИМЕРА: {categories['streamer_focus']} ({categories['streamer_focus']/len(posts)*100:.1f}%)
   - Посты про СЛОТ: {categories['slot_focus']} ({categories['slot_focus']/len(posts)*100:.1f}%)
   - Посты про ВЫИГРЫШ: {categories['win_focus']} ({categories['win_focus']/len(posts)*100:.1f}%)
   
2. ПОЗИЦИЯ СЛОТА:
   - В начале: {slot_positions['beginning']} постов
   - В середине/конце: {slot_positions['middle'] + slot_positions['end']} постов
   - Не упоминается: {slot_positions['not_mentioned']} постов

3. СТРУКТУРА:
   - Средняя длина: {avg_length:.0f} символов
   - С эмодзи: {emoji_count/len(posts)*100:.1f}%
   - Упоминают стримера: {posts_with_streamer/len(posts)*100:.1f}%

РЕКОМЕНДАЦИЯ:
""")

if categories['slot_focus'] > categories['streamer_focus']:
    output.append("⚠️ ПРОБЛЕМА ПОДТВЕРЖДЕНА: Посты слишком часто фокусируются на слоте!")
    output.append("✅ НУЖНО: Переписать промпты 4 и 5 для баланса.")
else:
    output.append("✅ Большинство постов фокусируются на стримере/выигрыше.")
    output.append("⚠️ Но всё равно стоит уточнить промпты 4 и 5 для явности.")

# Сохраняем
with open('posts_structure_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("OK: Deep analysis completed!")
print(f"   Analyzed {len(posts)} posts")
print(f"   Results saved to posts_structure_analysis.txt")
