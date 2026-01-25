#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования парсинга постов и имен файлов
"""

import sys
import io

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.streamer_post_parser import StreamerPostParser
from src.caption_parser import CaptionParser

def test_filename_parsing(filename):
    """Тестирует парсинг имени файла"""
    parser = StreamerPostParser()
    result = parser.parse_filename(filename)
    
    if result:
        print(f"✅ Файл: {filename}")
        print(f"   Стример: '{result.streamer}'")
        print(f"   Слот: '{result.slot}'")
        print(f"   Ставка: {result.bet}")
        print(f"   Выигрыш: {result.win}")
        print(f"   Множитель: x{result.multiplier}")
        print(f"   Валидный: {result.is_valid()}")
        return True
    else:
        print(f"❌ Файл: {filename} - не распарсился")
        return False

def test_caption_parsing(caption):
    """Тестирует парсинг подписи"""
    result = CaptionParser.parse(caption)
    
    print(f"📝 Подпись:")
    print(f"   {caption[:100]}..." if len(caption) > 100 else f"   {caption}")
    print(f"   Стример: '{result.streamer}'")
    print(f"   Слот: '{result.slot}'")
    print(f"   Ставка: {result.bet}")
    print(f"   Выигрыш: {result.win}")
    print(f"   Множитель: x{result.multiplier}")
    print(f"   Валюта: {result.currency}")
    print(f"   Валидный: {result.is_valid()}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ПАРСИНГА")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        # Если переданы аргументы - парсим их
        for arg in sys.argv[1:]:
            if arg.endswith('.mp4') or arg.endswith('.MP4'):
                test_filename_parsing(arg)
                print()
            else:
                test_caption_parsing(arg)
    else:
        print("Использование:")
        print("  python test_parsing.py 'имя_файла.mp4' 'подпись к видео'")
        print()
        print("Или введите данные вручную:")
        print()
        
        # Тестовые примеры
        print("📁 Тестирование имен файлов:")
        test_cases_files = [
            "725_14500.mp4",
            "Gates_of_Olympus_500_125000.mp4",
            "Sweet_Bonanza_100_25000.mp4",
            "Жека_Gates_of_Olympus_500_125000.mp4",
            "725EUR_14500EUR.mp4",
        ]
        
        for filename in test_cases_files:
            test_filename_parsing(filename)
            print()
        
        print("📝 Тестирование подписей:")
        test_cases_captions = [
            "слот Rip City\nвыигрыш 644580.00 р\nставка 300 р",
            "Слот: Gates of Olympus\nВыигрыш: 125 000₽\nСтавка: 500₽",
            "Gates of Olympus | 500₽ → 125000₽",
            "🎰 Sweet Bonanza\n💰 89 000 р\n💵 200 р",
        ]
        
        for caption in test_cases_captions:
            test_caption_parsing(caption)
