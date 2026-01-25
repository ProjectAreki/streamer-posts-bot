import json
import re

with open('data/my_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

posts = data.get('posts', [])
print(f'Всего постов: {len(posts)}')

# Ищем гиперссылки
hyperlink_count = 0
hyperlink_examples = []

for i, p in enumerate(posts):
    text = p.get('text', '')
    # Ищем <a href=
    if '<a href=' in text or '<a href="' in text:
        hyperlink_count += 1
        if len(hyperlink_examples) < 10:
            # Извлекаем пример
            match = re.search(r'<a href=[^>]+>[^<]+</a>', text)
            if match:
                hyperlink_examples.append(f'Post {i}: {match.group(0)[:150]}')

print(f'Постов с гиперссылками (<a href>): {hyperlink_count}')
print()
print('Примеры гиперссылок:')
for ex in hyperlink_examples:
    print(f'  {ex}')

# Проверим первые 20 постов детально
print()
print('=' * 60)
print('Первые 20 постов - детальный анализ ссылок:')
print('=' * 60)

for i, p in enumerate(posts[:20]):
    text = p.get('text', '')
    has_href = '<a href' in text
    has_plain_url = bool(re.search(r'https?://[^\s<>"\']+', text))
    
    # Считаем количество
    href_count = len(re.findall(r'<a href=', text))
    url_count = len(re.findall(r'https?://[^\s<>"\']+', text))
    
    print(f'  Post {i}: <a href>={href_count}, plain URLs={url_count}')

# Проверим посты 400-420 (новые)
print()
print('=' * 60)
print('Посты 415-425 (должны быть новые с гиперссылками):')
print('=' * 60)

for i, p in enumerate(posts[415:425], start=415):
    text = p.get('text', '')
    has_href = '<a href' in text
    href_count = len(re.findall(r'<a href=', text))
    url_count = len(re.findall(r'https?://[^\s<>"\']+', text))
    
    print(f'  Post {i}: <a href>={href_count}, plain URLs={url_count}')
    if has_href:
        match = re.search(r'<a href=[^>]+>[^<]+</a>', text)
        if match:
            print(f'    Example: {match.group(0)[:100]}')
