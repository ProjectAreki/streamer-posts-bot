"""
@file: topic_manager.py
@description: Менеджер тем для постов с картинками
@created: 2026-01-19

Функционал:
- Загрузка и сохранение тем из JSON
- Получение неиспользованных тем (в приоритете)
- Отметка использования темы
- Добавление пользовательских тем
- Генерация новых тем на основе существующих через AI
"""

import json
import os
import asyncio
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from openai import AsyncOpenAI


@dataclass
class Topic:
    """Тема для поста"""
    id: int
    category: str
    title: str
    description: str
    used_count: int = 0
    last_used: Optional[str] = None
    is_custom: bool = False
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Topic':
        return cls(**data)
    
    def full_text(self) -> str:
        """Полный текст темы для промпта"""
        return f"{self.title}: {self.description}"


class TopicManager:
    """
    Менеджер тем для постов с картинками.
    
    Обеспечивает:
    - Контроль использованных тем
    - Приоритет неиспользованных тем
    - Добавление пользовательских тем
    - Генерацию новых тем через AI
    """
    
    def __init__(self, data_path: str = None):
        """
        Args:
            data_path: Путь к JSON файлу с темами
        """
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "image_post_topics.json")
        
        self.data_path = data_path
        self.data = self._load_data()
        self.topics: List[Topic] = self._parse_topics()
        self.categories: Dict[str, dict] = {c['id']: c for c in self.data.get('categories', [])}
    
    def _load_data(self) -> dict:
        """Загружает данные из JSON"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"topics": [], "categories": [], "usage_history": [], "next_custom_id": 1000}
    
    def _save_data(self):
        """Сохраняет данные в JSON"""
        self.data['topics'] = [t.to_dict() for t in self.topics]
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def _parse_topics(self) -> List[Topic]:
        """Парсит темы из данных"""
        return [Topic.from_dict(t) for t in self.data.get('topics', [])]
    
    # ═══════════════════════════════════════════════════════════════
    # ПОЛУЧЕНИЕ ТЕМ
    # ═══════════════════════════════════════════════════════════════
    
    def get_all_topics(self) -> List[Topic]:
        """Возвращает все темы"""
        return self.topics
    
    def get_topics_by_category(self, category: str) -> List[Topic]:
        """Возвращает темы по категории"""
        return [t for t in self.topics if t.category == category]
    
    def get_unused_topics(self) -> List[Topic]:
        """Возвращает неиспользованные темы"""
        return [t for t in self.topics if t.used_count == 0]
    
    def get_least_used_topics(self, count: int = 20) -> List[Topic]:
        """
        Возвращает наименее использованные темы.
        Приоритет: сначала неиспользованные, потом по used_count.
        
        Args:
            count: Количество тем для возврата
            
        Returns:
            Список тем
        """
        sorted_topics = sorted(self.topics, key=lambda t: (t.used_count, t.last_used or ""))
        return sorted_topics[:count]
    
    def get_random_topics(self, count: int = 20, prefer_unused: bool = True) -> List[Topic]:
        """
        Возвращает случайные темы с приоритетом неиспользованных.
        
        Args:
            count: Количество тем
            prefer_unused: Приоритет неиспользованных
            
        Returns:
            Список случайных тем
        """
        if prefer_unused:
            unused = self.get_unused_topics()
            if len(unused) >= count:
                return random.sample(unused, count)
            
            # Дополняем использованными (наименее часто)
            used = [t for t in self.topics if t.used_count > 0]
            used_sorted = sorted(used, key=lambda t: t.used_count)
            
            result = unused.copy()
            remaining = count - len(result)
            result.extend(used_sorted[:remaining])
            
            random.shuffle(result)
            return result
        else:
            return random.sample(self.topics, min(count, len(self.topics)))
    
    def get_topics_balanced_by_category(self, count: int = 20) -> List[Topic]:
        """
        Возвращает темы с балансом по категориям.
        
        Args:
            count: Общее количество тем
            
        Returns:
            Сбалансированный список тем
        """
        result = []
        categories = list(self.categories.keys())
        per_category = max(1, count // len(categories))
        
        for cat in categories:
            cat_topics = self.get_topics_by_category(cat)
            cat_unused = [t for t in cat_topics if t.used_count == 0]
            
            if cat_unused:
                selected = random.sample(cat_unused, min(per_category, len(cat_unused)))
            else:
                selected = random.sample(cat_topics, min(per_category, len(cat_topics)))
            
            result.extend(selected)
        
        # Добавляем случайные если не хватает
        if len(result) < count:
            remaining = [t for t in self.topics if t not in result]
            additional = random.sample(remaining, min(count - len(result), len(remaining)))
            result.extend(additional)
        
        random.shuffle(result)
        return result[:count]
    
    # ═══════════════════════════════════════════════════════════════
    # УПРАВЛЕНИЕ ИСПОЛЬЗОВАНИЕМ
    # ═══════════════════════════════════════════════════════════════
    
    def mark_topic_used(self, topic_id: int):
        """
        Отмечает тему как использованную.
        
        Args:
            topic_id: ID темы
        """
        for topic in self.topics:
            if topic.id == topic_id:
                topic.used_count += 1
                topic.last_used = datetime.now().isoformat()
                
                # Добавляем в историю
                self.data.setdefault('usage_history', []).append({
                    'topic_id': topic_id,
                    'used_at': topic.last_used
                })
                
                self._save_data()
                return
    
    def mark_topics_used(self, topic_ids: List[int]):
        """Отмечает несколько тем как использованные"""
        for topic_id in topic_ids:
            self.mark_topic_used(topic_id)
    
    def reset_usage_stats(self):
        """Сбрасывает статистику использования всех тем"""
        for topic in self.topics:
            topic.used_count = 0
            topic.last_used = None
        self.data['usage_history'] = []
        self._save_data()
    
    def get_usage_stats(self) -> dict:
        """
        Возвращает статистику использования.
        
        Returns:
            Словарь со статистикой
        """
        total = len(self.topics)
        unused = len(self.get_unused_topics())
        used = total - unused
        
        by_category = {}
        for cat_id, cat_info in self.categories.items():
            cat_topics = self.get_topics_by_category(cat_id)
            cat_unused = len([t for t in cat_topics if t.used_count == 0])
            by_category[cat_info['name']] = {
                'total': len(cat_topics),
                'unused': cat_unused,
                'used': len(cat_topics) - cat_unused
            }
        
        return {
            'total_topics': total,
            'unused': unused,
            'used': used,
            'by_category': by_category
        }
    
    # ═══════════════════════════════════════════════════════════════
    # ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЬСКИХ ТЕМ
    # ═══════════════════════════════════════════════════════════════
    
    def add_custom_topic(self, title: str, description: str = "") -> Topic:
        """
        Добавляет пользовательскую тему.
        
        Args:
            title: Название темы
            description: Описание (опционально)
            
        Returns:
            Созданная тема
        """
        new_id = self.data.get('next_custom_id', 1000)
        self.data['next_custom_id'] = new_id + 1
        
        topic = Topic(
            id=new_id,
            category='custom',
            title=title,
            description=description,
            used_count=0,
            last_used=None,
            is_custom=True
        )
        
        self.topics.append(topic)
        self._save_data()
        
        return topic
    
    def add_custom_topics_bulk(self, topics_text: str) -> List[Topic]:
        """
        Добавляет несколько пользовательских тем из текста.
        Каждая тема на новой строке.
        Формат: "Название темы" или "Название темы: описание"
        
        Args:
            topics_text: Текст с темами (каждая на новой строке)
            
        Returns:
            Список созданных тем
        """
        lines = [l.strip() for l in topics_text.strip().split('\n') if l.strip()]
        created = []
        
        for line in lines:
            # Парсим формат "Название: описание" или просто "Название"
            if ':' in line:
                parts = line.split(':', 1)
                title = parts[0].strip()
                description = parts[1].strip()
            else:
                title = line
                description = ""
            
            topic = self.add_custom_topic(title, description)
            created.append(topic)
        
        return created
    
    def delete_custom_topic(self, topic_id: int) -> bool:
        """
        Удаляет пользовательскую тему.
        
        Args:
            topic_id: ID темы
            
        Returns:
            True если удалена, False если не найдена или не пользовательская
        """
        for i, topic in enumerate(self.topics):
            if topic.id == topic_id and topic.is_custom:
                self.topics.pop(i)
                self._save_data()
                return True
        return False
    
    # ═══════════════════════════════════════════════════════════════
    # ГЕНЕРАЦИЯ НОВЫХ ТЕМ ЧЕРЕЗ AI
    # ═══════════════════════════════════════════════════════════════
    
    async def generate_new_topics(
        self, 
        count: int = 10,
        client: AsyncOpenAI = None,
        model: str = "gpt-4o-mini",
        base_url: str = None
    ) -> List[Topic]:
        """
        Генерирует новые темы на основе существующих через AI.
        
        Args:
            count: Количество новых тем
            client: OpenAI клиент (если не передан - создаётся)
            model: Модель для генерации
            base_url: Base URL для OpenRouter
            
        Returns:
            Список сгенерированных тем
        """
        if client is None:
            api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("API ключ не найден")
            
            if base_url is None:
                base_url = "https://openrouter.ai/api/v1"
            
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        # Собираем примеры существующих тем
        sample_topics = random.sample(self.topics, min(20, len(self.topics)))
        examples = "\n".join([f"- {t.title}: {t.description}" for t in sample_topics])
        
        prompt = f"""Ты эксперт по гемблинг-индустрии и психологии игроков.

