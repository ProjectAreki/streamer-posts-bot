#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования парсинга постов из JSON экспорта Telegram
"""

import json
import sys
import io
from pathlib import Path

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.streamer_post_parser import StreamerPostParser
from src.caption_parser import CaptionParser


def extract_text_from_json_text(text_array):
    """Извлекает текст из массива объектов Telegram JSON"""
    if not text_array:
        return ""
    
    result = []
    for item in text_array:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            result.append(item.get('text', ''))
    
    return ''.join(result)


def test_json_file(json_path):
    """Тестирует парсинг постов из JSON файла"""
    print("=" * 80)
    print(f"📁 Файл: {json_path}")
    print("=" * 80)
    print()
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return
    
    messages = data.get('messages', [])
    print(f"📊 Всего сообщений: {len(messages)}")
    
    # Фильтруем только видео
    video_messages = [msg for msg in messages if msg.get('media_type') == 'video_file']
    print(f"🎬 Видео сообщений: {len(video_messages)}")
    print()
    
    filename_parser = StreamerPostParser()
    caption_parser = CaptionParser()
    
    stats = {
        'total': len(video_messages),
        'filename_parsed': 0,
        'filename_valid': 0,
        'caption_parsed': 0,
        'caption_valid': 0,
        'both_parsed': 0,
        'errors': []
    }
    
    print("🔍 Проверка постов:")
    print("-" * 80)
    
    for i, msg in enumerate(video_messages[:50], 1):  # Проверяем первые 50
        msg_id = msg.get('id', '?')
        file_name = msg.get('file_name', '')
        text_array = msg.get('text', [])
        caption = extract_text_from_json_text(text_array)
        
        print(f"\n📹 Пост #{i} (ID: {msg_id})")
        print(f"   Файл: {file_name}")
        print(f"   Подпись: {caption[:100]}..." if len(caption) > 100 else f"   Подпись: {caption}")
        
        # Парсинг имени файла
        filename_result = filename_parser.parse_filename(file_name)
        if filename_result:
            stats['filename_parsed'] += 1
            if filename_result.is_valid():
                stats['filename_valid'] += 1
                print(f"   ✅ Файл распарсен: ставка={filename_result.bet}, выигрыш={filename_result.win}, слот='{filename_result.slot}'")
            else:
                print(f"   ⚠️  Файл распарсен, но невалиден: ставка={filename_result.bet}, выигрыш={filename_result.win}")
        else:
            print(f"   ❌ Файл не распарсен")
        
        # Парсинг подписи
        caption_result = caption_parser.parse(caption)
        if caption_result:
            stats['caption_parsed'] += 1
            if caption_result.is_valid():
                stats['caption_valid'] += 1
                print(f"   ✅ Подпись распарсена: ставка={caption_result.bet}, выигрыш={caption_result.win}, слот='{caption_result.slot}', валюта={caption_result.currency}")
            else:
                print(f"   ⚠️  Подпись распарсена, но невалидна: ставка={caption_result.bet}, выигрыш={caption_result.win}, слот='{caption_result.slot}'")
        else:
            print(f"   ❌ Подпись не распарсена")
        
        # Если оба распарсились
        if filename_result and caption_result:
            stats['both_parsed'] += 1
        
        # Проверка на ошибки
        if not filename_result and not caption_result:
            stats['errors'].append({
                'id': msg_id,
                'file': file_name,
                'caption': caption
            })
    
    print()
    print("=" * 80)
    print("📊 СТАТИСТИКА:")
    print("=" * 80)
    print(f"Всего проверено: {stats['total']}")
    print(f"Файлы распарсены: {stats['filename_parsed']} ({stats['filename_parsed']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"Файлы валидны: {stats['filename_valid']} ({stats['filename_valid']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"Подписи распарсены: {stats['caption_parsed']} ({stats['caption_parsed']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"Подписи валидны: {stats['caption_valid']} ({stats['caption_valid']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"Оба распарсены: {stats['both_parsed']} ({stats['both_parsed']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    
    if stats['errors']:
        print()
        print("=" * 80)
        print("❌ ПОСТЫ С ОШИБКАМИ ПАРСИНГА:")
        print("=" * 80)
        for error in stats['errors'][:10]:  # Показываем первые 10
            print(f"ID: {error['id']}")
            print(f"  Файл: {error['file']}")
            print(f"  Подпись: {error['caption'][:150]}")
            print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        # Путь по умолчанию
        json_path = r"c:\Users\smike\Downloads\Telegram Desktop\ChatExport_2026-01-24 (1)\result.json"
    
    if not Path(json_path).exists():
        print(f"❌ Файл не найден: {json_path}")
        sys.exit(1)
    
    test_json_file(json_path)
