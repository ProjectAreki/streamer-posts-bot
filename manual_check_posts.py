import json

with open('data/my_posts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

posts = data.get('posts', [])

# Пишем в файл вместо print
output = []

output.append("="*80)
output.append("ПРОВЕРЯЕМ ПЕРВЫЕ 10 ПОСТОВ ВРУЧНУЮ")
output.append("="*80)

for i in range(min(10, len(posts))):
    post = posts[i]
    text = post.get('text', '')
    
    output.append(f"\n{'='*80}")
    output.append(f"ПОСТ #{i} (ID: {post.get('id')})")
    output.append(f"{'='*80}")
    
    # Показываем весь текст
    output.append(text)
    output.append("")
    
    # Анализируем
    has_href = '<a href' in text.lower()
    has_plain_url = 'http' in text
    
    output.append(f"Содержит <a href: {has_href}")
    output.append(f"Содержит http: {has_plain_url}")
    
    # Проверяем разные варианты написания
    variants = [
        '<a href=',
        '<a href="',
        "<a href='",
        'href=',
        '&lt;a href',  # HTML entities
    ]
    
    output.append("\nПроверка вариантов:")
    for variant in variants:
        if variant in text or variant.lower() in text.lower():
            output.append(f"  ✓ Найден: {variant}")

output.append("\n" + "="*80)
output.append("ПРОВЕРЯЕМ ПОСТЫ 100-105 (середина)")
output.append("="*80)

for i in range(100, min(105, len(posts))):
    post = posts[i]
    text = post.get('text', '')
    
    output.append(f"\n--- ПОСТ #{i} (ID: {post.get('id')}) ---")
    output.append(f"Длина: {len(text)} символов")
    output.append(f"Первые 200 символов:")
    output.append(text[:200])
    output.append("")
    
    has_href = '<a href' in text.lower()
    has_plain_url = 'http' in text
    output.append(f"<a href: {has_href}, http: {has_plain_url}")

# Сохраняем в файл
with open('manual_check_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("OK: Saved to manual_check_output.txt")
