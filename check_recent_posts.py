"""
Быстрая проверка недавних постов

Показывает посты созданные за последний час
"""

import json
from datetime import datetime, timedelta

def check_recent_posts(minutes_back: int = 60):
    """Проверяет посты за последние N минут"""
    
    print(f"\n{'='*60}")
    print(f"ПРОВЕРКА НЕДАВНИХ ПОСТОВ")
    print(f"{'='*60}\n")
    
    # Загружаем посты
    try:
        with open('data/my_posts.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_posts = data.get('posts', [])
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить посты: {e}")
        return
    
    print(f"Всего постов в базе: {len(all_posts)}")
    
    # Анализируем последние посты
    cutoff_time = datetime.now() - timedelta(minutes=minutes_back)
    recent_posts = []
    
    for post in all_posts:
        try:
            post_date = datetime.fromisoformat(post['date'])
            if post_date >= cutoff_time:
                recent_posts.append(post)
        except:
            pass
    
    print(f"Постов за последние {minutes_back} минут: {len(recent_posts)}")
    
    if not recent_posts:
        print(f"\n[!] Не найдено постов за последние {minutes_back} минут")
        print(f"    Попробуйте увеличить период поиска")
        return
    
    # Группируем по времени
    from collections import defaultdict
    by_hour = defaultdict(list)
    
    for post in recent_posts:
        try:
            post_date = datetime.fromisoformat(post['date'])
            hour_key = post_date.strftime('%Y-%m-%d %H:00')
            by_hour[hour_key].append(post)
        except:
            pass
    
    print(f"\n{'='*60}")
    print(f"РАСПРЕДЕЛЕНИЕ ПО ВРЕМЕНИ")
    print(f"{'='*60}\n")
    
    for hour in sorted(by_hour.keys(), reverse=True):
        posts = by_hour[hour]
        print(f"{hour}: {len(posts)} постов")
    
    # Показываем последние 10 постов
    print(f"\n{'='*60}")
    print(f"ПОСЛЕДНИЕ 10 ПОСТОВ")
    print(f"{'='*60}\n")
    
    recent_sorted = sorted(recent_posts, key=lambda x: x.get('date', ''), reverse=True)
    
    for i, post in enumerate(recent_sorted[:10], 1):
        post_id = post.get('id', '?')
        post_date = post.get('date', '?')
        slot = post.get('slot', 'Неизвестно')
        text_preview = post.get('text', '')[:60].replace('\n', ' ')
        
        print(f"{i}. ID: {post_id} | {post_date}")
        print(f"   Слот: {slot}")
        print(f"   {text_preview}...")
        print()
    
    print(f"{'='*60}")
    print(f"Анализ завершен")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import sys
    
    # Исправляем кодировку для Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\nАнализатор недавних постов\n")
    
    try:
        period = input("За сколько минут смотреть? (по умолчанию 60): ").strip()
        minutes = int(period) if period else 60
    except (ValueError, EOFError):
        print("Используем значение по умолчанию: 60 минут")
        minutes = 60
    
    check_recent_posts(minutes)
