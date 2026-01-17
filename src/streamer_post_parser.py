"""
@file: streamer_post_parser.py
@description: Парсер метаданных из имён файлов видео
@dependencies: re
@created: 2026-01-05
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class StreamerPostData:
    """Данные из имени файла"""
    streamer: str = ""
    slot: str = ""
    bet: int = 0
    win: int = 0
    multiplier: float = 0.0
    
    def is_valid(self) -> bool:
        """Проверяет что есть минимум слот, ставка и выигрыш"""
        return bool(self.slot and self.bet > 0 and self.win > 0)
    
    def __post_init__(self):
        """Вычисляет множитель если не указан"""
        if self.bet > 0 and self.win > 0 and self.multiplier == 0:
            self.multiplier = round(self.win / self.bet, 1)


class StreamerPostParser:
    """
    Парсер имён файлов видео.
    
    Поддерживаемый формат:
    Стример_Слот_Ставка_Выигрыш.mp4
    
    Примеры:
    - Жека_Gates of Olympus_500_125000.mp4
    - Gena88_Sweet Bonanza_200_89000.mp4
    - Player_Slot Name_1000_500000.mp4
    """
    
    def parse_filename(self, filename: str) -> Optional[StreamerPostData]:
        """
        Парсит имя файла и извлекает метаданные.
        
        Args:
            filename: Имя файла (например: "Жека_Gates of Olympus_500_125000.mp4")
            
        Returns:
            StreamerPostData с данными или None если не удалось распарсить
        """
        if not filename:
            return None
        
        # Убираем расширение
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Паттерн: Стример_Слот_Ставка_Выигрыш
        # Слот может содержать пробелы и подчёркивания
        pattern = r'^([^_]+)_(.+?)_(\d+)_(\d+)$'
        match = re.match(pattern, name_without_ext)
        
        if not match:
            return None
        
        try:
            streamer = match.group(1).strip()
            slot = match.group(2).strip().replace('_', ' ')  # Заменяем _ на пробелы в названии слота
            bet = int(match.group(3))
            win = int(match.group(4))
            
            if bet <= 0 or win <= 0:
                return None
            
            return StreamerPostData(
                streamer=streamer,
                slot=slot,
                bet=bet,
                win=win
            )
        except (ValueError, IndexError):
            return None
