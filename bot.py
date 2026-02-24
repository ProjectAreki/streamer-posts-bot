"""
Главный файл бота - Streamer Posts Bot
Генерация 100 уникальных постов про стримеров через AI (OpenRouter)
"""

import asyncio
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import Config
from src.config_manager import ConfigManager
from src.logger import BotLogger
# ChatScanner удален - используем TelethonClientManager
from src.handlers.streamer_posts_handlers import register_streamer_handlers
from src.handlers.image_posts_handlers import register_image_posts_handlers
from src.handlers.spanish_posts_handlers import register_spanish_handlers
from src.handlers.italian_posts_handlers import register_italian_handlers
from src.handlers.french_posts_handlers import register_french_handlers


class StreamerPostsBot:
    """Упрощенный бот только для генерации постов стримеров"""
    
    def __init__(self):
        # Создаём директорию для логов
        Path("logs").mkdir(exist_ok=True)
        
        # Загрузка конфигурации
        self.config = Config.from_env()
        
        # Инициализация компонентов
        self.logger = BotLogger()
        self.config_manager = ConfigManager.from_config(self.config)
        
        # Инициализация бота и диспетчера
        self.bot = Bot(token=self.config.bot.bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        
        # Chat scanner убран - используем TelethonClientManager в handlers
        self.chat_scanner = None
        
        # DB Manager (заглушка - не используется в этом боте)
        self.db_manager = None
        
        # Регистрация обработчиков
        self._register_base_handlers()
        register_streamer_handlers(self)
        register_image_posts_handlers(self)
        register_spanish_handlers(self)
        register_italian_handlers(self)
        register_french_handlers(self)
        
        self.logger.info("✅ Бот инициализирован")
    
    def get_allowed_scenarios_keyboard(self, user_id: int):
        """Получить клавиатуру сценариев (упрощенная версия)"""
        # В этом боте три сценария, всегда доступны
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📹 100 постов стримеров")],
                [KeyboardButton(text="📹ES 100 posteos")],
                [KeyboardButton(text="📹IT 100 post italiani")],
                [KeyboardButton(text="📹FR 100 posts francais")],
                [KeyboardButton(text="🖼 Посты с картинками")],
                [KeyboardButton(text="❓ Помощь")]
            ],
            resize_keyboard=True
        )
    
    def is_scenario_allowed(self, user_id: int, scenario: str) -> bool:
        """Проверка доступа к сценарию (упрощенная версия)"""
        # В этом боте все сценарии доступны всем
        return True
    
    async def get_user_channels(self, user_id: int):
        """Получить список каналов пользователя через TelethonClientManager"""
        try:
            from src.telethon_manager import TelethonClientManager
            
            manager = TelethonClientManager.get_instance(self.config_manager)
            await manager.ensure_initialized()
            
            if not manager._clients:
                return []
            
            # Используем первый доступный клиент
            client = manager._clients[0]
            dialogs = await client.get_dialogs()
            channels = []
            
            for dialog in dialogs:
                if hasattr(dialog.entity, 'broadcast') and dialog.entity.broadcast:
                    if (hasattr(dialog.entity, 'creator') and dialog.entity.creator) or \
                       (hasattr(dialog.entity, 'admin_rights') and dialog.entity.admin_rights and 
                        dialog.entity.admin_rights.post_messages):
                        channels.append({
                            'id': dialog.entity.id,
                            'title': dialog.entity.title,
                            'username': getattr(dialog.entity, 'username', None)
                        })
            
            return channels
        except Exception as e:
            self.logger.error(f"Ошибка получения каналов: {e}")
            return []
    
    async def show_user_channels(self, message: types.Message, state):
        """Показать каналы пользователя - использует TelethonClientManager"""
        try:
            from src.telethon_manager import TelethonClientManager
            
            manager = TelethonClientManager.get_instance(self.config_manager)
            await manager.ensure_initialized()
            
            if not manager._clients:
                await message.answer("❌ Telethon клиент не инициализирован")
                return
            
            # Используем первый доступный клиент
            client = manager._clients[0]
            dialogs = await client.get_dialogs()
            channels = []
            
            for dialog in dialogs:
                if hasattr(dialog.entity, 'broadcast') and dialog.entity.broadcast:
                    if (hasattr(dialog.entity, 'creator') and dialog.entity.creator) or \
                       (hasattr(dialog.entity, 'admin_rights') and dialog.entity.admin_rights and dialog.entity.admin_rights.post_messages):
                        channels.append({
                            'id': dialog.entity.id,
                            'title': dialog.entity.title,
                            'username': getattr(dialog.entity, 'username', None)
                        })
            
            if not channels:
                await message.answer(
                    "❌ Каналы не найдены.\n\n"
                    "Убедитесь, что:\n"
                    "• Вы создатель или администратор канала\n"
                    "• У вас есть права на публикацию\n"
                    "• API_ID и API_HASH настроены правильно"
                )
                return
            
            # Формируем клавиатуру с каналами
            keyboard_buttons = []
            for channel in channels:
                title = channel['title']
                if len(title) > 30:
                    title = title[:27] + "..."
                keyboard_buttons.append([KeyboardButton(text=f"📢 {title}")])
            
            keyboard_buttons.append([KeyboardButton(text="❌ Отмена")])
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=keyboard_buttons,
                resize_keyboard=True
            )
            
            # Сохраняем каналы в state для последующего использования
            from aiogram.fsm.context import FSMContext
            await state.update_data(available_channels=channels)
            
            await message.answer(
                f"📢 <b>Найдено каналов: {len(channels)}</b>\n\n"
                "Выберите канал для публикации:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка показа каналов: {e}")
            await message.answer(
                "❌ Ошибка получения каналов.\n"
                "Проверьте настройки Telegram API."
            )
    
    def _register_base_handlers(self):
        """Регистрация базовых обработчиков"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            """Обработчик команды /start"""
            keyboard = self.get_allowed_scenarios_keyboard(message.from_user.id)
            
            await message.answer(
                "👋 <b>Добро пожаловать в Streamer Posts Bot!</b>\n\n"
                "🎯 <b>Что я умею:</b>\n"
                "• Генерация 100 уникальных постов про стримеров казино\n"
                "• 80 видео + 20 картинок\n"
                "• AI генерация через 15+ моделей OpenRouter\n"
                "• Проверка уникальности через «Сторожевой AI»\n"
                "• Публикация в Telegram канал\n\n"
                "📱 Нажмите кнопку ниже, чтобы начать!",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
        @self.dp.message(Command("help"))
        @self.dp.message(lambda m: m.text == "❓ Помощь")
        async def cmd_help(message: types.Message):
            """Обработчик команды /help"""
            help_text = """