На основе этих существующих тем для постов:
{examples}

Сгенерируй {count} НОВЫХ уникальных тем для постов.

ПРАВИЛА:
1. Темы должны быть актуальны для 2025-2026 года
2. Не повторяй существующие темы
3. Темы должны быть интересны игрокам
4. Каждая тема: краткое название + описание

ФОРМАТ ОТВЕТА (строго):
Название темы: краткое описание
Название темы: краткое описание
...

Пиши только темы, без пояснений."""

        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Ты генерируешь темы для постов о гемблинге."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.9
                ),
                timeout=120
            )
            
            generated_text = response.choices[0].message.content.strip()
            new_topics = self.add_custom_topics_bulk(generated_text)
            
            return new_topics
            
        except Exception as e:
            print(f"❌ Ошибка генерации тем: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ═══════════════════════════════════════════════════════════════
    
    def get_topic_by_id(self, topic_id: int) -> Optional[Topic]:
        """Возвращает тему по ID"""
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        return None
    
    def search_topics(self, query: str) -> List[Topic]:
        """
        Поиск тем по ключевому слову.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных тем
        """
        query_lower = query.lower()
        return [
            t for t in self.topics 
            if query_lower in t.title.lower() or query_lower in t.description.lower()
        ]
    
    def format_topic_for_display(self, topic: Topic) -> str:
        """Форматирует тему для отображения в UI"""
        category_info = self.categories.get(topic.category, {})
        emoji = category_info.get('emoji', '📝')
        
        status = ""
        if topic.used_count > 0:
            status = f" (использована {topic.used_count}x)"
        
        return f"{emoji} <b>{topic.title}</b>{status}\n<i>{topic.description}</i>"
    
    def format_topics_list(self, topics: List[Topic], show_ids: bool = False) -> str:
        """Форматирует список тем для отображения"""
        lines = []
        for i, topic in enumerate(topics, 1):
            category_info = self.categories.get(topic.category, {})
            emoji = category_info.get('emoji', '📝')
            
            if show_ids:
                lines.append(f"{i}. [{topic.id}] {emoji} {topic.title}")
            else:
                lines.append(f"{i}. {emoji} {topic.title}")
        
        return "\n".join(lines)
