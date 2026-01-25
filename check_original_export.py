import json
import re

print("="*80)
print("ПРОВЕРКА ИСХОДНОЙ ВЫГРУЗКИ result.json")
print("="*80)

# Читаем исходный файл
with open(r'c:\Users\smike\Downloads\Telegram Desktop\ChatExport_2026-01-21\result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = [m for m in data.get('messages', []) if m.get('type') == 'message']
print(f"\nВсего сообщений: {len(messages)}")

# Анализируем text_entities
posts_with_text_link = 0
posts_with_link = 0
total_text_links = 0
total_plain_links = 0

examples_text_link = []
examples_plain_link = []

for i, msg in enumerate(messages):
    text_entities = msg.get('text_entities', [])
    
    has_text_link = False
    has_plain_link = False
    
    for entity in text_entities:
        if isinstance(entity, dict):
            entity_type = entity.get('type', '')
            
            if entity_type == 'text_link':
                total_text_links += 1
                has_text_link = True
                if len(examples_text_link) < 5:
                    text = entity.get('text', '')
                    href = entity.get('href', '')
                    examples_text_link.append(f"Msg {i}: text='{text}', href='{href}'")
            
            elif entity_type == 'link':
                total_plain_links += 1
                has_plain_link = True
                if len(examples_plain_link) < 5:
                    text = entity.get('text', '')
                    examples_plain_link.append(f"Msg {i}: '{text}'")
    
    if has_text_link:
        posts_with_text_link += 1
    if has_plain_link:
        posts_with_link += 1

print(f"\nСтатистика типов ссылок в ИСХОДНОЙ ВЫГРУЗКЕ:")
print(f"  Постов с text_link (гиперссылки): {posts_with_text_link}")
print(f"  Всего text_link: {total_text_links}")
print(f"\n  Постов с link (plain URL): {posts_with_link}")
print(f"  Всего link: {total_plain_links}")

print(f"\n{'='*80}")
print("ПРИМЕРЫ text_link (гиперссылки):")
print(f"{'='*80}")
for ex in examples_text_link:
    print(f"  {ex}")

print(f"\n{'='*80}")
print("ПРИМЕРЫ link (plain URL):")
print(f"{'='*80}")
for ex in examples_plain_link:
    print(f"  {ex}")

# Покажем как это выглядит в Telegram формате
print(f"\n{'='*80}")
print("КАК ЭТО ДОЛЖНО ВЫГЛЯДЕТЬ В HTML:")
print(f"{'='*80}")

# Берём первое сообщение с text_link
for msg in messages:
    text_entities = msg.get('text_entities', [])
    has_text_link = any(isinstance(e, dict) and e.get('type') == 'text_link' for e in text_entities)
    
    if has_text_link:
        print(f"\nПример сообщения ID {msg.get('id')}:")
        print("Telegram формат:")
        for entity in text_entities[:15]:  # Первые 15 entity
            if isinstance(entity, dict):
                entity_type = entity.get('type', '')
                text = entity.get('text', '')
                if entity_type == 'text_link':
                    href = entity.get('href', '')
                    print(f"  type={entity_type}, text='{text[:50]}', href='{href}'")
                elif entity_type == 'link':
                    print(f"  type={entity_type}, text='{text[:50]}'")
        break
