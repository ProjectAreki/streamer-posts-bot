"""
@file: ai_image_post_generator.py
@description: Генератор постов для картинок на основе тем
@created: 2026-01-19

Функционал:
- Генерация постов на основе тем из базы
- Обучение на примерах существующих постов
- Рандомное форматирование текста
- Интеграция с генератором изображений
"""

import os
import sys
import random
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from openai import AsyncOpenAI

from src.topic_manager import TopicManager, Topic
from src.image_posts_db import ImagePostsDB
from src.ai_image_generator import AIImageGenerator, GeneratedImage


@dataclass
class GeneratedImagePost:
    """Результат генерации поста с картинкой"""
    index: int
    topic: Topic
    text: str              # Текст поста (HTML)
    text_plain: str        # Текст без HTML
    image: Optional[GeneratedImage] = None
    image_base64: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'topic_id': self.topic.id,
            'topic_title': self.topic.title,
            'text': self.text,
            'text_plain': self.text_plain,
            'has_image': self.image is not None,
            'image_base64': self.image_base64
        }


class AIImagePostGenerator:
    """
    Генератор постов для картинок.
    
    Создает уникальные посты на основе тем с обучением на примерах.
    """
    
    # Системные промпты для разных стилей
    SYSTEM_PROMPTS = [
        """Ты копирайтер для Telegram-канала о гемблинге.
Пишешь живые, вовлекающие посты для аудитории игроков в слоты.
Стиль: дружеский, с юмором, без занудства.
Используешь эмодзи умеренно, но метко.""",

        """Ты автор популярного канала о казино.
Твои посты цепляют с первой строки.
Пишешь как будто рассказываешь другу интересную историю.
Не боишься использовать сленг и шутки.""",

        """Ты эксперт по слотам с харизмой.
Объясняешь сложное простым языком.
Твои посты информативные, но не скучные.
Добавляешь личные наблюдения и лайфхаки.""",

        """Ты маркетолог с чувством юмора.
Знаешь как зацепить внимание за 2 секунды.
Пишешь ёмко, каждое слово на своём месте.
Мастерски используешь форматирование.""",
    ]
    
    # Промпты для генерации постов
    POST_PROMPTS = [
        """Напиши пост на тему: {topic}

ДАННЫЕ:
- Тема: {topic_title}
- Детали: {topic_description}
- Ссылка 1: {url1} ({bonus1})
- Ссылка 2: {url2} ({bonus2})

СТРУКТУРА:
1. Цепляющий заголовок или вопрос
2. Раскрытие темы (2-3 абзаца)
3. Ссылки с призывом к действию
4. Финальная мысль или совет

ФОРМАТ:
- 500-800 символов
- HTML форматирование: <b>, <i>, <u>, <code>
- Эмодзи в начале абзацев
- Ссылки как простые URL или <a href="url">текст</a>""",

        """Напиши экспертный пост про: {topic}

ТЕМА: {topic_title} - {topic_description}
ССЫЛКИ: {url1} и {url2}
БОНУСЫ: {bonus1} / {bonus2}

СТИЛЬ: Как будто ты опытный игрок делишься знаниями.

ПРАВИЛА:
- 500-800 символов
- Начни с интригующего факта или вопроса
- Объясни тему простыми словами
- Добавь практический совет
- Вставь обе ссылки органично
- Используй <b>жирный</b> и <i>курсив</i>""",

        """Создай вовлекающий пост:

ТЕМА: {topic_title}
КОНТЕКСТ: {topic_description}
БОНУСЫ: {url1} ({bonus1}), {url2} ({bonus2})

ФОРМАТ ПОСТА:
🎯 Хук (цепляющее начало)
📝 Основная часть с раскрытием темы
🎁 Блок со ссылками и бонусами
💡 Завершающий совет или CTA

ТРЕБОВАНИЯ:
- 500-800 символов
- Живой язык без канцеляризмов
- HTML теги для форматирования
- Минимум 3 эмодзи""",

        """Пост-совет на тему: {topic}

{topic_title}: {topic_description}

ССЫЛКИ ДЛЯ ВСТАВКИ:
• {url1} - {bonus1}
• {url2} - {bonus2}

ЗАДАЧА:
1. Дай реальный полезный совет по теме
2. Подкрепи примером или аналогией
3. Интегрируй ссылки как решение/возможность
4. Заверши мотивирующей фразой

РАЗМЕР: 500-800 символов
ФОРМАТ: HTML (<b>, <i>, <u>)""",
    ]
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
        base_url: str = "https://openrouter.ai/api/v1",
        image_model: str = "nano_banana_pro"
    ):
        """
        Args:
            api_key: OpenRouter API ключ
            model: Модель для генерации текста
            base_url: Base URL для API
            image_model: Модель для генерации изображений
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY не найден")
        
        self.model = model
        self.base_url = base_url
        self.image_model = image_model
        
        # Инициализируем клиент
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=base_url)
        
        # Загружаем менеджер тем и БД примеров
        self.topic_manager = TopicManager()
        self.posts_db = ImagePostsDB()
        
        # Генератор изображений (инициализируется по требованию)
        self._image_generator: Optional[AIImageGenerator] = None
        
        # Данные о бонусах
        self.url1: str = ""
        self.url2: str = ""
        self.bonus1: str = ""
        self.bonus2: str = ""
        
        # Кэш сгенерированных постов для проверки уникальности
        self._generated_texts: List[str] = []
    
    def set_bonus_data(self, url1: str, bonus1: str, url2: str, bonus2: str):
        """Устанавливает данные о бонусах"""
        self.url1 = url1
        self.url2 = url2
        self.bonus1 = bonus1
        self.bonus2 = bonus2
    
    def get_image_generator(self) -> AIImageGenerator:
        """Возвращает генератор изображений (lazy init)"""
        if self._image_generator is None:
            self._image_generator = AIImageGenerator(
                api_key=self.api_key,
                model=self.image_model
            )
        return self._image_generator
    
    async def generate_post(
        self,
        topic: Topic,
        index: int = 0,
        generate_image: bool = True
    ) -> GeneratedImagePost:
        """
        Генерирует пост для конкретной темы.
        
        Args:
            topic: Тема для поста
            index: Порядковый номер
            generate_image: Генерировать ли изображение
            
        Returns:
            Сгенерированный пост
        """
        max_attempts = 3
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Выбираем случайный системный промпт
                system_prompt = random.choice(self.SYSTEM_PROMPTS)
                
                # Добавляем примеры из БД
                examples = self.posts_db.get_formatting_examples(3)
                if examples:
                    system_prompt += f"\n\nПРИМЕРЫ ПОСТОВ ДЛЯ ИЗУЧЕНИЯ СТИЛЯ:\n{examples}"
                
                # Выбираем случайный промпт для генерации
                prompt_template = random.choice(self.POST_PROMPTS)
                prompt = prompt_template.format(
                    topic=topic.full_text(),
                    topic_title=topic.title,
                    topic_description=topic.description,
                    url1=self.url1,
                    url2=self.url2,
                    bonus1=self.bonus1,
                    bonus2=self.bonus2
                )
                
                # Генерируем текст
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.9
                )
                
                text = response.choices[0].message.content.strip()
                
                # Постобработка текста
                text = self._postprocess_text(text)
                
                # Проверяем наличие ссылок
                if self.url1 not in text or self.url2 not in text:
                    print(f"   ⚠️ Пост #{index}: Ссылки пропали, попытка {attempt}/{max_attempts}")
                    continue
                
                # Проверяем уникальность
                if text in self._generated_texts:
                    print(f"   ⚠️ Пост #{index}: Дубликат, попытка {attempt}/{max_attempts}")
                    continue
                
                # Проверяем длину
                if len(text) < 300:
                    print(f"   ⚠️ Пост #{index}: Слишком короткий ({len(text)} символов)")
                    continue
                
                self._generated_texts.append(text)
                
                # Отмечаем тему как использованную
                self.topic_manager.mark_topic_used(topic.id)
                
                # Генерируем изображение если нужно
                image = None
                image_base64 = None
                if generate_image:
                    try:
                        print(f"   🎨 Генерирую картинку для поста #{index}...")
                        image_gen = self.get_image_generator()
                        image = await image_gen.generate_image(text)
                        image_base64 = image.image_base64
                        print(f"   ✅ Картинка готова за {image.generation_time:.1f}с")
                    except Exception as e:
                        print(f"   ⚠️ Ошибка генерации картинки: {e}")
                
                # Создаем plain text версию
                text_plain = self._strip_html(text)
                
                print(f"✅ Пост #{index} готов: {topic.title[:30]}...")
                
                return GeneratedImagePost(
                    index=index,
                    topic=topic,
                    text=text,
                    text_plain=text_plain,
                    image=image,
                    image_base64=image_base64
                )
                
            except Exception as e:
                last_error = e
                print(f"❌ Ошибка генерации поста #{index} (попытка {attempt}): {e}")
                await asyncio.sleep(1)
        
        # Fallback если все попытки провалились
        print(f"⚠️ Используем fallback для поста #{index}")
        fallback_text = f"""🎯 <b>{topic.title}</b>

