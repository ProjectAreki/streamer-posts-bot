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
        """Ты опытный копирайтер для Telegram-канала.
Пишешь живые, вовлекающие посты для аудитории игроков.
Стиль: дружеский, без агрессии, смягчаешь углы.
Твоя задача - донести мысль правдиво, но в мягкой форме, всегда переходя к позитивной мотивационной ноте в конце.
Используешь эмодзи умеренно, но метко.

⚠️ ЗАПРЕЩЕНО: слово "казино" (используй синонимы: платформа, сайт, площадка)""",

        """Ты автор популярного канала об онлайн-играх.
Твои посты цепляют с первой строки, но без агрессии.
Пишешь как будто рассказываешь другу полезную историю.
Смягчаешь острые углы, завершаешь на позитивной мотивационной ноте.

⚠️ ЗАПРЕЩЕНО: слово "казино" (используй: игровой клуб, платформа, сайт)""",

        """Ты эксперт с харизмой и позитивным настроем.
Объясняешь сложное простым языком без агрессии.
Твои посты информативные и мотивирующие.
Всегда завершаешь на позитивной ноте с призывом к действию.

⚠️ ЗАПРЕЩЕНО: слово "казино" (замени на: площадка, ресурс, сервис)""",

        """Ты маркетолог с чувством такта.
Знаешь как зацепить внимание без давления.
Пишешь ёмко, правдиво, но мягко.
Каждый пост завершается на мотивационной позитивной волне.

⚠️ ЗАПРЕЩЕНО: слово "казино" (используй: платформа, игровой портал, клуб)""",
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
2. Раскрытие темы (правдиво, но мягко, без агрессии)
3. Ссылки с призывом к действию
4. Позитивная мотивационная мысль в конце

ФОРМАТ ССЫЛОК (КРИТИЧНО!):
⚠️ ОБЕ ССЫЛКИ ДОЛЖНЫ БЫТЬ ОФОРМЛЕНЫ ОДИНАКОВО!
Если первая ссылка просто URL, то и вторая тоже просто URL.
Если первая <a href="">, то и вторая <a href="">.

Между двумя ссылками ОБЯЗАТЕЛЬНА пустая строка:
{url1}
описание первого бонуса

{url2}
описание второго бонуса

ТРЕБОВАНИЯ:
- Оптимально 400-700 символов (не обрезай текст!)
- HTML форматирование: <b>, <i>, <u>, <code>
- Эмодзи в начале абзацев
- БЕЗ слова "казино" (замени на: платформа, сайт, клуб)
- Тон: мягкий, позитивный, мотивирующий
- Полностью пиши описания бонусов, не обрезай!""",

        """Напиши экспертный пост про: {topic}

ТЕМА: {topic_title} - {topic_description}
ССЫЛКИ: {url1} и {url2}
БОНУСЫ: {bonus1} / {bonus2}

СТИЛЬ: Опытный игрок делится знаниями без агрессии, смягчая углы.

ФОРМАТ ССЫЛОК:
⚠️ ОБЕ ССЫЛКИ ОФОРМЛЕНЫ ОДИНАКОВО! Если первая просто URL, то и вторая тоже.
ВАЖНО! Между ссылками пустая строка:
{url1} - {bonus1}

{url2} - {bonus2}

ПРАВИЛА:
- Оптимально 400-700 символов (не обрезай!)
- Начни с интригующего факта или вопроса
- Объясни тему мягко и позитивно
- Добавь практический совет
- Вставь обе ссылки с пустой строкой между ними
- Используй <b>жирный</b> и <i>курсив</i>
- БЕЗ слова "казино"
- Заверши мотивационной нотой
- Полностью пиши описания бонусов!""",

        """Создай вовлекающий пост:

ТЕМА: {topic_title}
КОНТЕКСТ: {topic_description}
БОНУСЫ: {url1} ({bonus1}), {url2} ({bonus2})

ФОРМАТ ПОСТА:
🎯 Хук (цепляющее начало без агрессии)
📝 Основная часть с раскрытием темы (мягко и правдиво)
🎁 Блок со ссылками (с пустой строкой между ними!)
💡 Позитивная мотивационная концовка

ФОРМАТ ССЫЛОК:
⚠️ ОБЕ ССЫЛКИ ДОЛЖНЫ БЫТЬ ОДИНАКОВО ОФОРМЛЕНЫ!
{url1}
{bonus1}

{url2}
{bonus2}

ТРЕБОВАНИЯ:
- Оптимально 400-700 символов (не обрезай текст!)
- Живой язык без канцеляризмов
- HTML теги для форматирования
- Минимум 3 эмодзи
- БЕЗ слова "казино" (используй: платформа, сайт, площадка)
- Тон: позитивный, мотивирующий
- Описания бонусов пиши полностью!""",

        """Пост-совет на тему: {topic}

{topic_title}: {topic_description}

