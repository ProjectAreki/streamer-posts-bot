"""
@file: config_manager.py
@description: Упрощенный менеджер конфигурации для StreamerPostsBot
@created: 2026-01-14
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ConfigManager:
    """Упрощенный менеджер конфигурации"""
    
    # API ключи
    openrouter_api_key: str
    openai_api_key: str
    
    # Telegram
    bot_token: str
    api_id: int
    api_hash: str
    
    # Настройки генерации
    default_ai_provider: str = "openrouter"
    default_model: str = "deepseek/deepseek-chat"
    
    # Лимиты
    max_posts: int = 100
    max_video_size_mb: int = 50
    max_image_size_mb: int = 10
    
    @classmethod
    def from_config(cls, config: Any) -> "ConfigManager":
        """Создает ConfigManager из объекта Config"""
        return cls(
            openrouter_api_key=config.openrouter.api_key,
            openai_api_key=config.openai.api_key or "",
            bot_token=config.bot.bot_token,
            api_id=config.bot.api_id,
            api_hash=config.bot.api_hash,
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации"""
        return getattr(self, key, default)
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Получить конфигурацию AI"""
        return {
            "provider": self.default_ai_provider,
            "model": self.default_model,
            "openrouter_api_key": self.openrouter_api_key,
            "openai_api_key": self.openai_api_key,
        }
