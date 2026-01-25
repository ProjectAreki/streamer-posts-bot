import json
import re

with open('data/my_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

posts = data.get('posts', [])

print(f"Всего постов в базе: {len(posts)}")
print()

# Подсчёт по диапазонам
ranges = [
    (0, 100, "Посты 0-100"),
    (100, 200, "Посты 100-200"),
    (200, 300, "Посты 200-300"),
    (300, 400, "Посты 300-400"),
    (400, 420, "Посты 400-420"),
    (420, 500, "Посты 420-500 (новые)"),
]

print("="*80)
print("РАСПРЕДЕЛЕНИЕ ГИПЕРССЫЛОК ПО ДИАПАЗОНАМ:")
print("="*80)

total_with_href = 0

for start, end, label in ranges:
    count_href = 0
    count_plain = 0
    
    for i in range(start, min(end, len(posts))):
        text = posts[i].get('text', '')
        
        if '<a href' in text.lower():
            count_href += 1
            total_with_href += 1
        elif 'http' in text:
            count_plain += 1
    
    total_in_range = min(end, len(posts)) - start
    print(f"{label:25} | гиперссылки: {count_href:3} | plain URL: {count_plain:3} | всего: {total_in_range}")

print()
print(f"ИТОГО постов с гиперссылками: {total_with_href}")

# Покажем примеры с гиперссылками
print()
print("="*80)
print("ПРИМЕРЫ ПОСТОВ С ГИПЕРССЫЛКАМИ (первые 5):")
print("="*80)

count = 0
for i, p in enumerate(posts):
    text = p.get('text', '')
    if '<a href' in text.lower():
        count += 1
        if count <= 5:
            print(f"\nПост #{i} (ID: {p.get('id')}):")
            # Извлекаем гиперссылку
            match = re.search(r'<a href=[\'""]([^"\']+)[\'""]>([^<]+)</a>', text, re.IGNORECASE)
            if match:
                print(f"  Гиперссылка: <a href=\"{match.group(1)}\">{match.group(2)[:60]}</a>")
            # Показываем контекст
            href_pos = text.lower().find('<a href')
            if href_pos != -1:
                context = text[max(0, href_pos-50):min(len(text), href_pos+150)]
                print(f"  Контекст: {context[:100]}...")
