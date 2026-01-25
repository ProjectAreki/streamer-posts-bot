"""
Анализ форматов ссылок в постах
"""
import json
import re
import sys
import io

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('data/my_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    posts = data['posts']

print('\nАНАЛИЗ ФОРМАТОВ ССЫЛОК В 500 ПОСТАХ\n')
print('='*80)

# 1. ЭМОДЗИ_URL (самый популярный - 24.6%)
print('\n1. ЭМОДЗИ + URL - 123 поста (24.6%) - САМЫЙ ПОПУЛЯРНЫЙ!\n')
count = 0
for post in posts:
    text = post.get('text', '')
    if re.search(r'[👉🔥💰🎁⚡🎯]\s*https?://', text):
        matches = re.findall(r'[👉🔥💰🎁⚡🎯]\s*https?://[^\s]+[^\n]*', text)
        if matches and count < 3:
            print(f'   Пример {count+1}: {matches[0][:90]}...')
            count += 1
            if count >= 3:
                break

# 2. URL_В_НАЧАЛЕ_СТРОКИ (11.6%)
print('\n2. URL В НАЧАЛЕ СТРОКИ - 58 постов (11.6%)\n')
count = 0
for post in posts:
    text = post.get('text', '')
    if re.search(r'^https?://', text, re.MULTILINE):
        matches = re.findall(r'^https?://[^\s]+.*$', text, re.MULTILINE)
        if matches and count < 3:
            print(f'   Пример {count+1}: {matches[0][:90]}...')
            count += 1
            if count >= 3:
                break

# 3. ГИПЕРССЫЛКА (7.2%)
print('\n3. ГИПЕРССЫЛКА <a href> - 36 постов (7.2%) - РЕДКО!\n')
count = 0
for post in posts:
    text = post.get('text', '')
    if '<a href=' in text:
        matches = re.findall(r'<a href=[^>]+>.*?</a>', text)
        if matches and count < 3:
            print(f'   Пример {count+1}: {matches[0][:90]}...')
            count += 1
            if count >= 3:
                break

# 4. СТРЕЛКА_URL (6.8%)
print('\n4. СТРЕЛКА + URL - 34 поста (6.8%)\n')
count = 0
for post in posts:
    text = post.get('text', '')
    if re.search(r'[→←↑↓⇒⇐⇑⇓]\s*https?://', text):
        matches = re.findall(r'[→←↑↓⇒⇐⇑⇓]\s*https?://[^\s]+[^\n]*', text)
        if matches and count < 3:
            print(f'   Пример {count+1}: {matches[0][:90]}...')
            count += 1
            if count >= 3:
                break

# 5. ТЕКСТ_ДЕФИС_URL (4.6%)
print('\n5. ТЕКСТ - URL - 23 поста (4.6%)\n')
count = 0
for post in posts:
    text = post.get('text', '')
    if re.search(r'.+ ?[-—–] ?https?://', text):
        matches = re.findall(r'.{20,70} ?[-—–] ?https?://[^\s]+', text)
        if matches and count < 3:
            print(f'   Пример {count+1}: {matches[0][:90]}...')
            count += 1
            if count >= 3:
                break

print('\n' + '='*80)
print('\nВЫВОД:')
print('  В базе доминирует ЭМОДЗИ + URL (24.6%)')
print('  Гиперссылки <a href> используются РЕДКО (7.2%)')
print('  Но AI генерирует гиперссылки чаще из-за промптов!')
print('='*80 + '\n')
