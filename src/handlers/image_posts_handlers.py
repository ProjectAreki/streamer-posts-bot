"""
@file: image_posts_handlers.py
@description: Handlers для сценария "🖼 Посты с картинками"
@created: 2026-01-19

Сценарий генерации 20 постов с картинками на основе тем:
1. Ввод ссылок и бонусов
2. Выбор/генерация тем
3. Генерация текстов постов
4. Генерация картинок (Nano Banana)
5. Превью с возможностью перегенерации
6. Публикация в канал
"""

import os
import asyncio
import base64
from typing import List, Dict, Optional
from aiogram import types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from src.states import ImagePostsStates


def register_image_posts_handlers(bot_instance):
    """
    Регистрирует все handlers для сценария "Посты с картинками".
    
    Args:
        bot_instance: Экземпляр NinjaVideoBot
    """
    dp = bot_instance.dp
    bot = bot_instance.bot
    config_manager = bot_instance.config_manager
    logger = bot_instance.logger
    
    def get_scenarios_kb(user_id):
        return bot_instance.get_allowed_scenarios_keyboard(user_id)
    
    def is_allowed(user_id, scenario):
        return bot_instance.is_scenario_allowed(user_id, scenario)
    
    # ============================================
    # НАЧАЛО СЦЕНАРИЯ
    # ============================================
    
    @dp.message(lambda m: m.text == "🖼 Посты с картинками")
    async def image_posts_start(message: types.Message, state: FSMContext):
        """Начало сценария генерации постов с картинками"""
        await state.clear()
        
        if not is_allowed(message.from_user.id, "image_posts"):
            await message.answer("❌ У вас нет доступа к этому сценарию")
            return
        
        info_text = """
🖼 <b>Посты с картинками</b>

Генерация уникальных постов на основе тем с AI-картинками.

<b>Что входит:</b>
• 20 постов на разные темы
• AI-генерация картинок (Nano Banana)
• 2 ссылки с бонусами в каждом посте
• 80+ готовых тем + генерация новых

<b>Процесс:</b>
1. Укажите ссылки и бонусы
2. Выберите или сгенерируйте темы
3. AI создаст посты и картинки
4. Проверьте превью (можно перегенерировать)
5. Опубликуйте в канал

<b>Модели для картинок:</b>
🍌 Nano Banana - быстро и дёшево
🍌 Nano Banana Pro - лучшее качество

Начнём с ввода ссылок 👇
"""
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚀 Начать")],
                [KeyboardButton(text="📊 Статистика тем")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(info_text, parse_mode="HTML", reply_markup=keyboard)
        await state.set_state(ImagePostsStates.waiting_for_url1)
    
    @dp.message(ImagePostsStates.waiting_for_url1, lambda m: m.text == "📊 Статистика тем")
    async def show_topics_stats(message: types.Message, state: FSMContext):
        """Показывает статистику тем"""
        from src.topic_manager import TopicManager
        
        tm = TopicManager()
        stats = tm.get_usage_stats()
        
        text = f"""
📊 <b>Статистика тем</b>

📝 Всего тем: {stats['total_topics']}
✅ Неиспользованных: {stats['unused']}
🔄 Использованных: {stats['used']}

<b>По категориям:</b>
"""
        for cat_name, cat_stats in stats['by_category'].items():
            text += f"• {cat_name}: {cat_stats['unused']}/{cat_stats['total']}\n"
        
        await message.answer(text, parse_mode="HTML")
    
    @dp.message(ImagePostsStates.waiting_for_url1, lambda m: m.text == "❌ Отмена")
    async def cancel_image_posts(message: types.Message, state: FSMContext):
        """Отмена сценария"""
        await state.clear()
        await message.answer(
            "❌ Сценарий отменён",
            reply_markup=get_scenarios_kb(message.from_user.id)
        )
    
    # ============================================
    # ВВОД ССЫЛОК И БОНУСОВ
    # ============================================
    
    @dp.message(ImagePostsStates.waiting_for_url1, lambda m: m.text == "🚀 Начать")
    async def start_url_input(message: types.Message, state: FSMContext):
        """Начало ввода ссылок"""
        await message.answer(
            "🔗 <b>Шаг 1/4: Первая ссылка</b>\n\n"
            "Введите URL первого бонуса:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отмена")]],
                resize_keyboard=True
            )
        )
    
    @dp.message(ImagePostsStates.waiting_for_url1, lambda m: m.text and m.text.startswith("http"))
    async def url1_received(message: types.Message, state: FSMContext):
        """Получена первая ссылка"""
        await state.update_data(url1=message.text.strip())
        await state.set_state(ImagePostsStates.waiting_for_bonus1)
        
        await message.answer(
            "✅ Ссылка сохранена!\n\n"
            "🎁 <b>Опишите бонус первой ссылки</b>\n"
            "Например: <i>500 фриспинов + 150% к депозиту</i>",
            parse_mode="HTML"
        )
    
    @dp.message(ImagePostsStates.waiting_for_bonus1)
    async def bonus1_received(message: types.Message, state: FSMContext):
        """Получено описание первого бонуса"""
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Отменено", reply_markup=get_scenarios_kb(message.from_user.id))
            return
        
        await state.update_data(bonus1=message.text.strip())
        await state.set_state(ImagePostsStates.waiting_for_url2)
        
        await message.answer(
            "🔗 <b>Шаг 2/4: Вторая ссылка</b>\n\n"
            "Введите URL второго бонуса:",
            parse_mode="HTML"
        )
    
    @dp.message(ImagePostsStates.waiting_for_url2, lambda m: m.text and m.text.startswith("http"))
    async def url2_received(message: types.Message, state: FSMContext):
        """Получена вторая ссылка"""
        await state.update_data(url2=message.text.strip())
        await state.set_state(ImagePostsStates.waiting_for_bonus2)
        
        await message.answer(
            "✅ Ссылка сохранена!\n\n"
            "🎁 <b>Опишите бонус второй ссылки</b>\n"
            "Например: <i>30000₽ + 500 вращений</i>",
            parse_mode="HTML"
        )
    
    @dp.message(ImagePostsStates.waiting_for_bonus2)
    async def bonus2_received(message: types.Message, state: FSMContext):
        """Получено описание второго бонуса - переход к темам"""
        try:
            logger.info(f"[ImagePosts] bonus2_received triggered, text: {message.text[:50]}")
            
            if message.text == "❌ Отмена":
                await state.clear()
                await message.answer("❌ Отменено", reply_markup=get_scenarios_kb(message.from_user.id))
                return
            
            await state.update_data(bonus2=message.text.strip())
            await state.set_state(ImagePostsStates.topics_menu)
            
            logger.info("[ImagePosts] State set to topics_menu")
            
            # Показываем меню управления темами
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📝 Выбрать 20 тем автоматически")],
                    [KeyboardButton(text="👀 Посмотреть все темы")],
                    [KeyboardButton(text="✏️ Добавить свою тему")],
                    [KeyboardButton(text="🤖 Сгенерировать новые темы")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
            
            logger.info("[ImagePosts] Loading TopicManager...")
            from src.topic_manager import TopicManager
            tm = TopicManager()
            stats = tm.get_usage_stats()
            logger.info(f"[ImagePosts] Stats loaded: {stats}")
            
            await message.answer(
                f"📚 <b>Шаг 3/4: Темы для постов</b>\n\n"
                f"Доступно тем: {stats['total_topics']}\n"
                f"Неиспользованных: {stats['unused']}\n\n"
                f"Выберите действие:",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logger.info("[ImagePosts] Menu sent successfully")
            
        except Exception as e:
            logger.error(f"[ImagePosts] Error in bonus2_received: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await message.answer(f"❌ Ошибка: {e}")
    
    # ============================================
    # УПРАВЛЕНИЕ ТЕМАМИ
    # ============================================
    
    @dp.message(ImagePostsStates.topics_menu, lambda m: m.text == "📝 Выбрать 20 тем автоматически")
    async def auto_select_topics(message: types.Message, state: FSMContext):
        """Автоматический выбор 20 тем"""
        from src.topic_manager import TopicManager
        
        tm = TopicManager()
        topics = tm.get_topics_balanced_by_category(20)
        
        # Сохраняем выбранные темы
        await state.update_data(selected_topics=[t.to_dict() for t in topics])
        
        # Формируем список тем
        topics_text = tm.format_topics_list(topics)
        
        await state.set_state(ImagePostsStates.choosing_image_model)
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🍌 Nano Banana (быстро)")],
                [KeyboardButton(text="🍌 Nano Banana Pro (качество)")],
                [KeyboardButton(text="⏭ Без картинок")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            f"✅ <b>Выбрано 20 тем:</b>\n\n{topics_text}\n\n"
            f"📸 <b>Шаг 4/4: Генерация картинок</b>\n\n"
            f"Выберите модель для генерации картинок:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    @dp.message(ImagePostsStates.topics_menu, lambda m: m.text == "👀 Посмотреть все темы")
    async def view_all_topics(message: types.Message, state: FSMContext):
        """Просмотр всех тем"""
        from src.topic_manager import TopicManager
        
        tm = TopicManager()
        
        # Группируем по категориям
        text = "📚 <b>Все доступные темы:</b>\n\n"
        
        for cat_id, cat_info in tm.categories.items():
            topics = tm.get_topics_by_category(cat_id)
            if not topics:
                continue
            
            text += f"\n{cat_info['name']}:\n"
            for t in topics[:10]:  # Показываем первые 10
                status = "✅" if t.used_count == 0 else f"🔄 ({t.used_count}x)"
                text += f"  {status} {t.title}\n"
            
            if len(topics) > 10:
                text += f"  ... и ещё {len(topics) - 10} тем\n"
        
        await message.answer(text, parse_mode="HTML")
    
    @dp.message(ImagePostsStates.topics_menu, lambda m: m.text == "✏️ Добавить свою тему")
    async def start_add_topic(message: types.Message, state: FSMContext):
        """Начало добавления своей темы"""
        await state.set_state(ImagePostsStates.adding_custom_topic)
        
        await message.answer(
            "✏️ <b>Добавление темы</b>\n\n"
            "Введите тему в формате:\n"
            "<code>Название темы: описание</code>\n\n"
            "Или просто название темы.\n\n"
            "Можно добавить несколько тем (каждая на новой строке).",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Назад")]],
                resize_keyboard=True
            )
        )
    
    @dp.message(ImagePostsStates.adding_custom_topic)
    async def add_custom_topic(message: types.Message, state: FSMContext):
        """Добавление пользовательской темы"""
        if message.text == "⬅️ Назад":
            await state.set_state(ImagePostsStates.topics_menu)
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📝 Выбрать 20 тем автоматически")],
                    [KeyboardButton(text="👀 Посмотреть все темы")],
                    [KeyboardButton(text="✏️ Добавить свою тему")],
                    [KeyboardButton(text="🤖 Сгенерировать новые темы")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
            await message.answer("Меню тем:", reply_markup=keyboard)
            return
        
        from src.topic_manager import TopicManager
        
        tm = TopicManager()
        new_topics = tm.add_custom_topics_bulk(message.text)
        
        if new_topics:
            topics_list = "\n".join([f"• {t.title}" for t in new_topics])
            await message.answer(
                f"✅ <b>Добавлено {len(new_topics)} тем:</b>\n\n{topics_list}\n\n"
                f"Можете добавить ещё или нажмите ⬅️ Назад",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Не удалось добавить темы. Проверьте формат.")
    
    @dp.message(ImagePostsStates.topics_menu, lambda m: m.text == "🤖 Сгенерировать новые темы")
    async def start_generate_topics(message: types.Message, state: FSMContext):
        """Генерация новых тем через AI"""
        await state.set_state(ImagePostsStates.generating_new_topics)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="5 тем", callback_data="gen_topics:5")],
            [InlineKeyboardButton(text="10 тем", callback_data="gen_topics:10")],
            [InlineKeyboardButton(text="20 тем", callback_data="gen_topics:20")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="gen_topics:back")]
        ])
        
        await message.answer(
            "🤖 <b>Генерация новых тем</b>\n\n"
            "AI создаст новые уникальные темы на основе существующих 80.\n\n"
            "Сколько тем сгенерировать?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    @dp.callback_query(lambda c: c.data.startswith("gen_topics:"))
    async def generate_topics_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработка выбора количества тем для генерации"""
        action = callback.data.split(":")[1]
        
        if action == "back":
            await state.set_state(ImagePostsStates.topics_menu)
            await callback.message.delete()
            return
        
        count = int(action)
        await callback.message.edit_text(f"⏳ Генерирую {count} новых тем...")
        
        from src.topic_manager import TopicManager
        
        tm = TopicManager()
        
        try:
            new_topics = await tm.generate_new_topics(count)
            
            if new_topics:
                topics_list = "\n".join([f"• {t.title}: {t.description}" for t in new_topics])
                await callback.message.edit_text(
                    f"✅ <b>Сгенерировано {len(new_topics)} новых тем:</b>\n\n{topics_list}",
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text("❌ Не удалось сгенерировать темы")
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {e}")
        
        await state.set_state(ImagePostsStates.topics_menu)
    
    # ============================================
    # ВЫБОР МОДЕЛИ ДЛЯ КАРТИНОК
    # ============================================
    
    @dp.message(ImagePostsStates.choosing_image_model, lambda m: m.text in [
        "🍌 Nano Banana (быстро)", 
        "🍌 Nano Banana Pro (качество)",
        "⏭ Без картинок"
    ])
    async def image_model_selected(message: types.Message, state: FSMContext):
        """Выбрана модель для картинок - начинаем генерацию"""
        if message.text == "⏭ Без картинок":
            generate_images = False
            image_model = None
        elif "Pro" in message.text:
            generate_images = True
            image_model = "nano_banana_pro"
        else:
            generate_images = True
            image_model = "nano_banana"
        
        await state.update_data(
            generate_images=generate_images,
            image_model=image_model
        )
        
        data = await state.get_data()
        selected_topics = data.get('selected_topics', [])
        
        if not selected_topics:
            await message.answer("❌ Темы не выбраны!")
            return
        
        # Начинаем генерацию
        await state.set_state(ImagePostsStates.generating_posts)
        
        status_msg = await message.answer(
            f"🤖 <b>Генерация постов...</b>\n\n"
            f"📝 Тем: {len(selected_topics)}\n"
            f"📸 Картинки: {'Да' if generate_images else 'Нет'}\n"
            f"🧠 Модель картинок: {image_model or 'N/A'}\n\n"
            f"⏳ Прогресс: 0/{len(selected_topics)}",
            parse_mode="HTML"
        )
        
        # Запускаем генерацию
        try:
            from src.ai_image_post_generator import AIImagePostGenerator
            from src.topic_manager import Topic
            
            generator = AIImagePostGenerator(image_model=image_model or "nano_banana")
            generator.set_bonus_data(
                url1=data['url1'],
                bonus1=data['bonus1'],
                url2=data['url2'],
                bonus2=data['bonus2']
            )
            
            # Восстанавливаем объекты Topic
            topics = [Topic.from_dict(t) for t in selected_topics]
            
            generated_posts = []
            
            for i, topic in enumerate(topics):
                try:
                    await status_msg.edit_text(
                        f"🤖 <b>Генерация постов...</b>\n\n"
                        f"📝 Тема: {topic.title[:30]}...\n"
                        f"📸 Картинки: {'Да' if generate_images else 'Нет'}\n\n"
                        f"⏳ Прогресс: {i}/{len(topics)}\n"
                        f"{'█' * (i * 20 // len(topics))}{'░' * (20 - i * 20 // len(topics))}",
                        parse_mode="HTML"
                    )
                except:
                    pass
                
                post = await generator.generate_post(
                    topic=topic,
                    index=i,
                    generate_image=generate_images
                )
                generated_posts.append(post.to_dict())
                
                await asyncio.sleep(0.3)
            
            # Сохраняем результат
            await state.update_data(generated_posts=generated_posts)
            await state.set_state(ImagePostsStates.preview_posts)
            
            await status_msg.edit_text(
                f"✅ <b>Генерация завершена!</b>\n\n"
                f"📝 Постов: {len(generated_posts)}\n"
                f"📸 С картинками: {sum(1 for p in generated_posts if p.get('has_image'))}\n\n"
                f"Нажмите кнопку для превью:",
                parse_mode="HTML"
            )
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="👀 Превью постов")],
                    [KeyboardButton(text="📤 Выбрать канал и опубликовать")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
            
            await message.answer("Готово! Что дальше?", reply_markup=keyboard)
            
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка генерации: {e}")
            logger.error(f"Image posts generation error: {e}")
    
    # ============================================
    # ПРЕВЬЮ ПОСТОВ
    # ============================================
    
    @dp.message(ImagePostsStates.preview_posts, lambda m: m.text == "👀 Превью постов")
    async def show_posts_preview(message: types.Message, state: FSMContext):
        """Показывает превью сгенерированных постов"""
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        
        if not posts:
            await message.answer("❌ Нет сгенерированных постов")
            return
        
        await state.update_data(current_preview_index=0)
        await show_single_post_preview(message, state, 0)
    
    async def show_single_post_preview(message: types.Message, state: FSMContext, index: int):
        """Показывает превью одного поста"""
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        
        if index < 0 or index >= len(posts):
            return
        
        post = posts[index]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"preview_nav:{index-1}"),
                InlineKeyboardButton(text=f"{index+1}/{len(posts)}", callback_data="preview_info"),
                InlineKeyboardButton(text="➡️", callback_data=f"preview_nav:{index+1}")
            ],
            [
                InlineKeyboardButton(text="🔄 Перегенерировать картинку", callback_data=f"regen_img:{index}")
            ],
            [
                InlineKeyboardButton(text="✏️ Перегенерировать текст", callback_data=f"regen_txt:{index}")
            ]
        ])
        
        text = f"📝 <b>Пост #{index+1}</b>\n"
        text += f"📌 Тема: {post.get('topic_title', 'N/A')}\n\n"
        text += post.get('text', '')[:1000]
        
        if post.get('image_base64'):
            # Отправляем с картинкой
            try:
                image_bytes = base64.b64decode(post['image_base64'])
                photo = BufferedInputFile(image_bytes, filename=f"post_{index}.png")
                await message.answer_photo(
                    photo=photo,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            except Exception as e:
                await message.answer(
                    text + f"\n\n⚠️ Ошибка картинки: {e}",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        else:
            await message.answer(
                text + "\n\n📸 <i>Без картинки</i>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
    
    @dp.callback_query(lambda c: c.data.startswith("preview_nav:"))
    async def navigate_preview(callback: types.CallbackQuery, state: FSMContext):
        """Навигация по превью"""
        index = int(callback.data.split(":")[1])
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        
        if index < 0:
            index = len(posts) - 1
        elif index >= len(posts):
            index = 0
        
        await state.update_data(current_preview_index=index)
        await callback.message.delete()
        await show_single_post_preview(callback.message, state, index)
        await callback.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("regen_img:"))
    async def regenerate_image(callback: types.CallbackQuery, state: FSMContext):
        """Перегенерация картинки для поста"""
        index = int(callback.data.split(":")[1])
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        
        if index >= len(posts):
            await callback.answer("Ошибка")
            return
        
        await callback.answer("🎨 Генерирую новую картинку...")
        
        try:
            from src.ai_image_generator import AIImageGenerator
            
            post = posts[index]
            image_model = data.get('image_model', 'nano_banana')
            
            generator = AIImageGenerator(model=image_model)
            image = await generator.regenerate_image(post.get('text_plain', post.get('text', '')))
            
            # Обновляем пост
            post['image_base64'] = image.image_base64
            post['has_image'] = True
            posts[index] = post
            
            await state.update_data(generated_posts=posts)
            
            # Показываем обновленный пост
            await callback.message.delete()
            await show_single_post_preview(callback.message, state, index)
            
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка перегенерации: {e}")
    
    @dp.callback_query(lambda c: c.data.startswith("regen_txt:"))
    async def regenerate_text(callback: types.CallbackQuery, state: FSMContext):
        """Перегенерация текста поста"""
        index = int(callback.data.split(":")[1])
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        
        if index >= len(posts):
            await callback.answer("Ошибка")
            return
        
        await callback.answer("📝 Генерирую новый текст...")
        
        try:
            from src.ai_image_post_generator import AIImagePostGenerator
            from src.topic_manager import Topic
            
            post = posts[index]
            
            generator = AIImagePostGenerator()
            generator.set_bonus_data(
                url1=data['url1'],
                bonus1=data['bonus1'],
                url2=data['url2'],
                bonus2=data['bonus2']
            )
            
            # Восстанавливаем тему
            selected_topics = data.get('selected_topics', [])
            if index < len(selected_topics):
                topic = Topic.from_dict(selected_topics[index])
            else:
                topic = Topic(id=0, category="custom", title="Custom", description="")
            
            # Генерируем только текст
            new_post = await generator.generate_post(
                topic=topic,
                index=index,
                generate_image=False
            )
            
            # Сохраняем старую картинку
            old_image = post.get('image_base64')
            
            # Обновляем пост
            post['text'] = new_post.text
            post['text_plain'] = new_post.text_plain
            post['image_base64'] = old_image
            posts[index] = post
            
            await state.update_data(generated_posts=posts)
            
            # Показываем обновленный пост
            await callback.message.delete()
            await show_single_post_preview(callback.message, state, index)
            
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка перегенерации: {e}")
    
    # ============================================
    # ПУБЛИКАЦИЯ
    # ============================================
    
    @dp.message(ImagePostsStates.preview_posts, lambda m: m.text == "📤 Выбрать канал и опубликовать")
    async def select_channel_for_publish(message: types.Message, state: FSMContext):
        """Выбор канала для публикации - показываем меню"""
        await state.set_state(ImagePostsStates.waiting_for_target_channel)
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Мои каналы")],
                [KeyboardButton(text="📝 Ввести канал вручную")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
        
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        
        await message.answer(
            f"📺 <b>Выберите канал для публикации</b>\n\n"
            f"📝 Готово постов: {len(posts)}\n"
            f"📸 С картинками: {sum(1 for p in posts if p.get('has_image'))}",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    @dp.message(ImagePostsStates.waiting_for_target_channel, lambda m: m.text == "📋 Мои каналы")
    async def show_my_channels(message: types.Message, state: FSMContext):
        """Показать список каналов пользователя"""
        try:
            user_id = message.from_user.id
            
            # Получаем каналы через стандартный метод
            user_channels = await bot_instance.get_user_channels(user_id)
            
            if not user_channels:
                await message.answer(
                    "У вас нет сохранённых каналов.\n\n"
                    "Введите @username или ID канала вручную."
                )
                return
            
            # Сохраняем каналы в state для последующего поиска
            await state.update_data(user_channels=user_channels)
            
            keyboard_buttons = []
            for ch in user_channels[:15]:  # Макс 15 каналов
                name = ch.get('title') or ch.get('username') or str(ch.get('id'))
                keyboard_buttons.append([KeyboardButton(text=f"📢 {name}")])
            
            keyboard_buttons.append([KeyboardButton(text="📝 Ввести вручную")])
            keyboard_buttons.append([KeyboardButton(text="❌ Отмена")])
            
            keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)
            await message.answer("📺 Выберите канал для публикации:", reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Ошибка получения каналов: {e}")
            await message.answer(f"❌ Ошибка: {e}\n\nВведите @username или ID канала вручную.")
    
    @dp.message(ImagePostsStates.waiting_for_target_channel, lambda m: m.text == "📝 Ввести канал вручную")
    async def enter_channel_manually(message: types.Message, state: FSMContext):
        """Ввод канала вручную"""
        await message.answer(
            "Введите @username или ID канала:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отмена")]],
                resize_keyboard=True
            )
        )
    
    @dp.message(ImagePostsStates.waiting_for_target_channel)
    async def channel_selected(message: types.Message, state: FSMContext):
        """Канал выбран - подтверждение публикации"""
        if message.text == "❌ Отмена":
            await state.set_state(ImagePostsStates.preview_posts)
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="👀 Превью постов")],
                    [KeyboardButton(text="📤 Выбрать канал и опубликовать")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
            await message.answer("Возврат к превью", reply_markup=keyboard)
            return
        
        if message.text == "📝 Ввести вручную":
            await enter_channel_manually(message, state)
            return
        
        # Определяем канал
        channel_input = message.text.replace("📢 ", "").strip()
        
        try:
            # Сначала ищем в кэше каналов из state
            data = await state.get_data()
            user_channels = data.get('user_channels', [])
            channel_id = None
            channel_name = None
            
            for ch in user_channels:
                ch_name = ch.get('title') or ch.get('username')
                if ch_name == channel_input:
                    channel_id = ch.get('id')
                    channel_name = ch_name
                    break
            
            # Если не нашли в кэше - используем Telethon
            if not channel_id:
                from src.telethon_manager import TelethonClientManager
                manager = TelethonClientManager.get_instance(config_manager)
                await manager.ensure_initialized()
                client = manager.get_client()
                
                if not client:
                    await message.answer("❌ Telethon клиент не инициализирован")
                    return
                
                # Получаем entity через Telethon
                try:
                    if channel_input.startswith("@"):
                        entity = await client.get_entity(channel_input)
                    elif channel_input.lstrip('-').isdigit():
                        entity = await client.get_entity(int(channel_input))
                    else:
                        entity = await client.get_entity(channel_input)
                    
                    channel_id = entity.id
                    channel_name = getattr(entity, 'title', None) or getattr(entity, 'username', str(channel_id))
                except Exception as e:
                    await message.answer(
                        f"❌ Канал не найден: {e}\n\n"
                        "Проверьте правильность @username или ID"
                    )
                    return
            
            # Сохраняем канал для публикации
            await state.update_data(target_channel_id=channel_id, target_channel_name=channel_name)
        
        except Exception as e:
            logger.error(f"Ошибка определения канала: {e}")
            await message.answer(f"❌ Ошибка: {e}")
            return
        
        # Переходим к подтверждению
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        channel_name = data.get('target_channel_name', 'N/A')
        
        await state.set_state(ImagePostsStates.confirming_publish)
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Опубликовать")],
                [KeyboardButton(text="⬅️ Назад")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            f"📤 <b>Подтверждение публикации</b>\n\n"
            f"📝 Постов: {len(posts)}\n"
            f"📸 С картинками: {sum(1 for p in posts if p.get('has_image'))}\n"
            f"📢 Канал: {channel_name}\n\n"
            f"Опубликовать посты?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    @dp.message(ImagePostsStates.confirming_publish, lambda m: m.text == "✅ Опубликовать")
    async def publish_posts(message: types.Message, state: FSMContext):
        """Публикация постов через Telethon"""
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        channel_id = data.get('target_channel_id')
        channel_name = data.get('target_channel_name', 'канал')
        
        if not posts or not channel_id:
            await message.answer("❌ Нет данных для публикации")
            return
        
        await state.set_state(ImagePostsStates.publishing)
        
        status_msg = await message.answer("📤 Публикация постов...")
        
        published = 0
        errors = 0
        
        try:
            from src.telethon_manager import TelethonClientManager
            manager = TelethonClientManager.get_instance(config_manager)
            await manager.ensure_initialized()
            client = manager.get_client()
            
            if not client:
                await status_msg.edit_text("❌ Telethon клиент не инициализирован")
                return
            
            # Получаем entity канала
            entity = await client.get_entity(channel_id)
            
            for i, post in enumerate(posts):
                try:
                    text = post.get('text', '')
                    
                    if post.get('image_base64'):
                        import io
                        image_bytes = base64.b64decode(post['image_base64'])
                        image_file = io.BytesIO(image_bytes)
                        image_file.name = f"post_{i}.png"
                        
                        await client.send_file(
                            entity,
                            file=image_file,
                            caption=text,
                            parse_mode='html'
                        )
                    else:
                        await client.send_message(
                            entity,
                            message=text,
                            parse_mode='html'
                        )
                    
                    published += 1
                    
                    # Обновляем статус каждые 5 постов
                    if (i + 1) % 5 == 0:
                        try:
                            await status_msg.edit_text(
                                f"📤 Публикация: {i+1}/{len(posts)}\n"
                                f"{'█' * ((i+1) * 20 // len(posts))}{'░' * (20 - (i+1) * 20 // len(posts))}"
                            )
                        except:
                            pass
                    
                    await asyncio.sleep(1)  # Задержка между постами
                    
                except Exception as e:
                    errors += 1
                    logger.error(f"Error publishing post {i}: {e}")
            
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка публикации: {e}")
            logger.error(f"Publishing error: {e}")
            return
        
        await state.clear()
        
        await status_msg.edit_text(
            f"✅ <b>Публикация завершена!</b>\n\n"
            f"📝 Опубликовано: {published}\n"
            f"❌ Ошибок: {errors}\n"
            f"📢 Канал: {channel_name}",
            parse_mode="HTML"
        )
        
        await message.answer(
            "Готово! Возвращаюсь в главное меню.",
            reply_markup=get_scenarios_kb(message.from_user.id)
        )
    
    @dp.message(ImagePostsStates.confirming_publish, lambda m: m.text == "⬅️ Назад")
    async def back_to_preview(message: types.Message, state: FSMContext):
        """Назад к превью"""
        await state.set_state(ImagePostsStates.preview_posts)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👀 Превью постов")],
                [KeyboardButton(text="📤 Выбрать канал и опубликовать")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
        await message.answer("Возврат к превью", reply_markup=keyboard)
    
    # Общий обработчик отмены
    @dp.message(StateFilter(ImagePostsStates), lambda m: m.text == "❌ Отмена")
    async def cancel_anywhere(message: types.Message, state: FSMContext):
        """Отмена из любого состояния"""
        await state.clear()
        await message.answer(
            "❌ Сценарий отменён",
            reply_markup=get_scenarios_kb(message.from_user.id)
        )
