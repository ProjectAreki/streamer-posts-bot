"""
@file: spanish_posts_handlers.py
@description: Handlers para el escenario "100 posteos en español"
@dependencies: aiogram, src.states
@created: 2026-01-24

Este módulo contiene todos los handlers para el escenario de generación de 100 posts en español.
Para usar, llama register_spanish_handlers(bot_instance) desde _register_handlers().
"""

import os
import asyncio
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from src.states import SpanishPostsStates


def register_spanish_handlers(bot_instance):
    """
    Registra todos los handlers para el escenario "100 posteos en español".
    
    Args:
        bot_instance: Instancia del bot con acceso a dp, bot, config_manager, etc.
    """
    # Ссылки на нужные объекты
    dp = bot_instance.dp
    bot = bot_instance.bot
    config_manager = bot_instance.config_manager
    db_manager = bot_instance.db_manager
    logger = bot_instance.logger
    chat_scanner = bot_instance.chat_scanner
    
    # Хелпер для получения клавиатуры сценариев
    def get_scenarios_kb(user_id):
        return bot_instance.get_allowed_scenarios_keyboard(user_id)
    
    # Хелпер для проверки доступа
    def is_allowed(user_id, scenario):
        return bot_instance.is_scenario_allowed(user_id, scenario)
    
    # Хелпер для показа каналов
    async def show_channels(message, state):
        return await bot_instance.show_user_channels(message, state)

    # ============================================
    # ОБРАБОТЧИКИ СЦЕНАРИЯ "100 ПОСТОВ СТРИМЕРОВ"
    # ============================================

    @dp.message(lambda m: m.text == "📹ES 100 posteos")
    async def spanish_posts_start_handler(message: types.Message, state: FSMContext):
        """Начало сценария 100 постов на испанском"""
        await state.clear()
    
        if not is_allowed(message.from_user.id, "spanish_posts"):
            await message.answer("❌ У вас нет доступа к этому сценарию")
            return

        info_text = """
    📹ES <b>100 постов на испанском</b>

    Генерация уникальных постов о победах в слотах на испанском языке.

    <b>Что включает:</b>
    • 80 видео + текст (победы в слотах)
    • 20 изображений + текст (бонусы)
    • 1 ссылка с бонусом в каждой публикации

    <b>Что делает бот:</b>
    • 55 уникальных структур для видео
    • 20 стилей написания текста  
    • Рандомизация описаний бонусов
    • 15 форматов блоков ссылок

    <b>412,500 возможных комбинаций!</b>

    <b>Формат имен файлов видео:</b>
    <code>Slot_Ставка_Выигрыш.mp4</code>
    Пример: <code>Gates of Olympus_50_12500.mp4</code>

    <b>Шаги:</b>
    1. Укажи ссылку и бонус
    2. Отправь файлы видео
    3. Отправь изображения для бонусов
    4. Выбери канал для публикации
    5. Подтверди и запусти!

    Начнем со ссылок и бонусов 👇
    """

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚀 Начать настройку")],
                [KeyboardButton(text="📖 Как именовать файлы")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )

        await message.answer(info_text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(SpanishPostsStates.waiting_for_url1)

    @dp.message(SpanishPostsStates.waiting_for_url1, lambda m: m.text == "📖 Как именовать файлы")
    async def streamer_posts_naming_help(message: types.Message, state: FSMContext):
        """Справка по именованию файлов"""
        help_text = """
    📖 <b>Как именовать видео файлы</b>

    <b>Формат:</b>
    <code>Slot_Ставка_Выигрыш.mp4</code>
    или
    <code>Jugador_Slot_Ставка_Выигрыш.mp4</code>

    <b>Примеры:</b>
    • <code>Gates_of_Olympus_50USD_12500USD.mp4</code>
    • <code>Sweet_Bonanza_100EUR_25000EUR.mp4</code>
    • <code>Pedro_Gates_of_Olympus_50_12500.mp4</code>
    • <code>Book_of_Dead_10000CLP_500000CLP.mp4</code>

    <b>Разделители:</b>
    Можно использовать <code>_</code> или <code>-</code>

    <b>Автоматически рассчитывается:</b>
    • Множитель (x250)
    • Чистая прибыль
    • ROI в процентах

    <b>Если нет метаданных в имени:</b>
    Бот попросит ввести данные вручную.
    """
        await message.answer(help_text, parse_mode="HTML")

    @dp.message(SpanishPostsStates.waiting_for_url1, lambda m: m.text == "🚀 Начать настройку")
    async def streamer_posts_begin_setup(message: types.Message, state: FSMContext):
        """Начало настройки - запрос первой ссылки"""
        await message.answer(
            "🔗 <b>Шаг 1/3: Первая ссылка</b>\n\n"
            "Введите URL первого бонуса:\n"
            "(например: https://example.com/bonus1)",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отмена")]],
                resize_keyboard=True
            )
        )

    @dp.message(SpanishPostsStates.waiting_for_url1)
    async def streamer_posts_url1_handler(message: types.Message, state: FSMContext):
        """Обработка первой ссылки"""
        if message.text in ["❌ Отмена", "❌ Cancelar"]:
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        url1 = message.text.strip()
        if not url1.startswith("http"):
            await message.answer("❌ Введите корректный URL (начинается с http:// или https://)")
            return
    
        await state.update_data(url1=url1)
        await state.set_state(SpanishPostsStates.waiting_for_bonus1)
    
        await message.answer(
            f"✅ Ссылка: {url1}\n\n"
            "🎁 <b>Шаг 2/3: Описание бонуса</b>\n\n"
            "Введите описание бонуса:\n"
            "(например: 100 FS или 150% до $100)",
            parse_mode="HTML"
        )

    @dp.message(SpanishPostsStates.waiting_for_bonus1)
    async def streamer_posts_bonus1_handler(message: types.Message, state: FSMContext):
        """Обработка описания бонуса → выбор источника видео"""
        if message.text in ["❌ Отмена", "❌ Cancelar"]:
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        bonus1 = message.text.strip()
        await state.update_data(bonus1=bonus1, videos=[], video_metadata=[], images=[])
    
        data = await state.get_data()
    
        summary = f"""
    ✅ <b>Ссылка и бонус настроены!</b>

    🔗 Ссылка: {data['url1']}
    🎁 Бонус: {bonus1}

    ━━━━━━━━━━━━━━━━━━━━━━━
    <b>📹 Шаг 2: Откуда брать видео?</b>

    📡 <b>Из канала</b> — укажи канал с нарезанными видео
    📤 <b>Загрузить</b> — отправь видео прямо в чат
    """
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📡 Взять из канала")],
                [KeyboardButton(text="📤 Загрузить вручную")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        await state.set_state(SpanishPostsStates.choosing_video_source)
        await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")

    @dp.message(SpanishPostsStates.choosing_video_source, lambda m: m.text == "📡 Взять из канала")
    async def streamer_posts_choose_channel_source(message: types.Message, state: FSMContext):
        """Выбран источник - канал"""
        await state.set_state(SpanishPostsStates.waiting_for_source_channel)
        await state.update_data(streamer_posts_flow=True)
    
        await message.answer(
            "📡 <b>Канал с видео</b>\n\n"
            "Выберите способ указать источник:\n\n"
            "• 📋 <b>Мои каналы</b> — выбрать из списка\n"
            "• 🔗 <b>Ссылка на пост</b> — начать с конкретного поста\n"
            "• 📝 <b>Ввести вручную</b> — ввести @username или ID\n\n"
            "<i>Бот автоматически распарсит данные из подписей</i>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📋 Мои каналы"), KeyboardButton(text="🔗 Ссылка на пост")],
                    [KeyboardButton(text="📝 Ввести вручную"), KeyboardButton(text="🔄 Обновить мои каналы")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
        )

    @dp.message(SpanishPostsStates.waiting_for_source_channel)
    async def streamer_posts_source_channel_handler(message: types.Message, state: FSMContext):
        """Обработка канала-источника"""
        if message.text == "❌ Отмена":
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        # Игнорируем кнопки выбора источника (на случай дублирующих сообщений)
        if message.text in ["📡 Взять из канала", "📤 Загрузить вручную"]:
            return
    
        # Поддержка кнопки "Мои каналы"
        if message.text == "📋 Мои каналы":
            await state.update_data(streamer_posts_flow=True)
            await show_channels(message, state)
            return
    
        # Поддержка кнопки "Обновить каналы"
        if message.text == "🔄 Обновить мои каналы":
            await message.answer("🔄 Обновляю список каналов...")
            chat_scanner.refresh_cache()
            await state.update_data(streamer_posts_flow=True)
            await show_channels(message, state)
            return
    
        # Поддержка кнопки "Ввести вручную"
        if message.text == "📝 Ввести вручную":
            await message.answer(
                "📝 Введите @username или ID канала:",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="❌ Отмена")]],
                    resize_keyboard=True
                )
            )
            return
    
        # Поддержка кнопки "Ссылка на пост" (НОВОЕ!)
        if message.text == "🔗 Ссылка на пост":
            await state.set_state(SpanishPostsStates.waiting_for_post_link)
            await message.answer(
                "🔗 <b>Ссылка на стартовый пост</b>\n\n"
                "Отправьте ссылку на пост, с которого начать:\n\n"
                "Формат: <code>https://t.me/c/CHANNEL_ID/MESSAGE_ID</code>\n"
                "Пример: <code>https://t.me/c/3542533378/83</code>\n\n"
                "<i>Бот начнёт обработку с этого поста</i>",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="❌ Отмена")]],
                    resize_keyboard=True
                )
            )
            return
    
        channel_input = message.text.strip()
    
        # Проверяем - может это ссылка на пост?
        if 't.me/' in channel_input and ('/' in channel_input.split('t.me/')[1]):
            await message.answer(
                "⚠️ <b>Вы ввели ссылку на пост!</b>\n\n"
                "Для работы со ссылкой нажмите кнопку:\n"
                "🔗 <b>Ссылка на пост</b>\n\n"
                "Или введите просто @username или ID канала.",
                parse_mode="HTML"
            )
            return
    
        try:
            # Сначала проверяем - может это название канала из кэша?
            data = await state.get_data()
            user_channels = data.get('user_channels', [])
        
            channel_id = None
            channel_name = None
        
            # Ищем канал по названию в кэше
            for ch in user_channels:
                if ch.get('title') == channel_input:
                    channel_id = ch.get('id')
                    channel_name = ch.get('title')
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
                        # Пробуем как username
                        entity = await client.get_entity(channel_input)
                
                    channel_id = entity.id
                    channel_name = getattr(entity, 'title', None) or getattr(entity, 'username', str(channel_id))
                except Exception as e:
                    await message.answer(
                        f"❌ Канал не найден: {e}\n\n"
                        "Проверьте правильность @username или ID канала"
                    )
                    return
        
            await state.update_data(
                source_channel_id=channel_id,
                source_channel_name=channel_name
            )
        
            # Спрашиваем направление сканирования
            await message.answer(
                f"✅ Канал найден: <b>{channel_name}</b>\n\n"
                f"📂 <b>В каком порядке брать видео?</b>\n\n"
                f"🔼 <b>Сначала старые</b> — от первого поста к последнему\n"
                f"🔽 <b>Сначала новые</b> — от последнего поста к первому",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="🔼 Сначала старые")],
                        [KeyboardButton(text="🔽 Сначала новые")],
                        [KeyboardButton(text="❌ Отмена")]
                    ],
                    resize_keyboard=True
                )
            )
            await state.set_state(SpanishPostsStates.waiting_for_scan_direction)
        
        except Exception as e:
            logger.error(f"Ошибка доступа к каналу: {e}")
            await message.answer(
                f"❌ Ошибка: {e}\n\n"
                "Попробуйте ввести канал ещё раз"
            )

    @dp.message(SpanishPostsStates.waiting_for_post_link)
    async def streamer_posts_link_handler(message: types.Message, state: FSMContext):
        """Обработка ссылки на конкретный пост"""
        import re
    
        if message.text == "❌ Отмена":
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        link = message.text.strip()
    
        # Парсим ссылку формата https://t.me/c/CHANNEL_ID/MESSAGE_ID
        # Поддержка: t.me/c/3542533378/83 или https://t.me/c/3542533378/83
        pattern = r'(?:https?://)?t\.me/c/(\d+)/(\d+)'
        match = re.match(pattern, link)
    
        if not match:
            # Пробуем публичный формат: t.me/channel_name/123
            pattern_public = r'(?:https?://)?t\.me/([a-zA-Z0-9_]+)/(\d+)'
            match_public = re.match(pattern_public, link)
        
            if match_public:
                channel_username = match_public.group(1)
                message_id = int(match_public.group(2))
            
                # Получаем ID канала через Telethon
                try:
                    from src.telethon_manager import TelethonClientManager
                    manager = TelethonClientManager.get_instance(config_manager)
                    await manager.ensure_initialized()
                    client = manager.get_client()
                
                    entity = await client.get_entity(channel_username)
                    channel_id = entity.id
                    channel_name = getattr(entity, 'title', channel_username)
                
                    # Добавляем -100 для каналов
                    if not str(channel_id).startswith('-100'):
                        channel_id = int(f"-100{channel_id}")
                
                except Exception as e:
                    await message.answer(
                        f"❌ Не удалось найти канал @{channel_username}: {e}\n\n"
                        "Проверьте ссылку и попробуйте снова"
                    )
                    return
            else:
                await message.answer(
                    "❌ <b>Неверный формат ссылки!</b>\n\n"
                    "Ожидается:\n"
                    "• <code>https://t.me/c/3542533378/83</code>\n"
                    "• <code>https://t.me/channel_name/123</code>\n\n"
                    "Попробуйте ещё раз:",
                    parse_mode="HTML"
                )
                return
        else:
            # Приватный формат: t.me/c/CHANNEL_ID/MESSAGE_ID
            raw_channel_id = match.group(1)
            message_id = int(match.group(2))
        
            # Добавляем -100 для получения полного ID канала
            channel_id = int(f"-100{raw_channel_id}")
        
            # Получаем название канала
            try:
                from src.telethon_manager import TelethonClientManager
                manager = TelethonClientManager.get_instance(config_manager)
                await manager.ensure_initialized()
                client = manager.get_client()
            
                entity = await client.get_entity(channel_id)
                channel_name = getattr(entity, 'title', str(channel_id))
            except Exception as e:
                channel_name = f"Канал {raw_channel_id}"
                logger.warning(f"Не удалось получить название канала: {e}")
    
        # Сохраняем данные
        await state.update_data(
            source_channel_id=channel_id,
            source_channel_name=channel_name,
            start_message_id=message_id,  # Стартовый пост
            use_post_link=True  # Флаг что используем ссылку
        )
    
        # Спрашиваем направление
        await message.answer(
            f"✅ <b>Ссылка распознана!</b>\n\n"
            f"📺 Канал: <b>{channel_name}</b>\n"
            f"📝 Стартовый пост: <b>#{message_id}</b>\n\n"
            f"📂 <b>В каком направлении брать посты?</b>\n\n"
            f"🔽 <b>Вниз (к старым)</b> — #{message_id}, #{message_id-1}, #{message_id-2}...\n"
            f"🔼 <b>Вверх (к новым)</b> — #{message_id}, #{message_id+1}, #{message_id+2}...",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🔽 Вниз (к старым)")],
                    [KeyboardButton(text="🔼 Вверх (к новым)")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(SpanishPostsStates.waiting_for_scan_direction)

    @dp.message(SpanishPostsStates.waiting_for_scan_direction)
    async def streamer_posts_direction_handler(message: types.Message, state: FSMContext):
        """Обработка выбора направления сканирования"""
        if message.text == "❌ Отмена":
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        data = await state.get_data()
        use_post_link = data.get('use_post_link', False)
    
        # Поддержка обоих форматов кнопок
        if message.text in ["🔼 Сначала старые", "🔼 Вверх (к новым)"]:
            if use_post_link:
                # Для ссылки на пост: вверх = к новым постам
                scan_reverse = False
                direction_text = "к новым постам"
            else:
                # Для канала: сначала старые
                scan_reverse = True
                direction_text = "от старых к новым"
        elif message.text in ["🔽 Сначала новые", "🔽 Вниз (к старым)"]:
            if use_post_link:
                # Для ссылки на пост: вниз = к старым постам
                scan_reverse = True
                direction_text = "к старым постам"
            else:
                # Для канала: сначала новые
                scan_reverse = False
                direction_text = "от новых к старым"
        else:
            await message.answer("❌ Выберите направление кнопкой!")
            return
    
        await state.update_data(scan_reverse=scan_reverse)
    
        await message.answer(
            f"✅ Направление: <b>{direction_text}</b>\n\n"
            f"📊 <b>Сколько видео взять?</b>\n\n"
            f"Введите число (например: 80)",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="50"), KeyboardButton(text="80"), KeyboardButton(text="100")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(SpanishPostsStates.waiting_for_video_range)

    @dp.message(SpanishPostsStates.waiting_for_video_range)
    async def streamer_posts_video_range_handler(message: types.Message, state: FSMContext):
        """Обработка количества видео из канала"""
        if message.text == "❌ Отмена":
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        try:
            video_count = int(message.text.strip())
            if video_count < 1 or video_count > 500:
                await message.answer("❌ Введите число от 1 до 500")
                return
        except ValueError:
            await message.answer("❌ Введите число!")
            return
    
        data = await state.get_data()
        source_channel_id = data.get('source_channel_id')
        scan_reverse = data.get('scan_reverse', False)
        use_post_link = data.get('use_post_link', False)
        start_message_id = data.get('start_message_id')
    
        # Определяем текст направления
        if use_post_link and start_message_id:
            direction_text = "к старым" if scan_reverse else "к новым"
            start_text = f" от поста #{start_message_id}"
        else:
            direction_text = "от старых к новым" if scan_reverse else "от новых к старым"
            start_text = ""
    
        status_msg = await message.answer(
            f"🔍 <b>Сканирую канал...</b>\n\n"
            f"Ищу {video_count} видео ({direction_text}){start_text}...",
            parse_mode="HTML"
        )
    
        # Сканируем канал через Telethon
        try:
            from src.caption_parser import CaptionParser
            from src.telethon_manager import TelethonClientManager
        
            manager = TelethonClientManager.get_instance(config_manager)
            await manager.ensure_initialized()
            client = manager.get_client()
        
            if not client:
                await status_msg.edit_text("❌ Telethon клиент не инициализирован")
                return
        
            videos_found = []
            videos_auto_parsed = []  # Видео с автопарсингом данных
            videos_need_input = []   # Видео без данных - нужен ручной ввод
        
            # Параметры для iter_messages
            iter_params = {
                'entity': source_channel_id,
                'limit': video_count * 2
            }
        
            # Если указана ссылка на пост - используем min_id/max_id
            if use_post_link and start_message_id:
                if scan_reverse:
                    # Вниз (к старым): max_id ограничивает сверху
                    iter_params['max_id'] = start_message_id + 1
                    iter_params['reverse'] = False  # от новых к старым
                else:
                    # Вверх (к новым): min_id ограничивает снизу
                    iter_params['min_id'] = start_message_id - 1
                    iter_params['reverse'] = True  # от старых к новым
            else:
                # Обычное сканирование без ссылки
                iter_params['reverse'] = scan_reverse
        
            async for msg in client.iter_messages(**iter_params):
                if msg.video:
                    caption = msg.text or ''
                
                    # Пробуем автопарсинг данных из подписи
                    parsed = CaptionParser.parse(caption)
                
                    # Сохраняем source_channel_id и message_id для копирования через Telethon
                    video_info = {
                        'file_id': None,  # Не нужен - будем копировать через Telethon
                        'message_id': msg.id,
                        'source_channel_id': source_channel_id,  # Для копирования
                        'caption': caption,
                        'file_name': msg.file.name if msg.file else f"video_{msg.id}.mp4",
                        'date': msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else '',
                        # Данные из парсинга
                        'slot': parsed.slot,
                        'bet': parsed.bet,
                        'win': parsed.win,
                        'streamer': parsed.streamer,
                        'multiplier': parsed.multiplier,
                        'currency': parsed.currency,  # Добавляем валюту
                        'auto_parsed': parsed.bet > 0 and parsed.win > 0  # Для испанского сценария слот не обязателен
                    }
                
                    videos_found.append(video_info)
                
                    # Для испанского сценария слот НЕ обязателен - достаточно ставки и выигрыша
                    if parsed.bet > 0 and parsed.win > 0:
                        videos_auto_parsed.append(video_info)
                    else:
                        videos_need_input.append(video_info)
                
                    if len(videos_found) >= video_count:
                        break
        
            if not videos_found:
                await status_msg.edit_text(
                    "❌ В канале не найдено видео!\n\n"
                    "Убедитесь что в канале есть видео-посты."
                )
                return
        
            await state.update_data(
                channel_videos=videos_found,
                videos_auto_parsed=videos_auto_parsed,
                videos_need_input=videos_need_input,
                current_video_index=0
            )
        
            # Если все видео автопарсились - сразу добавляем
            if len(videos_auto_parsed) == len(videos_found):
                await state.update_data(videos=videos_auto_parsed)
                await status_msg.edit_text(
                    f"✅ Найдено <b>{len(videos_found)}</b> видео!\n\n"
                    f"🤖 <b>Все данные распознаны автоматически!</b>\n\n"
                    f"Переходим к картинкам...",
                    parse_mode="HTML"
                )
                await _proceed_to_target_channel(message, state)
            else:
                await status_msg.edit_text(
                    f"✅ Найдено <b>{len(videos_found)}</b> видео!\n\n"
                    f"🤖 Автоматически распознано: <b>{len(videos_auto_parsed)}</b>\n"
                    f"✏️ Нужен ввод данных: <b>{len(videos_need_input)}</b>\n\n"
                    f"Сейчас покажу видео без данных...",
                    parse_mode="HTML"
                )
            
                # Сохраняем автопарсенные в videos
                await state.update_data(videos=videos_auto_parsed)
            
                # Показываем первое видео которое нужно заполнить
                await _show_channel_video_for_metadata(message, state, 0)
        
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка сканирования: {e}")

    async def _show_channel_video_for_metadata(message, state: FSMContext, index: int):
        """Показать видео из канала для ввода метаданных"""
        data = await state.get_data()
        videos_need_input = data.get('videos_need_input', [])
        videos = data.get('videos', [])
    
        if index >= len(videos_need_input):
            # Все видео обработаны - переходим к картинкам
            await _proceed_to_target_channel(message, state)
            return
    
        video = videos_need_input[index]
        caption_preview = video['caption'][:150] + "..." if len(video['caption']) > 150 else video['caption']
    
        await state.update_data(current_video_index=index)
        await state.set_state(SpanishPostsStates.entering_metadata_for_channel)
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⏭ Пропустить это видео")],
                [KeyboardButton(text="✅ Все видео готовы")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        await message.answer(
            f"📹 <b>Видео {index + 1} из {len(videos_need_input)}</b> (нужен ввод)\n"
            f"<i>Уже добавлено: {len(videos)} видео</i>\n\n"
            f"📝 Подпись:\n<code>{caption_preview or '(нет)'}</code>\n\n"
            f"<b>Введите данные:</b>\n"
            f"<code>Слот | Ставка | Выигрыш</code>\n\n"
            f"Пример: <code>Rip City | 300 | 644580</code>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @dp.message(SpanishPostsStates.entering_metadata_for_channel)
    async def streamer_posts_channel_metadata_handler(message: types.Message, state: FSMContext):
        """Обработка метаданных для видео из канала"""
        if message.text == "❌ Отмена":
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        data = await state.get_data()
        videos_need_input = data.get('videos_need_input', [])
        current_index = data.get('current_video_index', 0)
        videos = data.get('videos', [])
    
        if message.text == "⏭ Пропустить это видео":
            # Пропускаем и переходим к следующему
            await _show_channel_video_for_metadata(message, state, current_index + 1)
            return
    
        if message.text == "✅ Все видео готовы":
            # Завершаем ввод и переходим к картинкам
            if not videos:
                await message.answer("⚠️ Вы не добавили ни одного видео! Добавьте хотя бы одно.")
                return
            await _proceed_to_target_channel(message, state)
            return
    
        # Парсим данные
        parts = message.text.split('|')
        if len(parts) < 3:
            await message.answer(
                "❌ Неверный формат! Минимум 3 значения:\n"
                "<code>Слот | Ставка | Выигрыш</code>",
                parse_mode="HTML"
            )
            return
    
        try:
            if len(parts) == 3:
                streamer = ""
                slot = parts[0].strip()
                bet = int(parts[1].strip().replace(' ', '').replace(',', ''))
                win = int(parts[2].strip().replace(' ', '').replace(',', ''))
            else:
                streamer = parts[0].strip()
                slot = parts[1].strip()
                bet = int(parts[2].strip().replace(' ', '').replace(',', ''))
                win = int(parts[3].strip().replace(' ', '').replace(',', ''))
        
            multiplier = round(win / bet, 1) if bet > 0 else 0
        except ValueError:
            await message.answer("❌ Ставка и выигрыш должны быть числами!")
            return
    
        # Добавляем видео
        video_data = videos_need_input[current_index].copy()
        video_data['streamer'] = streamer
        video_data['slot'] = slot
        video_data['bet'] = bet
        video_data['win'] = win
        video_data['multiplier'] = multiplier
    
        videos.append(video_data)
        await state.update_data(videos=videos)
    
        streamer_text = f"👤 {streamer}" if streamer else "👤 не указан"
        await message.answer(
            f"✅ Видео добавлено!\n\n"
            f"{streamer_text}\n"
            f"🎰 {slot}\n"
            f"💵 {bet}₽ → {win}₽\n"
            f"📊 x{multiplier}\n\n"
            f"<i>Всего добавлено: {len(videos)} видео</i>",
            parse_mode="HTML"
        )
    
        # Переходим к следующему видео
        await _show_channel_video_for_metadata(message, state, current_index + 1)

    async def _proceed_to_target_channel(message, state: FSMContext):
        """Переход к выбору канала для публикации (после видео)"""
        data = await state.get_data()
        videos = data.get('videos', [])
    
        await state.set_state(SpanishPostsStates.waiting_for_target_channel)
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Мои каналы")],
                [KeyboardButton(text="📝 Ввести канал вручную")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        await message.answer(
            f"✅ <b>Видео готовы!</b>\n\n"
            f"📹 Добавлено видео: {len(videos)}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>📺 Шаг 3: Выберите канал для публикации</b>\n\n"
            f"Куда будем публиковать готовые посты?",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @dp.message(SpanishPostsStates.choosing_video_source, lambda m: m.text == "📤 Загрузить вручную")
    async def streamer_posts_choose_manual_upload(message: types.Message, state: FSMContext):
        """Выбрана ручная загрузка видео"""
        await state.set_state(SpanishPostsStates.waiting_for_videos)
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Видео готовы")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        await message.answer(
            "📤 <b>Загрузка видео</b>\n\n"
            "Отправляйте видео прямо в этот чат.\n\n"
            "Формат имени файла:\n"
            "<code>Стример_Слот_Ставка_Выигрыш.mp4</code>\n\n"
            "Или отправьте любое видео — бот спросит данные.\n\n"
            "Когда все загрузите — нажмите «✅ Видео готовы»",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # ====== ОБРАБОТЧИКИ КАРТИНОК ======

    @dp.message(SpanishPostsStates.choosing_image_source, lambda m: m.text == "⏭ Без картинок")
    async def streamer_posts_skip_images(message: types.Message, state: FSMContext):
        """Пропуск картинок — переходим к выбору модели"""
        await state.update_data(images=[])
    
        # Сначала устанавливаем состояние waiting_for_images, 
        # затем вызываем хендлер (он ожидает это состояние)
        await state.set_state(SpanishPostsStates.waiting_for_images)
    
        # Переходим к генерации
        await streamer_posts_images_done(message, state)

    @dp.message(SpanishPostsStates.choosing_image_source, lambda m: m.text == "📤 Загрузить картинки")
    async def streamer_posts_upload_images(message: types.Message, state: FSMContext):
        """Ручная загрузка картинок"""
        await state.set_state(SpanishPostsStates.waiting_for_images)
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Картинки готовы")],
                [KeyboardButton(text="⏭ Пропустить картинки")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        await message.answer(
            "📤 <b>Загрузка картинок</b>\n\n"
            "Отправляйте картинки для бонусных постов.\n\n"
            "Когда все загрузите — нажмите «✅ Картинки готовы»",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @dp.message(SpanishPostsStates.choosing_image_source, lambda m: m.text == "📡 Картинки из канала")
    async def streamer_posts_images_from_channel(message: types.Message, state: FSMContext):
        """Картинки из канала"""
        await state.set_state(SpanishPostsStates.waiting_for_image_channel)
    
        await message.answer(
            "📡 <b>Канал с картинками</b>\n\n"
            "Введите @username или ID канала с картинками для бонусов:\n\n"
            "<i>Можно использовать тот же канал что и для видео</i>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отмена")]],
                resize_keyboard=True
            )
        )

    @dp.message(SpanishPostsStates.waiting_for_image_channel)
    async def streamer_posts_image_channel_handler(message: types.Message, state: FSMContext):
        """Обработка канала с картинками"""
        if message.text == "❌ Отмена":
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        channel_input = message.text.strip()
    
        try:
            from src.telethon_manager import TelethonClientManager
            manager = TelethonClientManager.get_instance(config_manager)
            await manager.ensure_initialized()
            client = manager.get_client()
        
            if not client:
                await message.answer("❌ Telethon клиент не инициализирован")
                return
        
            # Получаем канал через Telethon
            if channel_input.startswith("@"):
                entity = await client.get_entity(channel_input)
            elif channel_input.lstrip('-').isdigit():
                entity = await client.get_entity(int(channel_input))
            else:
                entity = await client.get_entity(channel_input)
        
            channel_id = entity.id
        
            status_msg = await message.answer("🔍 Ищу картинки в канале...")
        
            # Сканируем канал на картинки через Telethon
            images_found = []
            async for msg in client.iter_messages(channel_id, limit=100):
                if msg.photo:
                    images_found.append({
                        'message_id': msg.id,
                        'source_channel_id': channel_id,  # Для копирования через Telethon
                        'file_id': None  # Не нужен - копируем через Telethon
                    })
                    if len(images_found) >= 20:
                        break
        
            if not images_found:
                await status_msg.edit_text("❌ В канале не найдено картинок!")
                return
        
            await state.update_data(
                image_channel_id=channel_id,
                channel_images=images_found,
                images=images_found
            )
        
            await status_msg.edit_text(
                f"✅ Найдено {len(images_found)} картинок!\n\n"
                f"Переходим к генерации постов..."
            )
        
            # Переходим к генерации
            await streamer_posts_images_done(message, state)
        
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message(SpanishPostsStates.waiting_for_videos, lambda m: m.video is not None)
    async def streamer_posts_video_handler(message: types.Message, state: FSMContext):
        """Обработка полученного видео"""
        data = await state.get_data()
        videos = data.get('videos', [])
    
        # Сохраняем file_id видео
        video_info = {
            'file_id': message.video.file_id,
            'file_name': message.video.file_name or f"video_{len(videos)+1}.mp4",
            'file_size': message.video.file_size
        }
    
        # Пробуем распарсить метаданные из имени файла
        from src.streamer_post_parser import StreamerPostParser
        parser = StreamerPostParser()
        parsed = parser.parse_filename(video_info['file_name'])
    
        # Для испанского сценария слот НЕ обязателен - достаточно ставки и выигрыша
        if parsed and parsed.bet > 0 and parsed.win > 0:
            # Данные успешно извлечены из имени файла
            video_info['streamer'] = parsed.streamer
            video_info['slot'] = parsed.slot
            video_info['bet'] = parsed.bet
            video_info['win'] = parsed.win
            video_info['multiplier'] = parsed.multiplier
            video_info['parsed'] = True
        
            videos.append(video_info)
            await state.update_data(videos=videos)
        
            await message.answer(
                f"✅ Видео #{len(videos)} добавлено!\n\n"
                f"📹 Файл: {video_info['file_name']}\n"
                f"👤 Стример: {parsed.streamer}\n"
                f"🎰 Слот: {parsed.slot}\n"
                f"💵 Ставка: {parsed.bet}₽\n"
                f"💰 Выигрыш: {parsed.win}₽\n"
                f"📊 Множитель: x{parsed.multiplier}\n\n"
                f"<i>Всего видео: {len(videos)}</i>",
                parse_mode="HTML"
            )
        else:
            # Не удалось распарсить - запрашиваем данные вручную
            video_info['parsed'] = False
            await state.update_data(
                videos=videos,
                pending_video=video_info
            )
            await state.set_state(SpanishPostsStates.waiting_for_video_metadata)
        
            await message.answer(
                f"📹 Получено видео: {video_info['file_name']}\n\n"
                "⚠️ Не удалось извлечь данные из имени файла.\n\n"
                "<b>Введите данные в формате:</b>\n"
                "<code>Слот | Ставка | Выигрыш</code>\n"
                "или с именем стримера:\n"
                "<code>Стример | Слот | Ставка | Выигрыш</code>\n\n"
                "Примеры:\n"
                "<code>Gates of Olympus | 500 | 125000</code>\n"
                "<code>Жека | Gates of Olympus | 500 | 125000</code>",
                parse_mode="HTML"
            )

    @dp.message(SpanishPostsStates.waiting_for_video_metadata)
    async def streamer_posts_metadata_handler(message: types.Message, state: FSMContext):
        """Обработка ручного ввода метаданных"""
        if message.text == "❌ Отмена":
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        # Парсим введённые данные
        parts = message.text.split('|')
    
        # Поддерживаем 2 формата:
        # 3 значения: Слот | Ставка | Выигрыш (без стримера)
        # 4 значения: Стример | Слот | Ставка | Выигрыш
        if len(parts) < 2:
            await message.answer(
                "❌ Неверный формат!\n\n"
                "Введите минимум 2 значения через |:\n"
                "<code>Ставка | Выигрыш</code> (без слота)\n"
                "или 3 значения:\n"
                "<code>Слот | Ставка | Выигрыш</code>\n"
                "или 4 значения:\n"
                "<code>Стример | Слот | Ставка | Выигрыш</code>",
                parse_mode="HTML"
            )
            return
    
        try:
            if len(parts) == 2:
                # Без слота и стримера: Ставка | Выигрыш
                streamer = ""
                slot = ""  # Без слота
                bet = int(parts[0].strip().replace(' ', '').replace(',', '').replace('.', ''))
                win = int(parts[1].strip().replace(' ', '').replace(',', '').replace('.', ''))
            elif len(parts) == 3:
                # Без стримера: Слот | Ставка | Выигрыш
                streamer = ""
                slot = parts[0].strip()
                bet = int(parts[1].strip().replace(' ', '').replace(',', '').replace('.', ''))
                win = int(parts[2].strip().replace(' ', '').replace(',', '').replace('.', ''))
            else:
                # Со стримером: Стример | Слот | Ставка | Выигрыш
                streamer = parts[0].strip()
                slot = parts[1].strip()
                bet = int(parts[2].strip().replace(' ', '').replace(',', '').replace('.', ''))
                win = int(parts[3].strip().replace(' ', '').replace(',', '').replace('.', ''))
        
            multiplier = round(win / bet, 1) if bet > 0 else 0
        except ValueError:
            await message.answer(
                "❌ Ставка и выигрыш должны быть числами!\n\n"
                "Примеры:\n"
                "<code>725 | 14500</code> (без слота)\n"
                "<code>Gates of Olympus | 500 | 125000</code>\n"
                "<code>Жека | Gates | 500 | 125000</code>",
                parse_mode="HTML"
            )
            return
    
        data = await state.get_data()
        videos = data.get('videos', [])
        pending_video = data.get('pending_video', {})
    
        # Добавляем данные к видео
        # Пытаемся извлечь валюту из введенных данных
        currency = "RUB"  # По умолчанию
        text_upper = message.text.upper()
        text_lower = message.text.lower()
        if 'USD' in text_upper or '$' in message.text or 'доллар' in text_lower:
            currency = "USD"
        elif 'EUR' in text_upper or '€' in message.text or 'евро' in text_lower:
            currency = "EUR"
        elif 'GBP' in text_upper or '£' in message.text or 'фунт' in text_lower:
            currency = "GBP"
    
        pending_video['streamer'] = streamer
        pending_video['slot'] = slot
        pending_video['bet'] = bet
        pending_video['win'] = win
        pending_video['multiplier'] = multiplier
        pending_video['currency'] = currency
        pending_video['parsed'] = True
    
        videos.append(pending_video)
        await state.update_data(videos=videos, pending_video=None)
        await state.set_state(SpanishPostsStates.waiting_for_videos)
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Видео готовы")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        # Формируем сообщение (стример и слот опциональны)
        streamer_line = f"👤 Стример: {streamer}\n" if streamer else ""
        slot_line = f"🎰 Слот: {slot}\n" if slot else "🎰 Слот: не указан\n"
        
        # Валюта будет случайной в каждом посте, поэтому не показываем её здесь
        await message.answer(
            f"✅ Видео #{len(videos)} добавлено!\n\n"
            f"{streamer_line}"
            f"{slot_line}"
            f"💵 Ставка: {bet}\n"
            f"💰 Выигрыш: {win}\n"
            f"📊 Множитель: x{multiplier}\n\n"
            f"<i>Всего видео: {len(videos)}</i>\n\n"
            "Отправьте ещё видео или нажмите '✅ Видео готовы'",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    @dp.message(SpanishPostsStates.waiting_for_videos, lambda m: m.text == "✅ Видео готовы")
    async def streamer_posts_videos_done(message: types.Message, state: FSMContext):
        """Видео загружены - переход к выбору канала для публикации"""
        data = await state.get_data()
        videos = data.get('videos', [])
    
        if len(videos) == 0:
            await message.answer(
                "⚠️ Вы не загрузили ни одного видео!\n\n"
                "Отправьте хотя бы одно видео или нажмите '❌ Отмена'"
            )
            return
    
        # Переходим к выбору канала для публикации
        await state.set_state(SpanishPostsStates.waiting_for_target_channel)
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Мои каналы")],
                [KeyboardButton(text="📝 Ввести канал вручную")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        await message.answer(
            f"✅ <b>Видео готовы!</b>\n\n"
            f"📹 Добавлено видео: {len(videos)}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>📺 Шаг 3: Выберите канал для публикации</b>\n\n"
            f"Куда будем публиковать готовые посты?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    @dp.message(SpanishPostsStates.waiting_for_images, lambda m: m.photo is not None)
    async def streamer_posts_image_handler(message: types.Message, state: FSMContext):
        """Обработка полученной картинки"""
        data = await state.get_data()
        images = data.get('images', [])
    
        # Берём самое большое фото
        photo = message.photo[-1]
        image_info = {
            'file_id': photo.file_id,
            'file_unique_id': photo.file_unique_id
        }
    
        images.append(image_info)
        await state.update_data(images=images)
    
        await message.answer(
            f"✅ Картинка #{len(images)} добавлена!\n\n"
            f"<i>Всего картинок: {len(images)}</i>",
            parse_mode="HTML"
        )

    @dp.message(SpanishPostsStates.waiting_for_images, lambda m: m.text in ["✅ Картинки готовы", "⏭ Пропустить картинки"])
    async def streamer_posts_images_done(message: types.Message, state: FSMContext):
        """Картинки загружены - переходим к выбору модели"""
        data = await state.get_data()
        videos = data.get('videos', [])
        images = data.get('images', [])
    
        total_posts = len(videos) + len(images)
    
        # Переходим к выбору AI модели
        await state.set_state(SpanishPostsStates.choosing_ai_model)
    
        # Создаём клавиатуру с моделями и ценами
        model_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            # Ротации
            [InlineKeyboardButton(text="🔄 РОТАЦИЯ ВСЕХ", callback_data="ai_model:rotation:mixed")],
            [InlineKeyboardButton(text="💰 Ротация дешёвых (~0.05₽)", callback_data="ai_model:rotation:cheap"),
             InlineKeyboardButton(text="⚖️ Ротация средних (~0.3₽)", callback_data="ai_model:rotation:medium")],
            [InlineKeyboardButton(text="💎 Ротация премиум (~1₽)", callback_data="ai_model:rotation:premium"),
             InlineKeyboardButton(text="🔄 Ротация всех моделей", callback_data="ai_model:rotation:mixed")],
            # Дешёвые (до 0.1₽/пост)
            [InlineKeyboardButton(text="🔥 Grok 4.1 Fast — ~0.1₽", callback_data="ai_model:grok-4.1-fast:openrouter"),
             InlineKeyboardButton(text="🎨 Mistral Creative — ~0.05₽", callback_data="ai_model:mistral-small-creative:openrouter")],
            [InlineKeyboardButton(text="🔍 Llama 4 Scout — ~0.05₽", callback_data="ai_model:llama-4-scout:openrouter"),
             InlineKeyboardButton(text="🐋 DeepSeek V3 — ~0.05₽", callback_data="ai_model:deepseek-v3:openrouter")],
            [InlineKeyboardButton(text="💨 Seed Flash — ~0.05₽", callback_data="ai_model:seed-1.6-flash:openrouter"),
             InlineKeyboardButton(text="🐲 Qwen 3 235B — ~0.03₽", callback_data="ai_model:qwen-3-235b:openrouter")],
            # Средние (0.2-0.5₽/пост)
            [InlineKeyboardButton(text="⚡ Gemini 3 Flash — ~0.4₽", callback_data="ai_model:gemini-3-flash:openrouter"),
             InlineKeyboardButton(text="🤖 GPT-4.1 Mini — ~0.3₽", callback_data="ai_model:gpt-4.1-mini:openrouter")],
            [InlineKeyboardButton(text="🦙 Llama 4 Maverick — ~0.2₽", callback_data="ai_model:llama-4-maverick:openrouter"),
             InlineKeyboardButton(text="🌊 DeepSeek R1 — ~0.4₽", callback_data="ai_model:deepseek-r1:openrouter")],
            # Премиум (0.8-3₽/пост)
            [InlineKeyboardButton(text="🧠 GPT-5.2 — ~1.2₽", callback_data="ai_model:gpt-5.2:openrouter"),
             InlineKeyboardButton(text="💎 Gemini 3 Pro — ~1.2₽", callback_data="ai_model:gemini-3-pro:openrouter")],
            [InlineKeyboardButton(text="🎵 Claude Sonnet 4.5 — ~0.8₽", callback_data="ai_model:claude-sonnet-4.5:openrouter"),
             InlineKeyboardButton(text="🏔️ Mistral Large — ~0.8₽", callback_data="ai_model:mistral-large:openrouter")],
            # Топ премиум
            [InlineKeyboardButton(text="🔮 Claude Opus 4.5 — ~2.8₽ [TOP]", callback_data="ai_model:claude-opus-4.5:openrouter")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="ai_model:cancel")]
        ])
    
        await message.answer(
            f"🤖 <b>Выбери модель для генерации {total_posts} постов</b>\n\n"
            f"📹 Видео: {len(videos)} | 🖼 Картинки: {len(images)}\n\n"
            f"<b>🔄 Ротации (каждый пост — другая AI):</b>\n"
            f"• ВСЕ — GPT + Gemini + Grok (разнообразие)\n"
            f"• 💰 Дешёвые — 6 моделей (~0.05₽/пост)\n"
            f"• ⚖️ Средние — 4 модели (~0.3₽/пост)\n\n"
            f"<b>💰 Дешёвые (до 0.1₽):</b> Grok, Mistral, Llama, DeepSeek, Qwen\n"
            f"<b>⚖️ Средние (0.2-0.5₽):</b> Gemini Flash, GPT-4.1 Mini\n"
            f"<b>💎 Премиум (0.8-3₽):</b> GPT-5.2, Claude, Gemini Pro",
            parse_mode="HTML",
            reply_markup=model_keyboard
        )

    @dp.callback_query(lambda c: c.data.startswith("ai_model:"), StateFilter(SpanishPostsStates.choosing_ai_model))
    async def streamer_posts_model_selected(callback: types.CallbackQuery, state: FSMContext):
        """Обработка выбора AI модели"""
        try:
            await callback.answer()
        except Exception:
            pass  # Игнорируем сетевые ошибки при answer
    
        parts = callback.data.split(":")
        if parts[1] == "cancel":
            await state.clear()
            kb = get_scenarios_kb(callback.from_user.id)
            await callback.message.edit_text("❌ Отменено")
            await callback.message.answer("Выберите сценарий:", reply_markup=kb)
            return
    
        model_key = parts[1]  # gpt-5-mini, gpt-5.2, gemini-3-pro, rotation, etc.
        provider = parts[2]   # openai, openrouter или mixed (для ротации)
    
        data = await state.get_data()
        videos = data.get('videos', [])
        images = data.get('images', [])
        total_posts = len(videos) + len(images)
    
        # Определяем отображаемое имя модели
        model_names = {
            "gpt-5.2": "GPT-5.2",
            "gpt-4.1-mini": "GPT-4.1 Mini",
            "gemini-3-pro": "Gemini 3 Pro",
            "gemini-3-flash": "Gemini 3 Flash",
            "gemini-2.5-pro": "Gemini 2.5 Pro",
            "claude-opus-4.5": "Claude Opus 4.5",
            "claude-sonnet-4.5": "Claude Sonnet 4.5",
            "grok-4.1-fast": "Grok 4.1 Fast",
            "mistral-small-creative": "Mistral Creative",
            "mistral-large": "Mistral Large",
            "llama-4-maverick": "Llama 4 Maverick",
            "llama-4-scout": "Llama 4 Scout",
            "deepseek-r1": "DeepSeek R1",
            "deepseek-v3": "DeepSeek V3",
            "qwen-3-235b": "Qwen 3 235B",
            "seed-1.6": "ByteDance Seed",
            "seed-1.6-flash": "Seed Flash",
            "rotation": "🔄 РОТАЦИЯ"
        }
        model_display_name = model_names.get(model_key, model_key)
    
        # Режим ротации - чередование моделей
        is_rotation = model_key == "rotation"
        rotation_type = provider if is_rotation else None  # cheap, medium, mixed
    
        # Наборы моделей для разных ротаций
        rotation_cheap = [  # Дешёвые (~0.03-0.1₽/пост)
            ("grok-4.1-fast", "openrouter", "Grok 4.1 Fast"),
            ("mistral-small-creative", "openrouter", "Mistral Creative"),
            ("llama-4-scout", "openrouter", "Llama 4 Scout"),
            ("deepseek-v3", "openrouter", "DeepSeek V3"),
            ("seed-1.6-flash", "openrouter", "Seed Flash"),
            ("qwen-3-235b", "openrouter", "Qwen 3 235B"),
        ]
        rotation_medium = [  # Средние (~0.2-0.5₽/пост)
            ("gemini-3-flash", "openrouter", "Gemini 3 Flash"),
            ("gpt-4.1-mini", "openrouter", "GPT-4.1 Mini"),
            ("llama-4-maverick", "openrouter", "Llama 4 Maverick"),
            ("deepseek-r1", "openrouter", "DeepSeek R1"),
        ]
        rotation_premium = [  # Премиум (~0.5-3₽/пост) - 10 моделей для максимального разнообразия
            ("claude-opus-4.5", "openrouter", "Claude Opus 4.5"),
            ("claude-sonnet-4.5", "openrouter", "Claude Sonnet 4.5"),
            ("gpt-5.2", "openrouter", "GPT-5.2"),
            ("gemini-3-pro", "openrouter", "Gemini 3 Pro"),
            ("gemini-2.5-pro", "openrouter", "Gemini 2.5 Pro"),
            ("mistral-large", "openrouter", "Mistral Large"),
            ("deepseek-r1", "openrouter", "DeepSeek R1"),
            ("llama-4-maverick", "openrouter", "Llama 4 Maverick"),
            ("qwen-3-235b", "openrouter", "Qwen 3 235B"),
            ("grok-4.1-fast", "openrouter", "Grok 4.1 Fast"),
        ]
        rotation_mixed = [  # Все (дешёвые + средние + премиум) - максимальное разнообразие
            # Дешёвые
            ("grok-4.1-fast", "openrouter", "Grok 4.1 Fast"),
            ("mistral-small-creative", "openrouter", "Mistral Creative"),
            ("llama-4-scout", "openrouter", "Llama 4 Scout"),
            ("deepseek-v3", "openrouter", "DeepSeek V3"),
            ("seed-1.6-flash", "openrouter", "Seed Flash"),
            ("qwen-3-235b", "openrouter", "Qwen 3 235B"),
            # Средние
            ("gpt-4.1-mini", "openrouter", "GPT-4.1 Mini"),
            ("llama-4-maverick", "openrouter", "Llama 4 Maverick"),
            ("deepseek-r1", "openrouter", "DeepSeek R1"),
            # Премиум
            ("gemini-2.5-pro", "openrouter", "Gemini 2.5 Pro"),
            ("gpt-5.2", "openrouter", "GPT-5.2"),
            ("gemini-3-pro", "openrouter", "Gemini 3 Pro"),
            ("claude-sonnet-4.5", "openrouter", "Claude Sonnet 4.5"),
            ("mistral-large", "openrouter", "Mistral Large"),
            # Топ премиум
            ("claude-opus-4.5", "openrouter", "Claude Opus 4.5"),
        ]
    
        # Выбор набора
        if rotation_type == "cheap":
            rotation_models = rotation_cheap
            rotation_label = "💰 ДЕШЁВЫЕ"
        elif rotation_type == "medium":
            rotation_models = rotation_medium
            rotation_label = "⚖️ СРЕДНИЕ"
        elif rotation_type == "premium":
            rotation_models = rotation_premium
            rotation_label = "💎 ПРЕМИУМ"
        else:
            rotation_models = rotation_mixed
            rotation_label = "🔄 ВСЕ"
    
        await state.update_data(
            ai_model_key=model_key,
            ai_provider=provider,
            ai_model_display=model_display_name,
            is_rotation=is_rotation,
            rotation_type=rotation_type,
            rotation_models=rotation_models
        )
    
        # Сообщение о начале генерации
        provider_text = f"РОТАЦИЯ ({rotation_label})" if is_rotation else provider.upper()
        status_msg = await callback.message.edit_text(
            f"🤖 <b>AI генерирует уникальные посты...</b>\n\n"
            f"📹 Видео: {len(videos)}\n"
            f"🖼 Картинки: {len(images)}\n"
            f"📝 Всего: {total_posts}\n"
            f"🧠 Модель: <b>{model_display_name}</b>\n"
            f"🔌 Провайдер: {provider_text}\n\n"
            f"⏳ Прогресс: 0/{total_posts}\n\n"
            f"<i>Каждый пост генерируется с нуля через AI.\n"
            f"Это займёт ~{total_posts * 3} секунд.</i>",
            parse_mode="HTML"
        )
    
        # Импортируем AI генератор
        from src.ai_post_generator_es import AIPostGenerator, VideoData, OPENROUTER_MODELS
        from dotenv import load_dotenv
        load_dotenv()  # Загружаем переменные из .env
    
        openai_key = config_manager.openai_api_key
        openrouter_key = config_manager.openrouter_api_key
    
        # Проверяем наличие ключей для ротации
        if is_rotation and not openrouter_key:
            await status_msg.edit_text(
                "❌ <b>Ошибка:</b> Для ротации нужен OPENROUTER_API_KEY!\n\n"
                "Добавьте ключ в .env файл:\n"
                "<code>OPENROUTER_API_KEY=sk-or-v1-...</code>",
                parse_mode="HTML"
            )
            return
    
        # Функция для создания генератора по модели
        def create_generator(m_key, m_provider):
            if m_provider == "openrouter":
                model_info = OPENROUTER_MODELS.get(m_key)
                if model_info:
                    gen = AIPostGenerator(
                        openrouter_api_key=openrouter_key,
                        model=model_info['id'],
                        use_openrouter=True
                    )
                    # Загрузка существующих постов
                    try:
                        gen.load_existing_posts_from_file("data/my_posts.json")
                    except:
                        pass
                    return gen
            gen = AIPostGenerator(api_key=openai_key, model=m_key)
            # Загрузка существующих постов
            try:
                gen.load_existing_posts_from_file("data/my_posts.json")
            except:
                pass
            return gen
    
        # Создаём генератор в зависимости от режима
        if not is_rotation:
            if provider == "openrouter":
                if not openrouter_key:
                    await status_msg.edit_text(
                        "❌ <b>Ошибка:</b> OPENROUTER_API_KEY не найден!\n\n"
                        "Добавьте ключ в .env файл:\n"
                        "<code>OPENROUTER_API_KEY=sk-or-v1-...</code>",
                        parse_mode="HTML"
                    )
                    return
            
                model_info = OPENROUTER_MODELS.get(model_key)
                if not model_info:
                    await status_msg.edit_text(f"❌ Модель {model_key} не найдена в OPENROUTER_MODELS")
                    return
            
                model_id = model_info['id']
                generator = AIPostGenerator(
                    openrouter_api_key=openrouter_key,
                    model=model_id,
                    use_openrouter=True
                )
            else:
                generator = AIPostGenerator(api_key=openai_key, model=model_key)
    
        # Загрузка существующих постов для обучения AI
        try:
            generator.load_existing_posts_from_file("data/my_posts.json")
            logger.info("✅ Загружено существующих постов для обучения AI")
        except FileNotFoundError:
            logger.warning("⚠️ Файл data/my_posts.json не найден - AI будет работать без обучающей базы")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить существующие посты: {e}")
    
        # Преобразуем данные видео
        video_data_list = [
            VideoData(
                streamer=v.get('streamer', ''),
                slot=v.get('slot', 'Слот'),
                bet=v.get('bet', 100),
                win=v.get('win', 10000),
                currency=v.get('currency', 'RUB')  # Извлекаем валюту из данных или используем RUB по умолчанию
            )
            for v in videos
        ]
    
        # Генерируем посты через AI
        ai_posts = []
    
        if is_rotation:
            # РОТАЦИЯ: каждый пост - разная модель
            # ВАЖНО: используем локальные переменные rotation_models и rotation_type,
            # т.к. они уже определены выше (строки 26216-26224)
            # НЕ используем data.get() — там старые данные до update_data()
            rotation_models_list = rotation_models  # локальная переменная
            # rotation_type и rotation_label уже определены выше
            
            # КРИТИЧНО: глобальный счетчик для ротации форматов ссылок
            link_format_counter = 0
        
            for i, video in enumerate(video_data_list):
                # Выбираем модель по индексу (циклически)
                rot_model_key, rot_provider, rot_name = rotation_models_list[i % len(rotation_models_list)]
            
                try:
                    await status_msg.edit_text(
                        f"🤖 <b>AI генерирует уникальные посты...</b>\n\n"
                        f"📹 Видео: {len(videos)}\n"
                        f"📝 Всего: {total_posts}\n"
                        f"{rotation_label} <b>РОТАЦИЯ</b>\n\n"
                        f"⏳ Прогресс: {i}/{total_posts}\n"
                        f"🧠 Текущая: <b>{rot_name}</b>\n"
                        f"{'█' * (i * 20 // total_posts)}{'░' * (20 - i * 20 // total_posts)}",
                        parse_mode="HTML"
                    )
                except:
                    pass
            
                # Создаём генератор для этой модели
                rot_generator = create_generator(rot_model_key, rot_provider)
                rot_generator.set_bonus_data(
                    url1=data['url1'],
                    bonus1=data['bonus1']
                )
                # КРИТИЧНО: передаем текущий счетчик форматов
                rot_generator.set_link_format_counter(link_format_counter)
            
                try:
                    post = await rot_generator.generate_video_post(video, i)
                    post.model_used = rot_name  # Сохраняем какая модель использовалась
                    ai_posts.append(post)
                    # КРИТИЧНО: сохраняем обновленный счетчик для следующего генератора
                    link_format_counter = rot_generator.get_link_format_counter()
                except Exception as e:
                    print(f"❌ Ошибка ротации пост #{i} ({rot_name}): {e}")
                    # Пробуем fallback на Gemini Flash (быстрая и дешёвая)
                    try:
                        fallback_gen = create_generator("gemini-3-flash", "openrouter")
                        fallback_gen.set_bonus_data(
                            url1=data['url1'],
                            bonus1=data['bonus1']
                        )
                        # КРИТИЧНО: передаем счетчик форматов в fallback
                        fallback_gen.set_link_format_counter(link_format_counter)
                        post = await fallback_gen.generate_video_post(video, i)
                        post.model_used = "Gemini 3 Flash (fallback)"
                        ai_posts.append(post)
                        # КРИТИЧНО: сохраняем обновленный счетчик
                        link_format_counter = fallback_gen.get_link_format_counter()
                    except Exception as fallback_error:
                        print(f"❌ Fallback тоже не сработал для поста #{i}: {fallback_error}")
                        # КРИТИЧНО: Не прерываем цикл! Пост пропущен, но продолжаем генерацию
        
            # Генерация картинок (используем Gemini 3 Flash - быстрая и дешёвая)
            if images:
                img_generator = create_generator("gemini-3-flash", "openrouter")
                img_generator.set_bonus_data(
                    url1=data['url1'],
                    bonus1=data['bonus1']
                )
                # КРИТИЧНО: продолжаем ротацию форматов для картинок
                img_generator.set_link_format_counter(link_format_counter)
                for j in range(len(images)):
                    try:
                        post = await img_generator.generate_image_post(len(video_data_list) + j)
                        ai_posts.append(post)
                    except Exception as img_error:
                        print(f"❌ Ошибка генерации картинки #{j}: {img_error}")
        else:
            # Обычный режим - одна модель для всех
            generator.set_bonus_data(
                url1=data['url1'],
                bonus1=data['bonus1']
            )
        
            # Callback для обновления прогресса
            async def progress_callback(current, total):
                try:
                    await status_msg.edit_text(
                        f"🤖 <b>AI генерирует уникальные посты...</b>\n\n"
                        f"📹 Видео: {len(videos)}\n"
                        f"🖼 Картинки: {len(images)}\n"
                        f"📝 Всего: {total}\n"
                        f"🧠 Модель: <b>{model_display_name}</b>\n"
                        f"🔌 Провайдер: {provider.upper()}\n\n"
                        f"⏳ Прогресс: {current}/{total}\n"
                        f"{'█' * (current * 20 // total)}{'░' * (20 - current * 20 // total)}",
                        parse_mode="HTML"
                    )
                except:
                    pass
        
            try:
                ai_posts = await generator.generate_all_posts(
                    videos=video_data_list,
                    image_count=len(images),
                    progress_callback=progress_callback
                )
            except Exception as e:
                error_msg = str(e)
                if provider == "openrouter":
                    error_msg += "\n\n💡 Проверьте:\n• Баланс OpenRouter\n• Правильность API ключа"
                await status_msg.edit_text(
                    f"❌ <b>Ошибка AI генерации:</b>\n{error_msg}",
                    parse_mode="HTML"
                )
                return
            
            # 🚨 КРИТИЧНО: Проверяем были ли сгенерированы хотя бы некоторые посты
            if not ai_posts or len(ai_posts) == 0:
                await status_msg.edit_text(
                    "❌ <b>Не удалось сгенерировать ни одного поста</b>\n\n"
                    "💡 Проверьте:\n"
                    "• Баланс OpenRouter\n"
                    "• Правильность API ключа\n"
                    "• Логи бота",
                    parse_mode="HTML"
                )
                return
            
            # ⚠️ Если сгенерировано меньше постов чем ожидалось - уведомляем
            expected_total = len(videos) + len(images)
            if len(ai_posts) < expected_total:
                warning_msg = (
                    f"⚠️ <b>ВНИМАНИЕ!</b>\n"
                    f"Генерация прервана после {len(ai_posts)}/{expected_total} постов\n\n"
                    f"✅ Сохраняю {len(ai_posts)} успешно сгенерированных постов!\n"
                    f"💰 Бюджет не потерян - посты будут использованы!"
                )
                await status_msg.edit_text(warning_msg, parse_mode="HTML")
                await asyncio.sleep(3)
    
        # Сохраняем посты с привязкой к медиа
        generated_posts = []
        video_idx = 0
        image_idx = 0
    
        for post in ai_posts:
            if post.media_type == "video" and video_idx < len(videos):
                # КРИТИЧНО: Находим правильное видео по streamer+slot из поста!
                # Посты могут быть перемешаны после shuffle, поэтому не можем брать просто videos[video_idx]
                matching_video = None
                
                # Ищем видео которое соответствует этому посту
                for v in videos:
                    v_streamer = v.get('streamer', '').strip().lower()
                    v_slot = v.get('slot', '').strip().lower()
                    post_streamer = post.streamer.strip().lower()
                    post_slot = post.slot.strip().lower()
                    
                    # Сравниваем и стример и слот
                    if v_streamer == post_streamer and v_slot == post_slot:
                        matching_video = v
                        break
                
                # Если не нашли точное совпадение - берем по индексу (fallback)
                if not matching_video:
                    matching_video = videos[video_idx]
                    print(f"⚠️ Не найдено точное совпадение для поста #{post.index} ({post.streamer}, {post.slot}), используем video_idx={video_idx}")
                
                video_idx += 1
            
                generated_posts.append({
                    'index': post.index,
                    'media_path': matching_video.get('file_id'),  # ✅ Правильное видео!
                    'source_channel_id': matching_video.get('source_channel_id'),
                    'message_id': matching_video.get('message_id'),
                    'media_type': post.media_type,
                    'text': post.text,
                    'streamer': post.streamer,
                    'slot': post.slot
                })
            
            elif post.media_type == "image" and image_idx < len(images):
                image_data = images[image_idx]
                image_idx += 1
            
                generated_posts.append({
                    'index': post.index,
                    'media_path': image_data.get('file_id'),
                    'source_channel_id': image_data.get('source_channel_id'),
                    'message_id': image_data.get('message_id'),
                    'media_type': post.media_type,
                    'text': post.text,
                    'streamer': post.streamer,
                    'slot': post.slot
                })
    
        await state.update_data(
            generated_posts=generated_posts,
            ai_model_used=model_display_name,
            ai_posts_objects=ai_posts  # Сохраняем объекты для перегенерации
        )
    
        # Показываем меню выбора проверки уникальности
        target_channel_name = data.get('target_channel_name', 'не выбран')
    
        # Формируем информацию о моделях
        if is_rotation:
            models_used = set(getattr(p, 'model_used', 'Unknown') for p in ai_posts if hasattr(p, 'model_used'))
            models_info = f"🔄 Ротация: {', '.join(models_used)}" if models_used else "🔄 Ротация моделей"
        else:
            models_info = f"🤖 Модель: {model_display_name}\n🔌 Провайдер: {provider.upper()}"
    
        # Обновляем статус
        try:
            await status_msg.edit_text(
                f"✅ AI сгенерировал {len(generated_posts)} постов!",
                parse_mode="HTML"
            )
        except:
            pass
    
        # Показываем меню проверки уникальности
        uniqueness_summary = f"""
    ✅ <b>AI сгенерировал {len(generated_posts)} постов!</b>

    📹 Видео: {sum(1 for p in generated_posts if p['media_type'] == 'video')}
    🖼 Картинки: {sum(1 for p in generated_posts if p['media_type'] == 'image')}
    {models_info}
    📺 Канал: <b>{target_channel_name}</b>

    ━━━━━━━━━━━━━━━━━━━━━━━
    🛡️ <b>Проверка уникальности постов</b>

    Выберите модель для проверки похожих постов:

    ⚡ <b>Быстрая</b> (Gemini Flash) — ~0.02₽
       Базовая проверка, быстро

    👍 <b>Хорошая</b> (GPT-4o-mini) — ~0.05₽
       Надёжная проверка

    🔄 <b>Гибридная</b> (Flash + Gemini 3 Pro) — ~0.1₽
       Flash ищет, Pro перепроверяет

    ⭐ <b>Отличная</b> (Gemini 3 Pro) — ~2₽
       Глубокий семантический анализ

    💎 <b>Лучшая</b> (Claude Sonnet 4) — ~5₽
       Максимальное качество
    """
    
        await state.set_state(SpanishPostsStates.waiting_for_uniqueness_check)
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⚡ Быстрая (~0.02₽)"), KeyboardButton(text="👍 Хорошая (~0.05₽)")],
                [KeyboardButton(text="🔄 Гибридная (~0.1₽)"), KeyboardButton(text="⭐ Отличная (~2₽)")],
                [KeyboardButton(text="💎 Лучшая (~5₽)")],
                [KeyboardButton(text="⏭ Пропустить проверку")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        await callback.message.answer(uniqueness_summary, reply_markup=keyboard, parse_mode="HTML")

    # ═══════════════════════════════════════════════════════════════════════════════
    # ОБРАБОТЧИКИ ПРОВЕРКИ УНИКАЛЬНОСТИ (Сторожевой AI)
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _show_posts_preview_after_check(message: types.Message, state: FSMContext, result: dict):
        """Показать превью после проверки уникальности"""
        import re
    
        data = await state.get_data()
        generated_posts = data.get('generated_posts', [])
        target_channel_name = data.get('target_channel_name', 'не выбран')
        model_display_name = data.get('ai_model_used', 'AI')
    
        # Формируем превью (очищаем HTML чтобы избежать ошибок)
        preview_text = ""
        if generated_posts:
            raw_text = generated_posts[0].get('text', '')[:300]
            # Удаляем HTML теги для безопасного превью
            clean_text = re.sub(r'<[^>]+>', '', raw_text)
            preview_text = f"\n\n<b>Превью:</b>\n{clean_text}..."
    
        publish_time = len(generated_posts) * 3 // 60
    
        # Информация о проверке
        check_info = ""
        if result:
            if result.get("is_unique"):
                check_info = "\n✅ <b>Проверка: все посты уникальны!</b>\n"
            else:
                dups = len(result.get("duplicates", []))
                check_info = f"\n⚠️ <b>Проверка:</b> найдено {dups} похожих пар\n"
    
        summary = f"""
    ✅ <b>Готово к публикации!</b>

    📹 Видео: {sum(1 for p in generated_posts if p['media_type'] == 'video')}
    🖼 Картинки: {sum(1 for p in generated_posts if p['media_type'] == 'image')}
    🤖 Модель: {model_display_name}
    📺 Канал: <b>{target_channel_name}</b>
    {check_info}
    {preview_text}

    ━━━━━━━━━━━━━━━━━━━━━━━
    ⏱ Публикация займёт ~{publish_time} мин
    """
    
        # Обрезаем если слишком длинно
        if len(summary) > 4000:
            summary = f"""
    ✅ <b>Готово к публикации!</b>

    📹 Видео: {sum(1 for p in generated_posts if p['media_type'] == 'video')}
    🖼 Картинки: {sum(1 for p in generated_posts if p['media_type'] == 'image')}
    {check_info}
    📺 Канал: <b>{target_channel_name}</b>

    <i>Нажми «👁 Ещё превью» чтобы посмотреть посты</i>
    """
    
        await state.set_state(SpanishPostsStates.preview_and_publish)
    
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Начать публикацию")],
                [KeyboardButton(text="👁 Ещё превью")],
                [KeyboardButton(text="🔄 Перегенерировать все")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
        try:
            await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            # Если HTML ошибка - отправляем без превью
            fallback_summary = f"""
    ✅ <b>Готово к публикации!</b>

    📹 Видео: {sum(1 for p in generated_posts if p['media_type'] == 'video')}
    🖼 Картинки: {sum(1 for p in generated_posts if p['media_type'] == 'image')}
    📺 Канал: <b>{target_channel_name}</b>
    {check_info}

    <i>Нажми «👁 Ещё превью» чтобы посмотреть посты</i>
    """
            await message.answer(fallback_summary, reply_markup=keyboard, parse_mode="HTML")

    @dp.message(SpanishPostsStates.waiting_for_uniqueness_check)
    async def streamer_posts_uniqueness_check_handler(message: types.Message, state: FSMContext):
        """Обработка выбора модели проверки уникальности"""
        text = message.text.lower()
        data = await state.get_data()
        generated_posts = data.get('generated_posts', [])
    
        # Отмена
        if "отмена" in text:
            await state.clear()
            await message.answer(
                "❌ Отменено",
                reply_markup=get_scenarios_kb(message.from_user.id)
            )
            return
    
        # Пропустить проверку
        if "пропустить" in text:
            await _show_posts_preview_after_check(message, state, None)
            return
    
        # Определяем модель проверки и модель для перегенерации
        model_key = None
        model_name = None
        is_hybrid = False
        regenerate_model_key = None  # Модель для перегенерации дублей
        regenerate_model_id = None   # ID модели для OpenRouter
    
        if "быстрая" in text:
            model_key = "flash"
            model_name = "Gemini 2.0 Flash"
            regenerate_model_key = "flash"
            regenerate_model_id = "google/gemini-2.0-flash-001"
        elif "хорошая" in text:
            model_key = "gpt4o-mini"
            model_name = "GPT-4o Mini"
            regenerate_model_key = "gpt4o-mini"
            regenerate_model_id = "openai/gpt-4o-mini"
        elif "гибридная" in text:
            is_hybrid = True
            model_name = "Гибридная (Flash + Gemini 3 Pro)"
            regenerate_model_key = "gemini3-pro"
            regenerate_model_id = "google/gemini-3-pro-preview"  # Перегенерация через Gemini 3 Pro
        elif "отличная" in text:
            model_key = "gemini3-pro"
            model_name = "Gemini 3 Pro"
            regenerate_model_key = "gemini3-pro"
            regenerate_model_id = "google/gemini-3-pro-preview"
        elif "лучшая" in text:
            model_key = "claude-sonnet"
            model_name = "Claude Sonnet 4"
            regenerate_model_key = "claude-sonnet"
            regenerate_model_id = "anthropic/claude-sonnet-4"
        else:
            await message.answer("⚠️ Выберите модель из предложенных кнопок")
            return
    
        # Сохраняем модель для перегенерации в state
        await state.update_data(
            regenerate_model_key=regenerate_model_key,
            regenerate_model_id=regenerate_model_id,
            regenerate_model_name=model_name
        )
    
        # Показываем статус проверки
        status_msg = await message.answer(
            f"🔍 <b>Проверка уникальности...</b>\n\n"
            f"🤖 Модель: {model_name}\n"
            f"📝 Постов: {len(generated_posts)}\n\n"
            f"⏳ Анализирую тексты...",
            parse_mode="HTML"
        )
    
        try:
            # Получаем генератор для проверки
            from src.ai_post_generator import AIPostGenerator
            openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        
            if not openrouter_key:
                await status_msg.edit_text(
                    "❌ Не найден OPENROUTER_API_KEY\n\n"
                    "Добавьте ключ в config/settings.env",
                    parse_mode="HTML"
                )
                await _show_posts_preview_after_check(message, state, None)
                return
        
            checker = AIPostGenerator(
                openrouter_api_key=openrouter_key,
                model="google/gemini-2.0-flash-001",
                use_openrouter=True
            )
            
            # Загрузка существующих постов для проверки уникальности
            try:
                checker.load_existing_posts_from_file("data/my_posts.json")
            except:
                pass
        
            # Собираем тексты и слоты
            posts_texts = [p['text'] for p in generated_posts]
            posts_slots = [p.get('slot', 'Неизвестно') for p in generated_posts]
        
            # Выполняем проверку
            if is_hybrid:
                result = await checker.check_posts_uniqueness_hybrid(posts_texts, posts_slots)
            else:
                result = await checker.check_posts_uniqueness(posts_texts, posts_slots, model=model_key)
        
            # Сохраняем результат
            await state.update_data(uniqueness_result=result)
        
            # Показываем результаты
            if result.get("error"):
                await status_msg.edit_text(
                    f"⚠️ <b>Ошибка проверки:</b>\n{result['error']}\n\n"
                    f"Модель: {result.get('model_used', model_name)}",
                    parse_mode="HTML"
                )
                await _show_posts_preview_after_check(message, state, None)
                return
        
            duplicates = result.get("duplicates", [])
            warnings = result.get("warnings", [])
        
            if result.get("is_unique", True) and not duplicates:
                # Всё уникально!
                await status_msg.edit_text(
                    f"✅ <b>Все {len(generated_posts)} постов уникальны!</b>\n\n"
                    f"🤖 Модель: {result.get('model_used', model_name)}\n"
                    f"📊 {result.get('summary', 'Проверка завершена')}",
                    parse_mode="HTML"
                )
                await _show_posts_preview_after_check(message, state, result)
            else:
                # Найдены похожие посты
                dup_text = ""
                for i, dup in enumerate(duplicates[:5], 1):  # Показываем макс 5
                    dup_text += f"\n{i}. Пост #{dup['post1']} ↔ #{dup['post2']}\n"
                    dup_text += f"   📝 {dup['reason']}\n"
                    dup_text += f"   📊 Похожесть: {dup.get('similarity', '?')}%"
            
                if len(duplicates) > 5:
                    dup_text += f"\n\n... и ещё {len(duplicates) - 5} пар"
            
                await status_msg.edit_text(
                    f"⚠️ <b>Найдено {len(duplicates)} похожих пар!</b>\n\n"
                    f"🤖 Модель: {result.get('model_used', model_name)}\n"
                    f"📊 Уникальных: {result.get('total_unique', '?')}/{len(generated_posts)}"
                    f"{dup_text}",
                    parse_mode="HTML"
                )
            
                # Показываем кнопки действий
                await state.set_state(SpanishPostsStates.showing_uniqueness_results)
            
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="🔄 Перегенерировать дубли")],
                        [KeyboardButton(text="✅ Опубликовать как есть")],
                        [KeyboardButton(text="👁 Показать дубли детально")],
                        [KeyboardButton(text="❌ Отмена")]
                    ],
                    resize_keyboard=True
                )
            
                await message.answer(
                    f"Что делать с {len(duplicates)} похожими постами?",
                    reply_markup=keyboard
                )
                return
            
        except Exception as e:
            await status_msg.edit_text(
                f"❌ <b>Ошибка:</b>\n{str(e)[:200]}",
                parse_mode="HTML"
            )
            await _show_posts_preview_after_check(message, state, None)

    @dp.message(SpanishPostsStates.showing_uniqueness_results)
    async def streamer_posts_uniqueness_results_handler(message: types.Message, state: FSMContext):
        """Обработка действий после проверки уникальности"""
        text = message.text.lower()
        data = await state.get_data()
        result = data.get('uniqueness_result', {})
    
        if "отмена" in text:
            await state.clear()
            await message.answer(
                "❌ Отменено",
                reply_markup=get_scenarios_kb(message.from_user.id)
            )
            return
    
        if "опубликовать как есть" in text:
            await _show_posts_preview_after_check(message, state, result)
            return
    
        if "показать дубли" in text:
            duplicates = result.get("duplicates", [])
            generated_posts = data.get('generated_posts', [])
        
            detail_text = "📋 <b>Детальный просмотр похожих постов:</b>\n\n"
        
            for i, dup in enumerate(duplicates[:3], 1):  # Показываем 3 пары
                post1_idx = dup['post1'] - 1
                post2_idx = dup['post2'] - 1
            
                if 0 <= post1_idx < len(generated_posts) and 0 <= post2_idx < len(generated_posts):
                    post1_text = generated_posts[post1_idx]['text'][:200] + "..."
                    post2_text = generated_posts[post2_idx]['text'][:200] + "..."
                
                    detail_text += f"━━━ Пара {i} ━━━\n"
                    detail_text += f"<b>Пост #{dup['post1']}:</b>\n{post1_text}\n\n"
                    detail_text += f"<b>Пост #{dup['post2']}:</b>\n{post2_text}\n\n"
                    detail_text += f"📝 Причина: {dup['reason']}\n"
                    detail_text += f"📊 Похожесть: {dup.get('similarity', '?')}%\n\n"
        
            # Обрезаем если слишком длинно
            if len(detail_text) > 4000:
                detail_text = detail_text[:3900] + "\n\n... (обрезано)"
        
            await message.answer(detail_text, parse_mode="HTML")
            return
    
        if "перегенерировать дубли" in text:
            duplicates = result.get("duplicates", [])
            if not duplicates:
                await message.answer("✅ Нет дублей для перегенерации!")
                await _show_posts_preview_after_check(message, state, result)
                return
        
            # Собираем индексы постов для перегенерации (берём второй из пары)
            posts_to_regenerate = set()
            for dup in duplicates:
                # Перегенерируем второй пост из пары (post2)
                posts_to_regenerate.add(dup['post2'] - 1)  # -1 т.к. индексы с 0
        
            posts_to_regenerate = sorted(posts_to_regenerate)
        
            # Получаем модель для перегенерации из state
            regenerate_model_id = data.get('regenerate_model_id', 'openai/gpt-4o-mini')
            regenerate_model_name = data.get('regenerate_model_name', 'GPT-4o Mini')
        
            status_msg = await message.answer(
                f"🔄 <b>Перегенерация {len(posts_to_regenerate)} постов...</b>\n\n"
                f"🤖 Модель: {regenerate_model_name}\n"
                f"📝 Посты: {', '.join(f'#{i+1}' for i in posts_to_regenerate)}\n"
                f"⏳ Это займёт некоторое время...",
                parse_mode="HTML"
            )
        
            try:
                from src.ai_post_generator_es import AIPostGenerator, VideoData, OPENROUTER_MODELS
            
                generated_posts = data.get('generated_posts', [])
                videos = data.get('videos', [])
            
                # Получаем настройки генератора
                openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
                openai_key = os.getenv("OPENAI_API_KEY", "")
            
                # Бонусы
                url1 = data.get('url1', '')
                bonus1 = data.get('bonus1', '')
            
                regenerated_count = 0
            
                for idx in posts_to_regenerate:
                    if idx >= len(generated_posts):
                        continue
                
                    post_data = generated_posts[idx]
                
                    # Находим соответствующее видео
                    video_info = None
                    for v in videos:
                        if v.get('slot') == post_data.get('slot'):
                            video_info = v
                            break
                
                    if not video_info:
                        # Используем данные из поста
                        video_info = {
                            'streamer': post_data.get('streamer', ''),
                            'slot': post_data.get('slot', 'Слот'),
                            'bet': 100,
                            'win': 10000,
                            'currency': 'RUB'
                        }
                
                    # Создаём VideoData
                    video_data = VideoData(
                        streamer=video_info.get('streamer', ''),
                        slot=video_info.get('slot', 'Слот'),
                        bet=video_info.get('bet', 100),
                        win=video_info.get('win', 10000),
                        currency=video_info.get('currency', 'RUB')
                    )
                
                    # Создаём генератор с выбранной моделью
                    generator = AIPostGenerator(
                        openrouter_api_key=openrouter_key,
                        model=regenerate_model_id,
                        use_openrouter=True
                    )
                    # Загрузка существующих постов
                    try:
                        generator.load_existing_posts_from_file("data/my_posts.json")
                    except:
                        pass
                    generator.set_bonus_data(
                        url1=url1,
                        bonus1=bonus1,
                    )
                
                    # Генерируем новый пост
                    try:
                        new_post = await generator.generate_video_post(video_data, idx)
                    
                        # Обновляем пост в списке
                        generated_posts[idx]['text'] = new_post.text
                        regenerated_count += 1
                    
                        # Обновляем статус
                        await status_msg.edit_text(
                            f"🔄 <b>Перегенерация {len(posts_to_regenerate)} постов...</b>\n\n"
                            f"🤖 Модель: {regenerate_model_name}\n"
                            f"✅ Готово: {regenerated_count}/{len(posts_to_regenerate)}\n"
                            f"⏳ Осталось: {len(posts_to_regenerate) - regenerated_count}",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"Ошибка перегенерации поста #{idx+1}: {e}")
            
                # Сохраняем обновлённые посты
                await state.update_data(generated_posts=generated_posts)
            
                # Обновляем результат проверки
                result['duplicates'] = []
                result['is_unique'] = True
                result['summary'] = f"✅ Перегенерировано {regenerated_count} постов"
                await state.update_data(uniqueness_result=result)
            
                await status_msg.edit_text(
                    f"✅ <b>Перегенерация завершена!</b>\n\n"
                    f"🔄 Перегенерировано: {regenerated_count} постов\n"
                    f"📝 Всего постов: {len(generated_posts)}",
                    parse_mode="HTML"
                )
            
            except Exception as e:
                await status_msg.edit_text(
                    f"❌ <b>Ошибка перегенерации:</b>\n{str(e)[:200]}",
                    parse_mode="HTML"
                )
        
            await _show_posts_preview_after_check(message, state, result)
            return
    
        await message.answer("⚠️ Выберите действие из кнопок")

    @dp.message(SpanishPostsStates.preview_and_publish, lambda m: m.text == "👁 Ещё превью")
    async def streamer_posts_more_preview(message: types.Message, state: FSMContext):
        """Показать превью с листанием"""
        data = await state.get_data()
        posts = data.get('generated_posts', [])
    
        if not posts:
            await message.answer("⚠️ Нет постов для превью")
            return
    
        # Начинаем с первого поста
        await state.update_data(preview_index=0)
    
        post = posts[0]
        total = len(posts)
    
        # Inline кнопки навигации
        nav_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="preview_prev"),
                InlineKeyboardButton(text=f"1/{total}", callback_data="preview_info"),
                InlineKeyboardButton(text="▶️ Вперёд", callback_data="preview_next")
            ],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="preview_close")]
        ])
    
        await message.answer(
            f"📝 <b>Пост #{1} из {total}</b>\n\n"
            f"{post['text']}",
            parse_mode="HTML",
            reply_markup=nav_keyboard
        )

    @dp.callback_query(lambda c: c.data in ["preview_prev", "preview_next", "preview_close", "preview_info"])
    async def streamer_posts_preview_navigation(callback: types.CallbackQuery, state: FSMContext):
        """Навигация по превью постов"""
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        current_idx = data.get('preview_index', 0)
        total = len(posts)
    
        if callback.data == "preview_close":
            await callback.message.delete()
            await callback.answer()
            return
    
        if callback.data == "preview_info":
            await callback.answer(f"Пост {current_idx + 1} из {total}")
            return
    
        if callback.data == "preview_prev":
            current_idx = (current_idx - 1) % total
        elif callback.data == "preview_next":
            current_idx = (current_idx + 1) % total
    
        await state.update_data(preview_index=current_idx)
    
        post = posts[current_idx]
    
        nav_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="preview_prev"),
                InlineKeyboardButton(text=f"{current_idx + 1}/{total}", callback_data="preview_info"),
                InlineKeyboardButton(text="▶️ Вперёд", callback_data="preview_next")
            ],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="preview_close")]
        ])
    
        try:
            await callback.message.edit_text(
                f"📝 <b>Пост #{current_idx + 1} из {total}</b>\n\n"
                f"{post['text']}",
                parse_mode="HTML",
                reply_markup=nav_keyboard
            )
        except:
            pass  # Если текст не изменился
    
        await callback.answer()

    @dp.message(SpanishPostsStates.waiting_for_target_channel, lambda m: m.text == "📋 Мои каналы")
    async def streamer_posts_show_channels(message: types.Message, state: FSMContext):
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
        
            # Сохраняем в state для выбора
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

    @dp.message(SpanishPostsStates.waiting_for_target_channel)
    async def streamer_posts_channel_handler(message: types.Message, state: FSMContext):
        """Обработка выбора канала для публикации → переход к выбору видео"""
        if message.text == "❌ Отмена":
            await state.clear()
            kb = get_scenarios_kb(message.from_user.id)
            await message.answer("❌ Отменено", reply_markup=kb)
            return
    
        if message.text == "📝 Ввести канал вручную":
            await message.answer(
                "Введите @username или ID канала:",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="❌ Отмена")]],
                    resize_keyboard=True
                )
            )
            return
    
        if message.text in ["👁 Ещё превью", "🔄 Перегенерировать все"]:
            # Эти кнопки обрабатываются отдельными хендлерами
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
        
            # Переходим к выбору картинок
            await state.set_state(SpanishPostsStates.choosing_image_source)
        
            data = await state.get_data()
            videos = data.get('videos', [])
        
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📡 Картинки из канала")],
                    [KeyboardButton(text="📤 Загрузить картинки")],
                    [KeyboardButton(text="⏭ Без картинок")],
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
        
            await message.answer(
                f"✅ <b>Канал для публикации:</b> {channel_name}\n\n"
                f"📹 Видео: {len(videos)}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>🖼 Шаг 4: Картинки для бонусных постов</b>\n\n"
                f"Картинки используются для постов без видео\n"
                f"(обычно 20 из 100 постов)",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
        except Exception as e:
            logger.error(f"Ошибка доступа к каналу: {e}")
            await message.answer(
                f"❌ Ошибка: {e}\n\n"
                "Попробуйте ввести канал ещё раз"
            )

    @dp.message(SpanishPostsStates.confirming, lambda m: m.text == "🔄 Перегенерировать посты")
    @dp.message(SpanishPostsStates.preview_and_publish, lambda m: m.text == "🔄 Перегенерировать все")
    async def streamer_posts_regenerate(message: types.Message, state: FSMContext):
        """Перегенерация постов через AI"""
        data = await state.get_data()
        videos = data.get('videos', [])
        images = data.get('images', [])
    
        total_posts = len(videos) + len(images)
    
        status_msg = await message.answer(
            f"🔄 <b>AI перегенерирует все посты...</b>\n\n"
            f"⏳ Прогресс: 0/{total_posts}",
            parse_mode="HTML"
        )
    
        from src.ai_post_generator import AIPostGenerator, VideoData
    
        api_key = config_manager.openai_api_key
        model = data.get('ai_model_used') or config_manager.default_model or "gpt-4o-mini"
    
        generator = AIPostGenerator(api_key=api_key, model=model)
        # Загрузка существующих постов
        try:
            generator.load_existing_posts_from_file("data/my_posts.json")
        except:
            pass
        generator.set_bonus_data(
            url1=data['url1'],
            bonus1=data['bonus1']
        )
    
        video_data_list = [
            VideoData(
                streamer=v.get('streamer', ''),
                slot=v.get('slot', 'Слот'),
                bet=v.get('bet', 100),
                win=v.get('win', 10000),
                currency=v.get('currency', 'RUB')  # Извлекаем валюту из данных или используем RUB по умолчанию
            )
            for v in videos
        ]
    
        async def progress_callback(current, total):
            try:
                await status_msg.edit_text(
                    f"🔄 <b>AI перегенерирует посты...</b>\n\n"
                    f"⏳ Прогресс: {current}/{total}\n"
                    f"{'█' * (current * 20 // total)}{'░' * (20 - current * 20 // total)}",
                    parse_mode="HTML"
                )
            except:
                pass
    
        try:
            ai_posts = await generator.generate_all_posts(
                videos=video_data_list,
                image_count=len(images),
                progress_callback=progress_callback
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка: {e}", parse_mode="HTML")
            return
    
        # Сохраняем с привязкой к медиа
        generated_posts = []
        video_idx = 0
        image_idx = 0
    
        for post in ai_posts:
            if post.media_type == "video" and video_idx < len(videos):
                # КРИТИЧНО: Находим правильное видео по streamer+slot из поста!
                matching_video = None
                
                for v in videos:
                    v_streamer = v.get('streamer', '').strip().lower()
                    v_slot = v.get('slot', '').strip().lower()
                    post_streamer = post.streamer.strip().lower()
                    post_slot = post.slot.strip().lower()
                    
                    if v_streamer == post_streamer and v_slot == post_slot:
                        matching_video = v
                        break
                
                if not matching_video:
                    matching_video = videos[video_idx]
                    print(f"⚠️ Перегенерация: не найдено точное совпадение для поста #{post.index}")
                
                video_idx += 1
            
                generated_posts.append({
                    'index': post.index,
                    'media_path': matching_video.get('file_id'),
                    'source_channel_id': matching_video.get('source_channel_id'),
                    'message_id': matching_video.get('message_id'),
                    'media_type': post.media_type,
                    'text': post.text,
                    'streamer': post.streamer,
                    'slot': post.slot
                })
            
            elif post.media_type == "image" and image_idx < len(images):
                image_data = images[image_idx]
                image_idx += 1
            
                generated_posts.append({
                    'index': post.index,
                    'media_path': image_data.get('file_id'),
                    'source_channel_id': image_data.get('source_channel_id'),
                    'message_id': image_data.get('message_id'),
                    'media_type': post.media_type,
                    'text': post.text,
                    'streamer': post.streamer,
                    'slot': post.slot
                })
    
        await state.update_data(generated_posts=generated_posts)
    
        preview = generated_posts[0] if generated_posts else None
        await status_msg.edit_text(
            f"✅ <b>Посты перегенерированы!</b>\n\n"
            f"📝 Всего: {len(generated_posts)} постов\n\n"
            f"<b>Новое превью:</b>\n\n"
            f"{preview['text'] if preview else 'Нет постов'}",
            parse_mode="HTML"
        )

    @dp.message(SpanishPostsStates.confirming, lambda m: m.text == "✅ Начать публикацию")
    @dp.message(SpanishPostsStates.preview_and_publish, lambda m: m.text == "✅ Начать публикацию")
    async def streamer_posts_start_publishing(message: types.Message, state: FSMContext):
        """Начало публикации постов"""
        data = await state.get_data()
        posts = data.get('generated_posts', [])
        target_channel_id = data.get('target_channel_id')
    
        if not posts or not target_channel_id:
            await message.answer("❌ Ошибка: нет постов или канала")
            return
    
        await state.set_state(SpanishPostsStates.processing)
    
        # Инициализируем Telethon клиент
        from src.telethon_manager import TelethonClientManager
        manager = TelethonClientManager.get_instance(config_manager)
        await manager.ensure_initialized()
        client = manager.get_client()
    
        if not client:
            await message.answer("❌ Telethon клиент не инициализирован")
            return
    
        # Лимиты Telegram для безопасной публикации
        DELAY_MIN = 3  # Минимальная пауза между постами (сек)
        DELAY_MAX = 5  # Максимальная пауза между постами (сек)
        POSTS_BEFORE_LONG_PAUSE = 20  # После скольких постов делать длинную паузу
        LONG_PAUSE_SECONDS = 60  # Длинная пауза (сек)
        POSTS_BEFORE_VERY_LONG_PAUSE = 100  # После скольких постов - очень длинная пауза
        VERY_LONG_PAUSE_SECONDS = 300  # 5 минут
    
        import random as rnd
    
        # Флаг остановки публикации
        await state.update_data(stop_publishing=False)
    
        # Inline кнопка "Стоп"
        stop_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛑 Остановить публикацию", callback_data="stop_streamer_publishing")]
        ])
    
        status_msg = await message.answer(
            f"🚀 <b>Публикация началась!</b>\n\n"
            f"📝 Постов: {len(posts)}\n"
            f"⏱ Интервал: {DELAY_MIN}-{DELAY_MAX} сек\n"
            f"⏸ Пауза каждые {POSTS_BEFORE_LONG_PAUSE} постов: {LONG_PAUSE_SECONDS} сек\n\n"
            f"Прогресс: 0/{len(posts)}\n\n"
            f"<i>Нажмите кнопку ниже чтобы остановить</i>",
            parse_mode="HTML",
            reply_markup=stop_keyboard
        )
    
        published = 0
        errors = 0
        stopped = False
    
        for i, post in enumerate(posts):
            # Проверяем флаг остановки
            current_data = await state.get_data()
            if current_data.get('stop_publishing', False):
                stopped = True
                break
            try:
                # Если есть source_channel_id и message_id - копируем через Telethon
                if post.get('source_channel_id') and post.get('message_id'):
                    # Получаем оригинальное сообщение
                    original_msg = await client.get_messages(
                        post['source_channel_id'], 
                        ids=post['message_id']
                    )
                
                    if original_msg:
                        # Копируем с новым текстом (HTML форматирование)
                        await client.send_message(
                            target_channel_id,
                            post['text'],
                            file=original_msg.media,
                            parse_mode='html'  # HTML форматирование для Telethon
                        )
                        published += 1
                    else:
                        raise Exception("Сообщение не найдено в источнике")
            
                # Если есть file_id (загружено вручную) - отправляем через aiogram
                elif post.get('media_path'):
                    if post['media_type'] == 'video':
                        await bot.send_video(
                            chat_id=target_channel_id,
                            video=post['media_path'],  # file_id
                            caption=post['text'],
                            parse_mode="HTML"  # HTML форматирование
                        )
                    else:
                        await bot.send_photo(
                            chat_id=target_channel_id,
                            photo=post['media_path'],  # file_id
                            caption=post['text'],
                            parse_mode="HTML"  # HTML форматирование
                        )
                    published += 1
                else:
                    raise Exception("Нет источника медиа")
            
                # Обновляем статус каждые 10 постов
                if (i + 1) % 10 == 0:
                    try:
                        await status_msg.edit_text(
                            f"🚀 <b>Публикация...</b>\n\n"
                            f"✅ Опубликовано: {published}\n"
                            f"❌ Ошибок: {errors}\n\n"
                            f"Прогресс: {i+1}/{len(posts)}",
                            parse_mode="HTML"
                        )
                    except:
                        pass
            
                # Динамическая задержка с учётом лимитов Telegram
                post_num = i + 1
            
                # Очень длинная пауза каждые 100 постов (5 мин)
                if post_num > 0 and post_num % POSTS_BEFORE_VERY_LONG_PAUSE == 0:
                    try:
                        await status_msg.edit_text(
                            f"⏸ <b>Пауза {VERY_LONG_PAUSE_SECONDS // 60} мин...</b>\n\n"
                            f"Защита от лимитов Telegram\n"
                            f"✅ Опубликовано: {published}/{len(posts)}",
                            parse_mode="HTML"
                        )
                    except:
                        pass
                    await asyncio.sleep(VERY_LONG_PAUSE_SECONDS)
            
                # Длинная пауза каждые 20 постов (1 мин)
                elif post_num > 0 and post_num % POSTS_BEFORE_LONG_PAUSE == 0:
                    try:
                        await status_msg.edit_text(
                            f"⏸ <b>Пауза {LONG_PAUSE_SECONDS} сек...</b>\n\n"
                            f"Защита от лимитов Telegram\n"
                            f"✅ Опубликовано: {published}/{len(posts)}",
                            parse_mode="HTML"
                        )
                    except:
                        pass
                    await asyncio.sleep(LONG_PAUSE_SECONDS)
            
                else:
                    # Обычная рандомная задержка между постами
                    delay = rnd.uniform(DELAY_MIN, DELAY_MAX)
                    await asyncio.sleep(delay)
            
            except Exception as e:
                errors += 1
                print(f"Ошибка публикации поста {i}: {e}")
    
        await state.clear()
        kb = get_scenarios_kb(message.from_user.id)
    
        if stopped:
            await status_msg.edit_text(
                f"🛑 <b>Публикация остановлена!</b>\n\n"
                f"📝 Всего постов: {len(posts)}\n"
                f"✅ Опубликовано: {published}\n"
                f"⏸ Пропущено: {len(posts) - published - errors}\n"
                f"❌ Ошибок: {errors}",
                parse_mode="HTML"
            )
        
            await message.answer(
                f"🛑 Публикация остановлена.\n"
                f"Опубликовано {published} из {len(posts)} постов.",
                reply_markup=kb
            )
        else:
            await status_msg.edit_text(
                f"✅ <b>Публикация завершена!</b>\n\n"
                f"📝 Всего постов: {len(posts)}\n"
                f"✅ Опубликовано: {published}\n"
                f"❌ Ошибок: {errors}",
                parse_mode="HTML"
            )
        
            await message.answer(
                "🎉 Готово! Все посты опубликованы.",
                reply_markup=kb
            )

    @dp.callback_query(lambda c: c.data == "stop_streamer_publishing")
    async def streamer_posts_stop_publishing(callback: types.CallbackQuery, state: FSMContext):
        """Остановка публикации"""
        await state.update_data(stop_publishing=True)
        await callback.answer("🛑 Останавливаю публикацию...", show_alert=True)
    
        # Убираем кнопку
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass

    @dp.message(SpanishPostsStates.confirming, lambda m: m.text == "❌ Отмена")
    @dp.message(SpanishPostsStates.waiting_for_videos, lambda m: m.text == "❌ Отмена")
    @dp.message(SpanishPostsStates.waiting_for_images, lambda m: m.text == "❌ Отмена")
    async def streamer_posts_cancel(message: types.Message, state: FSMContext):
        """Отмена сценария"""
        await state.clear()
        kb = get_scenarios_kb(message.from_user.id)
        await message.answer("❌ Сценарий отменён", reply_markup=kb)