ССЫЛКИ ДЛЯ ВСТАВКИ:
• {url1} - {bonus1}
• {url2} - {bonus2}

ЗАДАЧА:
1. Дай реальный полезный совет (мягко, без агрессии)
2. Подкрепи примером или аналогией
3. Интегрируй ссылки с ПУСТОЙ СТРОКОЙ между ними
4. Заверши МОТИВИРУЮЩЕЙ позитивной фразой

ФОРМАТ ССЫЛОК:
⚠️ ОБЕ ССЫЛКИ ОФОРМЛЕНЫ ОДИНАКОВО!
{url1} - {bonus1}

{url2} - {bonus2}

ТРЕБОВАНИЯ:
- Оптимально 400-700 символов (не обрезай!)
- ФОРМАТ: HTML (<b>, <i>, <u>)
- БЕЗ слова "казино" (замена: клуб, платформа, сервис)
- Тон: доброжелательный, мотивирующий, позитивный
- Описания бонусов пиши полностью, не сокращай!""",
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
                examples = self.posts_db.get_formatting_examples(5)
                if examples:
                    system_prompt += f"\n\nПРИМЕРЫ ПОСТОВ ДЛЯ ИЗУЧЕНИЯ СТИЛЯ И СТРУКТУРЫ:\n{examples}"
                    system_prompt += "\n\n⚠️ ВАЖНО: Изучи структуру примеров выше и создай РАЗНООБРАЗНЫЙ пост с УНИКАЛЬНОЙ структурой, не копируя один и тот же паттерн!"
                
                # Генерируем уникальные описания бонусов
                bonus1_unique = self._get_unique_bonus_description(self.bonus1)
                bonus2_unique = self._get_unique_bonus_description(self.bonus2)
                
                # Выбираем случайный промпт для генерации
                prompt_template = random.choice(self.POST_PROMPTS)
                prompt = prompt_template.format(
                    topic=topic.full_text(),
                    topic_title=topic.title,
                    topic_description=topic.description,
                    url1=self.url1,
                    url2=self.url2,
                    bonus1=bonus1_unique,
                    bonus2=bonus2_unique
                )
                
                # Генерируем текст
                try:
                    response = await asyncio.wait_for(
                        self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=1500,
                            temperature=0.9
                        ),
                        timeout=120
                    )
                except asyncio.TimeoutError:
                    raise Exception(f"Таймаут: модель {self.model} не ответила за 120с")
                
                text = response.choices[0].message.content.strip()
                
                # Постобработка текста
                text = self._postprocess_text(text)
                
                # Проверяем слово "казино"
                if "казино" in text.lower():
                    print(f"   ⚠️ Пост #{index}: Содержит слово 'казино', попытка {attempt}/{max_attempts}")
                    continue
                
                # Проверяем наличие ссылок
                if self.url1 not in text or self.url2 not in text:
                    print(f"   ⚠️ Пост #{index}: Ссылки пропали, попытка {attempt}/{max_attempts}")
                    continue
                
                # ВАЖНО: НЕ ОБРЕЗАЕМ текст! Пользователь запретил обрезку.
                # AI должен сам создавать посты нужной длины согласно промпту.
                
                # Проверяем уникальность
                if text in self._generated_texts:
                    print(f"   ⚠️ Пост #{index}: Дубликат, попытка {attempt}/{max_attempts}")
                    continue
                
                # Проверяем длину
                if len(text) < 200:
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
    
    def _get_unique_bonus_description(self, original: str) -> str:
        """
        Генерирует уникальную вариацию описания бонуса.
        
        Пример: "500 фриспинов + 150% к депозиту"
        Вариации:
        - "500 бесплатных вращений и бонус 150% на депозит"
        - "пакет из 500 спинов + 150% к пополнению"
        - "500 круток в подарок и 150% к балансу"
        """
        import re
        
        text = original
        
        # Вариации для фриспинов/спинов
        fs_variations = [
            ("фриспинов", ["бесплатных вращений", "спинов", "круток", "бесплатных спинов", "FS", "вращений"]),
            ("фриспины", ["спины", "крутки", "бесплатные вращения", "фри-спины"]),
            ("FS", ["фриспинов", "спинов", "бесплатных вращений"]),
            ("вращений", ["фриспинов", "спинов", "круток"]),
            ("спинов", ["фриспинов", "вращений", "круток"])
        ]
        
        for original_word, variations in fs_variations:
            if original_word in text.lower():
                replacement = random.choice(variations)
                # Регистронезависимая замена
                pattern = re.compile(re.escape(original_word), re.IGNORECASE)
                text = pattern.sub(replacement, text, count=1)
                break
        
        # Вариации для депозита/пополнения
        deposit_variations = [
            ("к депозиту", ["на депозит", "к пополнению", "на баланс", "к счету", "на счёт"]),
            ("депозит", ["пополнение", "первый взнос", "баланс"]),
            ("пополнению", ["депозиту", "балансу", "счету"]),
        ]
        
        for original_phrase, variations in deposit_variations:
            if original_phrase in text.lower():
                replacement = random.choice(variations)
                pattern = re.compile(re.escape(original_phrase), re.IGNORECASE)
                text = pattern.sub(replacement, text, count=1)
                break
        
        # Вариации для процентов
        if "%" in text:
            percent_variations = [
                (r"(\d+)%", [r"\1 процентов", r"\1%", r"бонус \1%"]),
            ]
            for pattern_str, variations in percent_variations:
                pattern = re.compile(pattern_str)
                match = pattern.search(text)
                if match:
                    replacement = random.choice(variations)
                    text = pattern.sub(replacement, text, count=1)
                    break
        
        # Вариации для рублей
        rub_variations = [
            ("рублей", ["₽", "руб", "рубасов", "на счёт", "р"]),
            ("₽", ["рублей", "руб", "р"]),
            ("руб", ["рублей", "₽"]),
        ]
        
        for original_word, variations in rub_variations:
            if original_word in text.lower():
                replacement = random.choice(variations)
                pattern = re.compile(re.escape(original_word), re.IGNORECASE)
                text = pattern.sub(replacement, text, count=1)
                break
        
        # Вариации соединителей
        connector_variations = [
            (" + ", [" и ", " плюс ", " + ", " а также "]),
            (" и ", [" + ", " плюс ", " вместе с "]),
            (" плюс ", [" + ", " и ", " а ещё "]),
        ]
        
        for original_connector, variations in connector_variations:
            if original_connector in text:
                replacement = random.choice(variations)
                text = text.replace(original_connector, replacement, 1)
                break
        
        # Добавляем случайные обрамления
        if random.random() < 0.3:  # 30% шанс
            prefixes = ["до ", "целых ", "аж ", "щедрые ", ""]
            text = random.choice(prefixes) + text
        
        if random.random() < 0.3:  # 30% шанс
            suffixes = [" в подарок", " сверху", " бонусом", " на старте", ""]
            text = text + random.choice(suffixes)
        
        return text.strip()
    
    def _postprocess_text(self, text: str) -> str:
        """Постобработка текста поста"""
        import re

        # Удаление AI-преамбул
        ai_preamble_patterns = [
            r'^(?:вот\s+)?(?:мой\s+)?вариант\s+поста\s*[:\.!\-—–]\s*\n*',
            r'^вот\s+(?:готовый\s+)?(?:пост|текст)\s*[:\.!\-—–]\s*\n*',
            r'^(?:here\s*(?:is|\'s)\s+)?(?:the\s+|my\s+)?(?:post|text)\s*[:\.!\-—]\s*\n*',
            r'^конечно[,!]?\s*(?:вот\s+)?(?:пост|текст)\s*[:\.!\-—–]\s*\n*',
        ]
        for p in ai_preamble_patterns:
            text = re.sub(p, '', text, count=1, flags=re.IGNORECASE | re.MULTILINE)
        text = text.lstrip('\n')

        # Убираем лишние маркеры
        markers_to_remove = [
            "```html", "```", "---", "===",
            "[HOOK]", "[/HOOK]", "[CTA]", "[/CTA]",
            "[LINK1]", "[/LINK1]", "[LINK2]", "[/LINK2]"
        ]
        
        for marker in markers_to_remove:
            text = text.replace(marker, "")
        
        # Убираем множественные переносы строк (но не трогаем двойные между ссылками)
        while "\n\n\n\n" in text:
            text = text.replace("\n\n\n\n", "\n\n")
        
        return text.strip()
    
    def _smart_trim(self, text: str, max_length: int) -> str:
        """
        Умно обрезает текст до max_length, сохраняя ссылки.
        Старается обрезать по концу предложения.
        """
        if len(text) <= max_length:
            return text
        
        # Сначала находим позиции ссылок
        url1_pos = text.find(self.url1)
        url2_pos = text.find(self.url2)
        
        # Если обе ссылки в пределах max_length, просто обрезаем после них
        max_url_pos = max(url1_pos + len(self.url1), url2_pos + len(self.url2))
        
        if max_url_pos < max_length:
            # Ищем конец предложения после ссылок
            for i in range(max_url_pos, min(len(text), max_length)):
                if text[i] in '.!?':
                    return text[:i+1].strip()
            return text[:max_length].strip()
        
        # Если ссылки не помещаются, обрезаем до них и добавляем обратно
        # Ищем первое полное предложение где поместятся обе ссылки
        for i in range(max_length - 100, max_length):
            if i < len(text) and text[i] in '.!?\n':
                trimmed = text[:i+1].strip()
                # Проверяем что обе ссылки есть
                if self.url1 in trimmed and self.url2 in trimmed:
                    return trimmed
        
        # Fallback - просто обрезаем
        return text[:max_length].strip()
    
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
