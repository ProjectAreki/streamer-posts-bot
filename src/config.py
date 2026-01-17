"""
Конфигурация бота
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Конфигурация Telegram бота"""
    bot_token: str
    api_id: int
    api_hash: str
    session_name: str = "streamer_bot"


@dataclass
class OpenRouterConfig:
    """Конфигурация OpenRouter API"""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"


@dataclass
class OpenAIConfig:
    """Конфигурация OpenAI API (fallback)"""
    api_key: str = None


@dataclass
class Config:
    """Основная конфигурация"""
    bot: BotConfig
    openrouter: OpenRouterConfig
    openai: OpenAIConfig
    
    @classmethod
    def from_env(cls):
        """Создание конфигурации из переменных окружения"""
        return cls(
            bot=BotConfig(
                bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
                api_id=int(os.getenv("TELEGRAM_API_ID", "0")),
                api_hash=os.getenv("TELEGRAM_API_HASH", ""),
                session_name=os.getenv("TELEGRAM_SESSION_NAME", "streamer_bot")
            ),
            openrouter=OpenRouterConfig(
                api_key=os.getenv("OPENROUTER_API_KEY", "")
            ),
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY")
            )
        )
