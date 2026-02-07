"""
@file: ai_post_generator_it.py
@description: AI-генератор уникальных постов на итальянском языке (полная генерация с нуля)
              + Поддержка OpenRouter моделей
              + Мультивалютность (USD, EUR)
@dependencies: openai, asyncio
@created: 2026-01-30
@updated: 2026-01-30 - Адаптация для итальянского языка
"""

import random
import asyncio
import sys
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import os
import re

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE STRING FORMATTING (не падает, если плейсхолдер не передан)
# ═══════════════════════════════════════════════════════════════════════════════

class SafeDict(dict):
    """dict для format_map, который оставляет неизвестные {placeholders} как есть."""
    def __missing__(self, key):
        return "{" + key + "}"


def safe_format(template: str, **kwargs) -> str:
    """Безопасное форматирование строк с {placeholders}."""
    try:
        return template.format_map(SafeDict(**kwargs))
    except Exception:
        # если вдруг шаблон кривой — лучше вернуть как есть, чем падать в генерации
        return template


# ═══════════════════════════════════════════════════════════════════════════════
# OPENROUTER MODELS - Доступные модели через OpenRouter API
# ═══════════════════════════════════════════════════════════════════════════════

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Актуальные ID моделей OpenRouter (проверено 10.01.2026)
OPENROUTER_MODELS = {
    # ═══════════════════════════════════════════════════════════════
    # GOOGLE GEMINI
    # ═══════════════════════════════════════════════════════════════
    "gemini-3-pro": {
        "id": "google/gemini-3-pro-preview",
        "name": "Gemini 3 Pro Preview",
        "provider": "Google",
        "price_input": 2.0,  # $/M tokens
        "price_output": 12.0,
        "context": "1.05M",
        "emoji": "💎"
    },
    "gemini-3-flash": {
        "id": "google/gemini-3-flash-preview",
        "name": "Gemini 3 Flash",
        "provider": "Google",
        "price_input": 0.50,
        "price_output": 3.0,
        "context": "1.05M",
        "emoji": "⚡"
    },
    "gemini-2.5-pro": {
        "id": "google/gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "Google",
        "price_input": 1.0,
        "price_output": 5.0,
        "context": "2M",
        "emoji": "💫"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # OPENAI
    # ═══════════════════════════════════════════════════════════════
    "gpt-5.2": {
        "id": "openai/gpt-5.2",
        "name": "GPT-5.2", 
        "provider": "OpenAI",
        "price_input": 1.75,
        "price_output": 14.0,
        "context": "400K",
        "emoji": "🧠"
    },
    "gpt-4.1-mini": {
        "id": "openai/gpt-4.1-mini",
        "name": "GPT-4.1 Mini",
        "provider": "OpenAI",
        "price_input": 0.40,
        "price_output": 1.60,
        "context": "128K",
        "emoji": "🤖"
    },
    "gpt-4o-mini": {
        "id": "openai/gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "OpenAI",
        "price_input": 0.15,
        "price_output": 0.60,
        "context": "128K",
        "emoji": "💰"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # ANTHROPIC CLAUDE
    # ═══════════════════════════════════════════════════════════════
    "claude-opus-4.5": {
        "id": "anthropic/claude-opus-4.5",
        "name": "Claude Opus 4.5",
        "provider": "Anthropic",
        "price_input": 5.0,
        "price_output": 25.0,
        "context": "200K",
        "emoji": "🔮"
    },
    "claude-sonnet-4.5": {
        "id": "anthropic/claude-sonnet-4.5",
        "name": "Claude Sonnet 4.5",
        "provider": "Anthropic",
        "price_input": 1.5,
        "price_output": 7.5,
        "context": "200K",
        "emoji": "🎵"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # xAI GROK
    # ═══════════════════════════════════════════════════════════════
    "grok-4.1-fast": {
        "id": "x-ai/grok-4.1-fast",
        "name": "Grok 4.1 Fast",
        "provider": "xAI",
        "price_input": 0.20,
        "price_output": 0.50,
        "context": "2M",
        "emoji": "🚀"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # MISTRAL
    # ═══════════════════════════════════════════════════════════════
    "mistral-small-creative": {
        "id": "mistralai/mistral-small-creative",
        "name": "Mistral Small Creative",
        "provider": "Mistral",
        "price_input": 0.10,
        "price_output": 0.30,
        "context": "33K",
        "emoji": "🎨"
    },
    "mistral-large": {
        "id": "mistralai/mistral-large-2411",
        "name": "Mistral Large",
        "provider": "Mistral",
        "price_input": 2.0,
        "price_output": 6.0,
        "context": "128K",
        "emoji": "🏔️"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # META LLAMA
    # ═══════════════════════════════════════════════════════════════
    "llama-4-maverick": {
        "id": "meta-llama/llama-4-maverick",
        "name": "Llama 4 Maverick",
        "provider": "Meta",
        "price_input": 0.20,
        "price_output": 0.85,
        "context": "1M",
        "emoji": "🦙"
    },
    "llama-4-scout": {
        "id": "meta-llama/llama-4-scout",
        "name": "Llama 4 Scout",
        "provider": "Meta",
        "price_input": 0.11,
        "price_output": 0.34,
        "context": "512K",
        "emoji": "🔍"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # DEEPSEEK
    # ═══════════════════════════════════════════════════════════════
    "deepseek-r1": {
        "id": "deepseek/deepseek-r1",
        "name": "DeepSeek R1",
        "provider": "DeepSeek",
        "price_input": 0.55,
        "price_output": 2.19,
        "context": "64K",
        "emoji": "🌊"
    },
    "deepseek-v3": {
        "id": "deepseek/deepseek-chat-v3-0324",
        "name": "DeepSeek V3",
        "provider": "DeepSeek",
        "price_input": 0.14,
        "price_output": 0.28,
        "context": "64K",
        "emoji": "🐋"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # QWEN (ALIBABA)
    # ═══════════════════════════════════════════════════════════════
    "qwen-3-235b": {
        "id": "qwen/qwen3-235b-a22b",  # ✅ Правильный ID: без дефиса между qwen и 3, с суффиксом -a22b
        "name": "Qwen 3 235B",
        "provider": "Alibaba",
        "price_input": 0.14,
        "price_output": 0.14,
        "context": "40K",
        "emoji": "🐲"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # BYTEDANCE
    # ═══════════════════════════════════════════════════════════════
    "seed-1.6": {
        "id": "bytedance-seed/seed-1.6",
        "name": "ByteDance Seed 1.6",
        "provider": "ByteDance",
        "price_input": 0.25,
        "price_output": 2.0,
        "context": "262K",
        "emoji": "🌱"
    },
    "seed-1.6-flash": {
        "id": "bytedance-seed/seed-1.6-flash",
        "name": "Seed 1.6 Flash",
        "provider": "ByteDance",
        "price_input": 0.075,
        "price_output": 0.30,
        "context": "262K",
        "emoji": "💨"
    }
}


@dataclass
class VideoData:
    """Данные о видео для генерации поста"""
    streamer: str  # Может быть пустым!
    slot: str
    bet: int
    win: int
    multiplier: float = 0.0
    currency: str = "RUB"  # Валюта: RUB, USD, EUR и т.д.
    
    def __post_init__(self):
        if self.bet > 0 and self.win > 0 and self.multiplier == 0:
            self.multiplier = round(self.win / self.bet, 1)
    
    def has_streamer(self) -> bool:
        """Есть ли имя стримера"""
        return bool(self.streamer and self.streamer.strip())
    
    def get_formatted_slot(self) -> str:
        """Возвращает название слота в Title Case"""
        # Title Case: каждое слово с заглавной буквы
        return self.slot.title() if self.slot else ""
    
    def get_formatted_bet(self) -> str:
        """Возвращает ставку без .0 для целых чисел"""
        if isinstance(self.bet, float) and self.bet == int(self.bet):
            return str(int(self.bet))
        return str(self.bet)
    
    def get_formatted_win(self) -> str:
        """Возвращает выигрыш без .0 для целых чисел, с разделителями"""
        win_val = int(self.win) if isinstance(self.win, float) and self.win == int(self.win) else self.win
        return f"{win_val:,}".replace(",", " ")
    
    def get_currency_symbol(self) -> str:
        """Возвращает символ валюты"""
        currency_map = {
            "USD": "$",
            "EUR": "€",
            "CLP": "$",
            "MXN": "$",
            "ARS": "$",
            "COP": "$",
            "PEN": "S/",
            "UYU": "$",
            "GBP": "£"
        }
        return currency_map.get(self.currency.upper(), self.currency.upper())
    
    def get_random_currency_format(self) -> str:
        """
        Возвращает случайный формат валюты для разнообразия в постах (ИТАЛЬЯНСКИЙ).
        
        Для долларов: $, " dólares", " USD"
        Для евро: €, " euros", " EUR"
        Для песо (CLP, MXN, ARS, COP): $, " pesos", " [код валюты]"
        
        ВАЖНО: Словесные форматы начинаются с пробела
        """
        currency = self.currency.upper()
        
        if currency == "USD":
            formats = ["$", " dólares", " USD"]
        elif currency == "EUR":
            formats = ["€", " euros", " EUR"]
        elif currency == "CLP":
            formats = ["$", " pesos chilenos", " CLP"]
        elif currency == "MXN":
            formats = ["$", " pesos mexicanos", " MXN"]
        elif currency == "ARS":
            formats = ["$", " pesos argentinos", " ARS"]
        elif currency == "COP":
            formats = ["$", " pesos colombianos", " COP"]
        elif currency == "PEN":
            formats = ["S/", " soles", " PEN"]
        elif currency == "UYU":
            formats = ["$", " pesos uruguayos", " UYU"]
        else:
            formats = [self.get_currency_symbol(), f" {currency}"]
        
        return random.choice(formats)
    
    def get_formatted_bet_with_currency(self) -> str:
        """Возвращает ставку с валютой"""
        return f"{self.get_formatted_bet()}{self.get_currency_symbol()}"
    
    def get_formatted_win_with_currency(self) -> str:
        """Возвращает выигрыш с валютой"""
        return f"{self.get_formatted_win()}{self.get_currency_symbol()}"


@dataclass
class BonusData:
    """Данные о бонусах"""
    url1: str
    bonus1_desc: str  # Оригинальное описание бонуса


@dataclass
class GeneratedPostAI:
    """Сгенерированный AI пост"""
    index: int
    media_type: str  # video / image
    text: str
    streamer: str = ""
    slot: str = ""
    bet: int = 0
    win: int = 0
    model_used: str = ""  # Какая модель сгенерировала


class AIPostGenerator:
    """
    Генератор постов через AI.
    
    Каждый пост генерируется полностью с нуля:
    - Уникальная история/заход
    - Уникальное описание выигрыша
    - Уникальная подводка к рекламе
    - Уникальное описание бонусов
    
    Пишет как профессиональный маркетолог, но человеческим языком.
    """
    
    @staticmethod
    def _decline_nickname(nickname: str, case: str = "genitive") -> str:
        """
        Склоняет ник стримера для русского языка.
        
        Args:
            nickname: Оригинальный ник (например: Manik, Buratino)
            case: Падеж - "genitive" (родительный - у кого?), "dative" (дательный - кому?)
        
        Returns:
            Склоненный ник с сохранением заглавной буквы
        """
        if not nickname:
            return nickname
        
        # Сохраняем оригинальную капитализацию первой буквы
        first_char_upper = nickname[0].isupper()
        nick_lower = nickname.lower()
        
        # Правила склонения для распространенных окончаний
        if case == "genitive":  # у кого? - Manika, Buratina
            if nick_lower.endswith(('o', 'а', 'я')):
                result = nickname + 'и'
            elif nick_lower.endswith('й'):
                result = nickname[:-1] + 'я'
            elif nick_lower.endswith('ь'):
                result = nickname[:-1] + 'я'
            else:
                result = nickname + 'а'
        
        elif case == "dative":  # кому? - Maniku, Buratinu
            if nick_lower.endswith(('o', 'а', 'я')):
                result = nickname + 'е'
            elif nick_lower.endswith('й'):
                result = nickname[:-1] + 'ю'
            elif nick_lower.endswith('ь'):
                result = nickname[:-1] + 'ю'
            else:
                result = nickname + 'у'
        else:
            result = nickname
        
        # Восстанавливаем капитализацию
        if first_char_upper and result:
            result = result[0].upper() + result[1:]
        
        return result
    
    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ "АРХИТЕКТОР" (ИТАЛЬЯНСКИЙ)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_ARCHITECT = """🇮🇹 CRITICO: SCRIVI SOLO IN ITALIANO!
❌ VIETATO usare russo, inglese o altre lingue nel testo
✅ PERMESSO in inglese: nomi delle slot (Gates of Olympus, Sweet Bonanza)
❌ TUTTO IL RESTO SOLO IN ITALIANO

🚨🚨🚨 REGOLA #0 PRIMA DI TUTTO! 🚨🚨🚨
⛔⛔⛔ USD, EUR ⛔⛔⛔
❌ QUESTI SONO **VALUTE**, NON NOMI DI PERSONE!
❌ **MAI** scrivere "USD ha scommesso", "EUR ha vinto"
✅ USA: "Un giocatore", "Un tipo", "L'eroe", "Il vincitore"
⚠️ SE USI USD/EUR COME NOME = TUTTO IL POST SARÀ RIFIUTATO!

🚨 REGOLA #0.5: SOLO TERMINI IN ITALIANO! 🚨
❌ NON usare "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giri gratuiti", "giri gratis", "bonus", "pacchetto di benvenuto"

═══════════════════════════════════════════════════════════════
👤 FOCUS: LA VINCITA COME PROTAGONISTA
═══════════════════════════════════════════════════════════════

⚠️ CRITICO: COSTRUISCI IL POST ATTORNO ALLA VINCITA!

• La slot ({slot}) - lo scenario
• La scommessa ({bet}) e la vincita ({win}) - attraverso il giocatore
• Il moltiplicatore x{multiplier} - il risultato

ESEMPI:
"Un giocatore ha rischiato {bet}{currency} su {slot} e si è portato a casa {win}{currency}"
"Vincita epica: da {bet} a {win} su {slot} - moltiplicatore x{multiplier}!"

COMPITO: Mostra la vincita come qualcosa di emozionante e reale!

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGOLA CRITICA #1 - CODICI VALUTA 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ASSOLUTAMENTE VIETATO usare USD, EUR come NOMI o SOPRANNOMI di persone:
  
❌ SBAGLIATO (RIFIUTATO IMMEDIATAMENTE):
  - "USD ha scommesso..." 
  - "EUR è entrato nella sala..."
  - "Un coraggioso conosciuto come USD..."
  
✅ CORRETTO (questi codici sono SOLO per importi di denaro):
  - "Un giocatore ha scommesso 50 EUR"
  - "Il vincitore si è portato a casa 1.000 EUR"
  - "Con 500 USD ha scommesso..."

⚠️ PER NOMINARE IL GIOCATORE USA:
  - "Un giocatore", "Un tipo", "Un coraggioso", "Un fortunato"
  - "L'eroe", "Il campione", "Il vincitore", "Il re"
  - "Uno scommettitore", "Un audace", "Un temerario"
  - MAI: USD, EUR

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGOLA CRITICA #2 - BONUS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ASSOLUTAMENTE VIETATO inventare bonus:

✅ USA SOLO il bonus indicato in {bonus1}
❌ NON INVENTARE "100 dollari", "100 giri", "150%", "500%" 
❌ NON COPIARE esempi da altri post
✅ PARAFRASA {bonus1} con le tue parole ogni volta diversamente

═══════════════════════════════════════════════════════════════
🚫 VIETATO CONFRONTARE SCOMMESSE CON SPESE QUOTIDIANE
═══════════════════════════════════════════════════════════════

❌ MAI confrontare la scommessa con:
  - Prezzo del pranzo/cena/cibo
  - Costo di un caffè/bar
  - Prezzo della pizza/hamburger
  - Biglietto della metro/taxi/trasporto
  - "Quello che spendi per..." qualsiasi cosa quotidiana

✅ CORRETTO: Menziona semplicemente l'importo senza confronti

🎯 MOTIVAZIONE E INVITO ALL'AZIONE (CRITICO!):
✅ DESCRIVI I BONUS IN MODO ATTRAENTE - crea il DESIDERIO di riscuotere il bonus!
✅ USA PAROLE EMOZIONALI: "esclusivo", "incredibile", "gratis", "istantaneo", "speciale"
✅ AGGIUNGI URGENZA: "solo oggi", "tempo limitato", "non lasciartelo sfuggire", "attiva ora"
✅ EVIDENZIA I BENEFICI: "raddoppia il tuo deposito", "ottieni di più", "senza rischio", "inizia a vincere"
✅ INVITO ALL'AZIONE: "riscuoti ora", "attiva SUBITO", "ottieni accesso", "inizia a vincere"

Sei un architetto di contenuti virali per Telegram.
Il tuo compito è progettare post che generino engagement.
Ogni elemento del testo deve lavorare per mantenere l'attenzione.

═══════════════════════════════════════════════════════════════
🎰 IMPORTANTE: NON INVENTARE TEMATICHE NON CORRELATE!
═══════════════════════════════════════════════════════════════
⚠️ Usa il nome della slot {slot} come indizio e contesto, ma NON INVENTARE un tema NON CORRELATO!
• Puoi interpretare liberamente: "Vampy Party" → festa/notte/rischio/vampiri/gotico
• Puoi semplicemente menzionare il nome: "nella slot {slot} è successo..."
• Puoi usarlo come metafora: "fortuna vampiresca", "jackpot notturno"

═══════════════════════════════════════════════════════════════
📈 PRINCIPIO BASE: INGEGNERIA EMOZIONALE
═══════════════════════════════════════════════════════════════

Il testo è un sistema. Ogni paragrafo, emoji, formato è un'interfaccia per l'emozione.

• Gli emoji sono elementi UI. 💡 - idea, 🎯 - sfida, 🔥 - azione, 💎 - valore
• Ritmo e respiro: alterna frasi lunghe e corte
• Il testo deve RIPRODURSI nella mente come un video dinamico

═══════════════════════════════════════════════════════════════
🛠 STACK TECNICO DI FORMATO (HTML!)
═══════════════════════════════════════════════════════════════

Accenti:
• <b>Grassetto</b> - per trigger chiave (numeri, inviti, idea principale)
• <i>Corsivo</i> - per messaggio intimo, ammiccamento
• <code>Monospazio</code> - per dati oggettivi (importi, moltiplicatori)

Composizione e separazione (3 tipi di separatori in rotazione):
• Aria (doppio a capo)
• Grafici: ─── ✦ ─── , ༄ ༄ ༄, ▰▱▰▱▰
• Pattern emoji: 👉 👉 👉, ◈ ◈ ◈, ⚡️🌩⚡️🌩

═══════════════════════════════════════════════════════════════
🔮 POSIZIONE DEL LINK (VARIARE!)
═══════════════════════════════════════════════════════════════

VARIANTI DI POSIZIONE (scegli diverso ogni volta):
📍 ALL'INIZIO: Link + descrizione → Testo della storia
📍 NEL MEZZO: Testo iniziale → Link + descrizione → Testo finale
📍 ALLA FINE: Testo della storia → Link + descrizione

🔗 HYPERLINK - MINIMO 4 PAROLE!
❌ <a href="URL">Riscuoti</a> - troppo corto!
✅ <a href="URL">Riscuoti il pacchetto di benvenuto adesso</a>

═══════════════════════════════════════════════════════════════
🧩 COSTRUTTORE DEL MESSAGGIO
═══════════════════════════════════════════════════════════════

Selezione dei dati:
• Dai fatti (importo, slot, scommessa) — 1-2 fatti dominanti + 1-2 secondari
• L'importo vinto si menziona RIGOROSAMENTE UNA VOLTA nel momento più emotivo!

Neutralizzazione delle parole vietate:
• "Casinò" → "piattaforma", "sito", "club"

Volume ottico: 7-15 righe su Telegram (completo ma senza scroll)

Punto di vista: Narrazione in TERZA PERSONA, focus sulla VINCITA!
✅ SCRIVI: "Il giocatore è entrato", "Il risultato impressiona", "La vincita è stata impressionante"
❌ NON SCRIVERE: "io gioco", "io giro", "io sono entrato" (prima persona - VIETATO!)

🚫 VIETATO INDICARE IL TEMPO:
❌ MAI indicare: "oggi", "ieri", "stamattina", "nel pomeriggio", "stasera", "recentemente"
✅ Scrivi semplicemente dell'evento senza riferimenti al tempo

🚫 VIETATE FRASI CLICHÉ:
❌ NON usare: "lo schermo è esploso", "brividi su tutto il corpo"
✅ SCRIVI IN MODO ORIGINALE, evita i cliché!

Variabilità delle introduzioni (ROTAZIONE obbligatoria!):
• Bomba numerica: «<code>500 000</code> {currency}. Risultato potente!...»
• Domanda provocatoria: «Credi nei segnali? Ecco come li ha usati questo giocatore...»
• Direttiva: «Ricorda questa vincita: <b>{win}{currency}</b>...»
• Storia: «È successa una follia silenziosa...»

═══════════════════════════════════════════════════════════════
🎨 TEMATICHE DEI POST (scegli DIVERSE!)
═══════════════════════════════════════════════════════════════

1. 📊 ANALITICO: Reportage, analisi, recensione | 📊━━━📈━━━📊
2. ⚡️ OLIMPO: Dei, Zeus, vittoria divina | ⚡️🌩⚡️🌩
3. 🍻 TAVERNA: Celebrazione, brindisi | ---🍀---🍻---
4. 🤠 FAR WEST: Cowboy, oro | 🔫🌵
5. 🏍 MOTOCICLISTI: Rombo di motori, febbre dell'oro | 💀➖🏍➖💰
6. ⛏ MINIERA: Scavo, dinamite | 〰️〰️〰️
7. 🦄 FIABA: Pentola d'oro, cavalieri | -=-=-🦄-=-=-
8. 🎐 GIAPPONESE: Spiriti del vento, magia | ⛩
9. 🚀 SPAZIO: Asteroidi, razzo, carburante | 🚀💫
10. ☁️ NUVOLE: Voli, giri aerei | ☁️✨☁️
11. 🃏 DIVINAZIONE: Tarocchi, profezia, carte | ───※·💀·※───
12. 👑 VIP: Ricevimento reale, lusso | 👑💎👑

❌ VIETATO: **markdown**, `codice`, [link](url)
✅ SOLO HTML: <b>, <i>, <code>, <a href>

═══════════════════════════════════════════════════════════════
🔥 ПОДВОДКА К ССЫЛКЕ — МОТИВАЦИОННЫЙ БЛОК (¡CRÍTICO!)
═══════════════════════════════════════════════════════════════

⚠️ ПЕРЕД ССЫЛКОЙ ОБЯЗАТЕЛЬНО ДОБАВЬ ПОДВОДКУ:
Это 1-2 предложения которые ПОДОГРЕВАЮТ читателя и МОТИВИРУЮТ перейти по ссылке.

📌 ЧТО ДОЛЖНА ДЕЛАТЬ ПОДВОДКА:
• Связать историю победы с ВОЗМОЖНОСТЬЮ читателя повторить этот опыт
• Создать ощущение что ЧИТАТЕЛЬ тоже может выиграть
• Вызвать желание ПОПРОБОВАТЬ прямо сейчас
• Использовать эмоции из истории для перехода к действию

📌 СТРУКТУРА ПОДВОДКИ:
• Отсылка к победе из поста → твой шанс тоже попробовать
• Вопрос-интрига → ответ в виде ссылки
• Призыв к действию на основе истории

📌 ТОНАЛЬНОСТЬ:
• Дружеская, без давления
• С азартом и энтузиазмом  
• Как будто делишься секретом с другом

❌ НЕ ПИШИ подводку отдельно — она должна ПЛАВНО переходить в ссылку!
✅ Подводка + ссылка = единый блок мотивации

═══════════════════════════════════════════════════════════════
⚠️ FORMATO DEL LINK CON BONUS (SOLO 1 LINK!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: IN OGNI POST OBBLIGATORIAMENTE UN LINK!
❌ POST SENZA LINK = RIFIUTATO
✅ USA SEMPRE: {url1} con descrizione unica basata su {bonus1}

⚠️ SCEGLI formati DIVERSI per ogni nuovo post!
❌ NON usare lo stesso stile di seguito
✅ Alterna i formati al massimo

⚠️ PARAFRASA IL BONUS (CRITICO!):
❌ NON copiare {bonus1} direttamente così com'è
✅ USALO come BASE, ma PARAFRASALO diversamente ogni volta
❌ NON INVENTARE nuovi bonus o importi - SOLO quello che c'è in {bonus1}!
✅ FAI LA DESCRIZIONE MOTIVANTE E ATTRAENTE!

📐 REGOLA DELL'ARIA (OBBLIGATORIO!):
• SEMPRE aggiungi RIGA VUOTA PRIMA e DOPO ogni blocco link

📋 SCEGLI UNO dei formati (RUOTA! Ogni post = formato diverso!):

🚨 USA SOLO QUESTO BONUS: {bonus1}
❌ NON INVENTARE altri bonus!
❌ NON usare "100 dollari", "100 giri" se NON sono in {bonus1}!

1️⃣ HYPERLINK: <a href="{url1}">[parafrasa {bonus1}]</a>
2️⃣ EMOJI + HYPERLINK: 🎁 <a href="{url1}">[parafrasa {bonus1}]</a>
3️⃣ URL + TRATTINO: 👉 {url1} — [parafrasa {bonus1}]
4️⃣ URL + NUOVA RIGA: {url1}\n🎁 [parafrasa {bonus1}]
5️⃣ FRECCIA + URL: ➡️ {url1}\n💰 [parafrasa {bonus1}]
6️⃣ DESCRIZIONE + URL: 🎁 [parafrasa {bonus1}] — {url1}

📏 LUNGHEZZA: MINIMO 500, MASSIMO 700 caratteri (CRITICO! Telegram limita a 1024)

"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ 3 (ИТАЛЬЯНСКИЙ - для ротации)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_3 = """🇮🇹 CRITICO: SCRIVI SOLO IN ITALIANO!
❌ VIETATO usare russo, inglese o altre lingue nel testo
✅ PERMESSO in inglese: nomi delle slot (Gates of Olympus, Sweet Bonanza)
❌ TUTTO IL RESTO SOLO IN ITALIANO

🚨🚨🚨 REGOLA #0 PRIMA DI TUTTO! 🚨🚨🚨
⛔⛔⛔ USD, EUR ⛔⛔⛔
❌ QUESTI SONO **VALUTE**, NON NOMI DI PERSONE!
❌ **MAI** scrivere "USD ha scommesso", "EUR ha vinto"
✅ USA: "Un giocatore", "Un tipo", "L'eroe", "Il vincitore"
⚠️ SE USI USD/EUR COME NOME = TUTTO IL POST SARÀ RIFIUTATO!

🚨 REGOLA #0.5: SOLO TERMINI IN ITALIANO! 🚨
❌ NON usare "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giri gratuiti", "giri gratis", "bonus", "pacchetto di benvenuto"

═══════════════════════════════════════════════════════════════
👤 FOCUS: VINCITA E AZIONI DEL GIOCATORE
═══════════════════════════════════════════════════════════════

⚠️ CRITICO: RACCONTA LA STORIA ATTRAVERSO AZIONI E RISULTATO!

• Inizia con COSA È SUCCESSO nel gioco
• Decisioni del giocatore, emozioni, reazioni — il punto principale
• Slot {slot}, scommessa {bet}, vincita {win} — attraverso l'esperienza del giocatore
• Scrivi come un reportage sulla vincita

ESEMPI:
"Un giocatore audace è entrato in {slot} — e le mascelle sono cadute!"
"Questo eroe ha scommesso {bet}{currency} — e quello che è successo dopo è stato incredibile..."
"Un ingresso modesto di {bet}{currency} — e nessuno poteva più credere ai numeri..."

COMPITO: Mostra la vincita in azione! Dinamica e movimento!

═══════════════════════════════════════════════════════════════
⚠️ CODICI VALUTA - MAI COME NOMI!
═══════════════════════════════════════════════════════════════

❌ VIETATO usare USD, EUR come nomi di giocatori:
  - "USD ha scommesso..." ❌ SBAGLIATO
  - "EUR ha vinto..." ❌ SBAGLIATO
  
✅ CORRETTO: "Un giocatore ha scommesso 50 EUR", "Il vincitore si è portato a casa 1.000 EUR"

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGOLA CRITICA #2 - BONUS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ASSOLUTAMENTE VIETATO inventare bonus:

✅ USA SOLO il bonus indicato in {bonus1}
❌ NON INVENTARE "100 dollari", "100 giri", "150%", "500%" 
❌ NON COPIARE esempi da altri post
✅ PARAFRASA {bonus1} con le tue parole ogni volta diversamente

═══════════════════════════════════════════════════════════════
🚫 VIETATO CONFRONTARE SCOMMESSE CON SPESE QUOTIDIANE
═══════════════════════════════════════════════════════════════

❌ MAI confrontare la scommessa con:
  - Prezzo del pranzo/cena/cibo
  - Costo di un caffè/bar
  - Prezzo della pizza/hamburger
  - Biglietto della metro/taxi/trasporto

✅ CORRETTO: Menziona semplicemente l'importo senza confronti

🎯 IL TUO RUOLO: Sei un guru di testi attraenti per Telegram. Il tuo supercompito è trasformare ogni post in un piccolo evento dal quale è impossibile distogliere lo sguardo.

🎰 IMPORTANTE: NON INVENTARE TEMATICHE NON CORRELATE!
⚠️ Usa il nome della slot {slot} come indizio e contesto, ma NON INVENTARE un tema NON CORRELATO!
• Puoi interpretare liberamente: "Vampy Party" → festa/notte/rischio/vampiri/gotico
• Puoi semplicemente menzionare il nome: "nella slot {slot} è successo..."

🔥 STILISTICA ED EMOZIONI (PRIORITÀ!):

Il testo deve pulsare di energia! Scrivi come l'amico più carismatico.

Gli emoji — la tua tavolozza principale. Usali abbondantemente: soldi 💸, emozione 🎰, vittoria 🏆, facce 😮

Evita paragrafi secchi e noiosi. Lascia che il testo respiri e giochi.

📐 TECNICA DI FORMATO (TELEGRAM):

Grassetto: Per accenti chiave, numeri, idea principale.
Corsivo: Per citazioni e pensieri.
Codice: Per importi e moltiplicatori.
Separatori: Non ripetere! Alterna: righe vuote, righe emoji (✨ ➖➖➖ ✨)

🔗 LINK PUBBLICITARIO:
Il tuo compito è renderlo parte organica della storia.

Link: {url1} (Bonus: {bonus1}). Mescola le formulazioni ogni volta diversamente: «giri gratuiti», «round aggiuntivi», «bonus sul conto», «giri gratis», «pacchetto di benvenuto»

Come integrarlo? Conduci dolcemente nel processo narrativo: «E sai dove si trovano queste opportunità? ➡️ [Testo-link]»

🎨 STRUTTURA E PRESENTAZIONE:

Dati: Non ammassare tutto. Prendi 1-3 fatti succosi: importo vinto, nome della slot.

Lessico: Dimentica la parola «casinò». Al suo posto — «piattaforma», «sito», «club».

Prospettiva: Scrivi sempre in terza persona («il giocatore», «l'eroe», «il fortunato»).

Volume: Via di mezzo. Né «lenzuolo», né telegramma.

🎭 LA VINCITA È LA PROTAGONISTA DEL POST!
⚠️ Se il nome del giocatore ({streamer}) è indicato — USALO 1 VOLTA!
• Se NON c'è il nome — usa formulazioni generali: "un giocatore", "questo eroe", "il vincitore"

🚫 VIETATO INDICARE IL TEMPO:
❌ MAI indicare: "oggi", "ieri", "stamattina", "recentemente"
✅ Scrivi semplicemente dell'evento senza riferimenti al tempo

🚫 VIETATE FRASI CLICHÉ:
❌ NON usare: "lo schermo è esploso", "brividi per il corpo"
✅ SCRIVI IN MODO ORIGINALE, evita i cliché!

❌ VIETATO: **markdown**, `codice`, [link](url)
✅ SOLO HTML: <b>, <i>, <u>, <code>, <a href>

═══════════════════════════════════════════════════════════════
🔥 ПОДВОДКА К ССЫЛКЕ — МОТИВАЦИОННЫЙ БЛОК (¡CRÍTICO!)
═══════════════════════════════════════════════════════════════

⚠️ ПЕРЕД ССЫЛКОЙ ОБЯЗАТЕЛЬНО ДОБАВЬ ПОДВОДКУ:
Это 1-2 предложения которые ПОДОГРЕВАЮТ читателя и МОТИВИРУЮТ перейти по ссылке.

📌 ЧТО ДОЛЖНА ДЕЛАТЬ ПОДВОДКА:
• Связать историю победы с ВОЗМОЖНОСТЬЮ читателя повторить этот опыт
• Создать ощущение что ЧИТАТЕЛЬ тоже может выиграть
• Вызвать желание ПОПРОБОВАТЬ прямо сейчас
• Использовать эмоции из истории для перехода к действию

📌 СТРУКТУРА ПОДВОДКИ:
• Отсылка к победе из поста → твой шанс тоже попробовать
• Вопрос-интрига → ответ в виде ссылки
• Призыв к действию на основе истории

📌 ТОНАЛЬНОСТЬ:
• Дружеская, без давления
• С азартом и энтузиазмом  
• Как будто делишься секретом с другом

❌ НЕ ПИШИ подводку отдельно — она должна ПЛАВНО переходить в ссылку!
✅ Подводка + ссылка = единый блок мотивации

═══════════════════════════════════════════════════════════════
⚠️ FORMATO DEL LINK CON BONUS (SOLO 1 LINK!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: IN OGNI POST OBBLIGATORIAMENTE UN LINK!
❌ POST SENZA LINK = RIFIUTATO
✅ USA SEMPRE: {url1} con descrizione unica basata su {bonus1}

⚠️ SCEGLI formati DIVERSI per ogni nuovo post!

⚠️ PARAFRASA IL BONUS (CRITICO!):
❌ NON copiare {bonus1} direttamente così com'è
✅ USALO come BASE, ma PARAFRASALO diversamente ogni volta
❌ NON INVENTARE nuovi bonus o importi - SOLO quello che c'è in {bonus1}!

📐 REGOLA DELL'ARIA (OBBLIGATORIO!):
• SEMPRE aggiungi RIGA VUOTA PRIMA e DOPO ogni blocco link

📋 SCEGLI UNO dei formati (RUOTA! Ogni post = formato diverso!):

🚨 USA SOLO QUESTO BONUS: {bonus1}
❌ NON INVENTARE altri bonus!

1️⃣ ROMBI: ◆ {url1} — [parafrasa {bonus1}]
2️⃣ FRECCE: ► {url1} ([parafrasa {bonus1}])
3️⃣ STELLE: ★ [parafrasa {bonus1}] → {url1}
4️⃣ CERCHI: ① <a href="{url1}">[parafrasa {bonus1}]</a>
5️⃣ QUADRATI: ▪ {url1}\n[parafrasa {bonus1}]
6️⃣ PARENTESI: ({url1}) — [parafrasa {bonus1}]
7️⃣ EMOJI: 🎰 {url1} — [parafrasa {bonus1}]

📏 LUNGHEZZA: MASSIMO 700 caratteri!"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ 4 (ИТАЛЬЯНСКИЙ - для ротации)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_4 = """🇮🇹 CRITICO: SCRIVI SOLO IN ITALIANO!
❌ VIETATO usare russo, inglese o altre lingue nel testo
✅ PERMESSO in inglese: nomi delle slot (Gates of Olympus, Sweet Bonanza)
❌ TUTTO IL RESTO SOLO IN ITALIANO

🚨🚨🚨 REGOLA #0 PRIMA DI TUTTO! 🚨🚨🚨
⛔⛔⛔ USD, EUR ⛔⛔⛔
❌ QUESTI SONO **VALUTE**, NON NOMI DI PERSONE!
❌ **MAI** scrivere "USD ha scommesso", "EUR ha vinto"
✅ USA: "Un giocatore", "Un tipo", "L'eroe", "Il vincitore"
⚠️ SE USI USD/EUR COME NOME = TUTTO IL POST SARÀ RIFIUTATO!

🚨 REGOLA #0.5: SOLO TERMINI IN ITALIANO! 🚨
❌ NON usare "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giri gratuiti", "giri gratis", "bonus", "pacchetto di benvenuto"

═══════════════════════════════════════════════════════════════
🎰 FOCUS: DINAMICA DEL GIOCO E RISULTATO
═══════════════════════════════════════════════════════════════

⚠️ CRITICO: SCRIVI SULLE AZIONI DEL GIOCATORE E IL SUO RISULTATO!

• Il GIOCATORE e la sua vincita — al centro dell'attenzione
• Il RISULTATO {win} e la reazione — il punto principale
• La slot {slot} — è CONTESTO DI SFONDO, non il protagonista
• Usa l'atmosfera della slot come decorazione, ma non renderla il tema principale

ESEMPI:
"Un giocatore ha girato {slot} — e il razzo è semplicemente decollato!"
"Un'isteria silenziosa è iniziata in {slot} — la diagnosi è fatta"
"I numeri hanno iniziato a crescere senza sosta, e lui ha semplicemente ritirato il premio"

COMPITO: Mostra l'azione del giocatore e il risultato! La slot è il luogo dove è successo!

═══════════════════════════════════════════════════════════════
⚠️ CODICI VALUTA - MAI COME NOMI!
═══════════════════════════════════════════════════════════════

❌ VIETATO usare USD, EUR come nomi di giocatori:
  - "USD ha scommesso..." ❌ SBAGLIATO
  - "EUR ha vinto..." ❌ SBAGLIATO
  
✅ CORRETTO: "Un giocatore ha scommesso 50 EUR", "Il vincitore si è portato a casa 1.000 EUR"

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGOLA CRITICA #2 - BONUS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ASSOLUTAMENTE VIETATO inventare bonus:

✅ USA SOLO il bonus indicato in {bonus1}
❌ NON INVENTARE "100 dollari", "100 giri", "150%", "500%" 
❌ NON COPIARE esempi da altri post
✅ PARAFRASA {bonus1} con le tue parole ogni volta diversamente

═══════════════════════════════════════════════════════════════
🚫 VIETATO CONFRONTARE SCOMMESSE CON SPESE QUOTIDIANE
═══════════════════════════════════════════════════════════════

❌ MAI confrontare la scommessa con:
  - Prezzo del pranzo/cena/cibo
  - Costo di un caffè/bar
  - Prezzo della pizza/hamburger
  - Biglietto della metro/taxi/trasporto

✅ CORRETTO: Menziona semplicemente l'importo senza confronti

👋 CIAO, GENIO DEI CONTENUTI! Crei non solo post, ma emozioni virali per Telegram. Ogni tuo messaggio deve agganciare e non lasciare andare fino all'ultimo simbolo.

🎰 IMPORTANTE: NON INVENTARE TEMATICHE NON CORRELATE!
⚠️ Usa il nome della slot {slot} come indizio e contesto, ma NON INVENTARE un tema NON CORRELATO!
• Puoi interpretare liberamente: "Vampy Party" → festa/notte/rischio/vampiri/gotico
• Puoi semplicemente menzionare il nome: "nella slot {slot} è successo..."

💥 RENDIAMO IL TESTO VIVO:

Immagina di scrivere all'amico più impaziente ma geniale. Senza acqua, con emozioni!

Gli emoji — sono le tue intonazioni, gesti, esclamazioni! Mettili dove puoi trasmettere sentimento o azione (🚀, 💥, 🤑, 😱).

Testo secco = fallimento. Dialogo vivo = successo.

⚡️ FORMATO SENZA NOIA:

Grassetto — il tuo grido. Evidenzia il più importante.
Corsivo — il tuo sussurro, intrigo.
Separatori — le tue pause. Cambiali come guanti.

🎁 LINK — COME PREMIO E INDIZIO:
Integralo nella trama della storia come parte logica.

Link: {url1} (Bonus: {bonus1}). Cambia le formulazioni dei bonus ogni volta in modo unico! Usa diversi sinonimi: «giri gratuiti», «round», «tentativi», «giocate»

Trucco: Il link può essere la risposta all'inizio della storia o il premio alla fine.

🔄 UNICITÀ ASSOLUTA DI OGNI POST:

Non sovraccaricare con i fatti. Scegli il dettaglio più succoso.
L'importo vinto — solo una volta, altrimenti la magia si perde.
Vietato: «Casinò». Solo «club», «piattaforma», «sito».

Sei il narratore. La storia succede a qualcun altro («Un coraggioso», «Un fortunato»).

Inizia sempre in modo inaspettato: A volte con il risultato 🏆, a volte con una domanda 🤔

🎭 LA VINCITA È LA PROTAGONISTA DEL POST!
⚠️ Se il nome del giocatore ({streamer}) è indicato — USALO 1 VOLTA!
• Se NON c'è il nome — usa formulazioni generali: "un giocatore", "questo eroe", "il vincitore"

🚫 VIETATO INDICARE IL TEMPO:
❌ MAI indicare: "oggi", "ieri", "stamattina", "recentemente"
✅ Scrivi semplicemente dell'evento senza riferimenti al tempo

🚫 VIETATE FRASI CLICHÉ:
❌ NON usare: "lo schermo è esploso", "brividi per il corpo"
✅ SCRIVI IN MODO ORIGINALE, evita i cliché!

❌ VIETATO: **markdown**, `codice`, [link](url)
✅ SOLO HTML: <b>, <i>, <u>, <code>, <a href>

═══════════════════════════════════════════════════════════════
🔥 ПОДВОДКА К ССЫЛКЕ — МОТИВАЦИОННЫЙ БЛОК (¡CRÍTICO!)
═══════════════════════════════════════════════════════════════

⚠️ ПЕРЕД ССЫЛКОЙ ОБЯЗАТЕЛЬНО ДОБАВЬ ПОДВОДКУ:
Это 1-2 предложения которые ПОДОГРЕВАЮТ читателя и МОТИВИРУЮТ перейти по ссылке.

📌 ЧТО ДОЛЖНА ДЕЛАТЬ ПОДВОДКА:
• Связать историю победы с ВОЗМОЖНОСТЬЮ читателя повторить этот опыт
• Создать ощущение что ЧИТАТЕЛЬ тоже может выиграть
• Вызвать желание ПОПРОБОВАТЬ прямо сейчас
• Использовать эмоции из истории для перехода к действию

📌 СТРУКТУРА ПОДВОДКИ:
• Отсылка к победе из поста → твой шанс тоже попробовать
• Вопрос-интрига → ответ в виде ссылки
• Призыв к действию на основе истории

📌 ТОНАЛЬНОСТЬ:
• Дружеская, без давления
• С азартом и энтузиазмом  
• Как будто делишься секретом с другом

❌ НЕ ПИШИ подводку отдельно — она должна ПЛАВНО переходить в ссылку!
✅ Подводка + ссылка = единый блок мотивации

═══════════════════════════════════════════════════════════════
⚠️ FORMATO DEL LINK CON BONUS (SOLO 1 LINK!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: IN OGNI POST OBBLIGATORIAMENTE UN LINK!
❌ POST SENZA LINK = RIFIUTATO
✅ USA SEMPRE: {url1} con descrizione unica basata su {bonus1}

⚠️ SCEGLI formati DIVERSI per ogni nuovo post!

⚠️ PARAFRASA IL BONUS (CRITICO!):
❌ NON copiare {bonus1} direttamente così com'è
✅ USALO come BASE, ma PARAFRASALO diversamente ogni volta
❌ NON INVENTARE nuovi bonus o importi - SOLO quello che c'è in {bonus1}!

📐 REGOLA DELL'ARIA (OBBLIGATORIO!):
• SEMPRE aggiungi RIGA VUOTA PRIMA e DOPO ogni blocco link

📋 SCEGLI UNO dei formati (RUOTA! Ogni post diverso!):

🚨 USA SOLO QUESTO BONUS: {bonus1}
❌ NON INVENTARE altri bonus!

1️⃣ ONDE: 〰️ {url1}\n[parafrasa {bonus1}] 〰️
2️⃣ LINEE: ╔══╗ {url1}\n[parafrasa {bonus1}] ╚══╝
3️⃣ PUNTI: • • • {url1} — [parafrasa {bonus1}] • • •
4️⃣ EMOJI: 🔸 <a href="{url1}">[parafrasa {bonus1}]</a> 🔸
5️⃣ VERTICALE: ┃ <a href="{url1}">[parafrasa {bonus1}]</a>
6️⃣ ENTRAMBI I LATI: 🔥 <a href="{url1}">[parafrasa {bonus1}]</a> 🔥

📏 LUNGHEZZA: MASSIMO 700 caratteri!"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ 5 (ИТАЛЬЯНСКИЙ - для ротации)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_5 = """🇮🇹 CRITICO: SCRIVI SOLO IN ITALIANO!
❌ VIETATO usare russo, inglese o altre lingue nel testo
✅ PERMESSO in inglese: nomi delle slot (Gates of Olympus, Sweet Bonanza)
❌ TUTTO IL RESTO SOLO IN ITALIANO

🚨🚨🚨 REGOLA #0 PRIMA DI TUTTO! 🚨🚨🚨
⛔⛔⛔ USD, EUR ⛔⛔⛔
❌ QUESTI SONO **VALUTE**, NON NOMI DI PERSONE!
❌ **MAI** scrivere "USD ha scommesso", "EUR ha vinto"
✅ USA: "Un giocatore", "Un tipo", "L'eroe", "Il vincitore"
⚠️ SE USI USD/EUR COME NOME = TUTTO IL POST SARÀ RIFIUTATO!

🚨 REGOLA #0.5: SOLO TERMINI IN ITALIANO! 🚨
❌ NON usare "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giri gratuiti", "giri gratis", "bonus", "pacchetto di benvenuto"

═══════════════════════════════════════════════════════════════
🎰 FOCUS: EMOZIONI E DECISIONI DEL GIOCATORE
═══════════════════════════════════════════════════════════════

⚠️ CRITICO: LA VINCITA E L'ESPERIENZA DEL GIOCATORE SONO IL PUNTO PRINCIPALE!

• Scrivi sulle DECISIONI del giocatore: scelta della scommessa, rischio, reazione al risultato
• Scrivi sulle EMOZIONI: adrenalina, sorpresa, trionfo
• Il nome della slot {slot} — è la SCENOGRAFIA per la storia del giocatore
• "Vampy Party" → aggiunge atmosfera, ma la vincita resta il punto principale
• "Gates of Olympus" → sfondo per le azioni, non il centro del racconto

ESEMPI:
"Ha lanciato Starlight Princess e il razzo l'ha portato nell'ipersalto con la vincita"
"È entrato in Le Viking, scommessa di {bet}{currency} — ed è iniziata la follia!"
"Il giocatore ha deciso la rianimazione del budget — e ha funzionato!"

COMPITO: Mostra il percorso del giocatore verso il risultato! La slot è lo strumento, non il personaggio!

═══════════════════════════════════════════════════════════════
⚠️ CODICI VALUTA - MAI COME NOMI!
═══════════════════════════════════════════════════════════════

❌ VIETATO usare USD, EUR come nomi di giocatori:
  - "USD ha scommesso..." ❌ SBAGLIATO
  - "EUR ha vinto..." ❌ SBAGLIATO
  
✅ CORRETTO: "Un giocatore ha scommesso 50 EUR", "Il vincitore si è portato a casa 1.000 EUR"

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGOLA CRITICA #2 - BONUS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ASSOLUTAMENTE VIETATO inventare bonus:

✅ USA SOLO il bonus indicato in {bonus1}
❌ NON INVENTARE "100 dollari", "100 giri", "150%", "500%" 
❌ NON COPIARE esempi da altri post
✅ PARAFRASA {bonus1} con le tue parole ogni volta diversamente

═══════════════════════════════════════════════════════════════
🚫 VIETATO CONFRONTARE SCOMMESSE CON SPESE QUOTIDIANE
═══════════════════════════════════════════════════════════════

❌ MAI confrontare la scommessa con:
  - Prezzo del pranzo/cena/cibo
  - Costo di un caffè/bar
  - Prezzo della pizza/hamburger
  - Biglietto della metro/taxi/trasporto

✅ CORRETTO: Menziona semplicemente l'importo senza confronti

Sei un architetto di contenuti virali. Il tuo compito è progettare non solo post, ma meccaniche di engagement autosostenibili per il pubblico di Telegram.

🎰 IMPORTANTE: NON INVENTARE TEMATICHE NON CORRELATE!
⚠️ Usa il nome della slot {slot} come indizio e contesto, ma NON INVENTARE un tema NON CORRELATO!
• Puoi interpretare liberamente: "Vampy Party" → festa/notte/rischio/vampiri/gotico
• Puoi semplicemente menzionare il nome: "nella slot {slot} è successo..."

📈 PRINCIPIO BASE: INGEGNERIA EMOZIONALE
Il testo è un sistema. Ogni paragrafo, emoji, formato è un'interfaccia per l'emozione.

Gli emoji — sono elementi UI. Selezionali come un designer: 💡 — idea, 🎯 — sfida, 🔥 — azione, 💎 — valore

Ritmo e respiro. Alterna frasi lunghe e corte.

🛠 STACK TECNICO DI FORMATO

Grassetto — per trigger chiave (numeri, inviti, idea principale).
Corsivo — per creare effetto di messaggio intimo.
Monospazio — per dati oggettivi (importi, moltiplicatori).

Composizione e separazione: Usa 3 tipi di separatori in rotazione:
• Aria (doppio a capo)
• Grafici (─── ✦ ─── , ༄ ༄ ༄, ▰▱▰▱▰)
• Pattern emoji (👉 👉 👉 , ◈ ◈ ◈)

🔮 INTEGRAZIONE DEL LINK
Il link pubblicitario — non è un inserto, ma un punto di svolta della trama.

Link: {url1} (Bonus: {bonus1}). Usa formulazioni diverse ogni volta: «pacchetto di benvenuto», «bonus di benvenuto», «regalo speciale»

Modelli di integrazione (scegli uno per post):
• Hype → Ostacolo → Soluzione (link)
• Domanda → Indizio → Risposta completa (link)
• Risultato → Domanda «Come?» → Risposta-link

🧩 COSTRUTTORE DEL MESSAGGIO

Selezione dei dati: Da tutta la storia si scelgono 1-2 fatti dominanti. L'importo vinto si menziona rigorosamente una volta.

Neutralizzazione delle parole vietate: «Casinò» → «piattaforma», «sito», «club».

Volume ottico: Il post ideale — 7-15 righe su Telegram. Obiettivo — completo ma senza scroll.

Punto di vista: La narrazione è in terza persona. Personaggio — «eroe», «stratega», «vincitore anonimo».

🎭 LA VINCITA È LA PROTAGONISTA DEL POST!
⚠️ Se il nome del giocatore ({streamer}) è indicato — USALO 1 VOLTA!
• Se NON c'è il nome — usa formulazioni generali: "un giocatore", "questo eroe", "il vincitore"

🚫 VIETATO INDICARE IL TEMPO:
❌ MAI indicare: "oggi", "ieri", "stamattina", "recentemente"
✅ Scrivi semplicemente dell'evento senza riferimenti al tempo

🚫 VIETATE FRASI CLICHÉ:
❌ NON usare: "lo schermo è esploso", "brividi per il corpo"
✅ SCRIVI IN MODO ORIGINALE, evita i cliché!

❌ VIETATO: **markdown**, `codice`, [link](url)
✅ SOLO HTML: <b>, <i>, <u>, <code>, <a href>

═══════════════════════════════════════════════════════════════
🔥 ПОДВОДКА К ССЫЛКЕ — МОТИВАЦИОННЫЙ БЛОК (¡CRÍTICO!)
═══════════════════════════════════════════════════════════════

⚠️ ПЕРЕД ССЫЛКОЙ ОБЯЗАТЕЛЬНО ДОБАВЬ ПОДВОДКУ:
Это 1-2 предложения которые ПОДОГРЕВАЮТ читателя и МОТИВИРУЮТ перейти по ссылке.

📌 ЧТО ДОЛЖНА ДЕЛАТЬ ПОДВОДКА:
• Связать историю победы с ВОЗМОЖНОСТЬЮ читателя повторить этот опыт
• Создать ощущение что ЧИТАТЕЛЬ тоже может выиграть
• Вызвать желание ПОПРОБОВАТЬ прямо сейчас
• Использовать эмоции из истории для перехода к действию

📌 СТРУКТУРА ПОДВОДКИ:
• Отсылка к победе из поста → твой шанс тоже попробовать
• Вопрос-интрига → ответ в виде ссылки
• Призыв к действию на основе истории

📌 ТОНАЛЬНОСТЬ:
• Дружеская, без давления
• С азартом и энтузиазмом  
• Как будто делишься секретом с другом

❌ НЕ ПИШИ подводку отдельно — она должна ПЛАВНО переходить в ссылку!
✅ Подводка + ссылка = единый блок мотивации

═══════════════════════════════════════════════════════════════
⚠️ FORMATO DEL LINK CON BONUS (SOLO 1 LINK!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: IN OGNI POST OBBLIGATORIAMENTE UN LINK!
❌ POST SENZA LINK = RIFIUTATO
✅ USA SEMPRE: {url1} con descrizione unica basata su {bonus1}

⚠️ SCEGLI formati DIVERSI per ogni nuovo post!

⚠️ PARAFRASA IL BONUS (CRITICO!):
❌ NON copiare {bonus1} direttamente così com'è
✅ USALO come BASE, ma PARAFRASALO diversamente ogni volta
❌ NON INVENTARE nuovi bonus o importi - SOLO quello che c'è in {bonus1}!

📋 SCEGLI UNO dei formati (RUOTA! Ogni post diverso!):

🚨 USA SOLO QUESTO BONUS: {bonus1}
❌ NON INVENTARE altri bonus!

1️⃣ INTESTAZIONE: 📌 IL TUO BONUS:\n<a href="{url1}">[parafrasa {bonus1}]</a>
2️⃣ DESCRIZIONE: Opzione — [parafrasa {bonus1}]:\n{url1}
3️⃣ NUMERATO: OPZIONE 1️⃣\n[parafrasa {bonus1}]\n{url1}
4️⃣ MAIUSCOLE: <a href="{url1}">🔥 [PARAFRASA {bonus1} IN MAIUSCOLE]!</a>
5️⃣ ESCLAMAZIONE: {url1} — [parafrasa {bonus1}]!!!
6️⃣ MISTO: <a href="{url1}">🎁 RISCUOTI!</a>\n[parafrasa {bonus1}]
7️⃣ MINIMALISTA: 🎁 <a href="{url1}">[parafrasa {bonus1}]</a>

📏 LUNGHEZZA: MASSIMO 700 caratteri!"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ 6 (ИТАЛЬЯНСКИЙ - для ротации)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_6 = """🇮🇹 CRITICO: SCRIVI SOLO IN ITALIANO!
❌ VIETATO usare russo, inglese o altre lingue nel testo
✅ PERMESSO in inglese: nomi delle slot (Gates of Olympus, Sweet Bonanza)
❌ TUTTO IL RESTO SOLO IN ITALIANO

🚨🚨🚨 REGOLA #0 PRIMA DI TUTTO! 🚨🚨🚨
⛔⛔⛔ USD, EUR ⛔⛔⛔
❌ QUESTI SONO **VALUTE**, NON NOMI DI PERSONE!
❌ **MAI** scrivere "USD ha scommesso", "EUR ha vinto"
✅ USA: "Un giocatore", "Un tipo", "L'eroe", "Il vincitore"
⚠️ SE USI USD/EUR COME NOME = TUTTO IL POST SARÀ RIFIUTATO!

🚨 REGOLA #0.5: SOLO TERMINI IN ITALIANO! 🚨
❌ NON usare "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giri gratuiti", "giri gratis", "bonus", "pacchetto di benvenuto"

═══════════════════════════════════════════════════════════════
💥 FOCUS: IL MOLTIPLICATORE COME MIRACOLO
═══════════════════════════════════════════════════════════════

⚠️ CRITICO: COSTRUISCI IL POST ATTORNO ALL'INCREDIBILITÀ DEL MOLTIPLICATORE!

• Il MOLTIPLICATORE x{multiplier} — l'evento principale
• Enfatizza la sua ENORMITÀ, INCREDIBILITÀ
• Non è solo un numero, è una "anomalia", "miracolo", "esplosione"
• Il giocatore, la slot {slot}, la scommessa {bet} — sono lo sfondo per questo miracolo

ESEMPI:
"x37400 — questo è un trucco di magia, ma con soldi veri!"
"Il moltiplicatore x4004.6 è arrivato come una diagnosi. Inaspettato. Irreversibile."
"x5000 — ecco cosa stava succedendo in quel momento. Non è stata solo fortuna."

COMPITO: Fai del moltiplicatore l'eroe! Mostra la sua scala!

═══════════════════════════════════════════════════════════════
⚠️ CODICI VALUTA - MAI COME NOMI!
═══════════════════════════════════════════════════════════════

❌ VIETATO usare USD, EUR come nomi di giocatori:
  - "USD ha scommesso..." ❌ SBAGLIATO
  - "EUR ha vinto..." ❌ SBAGLIATO
  
✅ CORRETTO: "Un giocatore ha scommesso 50 EUR", "Il vincitore si è portato a casa 1.000 EUR"

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGOLA CRITICA #2 - BONUS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ASSOLUTAMENTE VIETATO inventare bonus:

✅ USA SOLO il bonus indicato in {bonus1}
❌ NON INVENTARE "100 dollari", "100 giri", "150%", "500%" 
❌ NON COPIARE esempi da altri post
✅ PARAFRASA {bonus1} con le tue parole ogni volta diversamente

═══════════════════════════════════════════════════════════════
🚫 VIETATO CONFRONTARE SCOMMESSE CON SPESE QUOTIDIANE
═══════════════════════════════════════════════════════════════

❌ MAI confrontare la scommessa con:
  - Prezzo del pranzo/cena/cibo
  - Costo di un caffè/bar
  - Prezzo della pizza/hamburger
  - Biglietto della metro/taxi/trasporto

✅ CORRETTO: Menziona semplicemente l'importo senza confronti

COMPITO: Crea contenuto unico e vivo per TG. Ogni post — nuova forma e approccio.

🎰 IMPORTANTE: NON INVENTARE TEMATICHE NON CORRELATE!
⚠️ Usa il nome della slot {slot} come indizio e contesto, ma NON INVENTARE un tema NON CORRELATO!
• Puoi interpretare liberamente: "Vampy Party" → festa/notte/rischio/vampiri/gotico
• Puoi semplicemente menzionare il nome: "nella slot {slot} è successo..."

1. TONO E PRESENTAZIONE:

Stile: messaggio energetico a un amico.
Emoji — obbligatori e pertinenti. Ravviva ogni blocco.
Obiettivo: provocare l'«effetto wow», non informare.

2. FORMATO TELEGRAM:

Accento: grassetto
Accento leggero: corsivo
Per gli importi: monospazio
Separatori: Alterna (a capo, ——, •••, 🎯🎯🎯)

3. INTEGRAZIONE PUBBLICITARIA (1 LINK):
Integralo nella narrazione (introduzione/climax/epilogo).

{url1} [Bonus: {bonus1}] → mescola le parole diversamente ogni volta! Usa diverse formulazioni: «ti diamo», «riscuoti», «ottieni», «ti aspettano» — unico ogni volta!

4. REGOLE DI CONTENUTO:

Dati: 1-3 fatti chiave per post. Vincita — nominare 1 volta.
Lessico: Sostituzione delle parole vietate («club», «storia», «risultato»).
Narrazione: In terza persona («il giocatore», «il cliente»).
Volume: Compatto ma sostanzioso.

LA STRUTTURA DEVE «CAMMINARE»: Rompi gli schemi. Inizi variabili: domanda, numero, link, storia.

🎭 LA VINCITA È LA PROTAGONISTA DEL POST!
⚠️ Se il nome del giocatore ({streamer}) è indicato — USALO 1 VOLTA!
• Se NON c'è il nome — usa formulazioni generali: "un giocatore", "questo eroe", "il vincitore"

🚫 VIETATO INDICARE IL TEMPO:
❌ MAI indicare: "oggi", "ieri", "stamattina", "recentemente"
✅ Scrivi semplicemente dell'evento senza riferimenti al tempo

🚫 VIETATE FRASI CLICHÉ:
❌ NON usare: "lo schermo è esploso", "brividi per il corpo"
✅ SCRIVI IN MODO ORIGINALE, evita i cliché!

❌ VIETATO: **markdown**, `codice`, [link](url)
✅ SOLO HTML: <b>, <i>, <u>, <code>, <a href>

═══════════════════════════════════════════════════════════════
🔥 ПОДВОДКА К ССЫЛКЕ — МОТИВАЦИОННЫЙ БЛОК (¡CRÍTICO!)
═══════════════════════════════════════════════════════════════

⚠️ ПЕРЕД ССЫЛКОЙ ОБЯЗАТЕЛЬНО ДОБАВЬ ПОДВОДКУ:
Это 1-2 предложения которые ПОДОГРЕВАЮТ читателя и МОТИВИРУЮТ перейти по ссылке.

📌 ЧТО ДОЛЖНА ДЕЛАТЬ ПОДВОДКА:
• Связать историю победы с ВОЗМОЖНОСТЬЮ читателя повторить этот опыт
• Создать ощущение что ЧИТАТЕЛЬ тоже может выиграть
• Вызвать желание ПОПРОБОВАТЬ прямо сейчас
• Использовать эмоции из истории для перехода к действию

📌 СТРУКТУРА ПОДВОДКИ:
• Отсылка к победе из поста → твой шанс тоже попробовать
• Вопрос-интрига → ответ в виде ссылки
• Призыв к действию на основе истории

📌 ТОНАЛЬНОСТЬ:
• Дружеская, без давления
• С азартом и энтузиазмом  
• Как будто делишься секретом с другом

❌ НЕ ПИШИ подводку отдельно — она должна ПЛАВНО переходить в ссылку!
✅ Подводка + ссылка = единый блок мотивации

═══════════════════════════════════════════════════════════════
⚠️ FORMATO DEL LINK CON BONUS (SOLO 1 LINK!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: IN OGNI POST OBBLIGATORIAMENTE UN LINK!
❌ POST SENZA LINK = RIFIUTATO
✅ USA SEMPRE: {url1} con descrizione unica basata su {bonus1}

⚠️ SCEGLI formati DIVERSI per ogni nuovo post!

⚠️ PARAFRASA IL BONUS (CRITICO!):
❌ NON copiare {bonus1} direttamente così com'è
✅ USALO come BASE, ma PARAFRASALO diversamente ogni volta
❌ NON INVENTARE nuovi bonus o importi - SOLO quello che c'è in {bonus1}!

📋 SCEGLI UNO dei formati (RUOTA! Ogni post diverso!):

🚨 USA SOLO QUESTO BONUS: {bonus1}
❌ NON INVENTARE altri bonus!

1️⃣ MAIUSCOLE: 🔥 <a href="{url1}">[PARAFRASA {bonus1}]!</a> 🔥
2️⃣ PUNTI: • • • "[parafrasa {bonus1}]" → {url1} • • •
3️⃣ INTESTAZIONE: 📌 IL TUO PASSO:\n<a href="{url1}">🔥 [PARAFRASA {bonus1}]!</a>
4️⃣ ONDE: 〰️ Vuoi [parafrasa {bonus1}]? {url1} 〰️
5️⃣ BLOCCHI: ╔══╗ {url1}\n[parafrasa {bonus1}]!!! ╚══╝
6️⃣ SIMBOLI: ⭐ {url1}\n[parafrasa {bonus1}]

📏 LUNGHEZZA: MASSIMO 700 caratteri!"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ (ОСНОВНОЙ - ИТАЛЬЯНСКИЙ)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT = """🇮🇹 CRITICO: SCRIVI SOLO IN ITALIANO!
❌ VIETATO usare russo, inglese o altre lingue nel testo
✅ PERMESSO in inglese: nomi delle slot (Gates of Olympus, Sweet Bonanza)
❌ TUTTO IL RESTO SOLO IN ITALIANO

🚨🚨🚨 REGOLA #0 PRIMA DI TUTTO! 🚨🚨🚨
⛔⛔⛔ USD, EUR ⛔⛔⛔
❌ QUESTI SONO **VALUTE**, NON NOMI DI PERSONE!
❌ **MAI** scrivere "USD ha scommesso", "EUR ha vinto"
✅ USA: "Un giocatore", "Un tipo", "L'eroe", "Il vincitore"
⚠️ SE USI USD/EUR COME NOME = TUTTO IL POST SARÀ RIFIUTATO!

🚨 REGOLA #0.5: SOLO TERMINI IN ITALIANO! 🚨
❌ NON usare "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giri gratuiti", "giri gratis", "bonus", "pacchetto di benvenuto"

═══════════════════════════════════════════════════════════════
💰 FOCUS: SCOMMESSA E RISCHIO
═══════════════════════════════════════════════════════════════

⚠️ CRITICO: COSTRUISCI IL POST ATTORNO ALLA DIMENSIONE DELLA SCOMMESSA E AL RISCHIO!

• La SCOMMESSA {bet} — il punto di partenza della storia
• Enfatizza il CONTRASTO: scommessa piccola → vincita enorme
• "Solo {bet}{currency}", "un importo modesto", "una scommessa piccola"
• Rischio, coraggio, audacia — l'emozione principale
• Il giocatore, la slot {slot}, la vincita {win} — attraverso il prisma della scommessa

ESEMPI:
"Solo {bet}{currency} — un importo che chiunque potrebbe rischiare"
"Una scommessa modesta di {bet}{currency} — e guarda cosa è successo"
"Con appena {bet}{currency} in gioco, nessuno si aspettava questo risultato"

COMPITO: Mostra il contrasto! Scommessa piccola = grande coraggio!

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGOLA CRITICA #1 - CODICI VALUTA 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ASSOLUTAMENTE VIETATO usare USD, EUR come NOMI o SOPRANNOMI di persone:
  
❌ SBAGLIATO (RIFIUTATO IMMEDIATAMENTE):
  - "USD ha scommesso..." 
  - "EUR è entrato nella sala..."
  - "Un coraggioso conosciuto come USD..."
  
✅ CORRETTO (questi codici sono SOLO per importi di denaro):
  - "Un giocatore ha scommesso 50 EUR"
  - "Il vincitore si è portato a casa 1.000 EUR"
  - "Con 500 USD ha scommesso..."

⚠️ PER NOMINARE IL GIOCATORE USA:
  - "Un giocatore", "Un tipo", "Un coraggioso", "Un fortunato"
  - "L'eroe", "Il campione", "Il vincitore", "Il re"
  - "Uno scommettitore", "Un audace", "Un temerario"
  - MAI: USD, EUR

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGOLA CRITICA #2 - BONUS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ASSOLUTAMENTE VIETATO inventare bonus:

✅ USA SOLO il bonus indicato in {bonus1}
❌ NON INVENTARE "100 dollari", "100 giri", "150%", "500%" 
❌ NON COPIARE esempi da altri post
✅ PARAFRASA {bonus1} con le tue parole ogni volta diversamente

═══════════════════════════════════════════════════════════════
🚫 VIETATO CONFRONTARE SCOMMESSE CON SPESE QUOTIDIANE
═══════════════════════════════════════════════════════════════

❌ MAI confrontare la scommessa con:
  - Prezzo del pranzo/cena/cibo
  - Costo di un caffè/bar
  - Prezzo della pizza/hamburger
  - Biglietto della metro/taxi/trasporto
  - "Quello che spendi per..." qualsiasi cosa quotidiana

✅ CORRETTO: Menziona semplicemente l'importo senza confronti

Sei un copywriter per un canale Telegram sulle vincite alle slot.
Crea post UNICI e VIVI. Scrivi come un amico racconta a un altro.

🎰 IMPORTANTE: NON INVENTARE TEMATICHE NON CORRELATE!
⚠️ Usa il nome della slot {slot} come indizio e contesto, ma NON INVENTARE un tema NON CORRELATO!
• Puoi interpretare liberamente: "Vampy Party" → festa/notte/rischio/vampiri/gotico
• Puoi semplicemente menzionare il nome: "nella slot {slot} è successo..."

⚠️ EVITA LE RIPETIZIONI!
• Ogni post deve iniziare in modo DIVERSO
• Usa set DIVERSI di emoji in ogni post
• NON ripetere struttura e formulazioni dei post precedenti

═══════════════════════════════════════════════════════════════
🚫 VIETATO INDICARE IL TEMPO
═══════════════════════════════════════════════════════════════

❌ MAI indicare:
• "oggi", "ieri", "domani"
• "stamattina", "nel pomeriggio", "stasera"
• "recentemente", "poco fa", "proprio ora"

✅ Invece scrivi semplicemente dell'evento senza riferimenti al tempo

═══════════════════════════════════════════════════════════════
🚫 VIETATE FRASI CLICHÉ
═══════════════════════════════════════════════════════════════

❌ NON usare frasi cliché:
• "lo schermo è esploso"
• "brividi su tutto il corpo"

✅ REGOLA DEL PUNTO DI VISTA:

📊 FATTI E AZIONI → TERZA PERSONA:
• "Il giocatore è entrato", "Il risultato impressiona"
• ❌ NO "io gioco", "io giro" (sono azioni del giocatore, non tue)

🎯 RISULTATO: Eventi in 3a persona
✅ Ogni post deve essere FRESCO e ORIGINALE!

═══════════════════════════════════════════════════════════════
⚠️ NUMERI E FORMATO
═══════════════════════════════════════════════════════════════

🔢 TUTTI I NUMERI IN <code>tags</code>!
• Entrata: <code>500€</code> ✅
• Risultato: <code>1 130 675€</code> ✅  
• Moltiplicatore: <code>x2261.3</code> ✅

📝 TAG HTML (usa TUTTI, non solo uno!):
• <b>grassetto</b> — slot, nomi, accenti, titoli
• <i>corsivo</i> — citazioni, chiarimenti, pensieri
• <code>monospazio</code> — TUTTI i numeri, importi, moltiplicatori
• <a href="URL">testo del link</a>

═══════════════════════════════════════════════════════════════
⚠️ POSIZIONE DEL LINK — VARIARE!
═══════════════════════════════════════════════════════════════

VARIANTI (alterna!):
• Link ALL'INIZIO → poi testo della storia
• Testo → Link NEL MEZZO → testo finale
• Testo della storia → Link ALLA FINE

🔗 HYPERLINK — MINIMO 4 PAROLE!
❌ <a href="URL">Riscuoti</a> — VIETATO! Troppo corto!
✅ <a href="URL">Riscuoti il pacchetto di benvenuto adesso</a> — OK!

═══════════════════════════════════════════════════════════════
🔥 ПОДВОДКА К ССЫЛКЕ — МОТИВАЦИОННЫЙ БЛОК (¡CRÍTICO!)
═══════════════════════════════════════════════════════════════

⚠️ ПЕРЕД ССЫЛКОЙ ОБЯЗАТЕЛЬНО ДОБАВЬ ПОДВОДКУ:
Это 1-2 предложения которые ПОДОГРЕВАЮТ читателя и МОТИВИРУЮТ перейти по ссылке.

📌 ЧТО ДОЛЖНА ДЕЛАТЬ ПОДВОДКА:
• Связать историю победы с ВОЗМОЖНОСТЬЮ читателя повторить этот опыт
• Создать ощущение что ЧИТАТЕЛЬ тоже может выиграть
• Вызвать желание ПОПРОБОВАТЬ прямо сейчас
• Использовать эмоции из истории для перехода к действию

📌 СТРУКТУРА ПОДВОДКИ:
• Отсылка к победе из поста → твой шанс тоже попробовать
• Вопрос-интрига → ответ в виде ссылки
• Призыв к действию на основе истории

📌 ТОНАЛЬНОСТЬ:
• Дружеская, без давления
• С азартом и энтузиазмом  
• Как будто делишься секретом с другом

❌ НЕ ПИШИ подводку отдельно — она должна ПЛАВНО переходить в ссылку!
✅ Подводка + ссылка = единый блок мотивации

═══════════════════════════════════════════════════════════════
⚠️ FORMATO DEL LINK CON BONUS (SOLO 1 LINK!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: IN OGNI POST OBBLIGATORIAMENTE UN LINK!
❌ POST SENZA LINK = RIFIUTATO
✅ USA SEMPRE: {url1} con descrizione unica basata su {bonus1}

⚠️ SCEGLI formati DIVERSI per ogni nuovo post!
❌ NON usare lo stesso stile di seguito
✅ Alterna i formati al massimo

⚠️ PARAFRASA IL BONUS (CRITICO!):
❌ NON copiare {bonus1} direttamente così com'è
✅ USALO come BASE, ma PARAFRASALO diversamente ogni volta
❌ NON INVENTARE nuovi bonus o importi - SOLO quello che c'è in {bonus1}!

🚨🚨🚨 USA SOLO QUESTO BONUS: {bonus1} 🚨🚨🚨
❌ NON INVENTARE "100 dollari", "100 giri" se NON sono in {bonus1}!
✅ PARAFRASA {bonus1} con le tue parole ogni volta diversamente

📐 REGOLA DELL'ARIA (OBBLIGATORIO!):
• SEMPRE aggiungi RIGA VUOTA PRIMA e DOPO ogni blocco link

📋 SCEGLI UNO dei formati (RUOTA! Ogni post diverso!):

1️⃣ CLASSICO: <a href="{url1}">🎁 [parafrasa {bonus1}]</a>
2️⃣ GRASSETTO: <b><a href="{url1}">🔥 [PARAFRASA {bonus1}]!</a></b>
3️⃣ ENERGETICO: <a href="{url1}">⚡ [parafrasa {bonus1}]!</a>
4️⃣ AMICHEVOLE: <a href="{url1}">👉 [parafrasa {bonus1}]!</a>
5️⃣ DIRETTO: <a href="{url1}">→ [parafrasa {bonus1}]</a>
6️⃣ DOMANDA: <a href="{url1}">🤔 Vuoi [parafrasa {bonus1}]?</a>
7️⃣ EMOJI: 🔥 <a href="{url1}">[parafrasa {bonus1}]</a> 🔥
8️⃣ URL + DESC: {url1}\n👆 [parafrasa {bonus1}]
9️⃣ DESC + URL: 🎁 [parafrasa {bonus1}]:\n{url1}

❌ VIETATO: **grassetto**, `codice`, __corsivo__, [testo](url) — questo è Markdown!

═══════════════════════════════════════════════════════════════
✅ GENERA POST UNICO SENZA TEMPLATE!
═══════════════════════════════════════════════════════════════

⚠️ IMPORTANTE: NON USARE template o strutture prefabbricate!
• Ogni post deve essere COMPLETAMENTE ORIGINALE
• Inventa il TUO approccio e presentazione unici
• Basati sui dati (giocatore, slot, vincita) e crea una NUOVA storia
• Posiziona i link in posti DIVERSI (inizio/metà/fine)

🎯 IL TUO COMPITO: Scrivi il post come se fosse il primo al mondo!
• Senza ripetizioni di strutture
• Senza copiare esempi
• Con inizio, metà e fine UNICI

═══════════════════════════════════════════════════════════════
REGOLE
═══════════════════════════════════════════════════════════════

📏 LUNGHEZZA: MINIMO 650 caratteri, MASSIMO 800 caratteri

🎭 LA VINCITA È LA PROTAGONISTA DEL POST!
⚠️ Se il nome del giocatore ({streamer}) è indicato — USALO 1 VOLTA!
• SEMPRE scrivi il nome CON LA MAIUSCOLA
• Costruisci il post attorno alla vincita, lei è la star della storia!
• Se il nome non è indicato — usa: "un giocatore", "questo eroe", "il vincitore", "{person}"

🎰 NOME DELLA SLOT (interpreta creativamente!):
• Sugar Rush → "dolce vittoria", "tempesta di zucchero"
• Le Viking → "il vichingo ha mostrato la forza", "guerriero scandinavo"
• Fruit Party → "festa fruttata", "i frutti sono maturati"

📊 BLOCCO VINCITA (FORMATI DIVERSI!):

✅ ALTERNA formati:
• Formato 1 (inline): Entrata <code>{bet}{currency}</code> → risultato <code>{win}{currency}</code> (x{multiplier})
• Formato 2 (con emoji): 💸 <code>{bet}{currency}</code> entrata | 💰 <code>{win}{currency}</code> risultato | 🔥 <code>x{multiplier}</code>
• Formato 3 (domanda): Chi avrebbe pensato che <code>{bet}{currency}</code> si sarebbero trasformati in <code>{win}{currency}</code>?!
• Formato 4 (storia): È iniziato con <code>{bet}{currency}</code>, ed è finito con <code>{win}{currency}</code>...

🔀 BLOCCHI — mescola 4 elementi CASUALMENTE:

1. INIZIO DEL POST (scegli tipo a caso):
   • 30% - Narrativa (storia, racconto dell'evento)
   • 25% - Domanda (intrigo, domanda retorica)
   • 20% - Titolo (brillante, maiuscole, cornici emoji)
   • 15% - Fatto (numeri, constatazione)
   • 10% - Emozione (esclamazione, reazione)

2. Fatti (entrata/risultato/moltiplicatore)

3. BLOCCO AGGIUNTIVO (scegli a caso):
   • Reazione emotiva
   • Contesto/dettagli dell'evento
   • Invito all'azione
   • Commento/valutazione

4. Link con bonus

❌ PAROLE VIETATE: casinò
✅ SOSTITUZIONI: piattaforma, prodotto, sito, club

😀 EMOJI: tanti, tematici: 🔥💰🚀💎😱🤑💸📈🏆😎👇

🎭 TONALITÀ (alterna): sorpresa / fiducia / entusiasmo / calma / ironia

═══════════════════════════════════════════════════════════════
FORMATO DI RISPOSTA
═══════════════════════════════════════════════════════════════

Genera un post PRONTO per Telegram.
Solo testo con tag HTML.
NON aggiungere spiegazioni, commenti, marcatori tipo [HOOK].

📏 LUNGHEZZA: MINIMO 650 caratteri, MASSIMO 800 caratteri
Scrivi in modo VIVO! Aggiungi reazioni, dettagli del momento!"""

    # ═══════════════════════════════════════════════════════════════════
    # УНИВЕРСАЛЬНЫЙ ПРОМПТ ДЛЯ ВИДЕО-ПОСТОВ (БЕЗ ЖЕСТКИХ СТРУКТУР!)
    # ═══════════════════════════════════════════════════════════════════
    
    VIDEO_POST_PROMPTS = [
        # Prompt universale - AI sceglie stile e struttura
        """Crea un post UNICO su una vincita.

DATI:
• Giocatore: {streamer} (se indicato - usalo 1 volta con la maiuscola, se NON c'è - usa "un giocatore", "questo eroe", "il vincitore")
• Slot: {slot}
• Scommessa: {bet}{currency}
• Vincita: {win}{currency}
• Moltiplicatore: x{multiplier}

LINK (obbligatorio!):
• Link: {url1} — {bonus1} (DESCRIVI IL BONUS IN MODO ATTRAENTE E MOTIVANTE!)

⚠️ REGOLA PRINCIPALE: LIBERTÀ TOTALE DI CREATIVITÀ!
• NON seguire nessun modello o esempio
• Inventa la TUA presentazione unica
• Posiziona i link in posti DIVERSI (inizio/metà/fine/alternanza)
• Usa emoji e separatori DIVERSI

🎨 TEMATICA: Puoi interpretare il nome della slot {slot} liberamente, ma NON inventare un tema NON CORRELATO!

📏 Lunghezza: MINIMO 650, MASSIMO 800 caratteri
✅ Solo HTML: <b>, <i>, <u>, <code>, <a href>
❌ Vietato: casinò"""
    ]
    
    IMAGE_POST_PROMPTS = [
        """Scrivi un post sui BONUS.
Link: {url1} ({bonus1}).

Stile: parla dei bonus come a un amico, in modo morbido e senza aggressività.
POSIZIONE DEI LINK: all'INIZIO del post.

FORMATO DEI LINK (CRITICO!):
⚠️ DESCRIVI IL BONUS IN MODO ATTRAENTE E MOTIVANTE!

🎯 MOTIVAZIONE: Fai in modo che le persone VOGLIANO cliccare!
✅ Usa parole emozionali: "esclusivo", "incredibile", "gratis", "istantaneo", "speciale"
✅ Crea urgenza: "solo oggi", "tempo limitato", "attiva ora"
✅ Evidenzia i benefici: "raddoppia il tuo deposito", "ottieni di più", "senza rischio"
✅ Invito all'azione: "riscuoti ORA", "attiva il tuo bonus", "inizia a vincere"

{url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!

REGOLE:
- MINIMO 500, MASSIMO 700 caratteri
- Inizia con 🎁 o 💎
- Bonus in <code>tags</code>: <code>[usa {bonus1}]</code>
- Tanti emoji 🍒🔥💰🚀
- SENZA la parola "casinò" (usa: piattaforma, sito, club)
- Termina con una nota motivazionale positiva
- Scrivi descrizioni COMPLETE e ATTRAENTI dei bonus!""",

        """Scrivi un post MOTIVANTE con bonus.
Link: {url1} ({bonus1}).

Stile: spiega perché vale la pena provare, morbido e senza pressione.
POSIZIONE DEL LINK: nel MEZZO del post.

🎯 MOTIVAZIONE: Fai in modo che le persone VOGLIANO cliccare!
✅ Usa parole emozionali: "esclusivo", "incredibile", "gratis", "speciale"
✅ Crea urgenza: "solo oggi", "tempo limitato", "attiva ora"
✅ Evidenzia i benefici: "raddoppia il tuo deposito", "ottieni di più", "senza rischio"
✅ Invito all'azione: "riscuoti ORA", "attiva il tuo bonus", "inizia a vincere"

FORMATO DEL LINK:
{url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!

REGOLE:
- MINIMO 500, MASSIMO 700 caratteri
- Inizia con una domanda ❓
- <b>Grassetto</b> per gli accenti
- Bonus in <code>tags</code>
- SENZA la parola "casinò"
- Finale: positivo e motivante
- Scrivi descrizioni COMPLETE e ATTRAENTI del bonus!""",

        """Scrivi un post-CONSIGLIO sui bonus.
Link: {url1} ({bonus1}).

Stile: come un lifehack amichevole, senza aggressività.
POSIZIONE DEL LINK: mescolato con i passaggi.

🎯 MOTIVAZIONE: Fai in modo che le persone VOGLIANO cliccare!
✅ Usa parole emozionali: "esclusivo", "incredibile", "gratis", "speciale"
✅ Crea urgenza: "solo oggi", "tempo limitato", "attiva ora"
✅ Invito all'azione: "riscuoti ORA", "attiva il tuo bonus", "inizia a vincere"

FORMATO DEL LINK:
{url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!

REGOLE:
- MINIMO 500, MASSIMO 700 caratteri
- Inizia con 💡
- Passaggi 1. 2. 3.
- Bonus in <code>tags</code>
- SENZA la parola "casinò" (sostituisci: piattaforma, portale)
- Termina con un pensiero motivante
- Scrivi descrizioni COMPLETE e ATTRAENTI del bonus!""",

        """Scrivi un post COMPARATIVO sui bonus.
Link: {url1} ({bonus1}).

Stile: aiuta a scegliere in modo morbido e amichevole.
POSIZIONE DEL LINK: dopo il confronto.

🎯 MOTIVAZIONE: Fai in modo che le persone VOGLIANO cliccare!
✅ Usa parole emozionali: "esclusivo", "incredibile", "gratis", "speciale"
✅ Crea urgenza: "solo oggi", "tempo limitato", "attiva ora"
✅ Invito all'azione: "riscuoti ORA", "attiva il tuo bonus", "inizia a vincere"

FORMATO DEL LINK:
{url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!

REGOLE:
- MINIMO 500, MASSIMO 700 caratteri
- Titolo «Cosa scegliere?» 🤔
- Vantaggi con ▸
- Bonus in <code>tags</code>
- SENZA la parola "casinò"
- Finale positivo e motivante
- Scrivi descrizioni COMPLETE e ATTRAENTI del bonus!""",

        """Scrivi un ANNUNCIO di bonus.
Link: {url1} ({bonus1}).

Stile: crea interesse senza aggressività!
POSIZIONE DEL LINK: alla FINE del post con riga vuota.

🎯 MOTIVAZIONE: Fai in modo che le persone VOGLIANO cliccare!
✅ Usa parole emozionali: "esclusivo", "incredibile", "gratis", "speciale"
✅ Crea urgenza: "solo oggi", "tempo limitato", "attiva ora"
✅ Invito all'azione: "riscuoti ORA", "attiva il tuo bonus", "inizia a vincere"

FORMATO DEL LINK:
{url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!

REGOLE:
- MINIMO 500, MASSIMO 700 caratteri
- Inizia con 🔔 o ⚡
- <b>Grassetto</b> per le cose importanti
- Bonus in <code>tags</code>
- SENZA la parola "casinò"
- Finale motivante
- Scrivi descrizioni COMPLETE e ATTRAENTI del bonus!""",

        """Scrivi un post-RECENSIONE sui bonus.
Link: {url1} ({bonus1}).

Stile: come se condividessi esperienza, morbido e onesto.
POSIZIONE DEL LINK: alla FINE come raccomandazione.

🎯 MOTIVAZIONE: Fai in modo che le persone VOGLIANO cliccare!
✅ Usa parole emozionali: "esclusivo", "incredibile", "gratis", "speciale"
✅ Crea urgenza: "solo oggi", "tempo limitato", "attiva ora"
✅ Invito all'azione: "riscuoti ORA", "attiva il tuo bonus", "inizia a vincere"

FORMATO DEL LINK:
{url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!

REGOLE:
- MINIMO 500, MASSIMO 700 caratteri
- Citazione tra «virgolette»
- Emoji di esperienza: 💬✅
- Bonus in <code>tags</code>
- SENZA la parola "casinò" (usa: sito, risorsa, servizio)
- Raccomandazione positiva
- Scrivi descrizioni COMPLETE e ATTRAENTI del bonus!""",

        """Scrivi un post con bonus.
Link: {url1} ({bonus1}).

Stile: informativo, vivace e amichevole.
POSIZIONE DEL LINK: link con freccia all'INIZIO.

🎯 MOTIVAZIONE: Fai in modo che le persone VOGLIANO cliccare!
✅ Usa parole emozionali: "esclusivo", "incredibile", "gratis", "speciale"
✅ Crea urgenza: "solo oggi", "tempo limitato", "attiva ora"
✅ Invito all'azione: "riscuoti ORA", "attiva il tuo bonus", "inizia a vincere"

FORMATO DEL LINK:
➡️ {url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!

REGOLE:
- MINIMO 500, MASSIMO 700 caratteri
- Bonus in <code>tags</code>
- SENZA la parola "casinò" (sostituisci: piattaforma, club di gioco)
- Termina in modo positivo
- Scrivi descrizioni COMPLETE e ATTRAENTI del bonus!""",
    ]
    
    # Промпты БЕЗ имени стримера (основной режим для итальянского)
    VIDEO_POST_PROMPTS_NO_STREAMER = [
        """Scrivi un post su una vincita (nome del giocatore SCONOSCIUTO).
{slot_plain}, scommessa <b>{bet}{currency}</b>, ha vinto <b>{win}{currency}</b> (x{multiplier}).
Link: {url1}.

⚠️ Chiama l'eroe in modo UNICO: {person}

🚨🚨🚨 REGOLA CRITICA! 🚨🚨🚨
USA ESATTAMENTE LE CIFRE INDICATE SOPRA:
- Scommessa: {bet}{currency}
- Vincita: {win}{currency}  
- Moltiplicatore: x{multiplier}
NON CAMBIARE, NON ARROTONDARE, NON INVENTARE ALTRI NUMERI!

REGOLE HTML:
- Importi: <b>grassetto</b> o <code>monospazio</code>
- Slot: <b>Con Maiuscola</b>
- Hyperlink: <a href="URL">testo</a> — descrizione del bonus LUNGA (50+ caratteri!)
- Emoji 🔥💰🍒
- MINIMO 500, MASSIMO 700 caratteri!

⚠️ FORMATO DEI LINK (scegli uno):
🚨 USA SOLO {bonus1} - NON inventare altri bonus!
1) {url1} - 🎁 [parafrasa {bonus1}]
2) {url1}\n🔥 [parafrasa {bonus1}]
3) <a href="{url1}">🚀 RISCUOTI IL TUO BONUS!</a> — [parafrasa {bonus1}]""",

        """Scrivi un reportage (SENZA nome).
{slot}, <b>{bet}{currency}</b> → <b>{win}{currency}</b>, x{multiplier}.
Link: {url1}.

⚠️ Chiama l'eroe: {person}

🚨🚨🚨 USA ESATTAMENTE QUESTI NUMERI! 🚨🚨🚨
Scommessa: {bet}{currency} | Vincita: {win}{currency} | x{multiplier}
NON CAMBIARE E NON INVENTARE ALTRI NUMERI!

REGOLE HTML:
- Inizia con 🔴 o ⚡
- Importi in <b>grassetto</b>
- Slot: <b>Con Maiuscola</b>
- MINIMO 500, MASSIMO 700 caratteri!

⚠️ FORMATO DEI LINK: URL - [parafrasa {bonus1}] 
🚨 USA SOLO {bonus1} - NON inventare altri bonus!""",

        """Scrivi un post con DOMANDA (senza nome del giocatore).
{slot}, entrata <b>{bet}{currency}</b>, uscita <b>{win}{currency}</b>, x{multiplier}.
Link: {url1}.

⚠️ Chiama l'eroe in modo unico: {person}

🚨 USA ESATTAMENTE: {bet}{currency} (entrata) → {win}{currency} (uscita) | x{multiplier}
NON CAMBIARE I NUMERI!

REGOLE HTML:
- Inizia con ❓
- Importi: <b>grassetto</b> o <code>mono</code>
- Intrigo → risposta
- Link con 👇
- MINIMO 500, MASSIMO 700 caratteri!

⚠️ FORMATO DEI LINK (MOTIVA A CLICCARE!):
👇 {url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!""",

        """Scrivi un post EMOZIONALE (senza nome).
{slot}, <b>{bet}{currency}</b> è diventato <b>{win}{currency}</b> (x{multiplier}).
Link: {url1}.

⚠️ Chiama l'eroe: {person}

🚨 NUMERI ESATTI: {bet}{currency} → {win}{currency} (x{multiplier})
NON INVENTARE ALTRE CIFRE!

REGOLE HTML:
- Emoji: 🔥💰😱🍋🍒
- Importi in <b>grassetto</b>
- Slot <b>Con Maiuscola</b>
- MINIMO 500, MASSIMO 700 caratteri!

⚠️ FORMATO DEI LINK: [parafrasa {bonus1}] PRIMA, poi URL
🚨 USA SOLO {bonus1} - NON inventare altri bonus!
📲 👉 {url1} 👈""",

        """Scrivi un post CASUAL (senza nome).
{slot}, <b>{bet}{currency}</b> → <b>{win}{currency}</b>, x{multiplier}.
Link: {url1}.

⚠️ Chiama l'eroe in modo casual: {person}

🚨 CIFRE ESATTE: {bet}{currency} → {win}{currency}, x{multiplier} - NON CAMBIARLE!

REGOLE HTML:
- Inizia con "Guarda," o "Senti," o "Ascolta,"
- Emoji: 💪😎🤙
- Importi in <b>grassetto</b>
- MINIMO 500, MASSIMO 700 caratteri!

⚠️ FORMATO DEI LINK: 👉 URL - [parafrasa {bonus1}]
🚨 USA SOLO {bonus1} - NON inventare altri bonus!""",

        """Scrivi un post con NUMERI (senza nome).
{slot}, entrata <b>{bet}{currency}</b>, risultato <b>{win}{currency}</b>, x{multiplier}.
Link: {url1}.

⚠️ Chiama l'eroe: {person}

🚨 USA QUESTI NUMERI ESATTI NEL TESTO: {bet}{currency}, {win}{currency}, x{multiplier}
VIETATO cambiare o inventare altre cifre!

REGOLE HTML:
- Prima riga: <b>{win}{currency}</b>!
- Importi in <b>grassetto</b> o <code>monospazio</code>
- Moltiplicatore: <b>x{multiplier}</b>
- Link dopo ━━━
- MINIMO 500, MASSIMO 700 caratteri!

⚠️ FORMATO DEI LINK dopo il separatore:
━━━━━━━━━━
➡️ {url1}
🎁 [parafrasa {bonus1}] - 🚨 USA SOLO {bonus1}!""",
    ]
    
    # BONUS_VARIATIONS убраны - теперь используем ТОЛЬКО оригинальный бонус пользователя {bonus1}
    BONUS_VARIATIONS = []  # Пустой список - НЕ используется
    
    # Форматы размещения ссылок (для разнообразия)
    # Распределение: ~12% гиперссылки, ~88% plain URL форматы
    LINK_FORMATS = [
        "hyperlink", "hyperlink",  # 2/17 = ~12% гиперссылки
        "emoji_url_text", "emoji_url_text", "emoji_url_text",  # 3/17 = ~18%
        "url_dash_text", "url_dash_text", "url_dash_text",  # 3/17 = ~18%
        "arrow_url_text", "arrow_url_text", "arrow_url_text",  # 3/17 = ~18%
        "text_dash_url", "text_dash_url", "text_dash_url",  # 3/17 = ~18%
        "url_newline_text", "url_newline_text", "url_newline_text",  # 3/17 = ~18%
    ]
    
    # Синонимы для "giri/FS" (ITALIANO)
    SPIN_SYNONYMS = [
        "giri", "round", "tentativi", "prove", 
        "giocate", "turni", "giri gratuiti", "giri gratis"
    ]
    
    def __init__(
        self, 
        api_key: str = None, 
        model: str = "gpt-4o-mini",
        openrouter_api_key: str = None,
        use_openrouter: bool = False
    ):
        """
        Инициализация генератора.
        
        Args:
            api_key: OpenAI API ключ (или из переменной окружения)
            model: Модель для генерации (OpenAI или OpenRouter)
            openrouter_api_key: OpenRouter API ключ
            use_openrouter: Использовать OpenRouter вместо OpenAI
        """
        self.model = model
        self.client = None
        self.use_openrouter = use_openrouter

        # Разводим ключи: это важно, потому что uniqueness-check всегда ходит в OpenRouter
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")

        # self.api_key оставляем как "активный" ключ текущего режима (для совместимости)
        self.api_key = self.openrouter_api_key if use_openrouter else self.openai_api_key

        if use_openrouter:
            # Используем OpenRouter
            if AsyncOpenAI and self.openrouter_api_key:
                self.client = AsyncOpenAI(
                    api_key=self.openrouter_api_key,
                    base_url=OPENROUTER_BASE_URL
                )
        else:
            # Используем OpenAI напрямую
            if AsyncOpenAI and self.openai_api_key:
                self.client = AsyncOpenAI(api_key=self.openai_api_key)

        self.bonus_data: Optional[BonusData] = None
        self._generated_posts: List[str] = []  # Для проверки уникальности
        self._prompt_counter = 0  # Счётчик для ротации системных промптов
        self._used_starts: List[str] = []  # Отслеживание начал постов (первые 100 символов)
        self._used_emoji_patterns: List[str] = []  # Отслеживание наборов смайликов
        self._used_structures: List[int] = []  # Отслеживание использованных структур из VIDEO_POST_PROMPTS
        self._used_slot_structure: Dict[str, List[int]] = {}  # Отслеживание структур по слотам {slot: [structure_indices]}
        self._existing_posts: List[str] = []  # База существующих постов для обучения AI
        self._used_bonus1_variations: List[str] = []  # Отслеживание использованных вариаций bonus1
        self._used_bonus2_variations: List[str] = []  # Отслеживание использованных вариаций bonus2
        self._link_format_counter = 0  # Счётчик для строгой ротации форматов ссылок (1-6)
    
    def set_link_format_counter(self, counter: int):
        """Устанавливает счетчик форматов ссылок (для ротации между генераторами)"""
        self._link_format_counter = counter
    
    def get_link_format_counter(self) -> int:
        """Возвращает текущее значение счетчика форматов ссылок"""
        return self._link_format_counter
    
    def _get_system_prompt(self) -> str:
        """
        Строгая ротация системных промптов для максимального разнообразия.
        Использует круговую ротацию: 1-2-3-4-5-6-1-2-3-4-5-6...
        """
        self._prompt_counter += 1
        
        # Список всех промптов
        all_prompts = [
            self.SYSTEM_PROMPT,
            self.SYSTEM_PROMPT_ARCHITECT,
            self.SYSTEM_PROMPT_3,
            self.SYSTEM_PROMPT_4,
            self.SYSTEM_PROMPT_5,
            self.SYSTEM_PROMPT_6
        ]
        
        # Строгая круговая ротация
        # Пост 1 -> промпт 0, Пост 2 -> промпт 1, ..., Пост 7 -> промпт 0
        prompt_index = (self._prompt_counter - 1) % 6
        return all_prompts[prompt_index]
    
    def set_bonus_data(self, url1: str, bonus1: str, url2: str = "", bonus2: str = ""):
        """Устанавливает данные о бонусах (для итальянского сценария используется только url1 и bonus1)"""
        self.bonus_data = BonusData(
            url1=url1,
            bonus1_desc=bonus1
        )
    
    def reset_bonus_variations(self):
        """Сбрасывает списки использованных вариаций бонусов"""
        self._used_bonus1_variations.clear()
        self._used_bonus2_variations.clear()
        print("   🔄 Списки использованных вариаций бонусов сброшены")
    
    def load_existing_posts(self, posts: List[str]):
        """
        Загружает существующие посты для обучения AI и проверки уникальности.
        
        Args:
            posts: Список текстов постов (твои 500 готовых постов)
        
        Как AI будет использовать эти посты:
        1. **Обучение стилю** - анализирует структуру, тон, форматирование
        2. **Избежание повторов** - не повторяет фразы и конструкции
        3. **Проверка уникальности** - сравнивает новые посты со старыми
        """
        self._existing_posts = posts
        print(f"✅ Загружено {len(posts)} существующих постов для обучения AI")
    
    def load_existing_posts_from_file(self, filepath: str):
        """
        Загружает существующие посты из JSON файла.
        
        Args:
            filepath: Путь к JSON файлу с постами
        
        Формат JSON:
        {
            "posts": [
                {"text": "пост 1...", "date": "2025-01-01"},
                {"text": "пост 2...", "date": "2025-01-02"}
            ]
        }
        
        или просто массив строк:
        ["пост 1...", "пост 2...", ...]
        """
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Поддержка двух форматов
            if isinstance(data, list):
                # Простой массив строк
                posts = data
            elif isinstance(data, dict) and 'posts' in data:
                # Объекты с метаданными
                posts = [p['text'] if isinstance(p, dict) else p for p in data['posts']]
            else:
                raise ValueError("Неверный формат JSON. Ожидается массив или объект с ключом 'posts'")
            
            self.load_existing_posts(posts)
            return len(posts)
        
        except FileNotFoundError:
            print(f"⚠️ Файл {filepath} не найден. Создайте его для обучения AI.")
            return 0
        except Exception as e:
            print(f"❌ Ошибка загрузки постов: {e}")
            return 0
    
    def _get_random_bonus_variation(self, original: str, is_bonus1: bool = True) -> str:
        """
        Возвращает оригинальное описание бонуса БЕЗ модификаций.
        
        ВАЖНО: Для итальянского сценария мы передаём бонус напрямую в AI,
        и AI сам парафразирует его согласно инструкциям в промпте.
        
        Это гарантирует, что бонус от пользователя используется как есть,
        без замены на hardcoded примеры.
        
        Args:
            original: Оригинальное описание бонуса от пользователя
            is_bonus1: True если это bonus1, False если bonus2
        
        Returns:
            Оригинальный бонус без изменений
        """
        # Просто возвращаем оригинал - AI сам парафразирует в промпте
        return original
    
    # ═══════════════════════════════════════════════════════════════════
    # СТРУКТУРЫ ПОСТОВ (ДЛЯ ПЕРЕМЕШИВАНИЯ БЛОКОВ)
    # ═══════════════════════════════════════════════════════════════════
    
    STRUCTURE_TEMPLATES = [
        # Классические
        ["HOOK", "FACTS", "LINK1", "LINK2", "CTA"],           # Стандарт
        ["HOOK", "FACTS", "CTA", "LINK1", "LINK2"],           # CTA перед ссылками
        ["FACTS", "HOOK", "LINK1", "LINK2", "CTA"],           # Факты вперёд
        # Агрессивные (ссылки раньше)
        ["HOOK", "LINK1", "FACTS", "LINK2", "CTA"],           # Ссылка в середине
        ["LINK1", "HOOK", "FACTS", "LINK2", "CTA"],           # Начинаем со ссылки
        ["HOOK", "LINK1", "LINK2", "FACTS", "CTA"],           # Обе ссылки рано
        # Минималистичные
        ["FACTS", "LINK1", "LINK2"],                          # Без хука и CTA
        ["HOOK", "FACTS", "LINK1", "LINK2"],                  # Без CTA
        ["FACTS", "CTA", "LINK1", "LINK2"],                   # Без хука
        # Нестандартные
        ["CTA", "HOOK", "FACTS", "LINK1", "LINK2"],           # CTA вначале (вопрос)
        ["HOOK", "CTA", "LINK1", "FACTS", "LINK2"],           # Перемешанные
        ["FACTS", "LINK1", "CTA", "LINK2"],                   # Компактный
    ]
    
    def _parse_blocks(self, text: str) -> Dict[str, str]:
        """
        Парсит текст с маркерами блоков.
        
        Возвращает словарь {block_name: content}
        """
        import re
        
        blocks = {}
        block_names = ["HOOK", "FACTS", "LINK1", "LINK2", "CTA"]
        
        for block_name in block_names:
            pattern = rf'\[{block_name}\](.*?)\[/{block_name}\]'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                if content:
                    blocks[block_name] = content
        
        return blocks
    
    def _assemble_post(self, blocks: Dict[str, str], structure: List[str]) -> str:
        """
        Собирает пост из блоков по заданной структуре.
        """
        parts = []
        for block_name in structure:
            if block_name in blocks and blocks[block_name]:
                parts.append(blocks[block_name])
        
        return "\n\n".join(parts)
    
    def _apply_random_formatting(self, text: str) -> str:
        """
        Применяет рандомное HTML форматирование к каждой строке текста.
        
        Форматы (HTML для Telegram - более надёжное):
        1. <b>жирный</b>
        2. <i>курсив</i>
        3. <b><i>жирный курсив</i></b>
        4. <u>подчёркнутый</u>
        5. <b><u>жирный подчёркнутый</u></b>
        6. <i><u>курсив подчёркнутый</u></i>
        7. <code>моноширный</code> (для чисел и названий)
        8. <tg-spoiler>спойлер</tg-spoiler>
        9. <blockquote>цитата</blockquote>
        10. без форматирования
        """
        import re
        
        if not text or len(text) < 5:
            return text
        
        lines = text.split('\n')
        formatted_lines = []
        
        # Счётчик для ограничения цитат (не более 1-2 на пост)
        quote_count = 0
        max_quotes = random.randint(1, 2)
        
        # Счётчик для ограничения спойлеров
        spoiler_count = 0
        max_spoilers = random.randint(0, 1)
        
        # Отслеживаем использованные форматы для разнообразия
        used_formats = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Пропускаем пустые строки
            if not line_stripped:
                formatted_lines.append(line)
                continue
            
            # Пропускаем строки с уже существующим форматированием (Markdown или HTML)
            if any(marker in line_stripped for marker in [
                '**', '__', '`', '<b>', '<i>', '<u>', '<code>', '<tg-spoiler>',
                '<blockquote>', '[', '](', '➡️', '🔗', '•', '||', '>'
            ]):
                formatted_lines.append(line)
                continue
            
            # Пропускаем строки-ссылки
            if line_stripped.startswith('http') or 'cutt.ly' in line_stripped:
                formatted_lines.append(line)
                continue
            
            # Извлекаем эмодзи в начале строки (расширенный паттерн)
            emoji_pattern = r'^((?:[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]|[\U0001FA00-\U0001FAFF])+)\s*(.+)$'
            emoji_match = re.match(emoji_pattern, line_stripped)
            
            if emoji_match:
                emoji = emoji_match.group(1)
                text_content = emoji_match.group(2)
            else:
                emoji = ""
                text_content = line_stripped
            
            # Извлекаем знаки препинания в конце для корректного форматирования
            punctuation_match = re.match(r'^(.+?)([.!?…,;:]+)$', text_content)
            if punctuation_match:
                text_without_punct = punctuation_match.group(1).strip()
                punctuation = punctuation_match.group(2)
            else:
                text_without_punct = text_content
                punctuation = ""
            
            # Проверяем, содержит ли строка данные о выигрыше (числа, ₽, $, x)
            has_win_data = bool(re.search(r'(\d+[\s,.]?\d*\s*[₽$€]|\d+\s*[₽$€]|[₽$€]\s*\d+|x\d+|х\d+|\d+\s*руб)', text_content, re.IGNORECASE))
            
            # Проверяем, похоже ли на название слота (английские слова, заглавные буквы)
            has_slot_name = bool(re.search(r'[A-Z][a-z]+\s+[A-Z]|Megaways|Gates|Dog\s+House|Sweet\s+Bonanza|Fire\s+Portals', text_content))
            
            # Расширенный набор форматов
            if has_win_data or has_slot_name:
                # Для данных о выигрыше и слотов - чаще моноширный
                format_choice = random.choice([
                    'code',           # <code>текст</code> - моноширный
                    'code',           # увеличиваем шанс моноширного
                    'bold',           # <b>текст</b>
                    'bold_underline', # <b><u>текст</u></b>
                    'quote',          # <blockquote>
                    'normal',
                ])
            else:
                # Для обычного текста - расширенный набор из 10 вариантов
                all_formats = [
                    'bold',             # <b>текст</b>
                    'italic',           # <i>текст</i>
                    'bold_italic',      # <b><i>текст</i></b>
                    'underline',        # <u>текст</u>
                    'bold_underline',   # <b><u>текст</u></b>
                    'italic_underline', # <i><u>текст</u></i>
                    'code',             # <code>текст</code>
                    'spoiler',          # <tg-spoiler>текст</tg-spoiler>
                    'quote',            # <blockquote>
                    'normal',           # без форматирования
                ]
                
                # Выбираем формат, который ещё не использовали (для разнообразия)
                available_formats = [f for f in all_formats if f not in used_formats]
                if not available_formats:
                    used_formats.clear()
                    available_formats = all_formats
                
                format_choice = random.choice(available_formats)
                used_formats.append(format_choice)
            
            # Ограничиваем количество цитат
            if format_choice == 'quote' and quote_count >= max_quotes:
                format_choice = random.choice(['bold', 'italic', 'underline', 'normal'])
            
            # Ограничиваем количество спойлеров
            if format_choice == 'spoiler' and spoiler_count >= max_spoilers:
                format_choice = random.choice(['bold', 'italic', 'normal'])
            
            # Не применяем код к очень длинным строкам
            if format_choice == 'code' and len(text_content) > 50:
                format_choice = random.choice(['bold', 'italic', 'bold_italic', 'normal'])
            
            # Не применяем спойлер к коротким строкам
            if format_choice == 'spoiler' and len(text_content) < 15:
                format_choice = random.choice(['bold', 'underline', 'normal'])
            
            # Применяем HTML форматирование (знаки препинания ВНЕ тегов!)
            if format_choice == 'bold':
                formatted_text = f"<b>{text_without_punct}</b>{punctuation}"
            elif format_choice == 'italic':
                formatted_text = f"<i>{text_without_punct}</i>{punctuation}"
            elif format_choice == 'bold_italic':
                formatted_text = f"<b><i>{text_without_punct}</i></b>{punctuation}"
            elif format_choice == 'underline':
                formatted_text = f"<u>{text_without_punct}</u>{punctuation}"
            elif format_choice == 'bold_underline':
                formatted_text = f"<b><u>{text_without_punct}</u></b>{punctuation}"
            elif format_choice == 'italic_underline':
                formatted_text = f"<i><u>{text_without_punct}</u></i>{punctuation}"
            elif format_choice == 'code':
                formatted_text = f"<code>{text_without_punct}</code>{punctuation}"
            elif format_choice == 'spoiler':
                spoiler_count += 1
                formatted_text = f"<tg-spoiler>{text_without_punct}</tg-spoiler>{punctuation}"
            elif format_choice == 'quote':
                # Цитата - вся строка с эмодзи через blockquote
                quote_count += 1
                if emoji:
                    formatted_lines.append(f"<blockquote>{emoji} {text_content}</blockquote>")
                else:
                    formatted_lines.append(f"<blockquote>{text_content}</blockquote>")
                continue  # Уже добавили, пропускаем остальное
            else:  # normal
                formatted_text = text_content
            
            # Собираем строку с эмодзи
            if emoji:
                formatted_line = f"{emoji} {formatted_text}"
            else:
                formatted_line = formatted_text
            
            formatted_lines.append(formatted_line)
        
        return '\n'.join(formatted_lines)
    
    # ═══════════════════════════════════════════════════════════════════
    # УНИКАЛЬНЫЕ ОПИСАНИЯ ПЕРСОНАЖЕЙ (для постов без имени стримера)
    # ═══════════════════════════════════════════════════════════════════
    
    PERSON_VARIANTS = [
        "un giocatore", "qualcuno nello stream", "uno scommettitore", "questo tipo",
        "un giocatore casuale", "un tipo qualunque", 
        "un tipo", "il nostro eroe", "un tipo nello stream", "questo giocatore",
        "un coraggioso", "un tipo audace", "un fortunato", "un tipo fortunato",
        "un temerario", "un ragazzo", "uno scommettitore nello stream", "un tizio",
        "un audace", "un giocatore nello stream", "questo fortunato", "il vincitore",
        "qualcuno", "il protagonista", "questo utente", "un utente"
    ]
    
    def _get_random_person(self) -> str:
        """Возвращает случайное описание персонажа"""
        return random.choice(self.PERSON_VARIANTS)
    
    def _extract_post_start(self, text: str, length: int = 100) -> str:
        """Извлекает начало поста (первые N символов) для отслеживания повторений"""
        # Убираем HTML теги для сравнения
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)
        return clean_text[:length].strip()
    
    def _extract_emoji_pattern(self, text: str) -> str:
        """Извлекает набор смайликов из поста (первые 200 символов)"""
        import re
        # Находим все эмодзи в первых 200 символах
        emojis = re.findall(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+', text[:200])
        # Сортируем для сравнения (одинаковые наборы в разном порядке = одинаковый паттерн)
        return ''.join(sorted(set(''.join(emojis))))
    
    def _get_unused_structure_index(self, available_structures: List[int], used_count: int = 10, slot: str = "") -> int:
        """Выбирает индекс структуры, которая не использовалась в последних N постах для данного слота"""
        # Если указан слот, проверяем структуры, использованные для этого слота
        slot_key = slot.lower() if slot else ""
        if slot_key and slot_key in self._used_slot_structure:
            slot_structures = self._used_slot_structure[slot_key]
            recent_slot_structures = slot_structures[-used_count:] if len(slot_structures) >= used_count else slot_structures
            
            # Находим структуры, которые не использовались для этого слота недавно
            unused_for_slot = [s for s in available_structures if s not in recent_slot_structures]
            
            if unused_for_slot:
                return random.choice(unused_for_slot)
        
        # Если слот не указан или все структуры использовались для слота, проверяем общую историю
        if not self._used_structures:
            return random.choice(available_structures)
        
        recent_structures = self._used_structures[-used_count:] if len(self._used_structures) > used_count else self._used_structures
        unused_structures = [s for s in available_structures if s not in recent_structures]
        
        if unused_structures:
            return random.choice(unused_structures)
        else:
            return random.choice(available_structures)
    
    def _get_anti_repetition_instruction(self) -> str:
        """Генерирует инструкцию для AI, чтобы избежать повторений"""
        instructions = []
        
        # Информация о последних началах постов
        if len(self._used_starts) >= 3:
            recent_starts = self._used_starts[-5:]  # Последние 5 начал
            instructions.append(f"⚠️ НЕ ИСПОЛЬЗУЙ похожие начала, как в последних постах:")
            for i, start in enumerate(recent_starts[-3:], 1):  # Показываем последние 3
                instructions.append(f"   {i}. '{start[:60]}...'")
            instructions.append("   Создай СОВЕРШЕННО ДРУГОЕ начало!")
        
        # Информация о последних наборах смайликов
        if len(self._used_emoji_patterns) >= 3:
            recent_emojis = self._used_emoji_patterns[-5:]  # Последние 5 наборов
            instructions.append(f"\n⚠️ НЕ ПОВТОРЯЙ наборы смайликов из последних постов!")
            instructions.append(f"   Используй ДРУГИЕ смайлики, не те же самые комбинации!")
        
        # СТРОГАЯ РОТАЦИЯ ФОРМАТОВ ССЫЛОК (критично!)
        self._link_format_counter += 1
        current_format = (self._link_format_counter % 14) + 1  # Циклически 1-14
        
        format_names = {
            1: "ГИПЕРССЫЛКА: <a href=\"URL\">Забрать бонус</a> — описание бонуса",
            2: "ЭМОДЗИ + URL: 👉 URL — описание бонуса",
            3: "URL + ТИРЕ: URL — описание бонуса",
            4: "СТРЕЛКА + URL: ➡️ URL\\nописание бонуса (с новой строки)",
            5: "ТЕКСТ + URL: описание бонуса — URL",
            6: "URL + НОВАЯ СТРОКА: URL\\nописание бонуса (с новой строки)",
            7: "ДВОЙНОЙ ЭМОДЗИ: 🔥🔥 URL — описание бонуса",
            8: "ЭМОДЗИ С ДВУХ СТОРОН: 👉 URL 👈\\nописание бонуса (с новой строки)",
            9: "ЖИРНЫЙ ТЕКСТ + URL: <b>ОПИСАНИЕ БОНУСА</b>\\nURL (с новой строки)",
            10: "БЛОЧНЫЙ ФОРМАТ: ┃ URL\\n┃ описание бонуса (вертикальная черта)",
            11: "ВОПРОС + URL: ❓ Хочешь описание бонуса?\\nURL (с новой строки)",
            12: "КАПСЛОК + ЭМОДЗИ: 🎁 URL — ОПИСАНИЕ БОНУСА (капслок для описания)",
            13: "ЦИТАТА + URL: <blockquote>описание бонуса</blockquote>\\nURL (с новой строки)",
            14: "НУМЕРАЦИЯ + URL: 1️⃣ URL\\nописание бонуса (с новой строки)"
        }
        
        instructions.append(f"\n🔗 КРИТИЧНО: ИСПОЛЬЗУЙ СТРОГО ФОРМАТ #{current_format}!")
        instructions.append(f"⚠️ Формат: {format_names[current_format]}")
        instructions.append(f"⚠️ НЕ используй другие форматы — только #{current_format}!")
        instructions.append(f"⚠️ Используй ТОЛЬКО этот формат #{current_format} для ссылки!")
        
        if instructions:
            return "\n\n" + "\n".join(instructions) + "\n"
        return ""
    
    def _format_bonus_link(self, url: str, bonus_desc: str) -> str:
        """
        Форматирует ссылку с описанием бонуса в разных стилях.
        
        Варианты:
        1) https://url - описание бонуса
        2) https://url\nописание бонуса  
        3) <a href="url">описание</a> (гиперссылка)
        4) описание бонуса - https://url
        5) 👉 https://url - описание
        6) ➡️ https://url\nописание
        """
        link_format = random.choice(self.LINK_FORMATS)
        
        # НЕ заменяем бонус пользователя - используем как есть
        # AI сам парафразирует бонус в промпте
        
        if link_format == "url_dash_text":
            # https://url - описание бонуса
            return f"{url} - {bonus_desc}"
        
        elif link_format == "url_newline_text":
            # https://url
            # описание бонуса
            return f"{url}\n{bonus_desc}"
        
        elif link_format == "hyperlink":
            # <a href="url">описание</a>
            # Короткий текст для гиперссылки (ITALIANO)
            short_texts = [
                "🔥 ¡Reclama tu bono!", "👉 Obtener", "💰 Activar bono", 
                "🎁 ¡Reclamar regalo!", "🎰 Jugar con bono", "⚡ ¡Obtener ahora!"
            ]
            return f'<a href="{url}">{random.choice(short_texts)}</a> — {bonus_desc}'
        
        elif link_format == "text_dash_url":
            # описание бонуса - https://url
            return f"{bonus_desc} — {url}"
        
        elif link_format == "emoji_url_text":
            # 👉 https://url - описание
            emojis = ["👉", "🔥", "💰", "🎁", "⚡", "🎯"]
            return f"{random.choice(emojis)} {url} - {bonus_desc}"
        
        elif link_format == "arrow_url_text":
            # ➡️ https://url
            # описание
            arrows = ["➡️", "▶️", "👇", "⬇️"]
            return f"{random.choice(arrows)} {url}\n{bonus_desc}"
        
        else:
            return f"{url} - {bonus_desc}"
    
    def _postprocess_text(self, text: str, slot_name: str = "") -> str:
        """
        Постобработка сгенерированного текста:
        - Замена бэктиков на HTML <code>
        - Замена Markdown на HTML
        - Форматирование названия слота
        """
        import re
        
        # 1. Замена бэктиков на <code>
        # `текст` → <code>текст</code>
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # 2. Замена Markdown жирного на HTML
        # **текст** → <b>текст</b>
        text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
        
        # 3. Замена Markdown курсива на HTML
        # *текст* или _текст_ → <i>текст</i>
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'<i>\1</i>', text)
        
        # 4. Замена Markdown ссылок на HTML
        # [текст](url) → <a href="url">текст</a>
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        
        # 5. Форматирование названия слота (Title Case + жирный)
        if slot_name:
            slot_title = slot_name.title()  # Title Case
            # Заменяем все варианты написания слота на правильный
            patterns = [
                slot_name,                    # оригинал (le viking)
                slot_name.lower(),            # нижний регистр
                slot_name.upper(),            # ВЕРХНИЙ РЕГИСТР
                slot_name.title(),            # Title Case
            ]
            for pattern in patterns:
                if pattern in text:
                    # Если слот уже в <b>, не оборачиваем повторно
                    if f'<b>{pattern}</b>' not in text and f'<b>{slot_title}</b>' not in text:
                        text = text.replace(pattern, f'<b>{slot_title}</b>')
                    else:
                        text = text.replace(pattern, slot_title)
        
        # 6. СЛУЧАЙНО убираем .0 из целых чисел (50/50 для разнообразия)
        # Иногда: 800.0₽ → 800₽, иногда оставляем как 800.0₽
        if random.choice([True, False]):
            text = re.sub(r'(\d)\.0([₽\s,])', r'\1\2', text)
            text = re.sub(r'(\d)\.0</code>', r'\1</code>', text)
            text = re.sub(r'(\d)\.0</b>', r'\1</b>', text)
        
        return text
    
    def _filter_non_russian(self, text: str) -> str:
        """
        Удаляет не-русские символы (китайские, украинские и т.д.).
        
        ОСТАВЛЯЕТ:
        - Русские буквы (кириллица)
        - Английские буквы (для названий слотов, URL)
        - Цифры, знаки препинания, пробелы
        - HTML-теги
        - Эмодзи
        
        УДАЛЯЕТ:
        - Китайские/японские/корейские иероглифы
        - Украинские специфические буквы (заменяет на русские)
        """
        import re
        
        # Удаляем китайские/японские/корейские иероглифы
        text = re.sub(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+', '', text)
        
        # Заменяем украинские буквы на русские эквиваленты
        # НЕ трогаем английские буквы — они нужны для слотов и URL!
        ukrainian_to_russian = {
            'і': 'и', 'І': 'И',  # украинская i
            'ї': 'и', 'Ї': 'И',  # украинская yi
            'є': 'е', 'Є': 'Е',  # украинская ye
            'ґ': 'г', 'Ґ': 'Г',  # украинская g
        }
        for ukr, rus in ukrainian_to_russian.items():
            text = text.replace(ukr, rus)
        
        # Фиксим конкретные известные баги моделей
        text = text.replace('Выхид', 'Выход')
        text = text.replace('выхид', 'выход')
        text = text.replace('Выхід', 'Выход')
        text = text.replace('выхід', 'выход')
        
        return text
    
    def _remove_chat_mentions(self, text: str) -> str:
        """
        Удаляет/заменяет упоминания чата, которые AI иногда всё равно вставляет.
        """
        import re
        
        # Заменяем фразы с "чат" на нейтральные
        replacements = [
            (r'[Сс]ижу в чате', 'Смотрю видео'),
            (r'[Вв] чате', ''),
            (r'[Ии]з чата', ''),
            (r'[Нн]аписал в чат', 'подумал'),
            (r'[Чч]ат взорвался', 'это было невероятно'),
            (r'[Чч]ат орал', 'это было невероятно'),
            (r'[Оо]рал чат', 'это было невероятно'),
            (r'[Чч]ат в экстазе', 'это было невероятно'),
            (r'[Зз]рители', 'все'),
            (r'[Пп]одписчики', 'все'),
            (r'[Вв] комментах', ''),
            (r'[Кк]омменты', ''),
            # Замены "стрим" удалены - оставляем как есть
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        
        # Удаляем двойные пробелы после замен
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n +', '\n', text)
        
        return text
    
    def _filter_ai_responses(self, text: str) -> str:
        """
        Удаляет типичные фразы-ответы AI, которые иногда попадают в начало поста.
        
        УДАЛЯЕТ:
        - "Aquí te va...", "Aquí tienes...", "Claro, aquí..."
        - "Por supuesto...", "Here is...", "Listo, aquí..."
        - "¡Claro!", "¡Por supuesto!"
        - Любые вводные фразы AI
        """
        import re
        
        # Фразы которые нужно удалить в начале текста
        ai_intro_patterns = [
            r'^¡?Aquí te va[:\.]?\s*',
            r'^¡?Aquí tienes[:\.]?\s*',
            r'^¡?Claro[,!]?\s*(?:aquí\s+)?',
            r'^¡?Por supuesto[,!]?\s*(?:aquí\s+)?',
            r'^¡?Listo[,!]?\s*(?:aquí\s+)?',
            r'^Here is[:\.]?\s*',
            r'^Here\'s[:\.]?\s*',
            r'^Te presento[:\.]?\s*',
            r'^Voy a[:\.]?\s*',
            r'^¡?Perfecto[,!]?\s*',
            r'^¡?Entendido[,!]?\s*',
            r'^¡?Ok[,!]?\s*',
            r'^¡?Muy bien[,!]?\s*',
            r'^¡?De acuerdo[,!]?\s*',
            r'^Il post[:\.]?\s*',
            r'^El post[:\.]?\s*',
            r'^Aquí está[:\.]?\s*',
            r'^¡?Excelente[,!]?\s*',
            r'^Sure[,!]?\s*',
            r'^Certainly[,!]?\s*',
        ]
        
        # Удаляем все вводные фразы AI
        for pattern in ai_intro_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Удаляем двойные пробелы и лишние переносы строк
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = text.strip()
        
        return text
    
    def _randomize_currency_format(self, text: str, video: VideoData) -> str:
        """
        Заменяет символы валюты в тексте на случайные форматы для разнообразия (ITALIANO).
        Например: 500$ → 500 dólares, 1000€ → 1000 euros
        """
        import re
        
        currency = video.currency.upper()
        
        # Определяем форматы для каждой валюты (итальянские)
        if currency == "USD":
            # Заменяем $ на случайный формат
            formats = ["$", " dólares", " USD"]
            # Находим все вхождения $ после чисел
            def replace_usd(match):
                return match.group(1) + random.choice(formats)
            text = re.sub(r'([\d\s,\.]+)\$', replace_usd, text)
            # Также заменяем $ перед числами
            text = re.sub(r'\$([\d\s,\.]+)', lambda m: random.choice(["$", ""]) + m.group(1) + random.choice(["", " dólares", " USD"]), text)
        elif currency == "EUR":
            # Заменяем € на случайный формат
            formats = ["€", " euros", " EUR"]
            def replace_eur(match):
                return match.group(1) + random.choice(formats)
            text = re.sub(r'([\d\s,\.]+)€', replace_eur, text)
        elif currency == "CLP":
            formats = ["$", " pesos chilenos", " CLP"]
            def replace_clp(match):
                return match.group(1) + random.choice(formats)
            text = re.sub(r'([\d\s,\.]+)\$', replace_clp, text)
        elif currency == "MXN":
            formats = ["$", " pesos mexicanos", " MXN"]
            def replace_mxn(match):
                return match.group(1) + random.choice(formats)
            text = re.sub(r'([\d\s,\.]+)\$', replace_mxn, text)
        elif currency == "ARS":
            formats = ["$", " pesos argentinos", " ARS"]
            def replace_ars(match):
                return match.group(1) + random.choice(formats)
            text = re.sub(r'([\d\s,\.]+)\$', replace_ars, text)
        elif currency == "COP":
            formats = ["$", " pesos colombianos", " COP"]
            def replace_cop(match):
                return match.group(1) + random.choice(formats)
            text = re.sub(r'([\d\s,\.]+)\$', replace_cop, text)
        
        return text
    
    def _remove_template_phrases(self, text: str) -> str:
        """
        Удаляет/заменяет шаблонные фразы на более оригинальные.
        """
        import re
        
        # Заменяем шаблонные фразы
        replacements = [
            (r'экран взорвался', 'результат впечатлил'),
            (r'взорвался экран', 'результат впечатлил'),
            (r'мурашки по коже', 'это впечатляет'),
            (r'мурашки по телу', 'это впечатляет'),
            (r'чашка кофе', 'небольшая сумма'),
            (r'дешевле чашки кофе', 'небольшая сумма'),
            (r'заварил кофе', 'начал сессию'),
            (r'\bя играю\b', 'игрок играет'),
            (r'\bя кручу\b', 'игрок крутит'),
            (r'\bя зашёл\b', 'игрок зашёл'),
            (r'\bя зашел\b', 'игрок зашёл'),
            (r'\bя поставил\b', 'игрок поставил'),
            (r'\bя выиграл\b', 'игрок выиграл'),
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Удаляем указания времени
        time_patterns = [
            r'\bсегодня\b',
            r'\bвчера\b',
            r'\bзавтра\b',
            r'\bутром\b',
            r'\bднём\b',
            r'\bднем\b',
            r'\bвечером\b',
            r'\bночью\b',
            r'\bнедавно\b',
            r'\bтолько что\b',
            r'\bтолько сейчас\b',
        ]
        
        for pattern in time_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Удаляем двойные пробелы после замен
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n +', '\n', text)
        
        return text
    
    def _fix_broken_urls(self, text: str) -> str:
        """
        Исправляет сломанные/обрезанные URL в тексте.
        
        AI иногда "галлюцинирует" неполные ссылки вида:
        - https://cutt.    (обрезано)
        - https://cutt.ly/abc (неправильный код)
        - cutt.ly/xxx     (без https://)
        
        Заменяет все неполные cutt.ly ссылки на реальные из bonus_data.
        """
        import re
        
        if not self.bonus_data:
            return text
        
        url1 = self.bonus_data.url1
        
        # Паттерн для поиска ЛЮБЫХ cutt.ly ссылок (полных и неполных)
        # Включая обрезанные: https://cutt. или https://cutt.ly или https://cutt.ly/xxx
        cutt_pattern = r'https?://cutt\.(?:ly/?\S*|ly/?|[^\s<>\)\]\}]*)?'
        
        # Находим все совпадения
        matches = list(re.finditer(cutt_pattern, text, re.IGNORECASE))
        
        if len(matches) == 0:
            # Попробуем найти без https
            cutt_pattern_no_https = r'cutt\.ly/?\S*'
            matches = list(re.finditer(cutt_pattern_no_https, text, re.IGNORECASE))
        
        if len(matches) == 0:
            return text
        
        # Определяем какие ссылки правильные
        correct_urls = []
        if url1 and 'cutt.ly' in url1:
            correct_urls.append(url1)
        # Для итальянского сценария используется только url1
        
        # Если нет правильных cutt.ly ссылок — ничего не делаем
        if not correct_urls:
            return text
        
        # Заменяем все найденные ссылки
        result = text
        replacements_made = 0
        
        for i, match in enumerate(reversed(matches)):  # reversed чтобы не сбить индексы
            found_url = match.group(0)
            
            # Проверяем, не является ли это уже правильной ссылкой
            is_correct = any(correct_url == found_url or found_url.startswith(correct_url) for correct_url in correct_urls)
            
            if not is_correct:
                # Заменяем на правильную ссылку (чередуя если их несколько)
                correct_url_idx = (len(matches) - 1 - i) % len(correct_urls)
                replacement_url = correct_urls[correct_url_idx]
                
                # Если совпадение внутри href="..." — аккуратно заменяем
                start, end = match.start(), match.end()
                
                # Проверяем контекст (не ломаем HTML теги)
                result = result[:start] + replacement_url + result[end:]
                replacements_made += 1
                print(f"   🔧 Исправлена ссылка: '{found_url}' → '{replacement_url}'")
        
        if replacements_made > 0:
            print(f"   ✅ Исправлено {replacements_made} сломанных ссылок")
        
        return result
    
    def _smart_trim_text(self, text: str, max_length: int = 950) -> str:
        """
        Умное сокращение текста с СОХРАНЕНИЕМ ссылок и их описаний.
        
        Стратегия:
        1. Убираем лишние пустые строки (оставляем одну)
        2. Убираем избыточные эмодзи (оставляем 1-2 на строку)
        3. Сокращаем длинные абзацы БЕЗ ссылок
        4. НИКОГДА не трогаем строки с URL/href
        """
        import re
        
        if len(text) <= max_length:
            return text
        
        lines = text.split('\n')
        
        # 1. Определяем "защищённые" строки (со ссылками)
        protected_indices = set()
        for i, line in enumerate(lines):
            # Строка с URL или href защищена
            if 'http' in line.lower() or 'href=' in line.lower() or 'cutt.ly' in line.lower():
                protected_indices.add(i)
                # Также защищаем соседние строки (описание бонуса может быть на следующей)
                if i + 1 < len(lines):
                    protected_indices.add(i + 1)
                if i > 0:
                    protected_indices.add(i - 1)
        
        # 2. Убираем множественные пустые строки → одна
        new_lines = []
        prev_empty = False
        for i, line in enumerate(lines):
            is_empty = not line.strip()
            if is_empty:
                if not prev_empty:
                    new_lines.append(line)
                prev_empty = True
            else:
                new_lines.append(line)
                prev_empty = False
        lines = new_lines
        
        text = '\n'.join(lines)
        if len(text) <= max_length:
            return text
        
        # 3. Убираем избыточные эмодзи (более 3 подряд → 2)
        emoji_pattern = r'([\U0001F300-\U0001F9FF])\1{2,}'
        text = re.sub(emoji_pattern, r'\1\1', text)
        
        if len(text) <= max_length:
            return text
        
        # 4. Сокращаем "воду" в незащищённых строках
        lines = text.split('\n')
        water_phrases = [
            'Никто не ожидал!', 'Это просто нечто!', 'Тот случай, когда',
            'Вот это да!', 'Просто вдумайся', 'Это не шутка',
            'Красота, на которую можно смотреть вечно',
            'смотришь и думаешь', 'а потом экран', 'Представь себе',
            'Такие моменты цепляют', 'Такой заход запоминается',
            'Двигайся уверенно', 'удача сама подтянется',
        ]
        
        for i, line in enumerate(lines):
            if i in protected_indices:
                continue
            
            for phrase in water_phrases:
                if phrase.lower() in line.lower():
                    # Убираем фразу
                    line = re.sub(re.escape(phrase), '', line, flags=re.IGNORECASE)
                    lines[i] = line.strip()
        
        # Убираем пустые строки которые могли образоваться
        lines = [l for l in lines if l.strip() or l == '']
        
        text = '\n'.join(lines)
        
        # 5. Если всё ещё длинный — обрезаем НО сохраняем последние строки со ссылками
        if len(text) > max_length:
            # Находим последнюю ссылку
            last_link_pos = max(
                text.rfind('http'),
                text.rfind('href='),
                text.rfind('cutt.ly')
            )
            
            if last_link_pos > 0:
                # Сохраняем всё от последней ссылки до конца
                link_block = text[last_link_pos:]
                # Находим начало абзаца с ссылкой
                start_of_link_block = text.rfind('\n', 0, last_link_pos)
                if start_of_link_block > 0:
                    link_block = text[start_of_link_block:]
                
                # Сколько символов осталось для текста
                available_for_text = max_length - len(link_block) - 50  # запас
                
                if available_for_text > 200:
                    # Обрезаем текст до ссылок
                    text_before_links = text[:start_of_link_block] if start_of_link_block > 0 else text[:last_link_pos]
                    
                    # Обрезаем текст на последнем полном предложении
                    if len(text_before_links) > available_for_text:
                        cut_text = text_before_links[:available_for_text]
                        # Ищем последнюю точку, ! или ?
                        last_sentence = max(
                            cut_text.rfind('.'),
                            cut_text.rfind('!'),
                            cut_text.rfind('?'),
                            cut_text.rfind('\n')
                        )
                        if last_sentence > available_for_text // 2:
                            cut_text = cut_text[:last_sentence + 1]
                        
                        text = cut_text.strip() + '\n' + link_block.strip()
                    else:
                        text = text_before_links.strip() + '\n' + link_block.strip()
        
        return text.strip()
    
    async def generate_video_post(self, video: VideoData, index: int = 0) -> GeneratedPostAI:
        """
        Генерирует уникальный пост для видео.
        
        Args:
            video: Данные о видео
            index: Порядковый номер поста
            
        Returns:
            Сгенерированный пост
        """
        if not self.client:
            raise ValueError("OpenAI клиент не инициализирован. Проверьте API ключ.")
        
        if not self.bonus_data:
            raise ValueError("Данные о бонусах не установлены. Вызовите set_bonus_data().")

        max_regens = 10  # нормальные ретраи генерации (не завязаны на index)
        last_error = None

        for regen in range(1, max_regens + 1):
            try:
                # Определяем, есть ли реальный ник стримера в исходных данных
                has_real_streamer = video.has_streamer()

                # Выбираем промпт в зависимости от наличия стримера
                used_structure_index = -1
                if has_real_streamer:
                    available_indices = list(range(len(self.VIDEO_POST_PROMPTS)))
                    structure_index = self._get_unused_structure_index(available_indices, used_count=15, slot=video.slot)
                    prompt_template = self.VIDEO_POST_PROMPTS[structure_index]
                    streamer_name = video.streamer.strip()
                    used_structure_index = structure_index
                else:
                    available_indices = list(range(len(self.VIDEO_POST_PROMPTS_NO_STREAMER)))
                    structure_index = self._get_unused_structure_index(available_indices, used_count=10, slot=video.slot)
                    prompt_template = self.VIDEO_POST_PROMPTS_NO_STREAMER[structure_index]
                    streamer_name = ""
                    used_structure_index = structure_index + 1000

                # Генерируем уникальное описание бонуса
                bonus1_var = self._get_random_bonus_variation(self.bonus_data.bonus1_desc, is_bonus1=True)

                # Форматируем данные
                formatted_bet = video.get_formatted_bet()
                formatted_win = video.get_formatted_win()
                formatted_slot = video.get_formatted_slot()
                currency_format = video.get_random_currency_format()
                
                # Если слот пустой, используем общие формулировки
                slot_unknown = False
                if not formatted_slot or formatted_slot.strip() == "":
                    slot_mention = "una slot"  # Общее упоминание
                    slot_bold = "una slot"  # Для HTML
                    slot_unknown = True
                else:
                    slot_mention = formatted_slot
                    slot_bold = f"<b>{formatted_slot}</b>"

                base_prompt = prompt_template.format(
                    streamer=streamer_name if has_real_streamer else self._get_random_person(),
                    slot=slot_bold,  # Используем форматированный слот
                    slot_plain=slot_mention,  # Простое упоминание без HTML
                    bet=formatted_bet,
                    win=formatted_win,
                    currency=currency_format,
                    multiplier=video.multiplier,
                    url1=self.bonus_data.url1,
                    bonus1=bonus1_var,
                    person=self._get_random_person()
                )
                
                # КРИТИЧНО: Если слот неизвестен - ЗАПРЕЩАЕМ придумывать название!
                if slot_unknown:
                    base_prompt = base_prompt + "\n\n🚨🚨🚨 ¡MUY IMPORTANTE! 🚨🚨🚨\n" \
                                                "El nombre de la slot es DESCONOCIDO — ¡NO INVENTES un nombre específico como 'Gates of Olympus', 'Big Bass', etc.!\n" \
                                                "USA SOLO frases generales: 'una slot', 'un juego', 'la máquina', 'los rodillos'.\n" \
                                                "PROHIBIDO inventar nombres de slots que no están en los datos originales!"

                streamer_info = streamer_name if has_real_streamer else "без ника (общие формулировки)"
                print(f"🤖 Генерация поста #{index} (regen {regen}/{max_regens}) для {streamer_info} на {video.slot}...")
                print(f"   📊 Данные: bet={video.bet}, win={video.win}, multiplier={video.multiplier}")
                print(f"   🎰 Модель: {self.model}")
                sys.stdout.flush()

                # Ротация системных промптов + ВАЖНО: форматируем его реальными данными
                raw_system_prompt = self._get_system_prompt()
                
                # Добавляем примеры из существующих постов для обучения AI
                if self._existing_posts and len(self._existing_posts) > 0:
                    # Берем 3 случайных поста как примеры стиля
                    example_posts = random.sample(self._existing_posts, min(3, len(self._existing_posts)))
                    examples_text = "\n\n═══════════════════════════════════════════════════════════════\n"
                    examples_text += "📚 ПРИМЕРЫ ТВОИХ СУЩЕСТВУЮЩИХ ПОСТОВ (изучи стиль!):\n"
                    examples_text += "═══════════════════════════════════════════════════════════════\n\n"
                    for i, post in enumerate(example_posts, 1):
                        # Обрезаем до 500 символов
                        post_preview = post[:500] + "..." if len(post) > 500 else post
                        examples_text += f"ПРИМЕР {i}:\n{post_preview}\n\n"
                    examples_text += "⚠️ ВАЖНО: Изучи структуру, тон, форматирование этих постов.\n"
                    examples_text += "НО делай НОВЫЕ посты - НЕ копируй фразы и конструкции!\n"
                    examples_text += "═══════════════════════════════════════════════════════════════\n"
                    
                    raw_system_prompt = raw_system_prompt + examples_text
                
                # Для системного промпта используем slot_mention (без HTML) или "una slot" если пусто
                system_slot = slot_mention if formatted_slot and formatted_slot.strip() else "una slot"
                
                system_prompt = safe_format(
                    raw_system_prompt,
                    slot=system_slot,  # Используем простое упоминание без HTML
                    streamer=streamer_name,
                    url1=self.bonus_data.url1,
                    bonus1=bonus1_var,
                    currency=currency_format,
                    person=self._get_random_person()
                )

                anti_repetition = self._get_anti_repetition_instruction()
                length_note = ""
                text = None

                # Генерируем до 3 попыток внутри одной регенерации (короткий/длинный)
                for attempt in range(3):
                    print(f"   Попытка {attempt + 1}/3...")
                    sys.stdout.flush()

                    new_models = ["gpt-4.1-nano", "gpt-4.1-mini"]  # Модели требующие max_completion_tokens

                    if attempt == 0:
                        print(f"   📝 Промпт (первые 200 символов): {base_prompt[:200]}...")
                        sys.stdout.flush()

                    user_prompt = base_prompt + length_note + anti_repetition

                    api_params = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    }

                    if self.model in new_models:
                        api_params["max_completion_tokens"] = 8000
                    elif self.use_openrouter:
                        api_params["max_tokens"] = 5000  # Gemini модели ОЧЕНЬ болтливые - даем запас
                        api_params["temperature"] = 0.95
                    else:
                        api_params["max_tokens"] = 1500
                        api_params["temperature"] = 0.95
                        api_params["presence_penalty"] = 0.7
                        api_params["frequency_penalty"] = 0.6

                    response = await self.client.chat.completions.create(**api_params)

                    if not response or not response.choices:
                        if attempt == 2:
                            raise Exception("Пустой ответ от API после всех попыток")
                        await asyncio.sleep(1)
                        continue

                    choice = response.choices[0]
                    finish_reason = getattr(choice, "finish_reason", None)
                    print(f"   DEBUG: finish_reason = {finish_reason}")
                    sys.stdout.flush()

                    if finish_reason == "content_filter":
                        if attempt == 2:
                            raise Exception("Контент был отфильтрован после всех попыток")
                        await asyncio.sleep(1)
                        continue

                    message_content = getattr(getattr(choice, "message", None), "content", None)
                    if not message_content:
                        if attempt == 2:
                            raise Exception(f"Ответ без content после всех попыток. finish_reason={finish_reason}")
                        await asyncio.sleep(1)
                        continue

                    raw_text = message_content.strip()
                    for marker in ["[HOOK]", "[/HOOK]", "[FACTS]", "[/FACTS]",
                                   "[LINK1]", "[/LINK1]", "[LINK2]", "[/LINK2]",
                                   "[CTA]", "[/CTA]"]:
                        raw_text = raw_text.replace(marker, "")

                    candidate = raw_text.strip()
                    print(f"   Получен текст длиной {len(candidate)} символов")
                    sys.stdout.flush()

                    # Telegram лимит caption = 1024 символа
                    # С учётом HTML тегов целимся в 500-750 символов
                    if 500 <= len(candidate) <= 750:
                        text = candidate
                        break

                    if len(candidate) > 750:
                        # следующая попытка просим короче
                        length_note = "\n\n⚠️ Пост слишком длинный! Сократи до максимум 700 символов, но СОХРАНИ ссылку и её описание."
                        text = candidate  # на всякий случай запомним
                    elif len(candidate) < 500:
                        # пост слишком короткий - просим длиннее
                        length_note = "\n\n⚠️ Пост слишком КОРОТКИЙ! Добавь больше деталей, эмоций, описания. Минимум 550 символов!"
                        text = candidate
                        continue

                    # слишком короткий - эта ветка больше не должна срабатывать т.к. мы обрабатываем это выше
                    length_note = "\n\n⚠️ Пост слишком короткий! Добавь больше деталей, эмоций, описания. Минимум 650 символов!"
                    text = candidate

                if text is None or len(text) < 300:
                    raise Exception("Не удалось получить валидный текст от API")

                # Постобработка
                text = self._filter_ai_responses(text)  # Убираем ответы AI типа "Aquí tienes..."
                text = self._postprocess_text(text, video.slot)
                text = self._fix_broken_urls(text)
                # _filter_non_russian НЕ используем для итальянского - она для русского
                text = self._remove_chat_mentions(text)
                text = self._remove_template_phrases(text)
                text = self._randomize_currency_format(text, video)

                # Проверка упоминания стримера (если есть)
                if has_real_streamer and streamer_name:
                    streamer_mentions = text.lower().count(streamer_name.lower())
                    # Ник должен быть упомянут 1 раз (допустимо 2 раза максимум)
                    if streamer_mentions < 1:
                        print(f"   ⚠️ Ник '{streamer_name}' не найден, регенерируем...")
                        sys.stdout.flush()
                        continue
                    if streamer_mentions > 2:
                        print(f"   ⚠️ Ник '{streamer_name}' найден {streamer_mentions} раз(а), должно быть 1-2. Регенерируем...")
                        sys.stdout.flush()
                        continue
                    
                    # Проверка что ник начинается с заглавной буквы
                    if streamer_name[0].isupper():
                        # Ищем ник в тексте и проверяем капитализацию
                        import re
                        # Находим все вхождения ника (учитывая возможные склонения)
                        base_nick = streamer_name.lower()
                        # Ищем точные совпадения с учетом регистра
                        if base_nick in text.lower() and not streamer_name in text:
                            # Есть ник но в неправильном регистре
                            print(f"   ⚠️ Ник '{streamer_name}' найден в неправильном регистре. Регенерируем...")
                            sys.stdout.flush()
                            continue

                # Обрезка отключена - оставляем текст как есть

                # КРИТИЧЕСКАЯ ПРОВЕРКА: Ссылка должна присутствовать в финальном тексте!
                url1_present = self.bonus_data.url1 in text or (self.bonus_data.url1.replace('https://', '') in text)
                
                if not url1_present:
                    print(f"   ⚠️ Пропала ссылка url1. Регенерируем...")
                    sys.stdout.flush()
                    continue
                
                # КРИТИЧНАЯ ПРОВЕРКА: Текст должен быть ТОЛЬКО на РУССКОМ языке!
                # Список частых английских ФРАЗ которые недопустимы
                # ВАЖНО: Отдельные слова как "wild", "gate" НЕ проверяем - они могут быть в названиях слотов!
                english_phrases = [
                    'the abyss', 'answered the call', 'summoning circle',
                    'play it safe', 'bright lights', 'chose to dive', 'deep into',
                    'dark forces', 'aligned', 'full-blown ritual', 'pulled straight',
                    'from the void', 'sometimes', 'when you stare', 'into the darkness',
                    'hands you', 'fortune in return', 'outcome is terrifyingly good',
                    'claim the', 'massive', 'boost', 'activate', 'balance power',
                    'visuals shifted', 'eerie sounds peaked', 'screen locked',
                    'random luck', 'felt like', 'handshake with the supernatural'
                ]
                
                # Проверяем наличие английских фраз (НО ИСКЛЮЧАЕМ слова из названия слота и валюты!)
                text_lower = text.lower()
                slot_lower = video.slot.lower()
                found_english = []
                
                # Список допустимых английских слов (валюты, аббревиатуры)
                allowed_words = ['usd', 'eur', 'gbp', 'rub', 'fs', 'x', 'max', 'bet', 'win']
                
                for phrase in english_phrases:
                    phrase_lower = phrase.lower()
                    # Проверяем есть ли фраза в тексте
                    if phrase_lower in text_lower:
                        # Пропускаем если это допустимое слово
                        if phrase_lower in allowed_words:
                            continue
                        
                        # Проверяем - не является ли эта фраза частью названия слота
                        # Например: "wild" есть в "2 wild 2 die"
                        if phrase_lower not in slot_lower:
                            found_english.append(phrase)
                
                # Если нашли английские фразы (которые НЕ из названия слота) - регенерируем
                if found_english:
                    print(f"   ⚠️ Обнаружен английский текст: {', '.join(found_english[:3])}... Регенерируем с РУССКИМ языком!")
                    sys.stdout.flush()
                    continue

                # Уникальность среди уже сгенерированных
                if text in self._generated_posts:
                    print(f"   ⚠️ Дубликат текста для поста #{index}, регенерируем...")
                    sys.stdout.flush()
                    continue

                # Сохраняем
                self._generated_posts.append(text)

                # История структур
                if used_structure_index >= 0:
                    self._used_structures.append(used_structure_index)
                    if len(self._used_structures) > 50:
                        self._used_structures = self._used_structures[-50:]

                    slot_key = video.slot.lower()
                    if slot_key not in self._used_slot_structure:
                        self._used_slot_structure[slot_key] = []
                    self._used_slot_structure[slot_key].append(used_structure_index)
                    if len(self._used_slot_structure[slot_key]) > 20:
                        self._used_slot_structure[slot_key] = self._used_slot_structure[slot_key][-20:]

                post_start = self._extract_post_start(text, length=100)
                self._used_starts.append(post_start)
                if len(self._used_starts) > 30:
                    self._used_starts = self._used_starts[-30:]

                emoji_pattern = self._extract_emoji_pattern(text)
                if emoji_pattern:
                    self._used_emoji_patterns.append(emoji_pattern)
                    if len(self._used_emoji_patterns) > 30:
                        self._used_emoji_patterns = self._used_emoji_patterns[-30:]

                print(f"   ✅ Пост #{index} готов (длина: {len(text)})")
                sys.stdout.flush()

                return GeneratedPostAI(
                    index=index,
                    media_type="video",
                    text=text,
                    streamer=video.streamer,
                    slot=video.slot,
                    bet=video.bet,
                    win=video.win
                )

            except Exception as e:
                last_error = e
                print(f"❌ Ошибка генерации поста #{index} (regen {regen}/{max_regens}): {e}")
                sys.stdout.flush()
                await asyncio.sleep(0.5)
                continue

        raise Exception(f"Не удалось сгенерировать пост после {max_regens} попыток: {last_error}")
    
    async def generate_image_post(self, index: int = 0) -> GeneratedPostAI:
        """
        Генерирует уникальный пост для картинки (бонусы).
        
        Args:
            index: Порядковый номер поста
            
        Returns:
            Сгенерированный пост
        """
        if not self.client:
            raise ValueError("OpenAI клиент не инициализирован.")
        
        if not self.bonus_data:
            raise ValueError("Данные о бонусах не установлены.")

        max_regens = 5  # для image постов достаточно 5 попыток
        last_error = None

        for regen in range(1, max_regens + 1):
            try:
                # Выбираем случайный промпт
                prompt_template = random.choice(self.IMAGE_POST_PROMPTS)
                
                # Генерируем уникальное описание бонуса
                bonus1_var = self._get_random_bonus_variation(self.bonus_data.bonus1_desc, is_bonus1=True)
                
                prompt = prompt_template.format(
                    url1=self.bonus_data.url1,
                    bonus1=bonus1_var
                )
                
                # Для новых моделей используется max_completion_tokens и НЕ поддерживаются penalty и temperature
                # Для старых - max_tokens + все параметры
                new_models = ["gpt-4.1-nano", "gpt-4.1-mini"]  # Модели требующие max_completion_tokens

                # Ротация системных промптов для разнообразия стилей
                raw_system_prompt = self._get_system_prompt()
                system_prompt = safe_format(
                    raw_system_prompt,
                    slot="",
                    streamer="",
                    url1=self.bonus_data.url1,
                    bonus1=bonus1_var,
                    currency="",
                    person=self._get_random_person()
                )

                api_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                }
                
                if self.model in new_models:
                    api_params["max_completion_tokens"] = 2000
                elif self.use_openrouter:
                    # OpenRouter - больше токенов для reasoning моделей
                    api_params["max_tokens"] = 4000
                    api_params["temperature"] = 0.95
                else:
                    api_params["max_tokens"] = 600
                    api_params["temperature"] = 0.95
                    api_params["presence_penalty"] = 0.7
                    api_params["frequency_penalty"] = 0.6
                
                response = await self.client.chat.completions.create(**api_params)
                
                raw_text = response.choices[0].message.content.strip()
                
                # ═══════════════════════════════════════════════════════════════
                # ПОСТОБРАБОТКА: Парсинг блоков + Перемешивание + Форматирование
                # ═══════════════════════════════════════════════════════════════
                
                # 1. Парсим блоки
                blocks = self._parse_blocks(raw_text)
                
                if blocks:
                    # 2. Выбираем рандомную структуру (для картинок - более короткие)
                    short_structures = [s for s in self.STRUCTURE_TEMPLATES if len(s) <= 4]
                    structure = random.choice(short_structures) if short_structures else random.choice(self.STRUCTURE_TEMPLATES)
                    
                    # 3. Собираем пост по структуре
                    text = self._assemble_post(blocks, structure)
                    
                    print(f"🔀 Пост-картинка #{index} (regen {regen}/{max_regens}): структура {' → '.join(structure)}")
                else:
                    text = raw_text
                    for marker in ["[HOOK]", "[/HOOK]", "[FACTS]", "[/FACTS]", 
                                  "[LINK1]", "[/LINK1]", "[LINK2]", "[/LINK2]",
                                  "[CTA]", "[/CTA]"]:
                        text = text.replace(marker, "")
                    text = text.strip()
                
                # 4. Форматирование уже применено AI (HTML теги в промпте)
                # НЕ применяем дополнительное форматирование чтобы не ломать HTML
                
                # 4.5. Исправляем сломанные/обрезанные ссылки
                text = self._fix_broken_urls(text)
                
                # 4.6. Фильтруем не-русские символы
                text = self._filter_non_russian(text)
                
                # 4.7. Удаляем упоминания чата
                text = self._remove_chat_mentions(text)
                
                # 4.8. Проверяем слово "casino" (единственное запрещенное)
                if "casino" in text.lower():
                    print(f"   ⚠️ Image post contiene palabra 'casino', regenerando...")
                    sys.stdout.flush()
                    continue
                
                # ВАЖНО: НЕ ОБРЕЗАЕМ текст! Пользователь запретил обрезку.
                # AI должен сам создавать посты оптимальной длины согласно промпту.
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: Ссылка должна присутствовать в финальном тексте!
                url1_present = self.bonus_data.url1 in text or (self.bonus_data.url1.replace('https://', '') in text)
                
                if not url1_present:
                    print(f"   ⚠️ Image пост: Пропала ссылка url1. Регенерируем...")
                    sys.stdout.flush()
                    continue
                
                # Проверка уникальности
                if text in self._generated_posts:
                    print(f"   ⚠️ Дубликат текста для image поста #{index}, регенерируем...")
                    continue
                
                self._generated_posts.append(text)
                
                return GeneratedPostAI(
                    index=index,
                    media_type="image",
                    text=text
                )

            except Exception as e:
                last_error = e
                print(f"❌ Ошибка генерации image поста #{index} (regen {regen}/{max_regens}): {e}")
                await asyncio.sleep(0.5)
                continue
        
        # Если все попытки провалились - возвращаем fallback
        print(f"⚠️ Не удалось сгенерировать image пост после {max_regens} попыток, используем fallback")
        fallback_text = f"""🎁 Бонусы дня!

{self.bonus_data.bonus1_desc}: {self.bonus_data.url1}"""
        
        return GeneratedPostAI(
            index=index,
            media_type="image",
            text=fallback_text
        )
    
    async def generate_all_posts(
        self, 
        videos: List[VideoData], 
        image_count: int = 0,
        progress_callback=None
    ) -> List[GeneratedPostAI]:
        """
        Генерирует все посты с сохранением промежуточных результатов.
        
        Args:
            videos: Список данных о видео
            image_count: Количество постов с картинками
            progress_callback: async функция(current, total) для отчёта о прогрессе
            
        Returns:
            Список сгенерированных постов
            
        Note:
            При ошибке возвращает частичные результаты вместо Exception!
        """
        posts = []
        total = len(videos) + image_count
        current = 0
        last_error = None
        
        # Генерируем посты для видео
        for i, video in enumerate(videos):
            try:
                post = await self.generate_video_post(video, current)
                posts.append(post)
                current += 1
                
                if progress_callback:
                    await progress_callback(current, total)
                
                # Небольшая задержка чтобы не перегружать API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                last_error = e
                print(f"❌ Критическая ошибка при генерации video поста #{current}: {e}")
                print(f"⚠️ СОХРАНЯЕМ {len(posts)} уже сгенерированных постов!")
                # НЕ ВЫБРАСЫВАЕМ EXCEPTION - возвращаем частичные результаты!
                break
        
        # Генерируем посты для картинок (только если нет критической ошибки)
        if last_error is None:
            for i in range(image_count):
                try:
                    post = await self.generate_image_post(current)
                    posts.append(post)
                    current += 1
                    
                    if progress_callback:
                        await progress_callback(current, total)
                    
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    last_error = e
                    print(f"❌ Критическая ошибка при генерации image поста #{current}: {e}")
                    print(f"⚠️ СОХРАНЯЕМ {len(posts)} уже сгенерированных постов!")
                    break
        
        # ОТКЛЮЧЕНО: Перемешивание постов
        # Комментарий: Раньше посты перемешивались для разнообразия,
        # но это нарушало порядок из исходников.
        # Теперь посты публикуются в том же порядке, что и видео.
        # random.shuffle(posts)
        
        # Индексы уже правильные (заданы при генерации)
        # Обновляем только если нужно
        for i, post in enumerate(posts):
            if post.index != i:
                post.index = i
        
        # КРИТИЧНО: Если были сгенерированы хотя бы некоторые посты - возвращаем их!
        if len(posts) > 0:
            if last_error:
                print(f"⚠️ Генерация прервана после {len(posts)}/{total} постов из-за ошибки: {last_error}")
                print(f"✅ Возвращаем {len(posts)} успешно сгенерированных постов")
            return posts
        
        # Если вообще ничего не сгенерировано - выбрасываем ошибку
        if last_error:
            raise last_error
        
        return posts
    
    def reset(self):
        """Сбрасывает кэш сгенерированных постов и историю повторений"""
        self._generated_posts.clear()
        self._used_starts.clear()
        self._used_emoji_patterns.clear()
        self._used_structures.clear()
        self._prompt_counter = 0
    
    @staticmethod
    def get_openrouter_models() -> Dict[str, Dict]:
        """Возвращает доступные модели OpenRouter"""
        return OPENROUTER_MODELS.copy()
    
    @staticmethod
    def get_openrouter_model_id(model_key: str) -> Optional[str]:
        """Возвращает ID модели для OpenRouter API"""
        model = OPENROUTER_MODELS.get(model_key)
        return model['id'] if model else None
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ПРОВЕРКА УНИКАЛЬНОСТИ ПОСТОВ (Сторожевой AI)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    UNIQUENESS_CHECK_MODELS = {
        "flash": {
            "id": "google/gemini-2.0-flash-001",
            "name": "Gemini 2.0 Flash",
            "price_approx": "~0.02₽",
            "quality": "⚡ Быстрая"
        },
        "gpt4o-mini": {
            "id": "openai/gpt-4o-mini",
            "name": "GPT-4o Mini",
            "price_approx": "~0.05₽",
            "quality": "👍 Хорошая"
        },
        "gemini3-pro": {
            "id": "google/gemini-3-pro-preview",
            "name": "Gemini 3 Pro",
            "price_approx": "~2₽",
            "quality": "⭐ Отличная"
        },
        "claude-sonnet": {
            "id": "anthropic/claude-sonnet-4",
            "name": "Claude Sonnet 4",
            "price_approx": "~5₽",
            "quality": "💎 Лучшая"
        }
    }
    
    UNIQUENESS_CHECK_PROMPT = """Sei un esperto nella verifica dell'unicità dei contenuti per Telegram.

Ti vengono dati {count} post. Il tuo compito è trovare post SIMILI.

CRITERI DI SOMIGLIANZA (se almeno 1 coincide - è un duplicato):
1. Inizio identico (le prime 5-10 parole coincidono o sono molto simili nel significato)
2. Struttura identica (entrambi iniziano con domanda / entrambi con esclamazione / entrambi con numero)
3. Frasi ripetute (3+ parole consecutive appaiono in entrambi i post)
4. Significato simile (descrivono la stessa cosa con parole diverse, stessa "storia")
5. Pattern emoji identici (entrambi iniziano con stessi emoji, entrambi finiscono uguale)
6. ELEMENTI TEMPLATE (questo è CRITICO!):
   - "PULSANTE №1", "PULSANTE №2" o marcatori simili
   - Separatori identici (—•—🍉🔥🍓—•—, ◈◈◈, ~~~)
   - Designazioni identiche dei link ("👇 primo 👇", "👇 secondo 👇")
   - Struttura ripetuta di posizionamento dei link (entrambi all'inizio/entrambi alla fine/entrambi tra paragrafi)

POST PER L'ANALISI:
{posts_json}

RISPONDI RIGOROSAMENTE IN FORMATO JSON (senza markdown, senza ```json):
{{
  "duplicates": [
    {{"post1": 3, "post2": 17, "reason": "inizio identico: 'Guarda cosa sta succedendo'", "similarity": 85}},
    {{"post1": 8, "post2": 45, "reason": "ripetizione di frase: 'il risultato è semplicemente esploso'", "similarity": 70}}
  ],
  "warnings": [
    {{"post": 5, "issue": "post troppo corto"}},
    {{"post": 12, "issue": "senza invito all'azione"}}
  ],
  "total_unique": 78,
  "total_duplicates": 2,
  "summary": "Trovate 2 coppie di post simili su 80. Consiglio di rigenerare i post #17 e #45."
}}

Se TUTTI i post sono unici:
{{
  "duplicates": [],
  "warnings": [],
  "total_unique": {count},
  "total_duplicates": 0,
  "summary": "Tutti i {count} post sono unici! Ottimo lavoro."
}}

IMPORTANTE: 
- Verifica TUTTE le coppie di post
- Considera i post per UNA slot - tendono ad essere più simili
- similarity - percentuale di somiglianza (50-100)
- Rispondi SOLO JSON, senza spiegazioni"""

    async def check_posts_uniqueness(
        self, 
        posts: List[str], 
        slots: List[str],
        model: str = "flash",
        hybrid_recheck: bool = False
    ) -> Dict:
        """
        Проверяет уникальность сгенерированных постов через AI.
        
        Args:
            posts: Список текстов постов
            slots: Список названий слотов (для каждого поста)
            model: Ключ модели из UNIQUENESS_CHECK_MODELS
            hybrid_recheck: True если это перепроверка дублей через более умную модель
            
        Returns:
            {
                "is_unique": True/False,
                "duplicates": [...],
                "warnings": [...],
                "total_unique": int,
                "total_duplicates": int,
                "summary": str,
                "model_used": str
            }
        """
        import json
        import aiohttp
        
        # Получаем модель
        model_info = self.UNIQUENESS_CHECK_MODELS.get(model)
        if not model_info:
            model_info = self.UNIQUENESS_CHECK_MODELS["flash"]
        
        # Формируем данные для проверки (обрезаем до 400 символов на пост)
        posts_data = []
        for i, post in enumerate(posts):
            slot = slots[i] if i < len(slots) else "Неизвестно"
            posts_data.append({
                "id": i + 1,
                "slot": slot,
                "text": post[:400] + "..." if len(post) > 400 else post
            })
        
        # Формируем промпт
        prompt = self.UNIQUENESS_CHECK_PROMPT.format(
            count=len(posts),
            posts_json=json.dumps(posts_data, ensure_ascii=False, indent=2)
        )
        
        # Добавляем существующие посты если они есть
        if self._existing_posts and len(self._existing_posts) > 0:
            # Берем случайные 10 постов из базы для сравнения
            sample_existing = random.sample(self._existing_posts, min(10, len(self._existing_posts)))
            existing_preview = []
            for i, post in enumerate(sample_existing, 1):
                existing_preview.append({
                    "id": f"OLD_{i}",
                    "text": post[:300] + "..." if len(post) > 300 else post
                })
            
            prompt += f"\n\n════════════════════════════════════════════════════════════\n"
            prompt += f"📚 СУЩЕСТВУЮЩИЕ ПОСТЫ (из базы {len(self._existing_posts)} постов):\n"
            prompt += f"════════════════════════════════════════════════════════════\n"
            prompt += json.dumps(existing_preview, ensure_ascii=False, indent=2)
            prompt += f"\n\n⚠️ ВАЖНО: Проверь также что НОВЫЕ посты НЕ ПОХОЖИ на СУЩЕСТВУЮЩИЕ!\n"
            prompt += f"Если новый пост похож на существующий - это КРИТИЧЕСКИЙ дубль!\n"

        # Uniqueness-check всегда идёт в OpenRouter → нужен именно OpenRouter ключ
        openrouter_key = self.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            return {
                "is_unique": None,
                "error": "Не найден OPENROUTER_API_KEY (нужен для uniqueness-check).",
                "model_used": model_info['name']
            }

        try:
            # Вызываем OpenRouter API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://t.me/ninja_video_bot",
                    "X-Title": "NinjaVideoBot Uniqueness Check"
                }
                
                payload = {
                    "model": model_info["id"],
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,  # Низкая температура для точности
                    "max_tokens": 16000  # Увеличено до 16000 для надежной проверки 80+ постов
                }
                
                async with session.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "is_unique": None,
                            "error": f"API ошибка: {response.status} - {error_text}",
                            "model_used": model_info["name"]
                        }
                    
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Сохраняем оригинальный ответ для отладки
                    original_content = content
                    
                    # Парсим JSON из ответа
                    # Убираем возможные markdown обертки
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    # Дополнительная очистка: убираем комментарии и trailing commas
                    import re
                    # Убираем однострочные комментарии //
                    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
                    # Убираем trailing commas перед } и ]
                    content = re.sub(r',(\s*[}\]])', r'\1', content)
                    
                    # КРИТИЧНО: Убираем невалидные управляющие символы внутри строк
                    # "Invalid control character" возникает когда \n, \t и т.д. не экранированы
                    # Заменяем непечатные символы на пробелы (кроме \n между элементами JSON)
                    def clean_json_strings(match):
                        """Очищаем содержимое JSON строк от управляющих символов"""
                        s = match.group(0)
                        # Заменяем неэкранированные управляющие символы
                        s = s.replace('\n', '\\n')
                        s = s.replace('\r', '\\r')
                        s = s.replace('\t', '\\t')
                        # Убираем другие управляющие символы (0x00-0x1F кроме уже обработанных)
                        s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', s)
                        return s
                    
                    # Находим все строки в JSON и очищаем их
                    content = re.sub(r'"(?:[^"\\]|\\.)*"', clean_json_strings, content)
                    
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError as e:
                        # Попытка починить оборванную строку
                        if "Unterminated string" in str(e):
                            # Находим позицию ошибки
                            error_pos = e.pos if hasattr(e, 'pos') else -1
                            if error_pos > 0:
                                # Обрезаем до последней валидной запятой или закрывающей скобки
                                # и пытаемся закрыть JSON
                                fixed_content = content[:error_pos]
                                # Убираем незавершенную строку
                                fixed_content = re.sub(r'"[^"]*$', '', fixed_content)
                                # Закрываем массивы и объекты
                                fixed_content = fixed_content.rstrip(',').rstrip()
                                # Добавляем закрывающие скобки
                                open_braces = fixed_content.count('{') - fixed_content.count('}')
                                open_brackets = fixed_content.count('[') - fixed_content.count(']')
                                fixed_content += ']' * open_brackets + '}' * open_braces
                                
                                try:
                                    result = json.loads(fixed_content)
                                    # Успешно починили! Добавляем warning
                                    if not isinstance(result, dict):
                                        result = {"duplicates": [], "warnings": []}
                                    result.setdefault("warnings", [])
                                    result["warnings"].append("⚠️ JSON был оборван, автоматически исправлено")
                                except json.JSONDecodeError:
                                    pass  # Продолжаем к следующему блоку обработки
                        # Пытаемся найти JSON в ответе
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', content)
                        if json_match:
                            try:
                                result = json.loads(json_match.group())
                            except json.JSONDecodeError:
                                # JSON всё равно невалидный - возвращаем ошибку
                                return {
                                    "is_unique": True,  # По умолчанию считаем уникальными
                                    "duplicates": [],
                                    "warnings": [],
                                    "total_unique": len(posts),
                                    "total_duplicates": 0,
                                    "summary": "⚠️ Проверка завершена с ошибкой парсинга JSON. Посты считаются уникальными по умолчанию.",
                                    "error": f"Ошибка парсинга JSON: {str(e)}. AI вернул невалидный JSON.",
                                    "model_used": model_info["name"],
                                    "raw_response": original_content[:1000],  # Увеличено до 1000 символов
                                    "error_details": {
                                        "error_type": type(e).__name__,
                                        "error_msg": str(e),
                                        "content_length": len(original_content)
                                    }
                                }
                        else:
                            return {
                                "is_unique": True,  # По умолчанию считаем уникальными
                                "duplicates": [],
                                "warnings": [],
                                "total_unique": len(posts),
                                "total_duplicates": 0,
                                "summary": "⚠️ Проверка завершена с ошибкой. Посты считаются уникальными по умолчанию.",
                                "error": f"Не удалось найти JSON в ответе AI: {content[:200]}",
                                "model_used": model_info["name"]
                            }
                    
                    # Добавляем мета-информацию
                    result["is_unique"] = len(result.get("duplicates", [])) == 0
                    result["model_used"] = model_info["name"]
                    result["model_key"] = model
                    
                    return result
                    
        except Exception as e:
            return {
                "is_unique": None,
                "error": f"Ошибка проверки: {str(e)}",
                "model_used": model_info["name"]
            }
    
    async def check_posts_uniqueness_hybrid(
        self, 
        posts: List[str], 
        slots: List[str]
    ) -> Dict:
        """
        Гибридная проверка: сначала быстрая (Flash), потом перепроверка дублей (Gemini 3 Pro).
        
        Returns:
            Результат проверки с подтверждёнными дублями
        """
        # Шаг 1: Быстрая проверка через Flash
        flash_result = await self.check_posts_uniqueness(posts, slots, model="flash")
        
        if flash_result.get("error"):
            return flash_result
        
        if flash_result.get("is_unique"):
            # Всё уникально по Flash
            flash_result["hybrid_mode"] = True
            flash_result["recheck_skipped"] = True
            return flash_result
        
        # Шаг 2: Есть подозрительные пары — перепроверяем через Gemini 3 Pro
        duplicates = flash_result.get("duplicates", [])
        if not duplicates:
            return flash_result
        
        # Собираем только подозрительные посты для перепроверки
        suspicious_ids = set()
        for dup in duplicates:
            suspicious_ids.add(dup["post1"])
            suspicious_ids.add(dup["post2"])
        
        # Создаём подмножество для перепроверки
        suspicious_posts = []
        suspicious_slots = []
        id_mapping = {}  # новый_id -> старый_id
        
        for i, (post, slot) in enumerate(zip(posts, slots)):
            if (i + 1) in suspicious_ids:
                id_mapping[len(suspicious_posts) + 1] = i + 1
                suspicious_posts.append(post)
                suspicious_slots.append(slot)
        
        # Перепроверяем через Gemini 3 Pro
        pro_result = await self.check_posts_uniqueness(
            suspicious_posts, 
            suspicious_slots, 
            model="gemini3-pro",
            hybrid_recheck=True
        )
        
        if pro_result.get("error"):
            # Если Pro не сработал, возвращаем результат Flash
            flash_result["hybrid_mode"] = True
            flash_result["recheck_failed"] = True
            return flash_result
        
        # Маппим ID обратно
        confirmed_duplicates = []
        for dup in pro_result.get("duplicates", []):
            confirmed_duplicates.append({
                "post1": id_mapping.get(dup["post1"], dup["post1"]),
                "post2": id_mapping.get(dup["post2"], dup["post2"]),
                "reason": dup["reason"],
                "similarity": dup["similarity"],
                "confirmed_by": "Gemini 3 Pro"
            })
        
        return {
            "is_unique": len(confirmed_duplicates) == 0,
            "duplicates": confirmed_duplicates,
            "warnings": flash_result.get("warnings", []),
            "total_unique": len(posts) - len(confirmed_duplicates),
            "total_duplicates": len(confirmed_duplicates),
            "summary": f"Гибридная проверка: Flash нашёл {len(duplicates)} подозрительных пар, Gemini 3 Pro подтвердил {len(confirmed_duplicates)}.",
            "hybrid_mode": True,
            "flash_found": len(duplicates),
            "pro_confirmed": len(confirmed_duplicates),
            "model_used": "Gemini Flash + Gemini 3 Pro"
        }


# Тестирование
if __name__ == "__main__":
    import asyncio
    
    async def test():
        generator = AIPostGenerator(model="gpt-4o-mini")
        
        generator.set_bonus_data(
            url1="https://example1.com",
            bonus1="100 FS",
            url2="https://example2.com", 
            bonus2="150% + 500 FS"
        )
        
        video = VideoData(
            streamer="Жека",
            slot="Gates of Olympus",
            bet=500,
            win=125000
        )
        
        print("Генерация тестового поста...")
        post = await generator.generate_video_post(video, 0)
        print(f"\n📝 Сгенерированный пост:\n{post.text}")
    
    # asyncio.run(test())
    print("AIPostGenerator готов к использованию!")

