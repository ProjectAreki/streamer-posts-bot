import json
import re

with open('data/my_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

posts = data.get('posts', [])

output_lines = []
output_lines.append(f"Всего постов: {len(posts)}")
output_lines.append("")

# Паттерны для "текстовых ссылок" (действия-призывы)
link_text_patterns = [
    r'[➡️→👉🔥]\s*(Забрать|Получить|Активировать|Взять|Попробовать|Зарядиться)',
    r'^\s*(Забрать|Получить|Активировать|Взять) [^<\n]{10,80}$',
]

# Находим посты с такими паттернами
posts_with_text_links = []

for i, p in enumerate(posts[:420]):  # Проверяем старые 420 постов
    text = p.get('text', '')
    lines = text.split('\n')
    
    for line in lines:
        for pattern in link_text_patterns:
            if re.search(pattern, line, re.MULTILINE | re.IGNORECASE):
                if i not in [x[0] for x in posts_with_text_links]:
                    posts_with_text_links.append((i, line.strip()[:100]))
                break

output_lines.append("="*80)
output_lines.append(f"ПОСТЫ С ТЕКСТОВЫМИ ПРИЗЫВАМИ (возможные гиперссылки):")
output_lines.append("="*80)
output_lines.append(f"Найдено: {len(posts_with_text_links)} постов из 420")
output_lines.append("")

# Показываем примеры
output_lines.append("Примеры (первые 20):")
for i, (post_idx, line_text) in enumerate(posts_with_text_links[:20], 1):
    output_lines.append(f"{i}. Пост #{post_idx}: {line_text}")

# Проверяем - есть ли рядом URL?
output_lines.append("")
output_lines.append("="*80)
output_lines.append("АНАЛИЗ: Есть ли URL рядом с этими текстами?")
output_lines.append("="*80)

count_with_url_nearby = 0
count_without_url = 0

for post_idx, _ in posts_with_text_links[:50]:
    text = posts[post_idx].get('text', '')
    
    # Ищем призыв к действию
    for pattern in link_text_patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            # Ищем URL в окрестности (±150 символов)
            pos = match.start()
            context = text[max(0, pos-150):min(len(text), pos+150)]
            
            if 'http' in context or 'cutt.ly' in context:
                count_with_url_nearby += 1
            else:
                count_without_url += 1
            break

output_lines.append(f"С URL рядом: {count_with_url_nearby}")
output_lines.append(f"БЕЗ URL рядом: {count_without_url}")

output_lines.append("")
output_lines.append("="*80)
output_lines.append("ВЫВОД:")
output_lines.append("="*80)

if count_without_url > count_with_url_nearby:
    output_lines.append("""
ЭТО ТЕКСТОВЫЕ ССЫЛКИ БЕЗ РАЗМЕТКИ!

В старых постах призывы к действию написаны ТЕКСТОМ без <a href>.
Например:
  "➡️ Забрать стартовый пакет"
  
Но в Telegram это НЕ кликабельно!

В новых 80 постах это конвертировано в:
  <a href="URL">Забрать стартовый пакет</a>
  
Что КЛИКАБЕЛЬНО в Telegram!
""")
else:
    output_lines.append("""
ЭТО ОПИСАНИЯ РЯДОМ С URL!

Текст идёт рядом с обычными URL:
  https://cutt.ly/xxx
  Забрать стартовый пакет
  
Такой формат тоже работает, но это НЕ гиперссылка.
""")

# Сохраняем
with open('text_links_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"OK: Found {len(posts_with_text_links)} posts with text links")
print(f"    Saved to text_links_analysis.txt")
