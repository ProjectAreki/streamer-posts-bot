"""
@file: ai_image_generator.py
@description: Генератор изображений через Nano Banana (Gemini) API
@created: 2026-01-19

Поддерживаемые модели:
- google/gemini-2.5-flash-image (Nano Banana) - быстрая, дешевая
- google/gemini-3-pro-image-preview (Nano Banana Pro) - лучшее качество, дороже

Функционал:
- Генерация изображений на основе текста поста
- Стиль: мемы + тренды 2025-2026
- Поддержка перегенерации
"""

import os
import base64
import aiohttp
import asyncio
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class GeneratedImage:
    """Результат генерации изображения"""
    image_data: bytes  # Бинарные данные изображения
    image_base64: str  # Base64 строка
    model_used: str    # Какая модель использовалась
    prompt_used: str   # Какой промпт использовался
    generation_time: float  # Время генерации в секундах
    
    def save_to_file(self, path: str):
        """Сохраняет изображение в файл"""
        with open(path, 'wb') as f:
            f.write(self.image_data)


class AIImageGenerator:
    """
    Генератор изображений через Gemini (Nano Banana) API.
    
    Использует OpenRouter для доступа к моделям Gemini.
    """
    
    # Доступные модели
    MODELS = {
        'nano_banana': 'google/gemini-2.5-flash-image',
        'nano_banana_pro': 'google/gemini-3-pro-image-preview',
    }
    
    # Базовый промпт для генерации изображений
    BASE_IMAGE_PROMPT = """Создай уникальную картинку для поста в Telegram-канале о гемблинге.

КОНТЕКСТ ПОСТА:
{post_text}

ТРЕБОВАНИЯ К КАРТИНКЕ:
1. СТИЛЬ: Актуальный мем 2025-2026 года ИЛИ узнаваемый интернет-персонаж
2. ТЕМА: Соответствует посту (казино, слоты, выигрыш, азарт, удача)
3. ЭМОЦИЯ: Смешная, ироничная, цепляющая взгляд
4. КАЧЕСТВО: Яркие цвета, высокий контраст, читаемость на маленьком экране

ОБЯЗАТЕЛЬНО:
- Персонаж или мем должен быть узнаваемым (популярные мемы 2025-2026)
- Картинка должна вызывать эмоцию (смех, интерес, узнавание)
- Подходить под тему поста
- Неоновые/яркие цвета приветствуются

ЗАПРЕЩЕНО:
- Текст на картинке (текст будет в самом посте)
- Логотипы казино или брендов
- Скучные стоковые фото
- Прямая реклама
- Насилие, оружие

ФОРМАТ: Квадрат 1024x1024, яркий, контрастный
ЯЗЫК КОНТЕКСТА: Русский"""

    def __init__(
        self,
        api_key: str = None,
        model: str = 'nano_banana_pro',
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        """
        Args:
            api_key: OpenRouter API ключ
            model: Модель для генерации ('nano_banana' или 'nano_banana_pro')
            base_url: Base URL для API
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY не найден")
        
        self.base_url = base_url
        self.model_key = model
        self.model = self.MODELS.get(model, self.MODELS['nano_banana_pro'])
        
        # Дополнительные промпты для разнообразия
        self.meme_styles = [
            "в стиле популярного мема 2025 года",
            "с узнаваемым интернет-персонажем",
            "в стиле абстрактного неонового арта",
            "с персонажем в стиле аниме",
            "в стиле ретро-аркады 80х",
            "с 3D персонажем в мультяшном стиле",
            "в стиле киберпанк",
            "с золотыми монетами и свечением",
        ]
    
    async def generate_image(
        self,
        post_text: str,
        custom_prompt: str = None,
        style_hint: str = None
    ) -> GeneratedImage:
        """
        Генерирует изображение на основе текста поста.
        
        Args:
            post_text: Текст поста для которого генерируем картинку
            custom_prompt: Кастомный промпт (если нужен)
            style_hint: Подсказка стиля (опционально)
            
        Returns:
            GeneratedImage с данными изображения
        """
        import random
        
        start_time = datetime.now()
        
        # Формируем промпт
        if custom_prompt:
            prompt = custom_prompt
        else:
            # Берем случайный стиль для разнообразия
            style = style_hint or random.choice(self.meme_styles)
            
            # Сокращаем текст поста до 500 символов
            short_post = post_text[:500] if len(post_text) > 500 else post_text
            
            prompt = self.BASE_IMAGE_PROMPT.format(post_text=short_post)
            prompt += f"\n\nДОПОЛНИТЕЛЬНО: Сделай картинку {style}"
        
        # Вызываем API
        image_data, image_base64 = await self._call_gemini_image_api(prompt)
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        return GeneratedImage(
            image_data=image_data,
            image_base64=image_base64,
            model_used=self.model,
            prompt_used=prompt[:200] + "..." if len(prompt) > 200 else prompt,
            generation_time=generation_time
        )
    
    async def _call_gemini_image_api(self, prompt: str) -> Tuple[bytes, str]:
        """
        Вызывает Gemini API для генерации изображения.
        
        Args:
            prompt: Промпт для генерации
            
        Returns:
            (image_bytes, image_base64)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/streamer-posts-bot",
            "X-Title": "Streamer Posts Bot"
        }
        
        # Формируем запрос для генерации изображения
        # OpenRouter поддерживает modalities для Gemini image моделей
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"],
            "max_tokens": 4096
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                
                result = await response.json()
                
                # Извлекаем изображение из ответа
                # Gemini возвращает изображение в message.content как base64
                choices = result.get('choices', [])
                if not choices:
                    raise Exception("No choices in response")
                
                message = choices[0].get('message', {})
                content = message.get('content', '')
                
                # Проверяем разные форматы ответа
                # Вариант 1: content содержит массив с image part
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            if part.get('type') == 'image':
                                image_data = part.get('image', {})
                                if 'data' in image_data:
                                    base64_data = image_data['data']
                                    return base64.b64decode(base64_data), base64_data
                
                # Вариант 2: images в response
                images = result.get('images', [])
                if images:
                    base64_data = images[0] if isinstance(images[0], str) else images[0].get('data', '')
                    return base64.b64decode(base64_data), base64_data
                
                # Вариант 3: inline_data в content
                if isinstance(content, str) and content.startswith('data:image'):
                    # Формат: data:image/png;base64,....
                    base64_data = content.split(',')[1]
                    return base64.b64decode(base64_data), base64_data
                
                # Вариант 4: проверяем message.images
                msg_images = message.get('images', [])
                if msg_images:
                    if isinstance(msg_images[0], dict):
                        base64_data = msg_images[0].get('data', '') or msg_images[0].get('base64', '')
                    else:
                        base64_data = msg_images[0]
                    return base64.b64decode(base64_data), base64_data
                
                # Если изображение не найдено
                raise Exception(f"Image not found in response. Content type: {type(content)}, keys: {result.keys()}")
    
    async def regenerate_image(
        self,
        post_text: str,
        previous_prompt: str = None
    ) -> GeneratedImage:
        """
        Перегенерирует изображение с другим стилем.
        
        Args:
            post_text: Текст поста
            previous_prompt: Предыдущий использованный промпт (чтобы не повторять)
            
        Returns:
            Новое изображение
        """
        import random
        
        # Выбираем другой стиль
        style = random.choice(self.meme_styles)
        
        # Добавляем случайность
        variations = [
            "сделай совершенно другой подход",
            "попробуй неожиданный ракурс",
            "используй более яркие цвета",
            "добавь динамики и движения",
            "сделай более минималистично",
        ]
        variation = random.choice(variations)
        
        return await self.generate_image(
            post_text=post_text,
            style_hint=f"{style}, {variation}"
        )
    
    def get_available_models(self) -> Dict[str, str]:
        """Возвращает доступные модели"""
        return self.MODELS.copy()
    
    def set_model(self, model_key: str):
        """
        Устанавливает модель для генерации.
        
        Args:
            model_key: 'nano_banana' или 'nano_banana_pro'
        """
        if model_key not in self.MODELS:
            raise ValueError(f"Unknown model: {model_key}. Available: {list(self.MODELS.keys())}")
        
        self.model_key = model_key
        self.model = self.MODELS[model_key]
    
    @staticmethod
    def get_model_info() -> str:
        """Возвращает информацию о моделях"""
        return """
📸 Доступные модели для генерации изображений:

🍌 <b>Nano Banana</b> (gemini-2.5-flash-image)
   • Быстрая генерация
   • Дешевле (~$0.50 за 20 картинок)
   • Хорошее качество

🍌 <b>Nano Banana Pro</b> (gemini-3-pro-image-preview)
   • Лучшее качество
   • Дороже (~$3-5 за 20 картинок)
   • До 4K разрешение
   • Лучший рендеринг текста
"""


# ═══════════════════════════════════════════════════════════════
# ТЕСТИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════

async def test_image_generation():
    """Тестовая генерация"""
    generator = AIImageGenerator(model='nano_banana')
    
    test_post = """
    🎰 СЛОТ ДНЯ: GATES OF OLYMPUS
    
    Если хочешь экшена — это тот самый «греческий гром». ⚡️ 
    Графика яркая, анимации быстрые, без лишнего «мыла».
    
    Кластеры вместо линий — занос может прилететь с любого места.
    Мультипликаторы до х100… и да, иногда они стакаются.
    """
    
    try:
        print("🎨 Генерирую изображение...")
        result = await generator.generate_image(test_post)
        
        # Сохраняем результат
        output_path = "test_generated_image.png"
        result.save_to_file(output_path)
        
        print(f"✅ Изображение сохранено: {output_path}")
        print(f"⏱ Время генерации: {result.generation_time:.2f}с")
        print(f"🧠 Модель: {result.model_used}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_image_generation())
