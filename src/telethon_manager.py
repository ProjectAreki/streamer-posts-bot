"""
@file: telethon_manager.py
@description: Единый менеджер Telethon-клиента (singleton) для совместного использования в модулях.
@dependencies: telethon, asyncio, typing, src.config, src.logger
@created: 2025-08-09
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, List
import os

from telethon import TelegramClient

from src.config import ConfigManager
from src.logger import BotLogger


class TelethonClientManager:
    """Единый менеджер Telethon клиента для всего процесса.

    Предоставляет общий клиент для модулей `ChatScanner` и `TelethonExtractor`.
    Поддерживает пер-пользовательский выбор активного клиента.
    """

    _instance: Optional["TelethonClientManager"] = None
    _client: Optional[TelegramClient] = None  # Дефолтный клиент (для обратной совместимости)
    _clients: List[TelegramClient] = []
    _rr_index: int = 0
    _lock = asyncio.Lock()
    _accounts_meta: List[dict] = []
    _user_active_clients: dict = {}  # user_id -> active_client_index
    _user_allowed_accounts: dict = {}  # user_id -> List[account_index] - разрешенные аккаунты

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = BotLogger()
        self.session_name = self._select_session_name()

    def _select_session_name(self) -> str:
        """Выбирает наиболее подходящее имя Telethon-сессии.
        Приоритет:
        1) chat_scanner_session
        2) content_extractor_session
        3) working_bot_session
        4) ninja_shared_session (по умолчанию)
        """
        candidates = []
        # Из известных ранее
        candidates.extend([
            "chat_scanner_session",
            "content_extractor_session",
            "working_bot_session",
        ])
        for name in candidates:
            session_file = Path(f"{name}.session")
            if session_file.exists():
                self.logger.info("Используем существующую Telethon сессию", session=str(session_file))
                return name
        # Фолбэк
        return "ninja_shared_session"

    @classmethod
    def get_instance(cls, config_manager: ConfigManager) -> "TelethonClientManager":
        if cls._instance is None:
            cls._instance = TelethonClientManager(config_manager)
        return cls._instance

    async def ensure_initialized(self) -> bool:
        """Инициализирует Telethon клиент один раз."""
        async with self._lock:
            if self._client is not None and self._clients:
                return True
            try:
                # Список аккаунтов: основной + доп. через переменные *_2..*_10
                accounts = []
                primary = (
                    self.config_manager.api_id,
                    self.config_manager.api_hash,
                    self.session_name,
                )
                accounts.append(primary)

                for i in range(2, 11):  # Поддержка до 10 аккаунтов
                    api_id_str = os.getenv(f"TELEGRAM_API_ID_{i}")
                    api_hash = os.getenv(f"TELEGRAM_API_HASH_{i}")
                    if api_id_str and api_hash:
                        try:
                            api_id_i = int(api_id_str)
                        except Exception:
                            continue
                        if api_id_i <= 0:
                            continue
                        session_name_i = os.getenv(
                            f"TELEGRAM_SESSION_NAME_{i}", f"ninja_shared_session_{i}"
                        )
                        accounts.append((api_id_i, api_hash, session_name_i))

                self._clients = []
                self._accounts_meta = []
                for idx, (api_id, api_hash, session_name) in enumerate(accounts, start=1):
                    if not api_id or not api_hash:
                        self.logger.error("Telethon API креды не настроены для аккаунта", account_index=idx)
                        continue
                    client = TelegramClient(
                        session_name,
                        api_id,
                        api_hash,
                        device_model="Desktop",
                        system_version="Windows",
                        app_version="1.0",
                        connection_retries=5,
                        retry_delay=1,
                        timeout=30,
                        request_retries=3,
                    )
                    await client.start()
                    # Собираем метаданные аккаунта
                    try:
                        me = await client.get_me()
                        meta = {
                            'index': idx - 1,
                            'session_name': session_name,
                            'user_id': getattr(me, 'id', None),
                            'username': getattr(me, 'username', None),
                            'phone': getattr(me, 'phone', None),
                        }
                        self._accounts_meta.append(meta)
                    except Exception:
                        self._accounts_meta.append({
                            'index': idx - 1,
                            'session_name': session_name,
                            'user_id': None,
                            'username': None,
                            'phone': None,
                        })
                    self._clients.append(client)

                if not self._clients:
                    self.logger.error("Не удалось инициализировать ни одного Telethon клиента")
                    return False

                self._client = self._clients[0]
                self._rr_index = 0
                self.logger.info("Telethon клиенты инициализированы", total=len(self._clients))
                return True
            except Exception as exc:
                self.logger.error("Ошибка инициализации Telethon общего клиента", error=str(exc))
                self._client = None
                self._clients = []
                return False

    def get_client(self, user_id: Optional[int] = None) -> Optional[TelegramClient]:
        """Возвращает активный клиент для указанного пользователя.
        
        Args:
            user_id: ID пользователя Telegram. Если None, возвращает глобальный активный клиент.
        """
        if not self._clients:
            return None
        
        # Если указан user_id и у него есть выбранный клиент
        if user_id is not None and user_id in self._user_active_clients:
            index = self._user_active_clients[user_id]
            if 0 <= index < len(self._clients):
                return self._clients[index]
        
        # Иначе возвращаем глобальный активный клиент
        return self._client

    def get_all_clients(self) -> List[TelegramClient]:
        """Возвращает список всех инициализированных клиентов."""
        return list(self._clients)

    def get_next_client(self) -> Optional[TelegramClient]:
        """Возвращает следующий клиент по кругу (round-robin)."""
        if not self._clients:
            return self._client
        client = self._clients[self._rr_index % len(self._clients)]
        self._rr_index = (self._rr_index + 1) % len(self._clients)
        return client

    def get_accounts_info(self) -> List[dict]:
        """Метаданные инициализированных аккаунтов (index, session_name, user_id, username, phone)."""
        return list(self._accounts_meta)

    def get_active_index(self, user_id: Optional[int] = None, db_manager=None) -> int:
        """Возвращает индекс активного клиента для указанного пользователя.
        
        Args:
            user_id: ID пользователя Telegram. Если None, возвращает глобальный активный клиент.
            db_manager: DatabaseManager для проверки прав из БД
        """
        if not self._clients:
            return -1
        
        # Если указан user_id, возвращаем его активный клиент
        if user_id is not None:
            if user_id in self._user_active_clients:
                return self._user_active_clients[user_id]
            
            # Если у пользователя еще нет активного клиента, установим первый разрешенный
            allowed = self.get_user_allowed_accounts(user_id, db_manager)
            if allowed is not None and len(allowed) > 0:
                # Устанавливаем первый разрешенный аккаунт
                first_allowed = allowed[0]
                self._user_active_clients[user_id] = first_allowed
                self.logger.info("🔧 Установлен первый разрешенный аккаунт для нового пользователя",
                                user_id=user_id, account_index=first_allowed,
                                allowed_accounts=allowed)
                return first_allowed
        
        # Иначе возвращаем глобальный активный клиент
        if self._client is None:
            return -1
        try:
            return self._clients.index(self._client)
        except ValueError:
            return -1

    async def set_active_client(self, index: int, user_id: Optional[int] = None, db_manager=None) -> bool:
        """Делает выбранный клиент активным для указанного пользователя.
        
        Args:
            index: Индекс клиента (0-based)
            user_id: ID пользователя Telegram. Если None, меняет глобальный активный клиент.
            db_manager: DatabaseManager для проверки прав из БД
            
        Returns:
            False если аккаунт запрещен для пользователя
        """
        async with self._lock:
            if not self._clients or index < 0 or index >= len(self._clients):
                return False
            
            # Проверка прав доступа к аккаунту
            if user_id is not None and not self.is_account_allowed_for_user(user_id, index, db_manager):
                self.logger.warning("Попытка переключения на запрещенный аккаунт",
                                   user_id=user_id, account_index=index)
                return False
            
            # Если указан user_id, сохраняем выбор для этого пользователя
            if user_id is not None:
                self._user_active_clients[user_id] = index
                self.logger.info("Активный Telethon аккаунт переключён для пользователя", 
                                user_id=user_id,
                                index=index,
                                session_name=self._accounts_meta[index]['session_name'] if index < len(self._accounts_meta) else None,
                                account_user_id=self._accounts_meta[index].get('user_id') if index < len(self._accounts_meta) else None)
            else:
                # Меняем глобальный активный клиент
                self._client = self._clients[index]
                self._rr_index = index % len(self._clients)
                self.logger.info("Глобальный активный Telethon аккаунт переключён", index=index,
                                 session_name=self._accounts_meta[index]['session_name'] if index < len(self._accounts_meta) else None,
                                 account_user_id=self._accounts_meta[index].get('user_id') if index < len(self._accounts_meta) else None)
            return True

    def set_user_allowed_accounts(self, user_id: int, allowed_indices: List[int], db_manager=None) -> None:
        """Устанавливает список разрешенных аккаунтов для пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            allowed_indices: Список индексов разрешенных аккаунтов (0-based)
            db_manager: DatabaseManager для сохранения в БД
        """
        self._user_allowed_accounts[user_id] = allowed_indices
        self.logger.info("Установлены разрешенные аккаунты для пользователя",
                        user_id=user_id, allowed_accounts=allowed_indices)
        
        # Сохраняем в БД если передан db_manager
        if db_manager:
            db_manager.set_user_allowed_accounts(user_id, allowed_indices)
    
    def get_user_allowed_accounts(self, user_id: int, db_manager=None) -> Optional[List[int]]:
        """Возвращает список разрешенных аккаунтов для пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            db_manager: DatabaseManager для загрузки из БД
            
        Returns:
            Список индексов разрешенных аккаунтов или None (все разрешены)
        """
        # Сначала проверяем кэш в памяти
        if user_id in self._user_allowed_accounts:
            return self._user_allowed_accounts.get(user_id)
        
        # Если нет в памяти и передан db_manager, загружаем из БД
        if db_manager:
            accounts = db_manager.get_user_allowed_accounts(user_id)
            if accounts is not None:
                self._user_allowed_accounts[user_id] = accounts
            return accounts
        
        return None
    
    def is_account_allowed_for_user(self, user_id: int, account_index: int, db_manager=None) -> bool:
        """Проверяет, разрешен ли аккаунт для пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            account_index: Индекс аккаунта
            db_manager: DatabaseManager для загрузки из БД
            
        Returns:
            True если разрешен или нет ограничений, False если запрещен
        """
        allowed = self.get_user_allowed_accounts(user_id, db_manager)
        if allowed is None:
            return True  # Нет ограничений - все разрешены
        return account_index in allowed
    
    def load_all_user_accounts_from_db(self, db_manager) -> None:
        """Загружает все права доступа к аккаунтам из БД в память.
        
        Args:
            db_manager: DatabaseManager для загрузки из БД
        """
        try:
            # Получаем список всех пользователей с ограничениями
            # Для этого нужно добавить метод в DatabaseManager или загружать по запросу
            self.logger.info("Права доступа к аккаунтам будут загружаться по требованию из БД")
        except Exception as e:
            self.logger.error("Ошибка загрузки прав доступа к аккаунтам", error=str(e))

    async def reconnect(self) -> bool:
        """Переподключает Telethon клиента."""
        async with self._lock:
            try:
                # Отключаем все, если были
                for cl in self._clients:
                    try:
                        await cl.disconnect()
                    except Exception:
                        pass
                self._clients = []
                self._client = None
                self._rr_index = 0
                return await self.ensure_initialized()
            except Exception as exc:
                self.logger.error("Ошибка переподключения Telethon общего клиента", error=str(exc))
                return False

