import re

# Читаем файл с промптами
with open('src/ai_post_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Извлекаем все SYSTEM_PROMPT
prompts = {}

# Паттерн для поиска промптов
pattern = r'(SYSTEM_PROMPT[_A-Z0-9]*)\s*=\s*"""(.*?)"""'
matches = re.findall(pattern, content, re.DOTALL)

for name, prompt_text in matches:
    prompts[name] = prompt_text

output = []
output.append("="*80)
output.append("АНАЛИЗ ВСЕХ 6 СИСТЕМНЫХ ПРОМПТОВ")
output.append("="*80)
output.append("")

# Ключевые слова, указывающие на фокус на слоте
slot_focus_keywords = [
    r'слот[аеы]?\s+\{slot\}',
    r'в\s+\{slot\}',
    r'название\s+слота',
    r'слот[а-я]*\s+как',
    r'слот[а-я]*\s+должен',
    r'вокруг\s+слота',
    r'про\s+слот',
    r'о\s+слоте',
    r'атмосфер[а-я]*\s+слота',
    r'тематик[а-я]*\s+слота',
]

for i, (prompt_name, prompt_text) in enumerate(sorted(prompts.items()), 1):
    output.append(f"\n{'='*80}")
    output.append(f"ПРОМПТ #{i}: {prompt_name}")
    output.append(f"{'='*80}")
    
    # Ищем упоминания слота
    slot_mentions = []
    for keyword_pattern in slot_focus_keywords:
        matches = re.finditer(keyword_pattern, prompt_text, re.IGNORECASE)
        for match in matches:
            # Находим контекст (строку, где это упоминание)
            start = prompt_text.rfind('\n', 0, match.start()) + 1
            end = prompt_text.find('\n', match.end())
            if end == -1:
                end = len(prompt_text)
            context_line = prompt_text[start:end].strip()
            if context_line and context_line not in slot_mentions:
                slot_mentions.append(context_line)
    
    if slot_mentions:
        output.append(f"\n⚠️ ФОКУС НА СЛОТЕ ОБНАРУЖЕН ({len(slot_mentions)} упоминаний):")
        output.append("")
        for mention in slot_mentions[:10]:  # Первые 10
            output.append(f"  • {mention[:150]}")
    else:
        output.append(f"\n✅ Слот НЕ в фокусе (минимальные упоминания)")
    
    # Проверяем, есть ли инструкции про разнообразие
    diversity_keywords = [
        'разнообраз',
        'уникальн',
        'различн',
        'не повторя',
        'варьиру',
        'креативн',
    ]
    
    has_diversity = any(kw in prompt_text.lower() for kw in diversity_keywords)
    
    if has_diversity:
        output.append(f"\n✅ Есть инструкции про РАЗНООБРАЗИЕ")
    else:
        output.append(f"\n⚠️ НЕТ инструкций про разнообразие")
    
    # Проверяем, есть ли про эмоции стримера
    emotion_keywords = [
        'эмоци',
        'реакци',
        'чувств',
        'восторг',
        'радост',
        'удивлен',
        'адреналин',
    ]
    
    has_emotions = any(kw in prompt_text.lower() for kw in emotion_keywords)
    
    if has_emotions:
        output.append(f"✅ Есть про ЭМОЦИИ стримера")
    else:
        output.append(f"⚠️ НЕТ про эмоции стримера")

output.append("\n\n" + "="*80)
output.append("ИТОГОВЫЕ РЕКОМЕНДАЦИИ:")
output.append("="*80)
output.append("""
ПРОБЛЕМНЫЕ ПРОМПТЫ (требуют переписывания):
  - Промпты с сильным фокусом на слоте
  - Промпты без инструкций про разнообразие
  - Промпты без упоминания эмоций стримера

ХОРОШИЕ ПРОМПТЫ (оставить как есть):
  - Промпты с минимальным упоминанием слота
  - Промпты с фокусом на стримере и его действиях
  - Промпты с инструкциями про разнообразие
""")

# Сохраняем
with open('prompts_focus_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("OK: Analysis saved to prompts_focus_analysis.txt")
print(f"   Found {len(prompts)} system prompts")