{topic.description}

🎁 Бонус 1: {self.url1}
🚀 Бонус 2: {self.url2}"""
        
        return GeneratedImagePost(
            index=index,
            topic=topic,
            text=fallback_text,
            text_plain=self._strip_html(fallback_text),
            image=None,
            image_base64=None
        )
    
    async def generate_posts_batch(
        self,
        count: int = 20,
        topics: List[Topic] = None,
        generate_images: bool = True,
        progress_callback=None
    ) -> List[GeneratedImagePost]:
        """
        Генерирует пакет постов.
        
        Args:
            count: Количество постов
            topics: Список тем (если не указан - выбираются автоматически)
            generate_images: Генерировать ли изображения
            progress_callback: async callback(current, total) для отчёта
            
        Returns:
            Список сгенерированных постов
        """
        # Получаем темы
        if topics is None:
            topics = self.topic_manager.get_topics_balanced_by_category(count)
        
        posts = []
        
        for i, topic in enumerate(topics):
            if progress_callback:
                await progress_callback(i, count)
            
            post = await self.generate_post(
                topic=topic,
                index=i,
                generate_image=generate_images
            )
            posts.append(post)
            
            # Небольшая задержка между запросами
            await asyncio.sleep(0.5)
        
        if progress_callback:
            await progress_callback(count, count)
        
        return posts
    
    async def regenerate_image(
        self,
        post: GeneratedImagePost
    ) -> GeneratedImagePost:
        """
        Перегенерирует изображение для поста.
        
        Args:
            post: Пост для которого нужна новая картинка
            
        Returns:
            Пост с новым изображением
        """
        try:
            image_gen = self.get_image_generator()
            image = await image_gen.regenerate_image(post.text_plain)
            
            post.image = image
            post.image_base64 = image.image_base64
            
            return post
        except Exception as e:
            print(f"❌ Ошибка перегенерации картинки: {e}")
            return post
    
    def _postprocess_text(self, text: str) -> str:
        """Постобработка текста поста"""
        # Убираем лишние маркеры
        markers_to_remove = [
            "```html", "```", "---", "===",
            "[HOOK]", "[/HOOK]", "[CTA]", "[/CTA]",
            "[LINK1]", "[/LINK1]", "[LINK2]", "[/LINK2]"
        ]
        
        for marker in markers_to_remove:
            text = text.replace(marker, "")
        
        # Убираем множественные переносы строк
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        
        return text.strip()
    
    def _strip_html(self, text: str) -> str:
        """Убирает HTML теги из текста"""
        import re
        clean = re.sub('<[^<]+?>', '', text)
        return clean
    
    def get_topic_stats(self) -> str:
        """Возвращает статистику тем для отображения"""
        stats = self.topic_manager.get_usage_stats()
        
        lines = [
            f"📊 <b>Статистика тем:</b>",
            f"   Всего: {stats['total_topics']}",
            f"   Неиспользованных: {stats['unused']}",
            f"   Использованных: {stats['used']}",
            "",
            "📁 <b>По категориям:</b>"
        ]
        
        for cat_name, cat_stats in stats['by_category'].items():
            lines.append(f"   {cat_name}: {cat_stats['unused']}/{cat_stats['total']}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# ТЕСТИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════

async def test_post_generation():
    """Тестовая генерация поста"""
    generator = AIImagePostGenerator()
    
    generator.set_bonus_data(
        url1="https://example.com/bonus1",
        bonus1="500 фриспинов + 150% к депозиту",
        url2="https://example.com/bonus2", 
        bonus2="30000₽ + 500 вращений"
    )
    
    # Получаем случайную тему
    topics = generator.topic_manager.get_random_topics(1)
    if not topics:
        print("Нет доступных тем")
        return
    
    topic = topics[0]
    print(f"📝 Тема: {topic.title}")
    print(f"📄 Описание: {topic.description}")
    print()
    
    # Генерируем пост БЕЗ картинки для теста
    post = await generator.generate_post(topic, index=0, generate_image=False)
    
    print("═" * 50)
    print("СГЕНЕРИРОВАННЫЙ ПОСТ:")
    print("═" * 50)
    print(post.text)
    print("═" * 50)
    print(f"Длина: {len(post.text)} символов")


if __name__ == "__main__":
    asyncio.run(test_post_generation())
