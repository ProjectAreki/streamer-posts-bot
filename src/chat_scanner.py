"""
@file: chat_scanner.py
@description: Telethon клиент для работы с Telegram каналами
@created: 2026-01-14
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict
from telethon import TelegramClient, types
from telethon.tl.types import InputMediaPhotoExternal, InputMediaDocumentExternal


class ChatScanner:
    """Класс для работы с Telegram каналами через Telethon"""
    
    def __init__(self, api_id: int, api_hash: str, logger=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.logger = logger
        self.client: Optional[TelegramClient] = None
        # Используем путь к сессии в data/
        self.session_file = "data/streamer_bot"
    
    async def start(self):
        """Запуск Telethon клиента"""
        try:
            # Создаём директорию для сессий
            Path("data").mkdir(exist_ok=True)
            
            self.client = TelegramClient(
                self.session_file,
                self.api_id,
                self.api_hash
            )
            
            # Подключаемся без интерактивной авторизации
            # Сессия должна быть уже создана заранее
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                if self.logger:
                    self.logger.warning("Telethon сессия не авторизована! Работа в ограниченном режиме.")
                return False
            
            if self.logger:
                self.logger.info("Telethon клиент запущен")
            
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка запуска Telethon: {e}")
            return False
    
    async def stop(self):
        """Остановка Telethon клиента"""
        if self.client:
            await self.client.disconnect()
            if self.logger:
                self.logger.info("Telethon клиент остановлен")
    
    async def get_user_channels(self) -> List[Dict[str, any]]:
        """Получить список каналов пользователя"""
        try:
            dialogs = await self.client.get_dialogs()
            channels = []
            
            for dialog in dialogs:
                if hasattr(dialog.entity, 'broadcast') and dialog.entity.broadcast:
                    # Это канал (не группа)
                    if hasattr(dialog.entity, 'creator') and dialog.entity.creator:
                        # Пользователь - создатель канала
                        channels.append({
                            'id': dialog.entity.id,
                            'title': dialog.entity.title,
                            'username': getattr(dialog.entity, 'username', None)
                        })
                    elif hasattr(dialog.entity, 'admin_rights') and dialog.entity.admin_rights:
                        # Пользователь - администратор с правами публикации
                        if dialog.entity.admin_rights.post_messages:
                            channels.append({
                                'id': dialog.entity.id,
                                'title': dialog.entity.title,
                                'username': getattr(dialog.entity, 'username', None)
                            })
            
            return channels
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка получения каналов: {e}")
            return []
    
    async def send_media_to_channel(
        self,
        channel_id: int,
        media_path: str,
        caption: str,
        parse_mode: str = "html"
    ) -> bool:
        """
        Отправить медиа в канал
        
        Args:
            channel_id: ID канала
            media_path: Путь к медиа файлу
            caption: Текст поста
            parse_mode: Режим парсинга (html/markdown)
        
        Returns:
            True если успешно, False в противном случае
        """
        try:
            # Получаем entity канала
            channel = await self.client.get_entity(channel_id)
            
            # Отправляем медиа
            await self.client.send_file(
                channel,
                media_path,
                caption=caption,
                parse_mode=parse_mode
            )
            
            if self.logger:
                self.logger.info(
                    f"Медиа отправлено",
                    channel_id=channel_id,
                    media=Path(media_path).name
                )
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Ошибка отправки медиа",
                    channel_id=channel_id,
                    error=str(e)
                )
            return False
    
    async def copy_media_from_message(
        self,
        source_channel: int,
        message_id: int,
        target_channel: int,
        new_caption: str
    ) -> bool:
        """
        Копировать медиа из одного сообщения в другой канал
        
        Args:
            source_channel: ID канала-источника
            message_id: ID сообщения
            target_channel: ID целевого канала
            new_caption: Новый текст поста
        
        Returns:
            True если успешно, False в противном случае
        """
        try:
            # Получаем исходное сообщение
            source = await self.client.get_entity(source_channel)
            message = await self.client.get_messages(source, ids=message_id)
            
            if not message or not message.media:
                if self.logger:
                    self.logger.warning(f"Сообщение не найдено или нет медиа")
                return False
            
            # Получаем целевой канал
            target = await self.client.get_entity(target_channel)
            
            # Копируем медиа
            await self.client.send_file(
                target,
                message.media,
                caption=new_caption,
                parse_mode="html"
            )
            
            if self.logger:
                self.logger.info(
                    f"Медиа скопировано",
                    source=source_channel,
                    target=target_channel,
                    msg_id=message_id
                )
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка копирования медиа: {e}")
            return False
