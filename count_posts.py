import json

file_path = r"c:\Users\smike\Downloads\Telegram Desktop\ChatExport_2026-01-21\result.json"

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

total_messages = len(data["messages"])
text_messages = [m for m in data["messages"] if m["type"] == "message" and "text" in m and m["text"]]
video_messages = [m for m in data["messages"] if m.get("media_type") == "video_file"]

print("Статистика выгрузки:")
print(f"   Всего сообщений: {total_messages}")
print(f"   Сообщения с текстом: {len(text_messages)}")
print(f"   Сообщения с видео: {len(video_messages)}")
print(f"   Service сообщения: {len([m for m in data['messages'] if m['type'] == 'service'])}")

# Показываем первые 5 ID для проверки
print(f"\nПервые 5 ID сообщений с текстом:")
for i, msg in enumerate(text_messages[:5]):
    text_preview = str(msg["text"])[:50] if isinstance(msg["text"], str) else "..."
    print(f"   ID {msg['id']}: {text_preview}...")
