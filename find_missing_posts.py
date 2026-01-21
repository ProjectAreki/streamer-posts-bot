"""
Скрипт для поиска пропущенных постов

Помогает найти какие посты из исходного сценария не были созданы.
"""

import json
from datetime import datetime
from typing import List, Dict, Set

def load_posts(filename: str = "data/my_posts.json") -> List[Dict]:
    """Загрузка постов из файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('posts', [])
    except FileNotFoundError:
        print(f"[ERROR] Файл {filename} не найден")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Ошибка чтения JSON: {e}")
        return []

def analyze_recent_posts(posts: List[Dict], hours_back: int = 24):
    """
    Анализирует посты за последние N часов
    
    Args:
        posts: Список постов
        hours_back: Сколько часов назад смотреть
    """
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    recent_posts = []
    for post in posts:
        try:
            post_date = datetime.fromisoformat(post['date'])
            if post_date >= cutoff_time:
                recent_posts.append(post)
        except:
            pass
    
    return recent_posts

def find_used_slots(posts: List[Dict]) -> Dict[str, int]:
    """Находит какие слоты использовались и сколько раз"""
    from collections import Counter
    
    slots = []
    for post in posts:
        slot = post.get('slot', 'Неизвестно')
        if slot and slot != 'Неизвестно':
            slots.append(slot)
    
    return Counter(slots)

def analyze_missing_posts(target_count: int = 80, hours_back: int = 24):
    """
    Основная функция анализа пропущенных постов
    
    Args:
        target_count: Ожидаемое количество постов
        hours_back: За какой период смотреть
    """
    print(f"\n{'='*60}")
    print(f"ПОИСК ПРОПУЩЕННЫХ ПОСТОВ")
    print(f"{'='*60}\n")
    
    # Загружаем все посты
    all_posts = load_posts()
    print(f"Всего постов в базе: {len(all_posts)}")
    
    # Анализируем последние посты
    recent = analyze_recent_posts(all_posts, hours_back)
    print(f"Постов за последние {hours_back}ч: {len(recent)}")
    
    # Ищем самую свежую сессию
    if recent:
        # Сортируем по дате (свежие первые)
        recent_sorted = sorted(recent, key=lambda x: x.get('date', ''), reverse=True)
        
        # Берем посты с одинаковой датой (в пределах 1 часа от самого свежего)
        latest_date = datetime.fromisoformat(recent_sorted[0]['date'])
        session_posts = []
        
        for post in recent_sorted:
            try:
                post_date = datetime.fromisoformat(post['date'])
                time_diff = (latest_date - post_date).total_seconds() / 3600
                if time_diff <= 1:  # В пределах 1 часа
                    session_posts.append(post)
            except:
                pass
        
        print(f"\n{'='*60}")
        print(f"ПОСЛЕДНЯЯ СЕССИЯ ГЕНЕРАЦИИ")
        print(f"{'='*60}")
        print(f"Дата: {latest_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Постов создано: {len(session_posts)}")
        print(f"Ожидалось: {target_count}")
        
        if len(session_posts) < target_count:
            missing = target_count - len(session_posts)
            print(f"\n[!] ПРОПУЩЕНО ПОСТОВ: {missing}\n")
            
            # Анализируем какие слоты использовались
            used_slots = find_used_slots(session_posts)
            print(f"Использованные слоты:")
            for slot, count in sorted(used_slots.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {slot}: {count} постов")
            
            # Показываем ID последних постов
            print(f"\nДиапазон ID созданных постов:")
            ids = [p.get('id') for p in session_posts if p.get('id')]
            if ids:
                print(f"   От #{min(ids)} до #{max(ids)}")
            
            print(f"\nРЕКОМЕНДАЦИИ:")
            print(f"   1. Проверьте логи бота на наличие ошибок")
            print(f"   2. Посмотрите последние {missing} видео в исходном канале")
            print(f"   3. Возможно, некоторые видео не прошли валидацию")
            print(f"   4. Запустите генерацию недостающих {missing} постов")
        else:
            print(f"\n[OK] Все {target_count} постов созданы успешно!")
        
        # Показываем примеры последних постов
        print(f"\n{'='*60}")
        print(f"ПОСЛЕДНИЕ 5 ПОСТОВ ИЗ СЕССИИ:")
        print(f"{'='*60}\n")
        
        for i, post in enumerate(session_posts[:5], 1):
            post_id = post.get('id', '?')
            slot = post.get('slot', 'Неизвестно')
            text_preview = post.get('text', '')[:80].replace('\n', ' ')
            print(f"{i}. ID: {post_id} | Слот: {slot}")
            print(f"   {text_preview}...")
            print()
    
    else:
        print(f"[!] Не найдено постов за последние {hours_back} часов")
        print(f"Попробуйте увеличить период поиска")

def main():
    """Главная функция"""
    import sys
    
    # Исправляем кодировку для Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\nАнализатор пропущенных постов\n")
    
    # Спрашиваем параметры
    try:
        target = input("Сколько постов ожидалось? (по умолчанию 80): ").strip()
        target_count = int(target) if target else 80
        
        hours = input("За какой период смотреть (часов назад)? (по умолчанию 24): ").strip()
        hours_back = int(hours) if hours else 24
    except ValueError:
        print("Неверный ввод, используем значения по умолчанию")
        target_count = 80
        hours_back = 24
    except EOFError:
        # Если нет интерактивного ввода, используем значения по умолчанию
        print("Используем значения по умолчанию: 80 постов, 24 часа")
        target_count = 80
        hours_back = 24
    
    # Запускаем анализ
    analyze_missing_posts(target_count, hours_back)
    
    print(f"\n{'='*60}")
    print(f"Анализ завершен")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