📖 <b>Как пользоваться ботом:</b>

<b>1️⃣ Нажмите "📹 100 постов стримеров"</b>

<b>2️⃣ Введите данные:</b>
   • 2 ссылки с бонусами
   • Выберите канал для публикации
   • Загрузите видео (или возьмите из канала)
   • Загрузите картинки (опционально)

<b>3️⃣ Выберите AI модель:</b>
   💰 Дешёвые: ~5₽ за 100 постов
   ⚖️ Средние: ~40₽ за 100 постов
   💎 Премиум: ~100₽ за 100 постов

<b>4️⃣ AI сгенерирует уникальные тексты</b>

<b>5️⃣ Проверка уникальности</b>
   "Сторожевой AI" найдёт похожие посты

<b>6️⃣ Публикация в канал</b>
   Автоматическая отправка с умными паузами

<b>⚙️ Требования:</b>
• OPENROUTER_API_KEY - обязательно!
• TELEGRAM_API_ID и API_HASH - для работы с каналами

<b>💰 Стоимость:</b>
Зависит от выбранной AI модели:
• Qwen 3 235B: ~0.03₽/пост
• Gemini Flash: ~0.4₽/пост
• Claude Opus: ~2.8₽/пост

<b>🔗 Полезные ссылки:</b>
• OpenRouter: https://openrouter.ai/
• Telegram API: https://my.telegram.org/apps
"""
            await message.answer(help_text, parse_mode="HTML")
    
    async def start(self):
        """Запуск бота"""
        try:
            self.logger.info("🚀 Запуск бота...")
            
            # Chat scanner удален - Telethon инициализируется в handlers при первом использовании
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except KeyboardInterrupt:
            self.logger.info("⏹️ Остановка бота...")
        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")
        finally:
            # Cleanup если нужен
            pass
            await self.bot.session.close()
    
    def run(self):
        """Запуск бота в синхронном режиме"""
        asyncio.run(self.start())


if __name__ == "__main__":
    bot = StreamerPostsBot()
    bot.run()
