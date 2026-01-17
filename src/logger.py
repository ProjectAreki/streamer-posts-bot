"""
@file: logger.py
@description: Упрощенная система логирования для StreamerPostsBot
@created: 2026-01-14
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


class BotLogger:
    """Упрощенный логгер для бота"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Настраиваем основной логгер
        self.logger = logging.getLogger("StreamerPostsBot")
        self.logger.setLevel(logging.INFO)
        
        # Очищаем старые handlers
        self.logger.handlers.clear()
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.log_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Информационное сообщение"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        log_msg = f"{message} | {extra_info}" if kwargs else message
        self.logger.info(log_msg)
    
    def warning(self, message: str, **kwargs):
        """Предупреждение"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        log_msg = f"{message} | {extra_info}" if kwargs else message
        self.logger.warning(log_msg)
    
    def error(self, message: str, **kwargs):
        """Ошибка"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        log_msg = f"{message} | {extra_info}" if kwargs else message
        self.logger.error(log_msg)
    
    def debug(self, message: str, **kwargs):
        """Отладочное сообщение"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        log_msg = f"{message} | {extra_info}" if kwargs else message
        self.logger.debug(log_msg)
