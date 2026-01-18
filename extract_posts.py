#!/usr/bin/env python3
"""
Скрипт для извлечения всех текстовых постов из Telegram экспорта
"""
import json
import sys

def extract_text_from_entities(text_entities):
    """Извлекает текст из text_entities"""
    if not text_entities:
        return ""
    
    result = []
    for entity in text_entities:
        if isinstance(entity, dict):
            if 'text' in entity:
                result.append(entity['text'])
        elif isinstance(entity, str):
            result.append(entity)
    
    return "".join(result)

def extract_posts_from_telegram_export(input_file, output_file):
    """Извлекает все посты из Telegram экспорта"""
    print(f"Читаю файл: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    messages = data.get('messages', [])
    print(f"Найдено сообщений: {len(messages)}")
    
    posts = []
    
    for msg in messages:
        # Пропускаем служебные сообщения
        if msg.get('type') != 'message':
            continue
        
        # Извлекаем текст
        text = ""
        if 'text' in msg:
            if isinstance(msg['text'], str):
                text = msg['text']
            elif isinstance(msg['text'], list):
                text = extract_text_from_entities(msg.get('text_entities', []))
        
        # Пропускаем пустые
        if not text or len(text.strip()) < 50:
            continue
        
        # Добавляем в список
        posts.append({
            "text": text.strip(),
            "date": msg.get('date', ''),
            "id": msg.get('id', 0)
        })
    
    print(f"Извлечено постов: {len(posts)}")
    
    # Сохраняем в JSON
    output_data = {
        "posts": posts,
        "total": len(posts),
        "source": input_file
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"Сохранено в: {output_file}")
    print(f"\nВсего постов: {len(posts)}")
    print("Готово!")

if __name__ == "__main__":
    input_file = r"c:\Users\smike\Downloads\Telegram Desktop\ChatExport_2026-01-18\result.json"
    output_file = r"c:\Users\smike\OneDrive\Documents\Cursor\BOT CONTENT\boy content boyyy\streamer_posts_bot\data\my_posts.json"
    
    extract_posts_from_telegram_export(input_file, output_file)
    print("\nГотово! Теперь можно использовать в боте.")
