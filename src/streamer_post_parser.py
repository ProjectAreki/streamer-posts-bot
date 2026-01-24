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
        """Проверяет что есть минимум ставка и выигрыш (слот опционален)"""
        return bool(self.bet > 0 and self.win > 0)
    
    def __post_init__(self):
        """Вычисляет множитель если не указан"""
        if self.bet > 0 and self.win > 0 and self.multiplier == 0:
            self.multiplier = round(self.win / self.bet, 1)


class StreamerPostParser:
    """
    Парсер имён файлов видео.
    
    Поддерживаемые форматы:
    1. Ставка_Выигрыш.mp4 (без слота и стримера)
    2. Слот_Ставка_Выигрыш.mp4 (со слотом, без стримера)
    3. Стример_Слот_Ставка_Выигрыш.mp4 (полный формат)
    
    Примеры:
    - 725_14500.mp4 (без слота)
    - Gates_of_Olympus_500_125000.mp4 (со слотом)
    - Жека_Gates_of_Olympus_500_125000.mp4 (полный)
    """
    
    def parse_filename(self, filename: str) -> Optional[StreamerPostData]:
        """
        Парсит имя файла и извлекает метаданные.
        
        Args:
            filename: Имя файла
            
        Returns:
            StreamerPostData с данными или None если не удалось распарсить
        """
        if not filename:
            return None
        
        # Убираем расширение
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Убираем валютные символы и буквы из чисел (например: 725EUR, 14500USD)
        # Заменяем на просто числа для парсинга
        name_clean = re.sub(r'([A-Z]{3}|[€$£])', '', name_without_ext)
        
        # Паттерн 1: Ставка_Выигрыш (2 числа)
        pattern_2 = r'^(\d+)_(\d+)$'
        match_2 = re.match(pattern_2, name_clean)
        if match_2:
            try:
                bet = int(match_2.group(1))
                win = int(match_2.group(2))
                if bet > 0 and win > 0:
                    return StreamerPostData(
                        streamer="",
                        slot="",  # Без слота
                        bet=bet,
                        win=win
                    )
            except ValueError:
                pass
        
        # Паттерн 2: Слот_Ставка_Выигрыш (3 части, последние 2 - числа)
        pattern_3 = r'^(.+?)_(\d+)_(\d+)$'
        match_3 = re.match(pattern_3, name_clean)
        if match_3:
            try:
                slot = match_3.group(1).strip().replace('_', ' ')
                bet = int(match_3.group(2))
                win = int(match_3.group(3))
                if bet > 0 and win > 0:
                    return StreamerPostData(
                        streamer="",  # Без стримера
                        slot=slot,
                        bet=bet,
                        win=win
                    )
            except ValueError:
                pass
        
        # Паттерн 3: Стример_Слот_Ставка_Выигрыш (4 части, последние 2 - числа)
        # Ищем последние 2 числа и всё что перед ними
        pattern_4 = r'^(.+?)_(.+?)_(\d+)_(\d+)$'
        match_4 = re.match(pattern_4, name_clean)
        if match_4:
            try:
                streamer = match_4.group(1).strip()
                slot = match_4.group(2).strip().replace('_', ' ')
                bet = int(match_4.group(3))
                win = int(match_4.group(4))
                if bet > 0 and win > 0:
                    return StreamerPostData(
                        streamer=streamer,
                        slot=slot,
                        bet=bet,
                        win=win
                    )
            except ValueError:
                pass
        
        return None
