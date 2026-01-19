"""
@file: image_posts_db.py
@description: База данных примеров постов с картинками для обучения AI
@created: 2026-01-19

Функционал:
- Парсинг JSON экспорта из Telegram
- Хранение примеров постов
- Получение случайных примеров для обучения AI
"""

import json
import os
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field


@dataclass
class ImagePostExample:
    """Пример поста с картинкой"""
    id: int
    text_plain: str  # Текст без форматирования
    text_html: str   # Текст с HTML форматированием
    formatting: List[Dict]  # Структура форматирования
    has_photo: bool = True
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ImagePostExample':
        return cls(**data)


class ImagePostsDB:
    """
    База данных примеров постов с картинками.
    Используется для обучения AI стилю написания.
    """
    
    def __init__(self, data_path: str = None):
        """
        Args:
            data_path: Путь к JSON файлу с примерами
        """
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "image_posts_examples.json")
        
        self.data_path = data_path
        self.posts: List[ImagePostExample] = self._load_posts()
    
    def _load_posts(self) -> List[ImagePostExample]:
        """Загружает посты из JSON"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ImagePostExample.from_dict(p) for p in data.get('posts', [])]
        except FileNotFoundError:
            return []
    
    def _save_posts(self):
        """Сохраняет посты в JSON"""
        data = {
            'version': '1.0',
            'description': 'Примеры постов с картинками для обучения AI',
            'total_posts': len(self.posts),
            'posts': [p.to_dict() for p in self.posts]
        }
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ═══════════════════════════════════════════════════════════════
    # ПАРСИНГ TELEGRAM EXPORT
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def _parse_text_entities(text_data) -> Tuple[str, str, List[Dict]]:
        """
        Парсит text_entities из Telegram export.
        
        Returns:
            (plain_text, html_text, formatting_list)
        """
        if isinstance(text_data, str):
            return text_data, text_data, []
        
        if not isinstance(text_data, list):
            return "", "", []
        
        plain_parts = []
        html_parts = []
        formatting = []
        
        for item in text_data:
            if isinstance(item, str):
                plain_parts.append(item)
                html_parts.append(item)
            elif isinstance(item, dict):
                text = item.get('text', '')
                item_type = item.get('type', 'plain')
                
                plain_parts.append(text)
                
                # Конвертируем в HTML
                if item_type == 'bold':
                    html_parts.append(f'<b>{text}</b>')
                elif item_type == 'italic':
                    html_parts.append(f'<i>{text}</i>')
                elif item_type == 'underline':
                    html_parts.append(f'<u>{text}</u>')
                elif item_type == 'code':
                    html_parts.append(f'<code>{text}</code>')
                elif item_type == 'link':
                    html_parts.append(text)  # Ссылка как текст
                elif item_type == 'text_link':
                    href = item.get('href', '')
                    html_parts.append(f'<a href="{href}">{text}</a>')
                elif item_type == 'blockquote':
                    # Telegram blockquote - конвертируем в курсив с отступом
                    html_parts.append(f'<blockquote>{text}</blockquote>')
                else:
                    html_parts.append(text)
                
                # Сохраняем информацию о форматировании
                if item_type != 'plain':
                    formatting.append({
                        'type': item_type,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'href': item.get('href')
                    })
        
        return ''.join(plain_parts), ''.join(html_parts), formatting
    
    def import_from_telegram_export(self, json_path: str) -> int:
        """
        Импортирует посты из Telegram export JSON.
        
        Args:
            json_path: Путь к result.json файлу
            
        Returns:
            Количество импортированных постов
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get('messages', [])
        imported = 0
        
        for msg in messages:
            # Пропускаем сервисные сообщения
            if msg.get('type') != 'message':
                continue
            
            # Берем только сообщения с фото
            if not msg.get('photo'):
                continue
            
            text_data = msg.get('text', [])
            plain_text, html_text, formatting = self._parse_text_entities(text_data)
            
            # Пропускаем пустые
            if not plain_text.strip():
                continue
            
            post = ImagePostExample(
                id=msg.get('id', len(self.posts) + 1),
                text_plain=plain_text.strip(),
                text_html=html_text.strip(),
                formatting=formatting,
                has_photo=True
            )
            
            self.posts.append(post)
            imported += 1
        
        self._save_posts()
        return imported
    
    # ═══════════════════════════════════════════════════════════════
    # ПОЛУЧЕНИЕ ПРИМЕРОВ
    # ═══════════════════════════════════════════════════════════════
    
    def get_all_posts(self) -> List[ImagePostExample]:
        """Возвращает все посты"""
        return self.posts
    
    def get_random_posts(self, count: int = 5) -> List[ImagePostExample]:
        """
        Возвращает случайные посты для примера.
        
        Args:
            count: Количество постов
            
        Returns:
            Список случайных постов
        """
        if not self.posts:
            return []
        return random.sample(self.posts, min(count, len(self.posts)))
    
    def get_random_texts_for_training(self, count: int = 5) -> List[str]:
        """
        Возвращает тексты постов для обучения AI.
        
        Args:
            count: Количество текстов
            
        Returns:
            Список текстов (plain)
        """
        posts = self.get_random_posts(count)
        return [p.text_plain for p in posts]
    
    def get_random_html_for_training(self, count: int = 5) -> List[str]:
        """
        Возвращает HTML тексты для обучения AI форматированию.
        
        Args:
            count: Количество текстов
            
        Returns:
            Список HTML текстов
        """
        posts = self.get_random_posts(count)
        return [p.text_html for p in posts]
    
    def get_formatting_examples(self, count: int = 5) -> str:
        """
        Возвращает примеры форматирования для промпта AI.
        
        Args:
            count: Количество примеров
            
        Returns:
            Форматированная строка с примерами
        """
        posts = self.get_random_posts(count)
        examples = []
        
        for i, post in enumerate(posts, 1):
            # Обрезаем до 600 символов
            text = post.text_plain[:600]
            if len(post.text_plain) > 600:
                text += "..."
            
            examples.append(f"═══ ПРИМЕР {i} ═══\n{text}")
        
        return "\n\n".join(examples)
    
    # ═══════════════════════════════════════════════════════════════
    # СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════════
    
    def get_stats(self) -> dict:
        """Возвращает статистику БД"""
        if not self.posts:
            return {'total': 0, 'avg_length': 0}
        
        lengths = [len(p.text_plain) for p in self.posts]
        
        return {
            'total': len(self.posts),
            'avg_length': sum(lengths) // len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths)
        }


# ═══════════════════════════════════════════════════════════════
# УТИЛИТА ДЛЯ ИМПОРТА
# ═══════════════════════════════════════════════════════════════

def import_telegram_export(json_path: str):
    """
    Утилита для импорта постов из Telegram export.
    
    Usage:
        python -m src.image_posts_db "path/to/result.json"
    """
    db = ImagePostsDB()
    count = db.import_from_telegram_export(json_path)
    print(f"✅ Импортировано {count} постов")
    print(f"📊 Статистика: {db.get_stats()}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import_telegram_export(sys.argv[1])
    else:
        print("Usage: python -m src.image_posts_db <path_to_result.json>")
