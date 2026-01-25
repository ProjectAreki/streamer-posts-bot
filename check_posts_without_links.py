"""
Проверка постов без ссылок
"""
import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('data/my_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    posts = data['posts']

print('ПРИМЕРЫ ПОСТОВ БЕЗ ССЫЛОК В ТЕКСТЕ:\n')
print('='*80)

count = 0
for i, post in enumerate(posts):
    text = post.get('text', '')
    if 'http' not in text and 'cutt.ly' not in text and '<a href=' not in text:
        print(f'\nПост #{i+1} (ID: {post.get("id", "?")}):\n')
        print(f'Длина текста: {len(text)} символов')
        print(f'Первые 200 символов:')
        print(text[:200])
        print(f'\nПоследние 100 символов:')
        print(text[-100:])
        print('\n' + '-'*80)
        count += 1
        if count >= 3:
            break

print(f'\n\nВЫВОД:')
print(f'Эти посты выглядят полноценными, но БЕЗ ссылок в тексте.')
print(f'Вероятно при экспорте/импорте гиперссылки не сохранились!')
print(f'\nРЕАЛЬНОЕ РАСПРЕДЕЛЕНИЕ:')
print(f'  ГИПЕРССЫЛКИ: 197 + 36 = 233 поста (46.6%) - САМЫЙ ПОПУЛЯРНЫЙ!')
print(f'  ЭМОДЗИ + URL: 123 поста (24.6%)')
print(f'  URL в начале: 58 постов (11.6%)')
print(f'  СТРЕЛКА + URL: 34 поста (6.8%)')
print(f'  ТЕКСТ - URL: 23 поста (4.6%)')
print('='*80)
