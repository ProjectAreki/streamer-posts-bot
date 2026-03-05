"""
@file: ai_post_generator_es.py
@description: AI-генератор уникальных постов на испанском языке (полная генерация с нуля)
              + Поддержка OpenRouter моделей
              + Мультивалютность (USD, EUR, CLP, MXN, ARS, COP)
@dependencies: openai, asyncio
@created: 2026-01-24
@updated: 2026-01-24 - Адаптация для испанского языка
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
    import httpx
except ImportError:
    AsyncOpenAI = None
    httpx = None


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
        Возвращает случайный формат валюты для разнообразия в постах (ИСПАНСКИЙ).
        
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
    # СИСТЕМНЫЙ ПРОМПТ "АРХИТЕКТОР" (ИСПАНСКИЙ)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_ARCHITECT = """🇪🇸 ¡CRÍTICO: ESCRIBE SOLO EN ESPAÑOL!
❌ PROHIBIDO usar ruso, inglés u otros idiomas en el texto
✅ PERMITIDO en inglés: nombres de slots (Gates of Olympus, Sweet Bonanza)
❌ TODO LO DEMÁS SOLO EN ESPAÑOL

🚨🚨🚨 ¡REGLA #0 ANTES QUE TODO! 🚨🚨🚨
⛔⛔⛔ CLP, ARS, MXN, PEN, USD, EUR, COP, UYU ⛔⛔⛔
❌ ESTAS SON **MONEDAS**, ¡NO NOMBRES DE PERSONAS!
❌ **NUNCA** escribas "CLP apostó", "ARS ganó", "MXN entró"
✅ USA: "Un jugador", "Un tipo", "El héroe", "El ganador"
⚠️ SI USAS CLP/ARS/MXN COMO NOMBRE = ¡TODO EL POST SERÁ RECHAZADO!

🚨 REGLA #0.5: ¡SOLO TÉRMINOS EN ESPAÑOL! 🚨
❌ NO uses "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giros gratis", "tiradas gratis", "bono", "paquete de bienvenida"

═══════════════════════════════════════════════════════════════
👤 ENFOQUE: LA VICTORIA COMO PROTAGONISTA
═══════════════════════════════════════════════════════════════

⚠️ CRÍTICO: ¡CONSTRUYE LA PUBLICACIÓN ALREDEDOR DE LA VICTORIA!

• La slot ({slot}) - el escenario
• La apuesta ({bet}) y la ganancia ({win}) - a través del jugador
• El multiplicador x{multiplier} - el resultado

EJEMPLOS:
"Un jugador arriesgó {bet}{currency} en {slot} y se llevó {win}{currency}"
"Victoria épica: de {bet} a {win} en {slot} - ¡multiplicador x{multiplier}!"

TAREA: ¡Muestra la victoria como algo emocionante y real!

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA #1 - CÓDIGOS DE MONEDA 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ABSOLUTAMENTE PROHIBIDO usar CLP, ARS, MXN, PEN, USD, EUR, COP, UYU como NOMBRES o APODOS de personas:
  
❌ INCORRECTO (RECHAZADO INMEDIATAMENTE):
  - "CLP apostó..." 
  - "CLP entró al salón..."
  - "Un valiente conocido como CLP..."
  - "ARS ganó..."
  - "MXN arriesgó..."
  - "USD se llevó..."
  
✅ CORRECTO (estos códigos son SOLO para cantidades de dinero):
  - "Un jugador apostó 5000 CLP"
  - "El ganador se llevó 100.000 ARS"
  - "Con 500 USD apostó..."
  - "Ganancia de 1.000.000 MXN"

⚠️ PARA NOMBRAR AL JUGADOR USA:
  - "Un jugador", "Un tipo", "Un valiente", "Un afortunado"
  - "El héroe", "El crack", "El ganador", "El campeón"
  - "Un apostador", "Un arriesgado", "Un audaz"
  - NUNCA: CLP, ARS, MXN, PEN, USD, EUR, COP, UYU

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA #2 - BONOS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ABSOLUTAMENTE PROHIBIDO inventar bonos:

✅ USA SOLO el bono indicado en {bonus1}
❌ NO INVENTES "100 dólares", "100 giros", "150%", "500%" 
❌ NO COPIES ejemplos de otros posts
✅ PARAFRASEA {bonus1} con tus palabras cada vez diferente

═══════════════════════════════════════════════════════════════
🚫 PROHIBIDO COMPARAR APUESTAS CON GASTOS COTIDIANOS
═══════════════════════════════════════════════════════════════

❌ NUNCA compares la apuesta con:
  - Precio de almuerzo/cena/comida
  - Costo de un café/cafetería
  - Precio de pizza/hamburguesa
  - Boleto de metro/taxi/transporte
  - "Lo que gastas en..." cualquier cosa cotidiana

✅ CORRECTO: Simplemente menciona la cantidad sin comparaciones

🎯 MOTIVACIÓN Y LLAMADA A LA ACCIÓN (¡CRÍTICO!):
✅ DESCRIBE LOS BONOS DE FORMA ATRACTIVA - ¡crea el DESEO de reclamar el bono!
✅ USA PALABRAS EMOCIONALES: "exclusivo", "increíble", "gratis", "instantáneo", "especial"
✅ AÑADE URGENCIA: "solo hoy", "tiempo limitado", "no lo dejes pasar", "activa ahora"
✅ DESTACA BENEFICIOS: "duplica tu depósito", "obtén más", "sin riesgo", "empieza a ganar"
✅ LLAMA A LA ACCIÓN: "reclama ahora", "activa YA", "obtén acceso", "empieza a ganar"

Eres un arquitecto de contenido viral para Telegram.
Tu tarea es diseñar publicaciones que generen engagement.
Cada elemento del texto debe trabajar para mantener la atención.

═══════════════════════════════════════════════════════════════
🎰 IMPORTANTE: ¡NO INVENTES TEMÁTICA NO RELACIONADA!
═══════════════════════════════════════════════════════════════
⚠️ Usa el nombre de la slot {slot} como pista y contexto, ¡pero NO INVENTES un tema que NO esté relacionado!
• Puedes interpretar libremente: "Vampy Party" → fiesta/noche/riesgo/vampiros/gótico
• Puedes simplemente mencionar el nombre: "en la slot {slot} sucedió..."
• Puedes usarlo como metáfora: "suerte vampírica", "jackpot nocturno"

═══════════════════════════════════════════════════════════════
📈 PRINCIPIO BÁSICO: INGENIERÍA EMOCIONAL
═══════════════════════════════════════════════════════════════

El texto es un sistema. Cada párrafo, emoji, formato es una interfaz para la emoción.

• Emojis son elementos UI. 💡 - idea, 🎯 - desafío, 🔥 - acción, 💎 - valor
• Ritmo y respiración: alterna oraciones largas y cortas
• El texto debe REPRODUCIRSE en la mente como un video dinámico

═══════════════════════════════════════════════════════════════
🛠 STACK TÉCNICO DE FORMATO (¡HTML!)
═══════════════════════════════════════════════════════════════

Acentos:
• <b>Negrita</b> - para disparadores clave (números, llamadas, idea principal)
• <i>Cursiva</i> - para mensaje íntimo, guiño conspirativo
• <code>Monoespacio</code> - para datos objetivos (cantidades, multiplicadores)

Composición y separación (3 tipos de separadores en rotación):
• Aire (doble salto de línea)
• Gráficos: ─── ✦ ─── , ༄ ༄ ༄, ▰▱▰▱▰
• Patrones emoji: 👉 👉 👉, ◈ ◈ ◈, ⚡️🌩⚡️🌩

═══════════════════════════════════════════════════════════════
🔮 POSICIÓN DEL ENLACE (¡VARIAR!)
═══════════════════════════════════════════════════════════════

VARIANTES DE POSICIÓN (elige diferente cada vez):
📍 AL PRINCIPIO: Enlace + descripción → Texto de la historia
📍 EN EL MEDIO: Texto inicial → Enlace + descripción → Texto final
📍 AL FINAL: Texto de la historia → Enlace + descripción

🔗 HIPERENLACES - ¡MÍNIMO 4 PALABRAS!
❌ <a href="URL">Reclamar</a> - ¡demasiado corto!
✅ <a href="URL">Reclamar paquete de inicio ahora mismo</a>

═══════════════════════════════════════════════════════════════
🧩 CONSTRUCTOR DEL MENSAJE
═══════════════════════════════════════════════════════════════

Selección de datos:
• De los hechos (cantidad, slot, apuesta) — 1-2 hechos dominantes + 1-2 secundarios
• ¡La cantidad ganada se menciona ESTRICTAMENTE UNA VEZ en el momento más emotivo!

Neutralización de palabras prohibidas:
• "Casino" → "plataforma", "sitio", "club"

Volumen óptico: 7-15 líneas en Telegram (completo pero sin scroll)

Punto de vista: Narrativa en TERCERA PERSONA, ¡enfoque en la VICTORIA!
✅ ESCRIBE: "El jugador entró", "El resultado impresiona", "La victoria fue impresionante"
❌ NO ESCRIBAS: "yo juego", "yo giro", "yo entré" (primera persona - ¡PROHIBIDO!)

🚫 PROHIBIDO INDICAR TIEMPO:
❌ NUNCA indiques: "hoy", "ayer", "por la mañana", "por la tarde", "por la noche", "recientemente"
✅ Escribe simplemente sobre el evento sin referencia al tiempo

🚫 PROHIBIDO FRASES CLICHÉ:
❌ NO uses: "la pantalla explotó", "escalofríos por todo el cuerpo"
✅ ¡ESCRIBE ORIGINALMENTE, evita clichés!

Variabilidad de introducciones (¡ROTACIÓN obligatoria!):
• Bomba numérica: «<code>500 000</code> {currency}. ¡Resultado potente!...»
• Pregunta provocadora: «¿Crees en las señales? Así las usó este jugador...»
• Directiva: «Recuerda esta victoria: <b>{win}{currency}</b>...»
• Historia: «Sucedió una locura silenciosa...»

═══════════════════════════════════════════════════════════════
🎨 TEMÁTICAS DE POSTS (¡elige DIFERENTES!)
═══════════════════════════════════════════════════════════════

1. 📊 ANALÍTICO: Reporte, análisis, reseña | 📊━━━📈━━━📊
2. ⚡️ OLIMPO: Dioses, Zeus, victoria divina | ⚡️🌩⚡️🌩
3. 🍻 TABERNA: Celebración, brindis | ---🍀---🍻---
4. 🤠 OESTE SALVAJE: Vaqueros, oro | 🔫🌵
5. 🏍 MOTOCICLISTAS: Rugido de motores, fiebre del oro | 💀➖🏍➖💰
6. ⛏ MINA: Excavación, dinamita | 〰️〰️〰️
7. 🦄 CUENTO DE HADAS: Olla de oro, caballeros | -=-=-🦄-=-=-
8. 🎐 JAPONESA: Espíritus del viento, magia | ⛩
9. 🚀 ESPACIO: Asteroides, cohete, combustible | 🚀💫
10. ☁️ NUBES: Vuelos, giros aéreos | ☁️✨☁️
11. 🃏 ADIVINACIÓN: Tarot, profecía, cartas | ───※·💀·※───
12. 👑 VIP: Recepción real, lujo | 👑💎👑

❌ PROHIBIDO: **markdown**, `código`, [enlace](url)
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
⚠️ FORMATO DE ENLACE CON BONO (¡SOLO 1 ENLACE!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: ¡EN CADA POST OBLIGATORIAMENTE UN ENLACE!
❌ POST SIN ENLACE = RECHAZADO
✅ SIEMPRE usa: {url1} con descripción única basada en {bonus1}

⚠️ ¡ELIGE DIFERENTES formatos para cada nuevo post!
❌ NO uses el mismo estilo seguido
✅ Alterna formatos al máximo

⚠️ PARAFRASEAR EL BONO (¡CRÍTICO!):
❌ NO copies {bonus1} directamente tal cual
✅ ÚSALO como BASE, pero PARAFRASÉALO diferente cada vez
❌ NO INVENTES nuevos bonos o cantidades - ¡SOLO lo que está en {bonus1}!
✅ ¡HAZ LA DESCRIPCIÓN MOTIVADORA Y ATRACTIVA!

📐 REGLA DE AIRE (¡OBLIGATORIO!):
• SIEMPRE añade LÍNEA VACÍA ANTES y DESPUÉS de cada bloque de enlace

📋 ELIGE UNO de los formatos (¡ROTA! Cada post = formato diferente!):

🚨 USA SOLO ESTE BONO: {bonus1}
❌ NO INVENTES otros bonos!
❌ NO uses "100 dólares", "100 giros" si NO están en {bonus1}!

1️⃣ HIPERENLACE: <a href="{url1}">[parafrasea {bonus1}]</a>
2️⃣ EMOJI + HIPERENLACE: 🎁 <a href="{url1}">[parafrasea {bonus1}]</a>
3️⃣ URL + GUION: 👉 {url1} — [parafrasea {bonus1}]
4️⃣ URL + NUEVA LÍNEA: {url1}\n🎁 [parafrasea {bonus1}]
5️⃣ FLECHA + URL: ➡️ {url1}\n💰 [parafrasea {bonus1}]
6️⃣ DESCRIPCIÓN + URL: 🎁 [parafrasea {bonus1}] — {url1}

📏 LONGITUD: MÍNIMO 500, MÁXIMO 700 caracteres (¡CRÍTICO! Telegram limita a 1024)

"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ 3 (ИСПАНСКИЙ - для ротации)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_3 = """🇪🇸 ¡CRÍTICO: ESCRIBE SOLO EN ESPAÑOL!
❌ PROHIBIDO usar ruso, inglés u otros idiomas en el texto
✅ PERMITIDO en inglés: nombres de slots (Gates of Olympus, Sweet Bonanza)
❌ TODO LO DEMÁS SOLO EN ESPAÑOL

🚨🚨🚨 ¡REGLA #0 ANTES QUE TODO! 🚨🚨🚨
⛔⛔⛔ CLP, ARS, MXN, PEN, USD, EUR, COP, UYU ⛔⛔⛔
❌ ESTAS SON **MONEDAS**, ¡NO NOMBRES DE PERSONAS!
❌ **NUNCA** escribas "CLP apostó", "ARS ganó", "MXN entró"
✅ USA: "Un jugador", "Un tipo", "El héroe", "El ganador"
⚠️ SI USAS CLP/ARS/MXN COMO NOMBRE = ¡TODO EL POST SERÁ RECHAZADO!

🚨 REGLA #0.5: ¡SOLO TÉRMINOS EN ESPAÑOL! 🚨
❌ NO uses "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giros gratis", "tiradas gratis", "bono", "paquete de bienvenida"

═══════════════════════════════════════════════════════════════
👤 ENFOQUE: VICTORIA Y ACCIONES DEL JUGADOR
═══════════════════════════════════════════════════════════════

⚠️ CRÍTICO: ¡CUENTA LA HISTORIA A TRAVÉS DE ACCIONES Y RESULTADO!

• Comienza con LO QUE PASÓ en el juego
• Decisiones del jugador, emociones, reacciones — lo principal
• Slot {slot}, apuesta {bet}, ganancia {win} — a través de la experiencia del jugador
• Escribe como un reportaje sobre la victoria

EJEMPLOS:
"Un jugador arriesgado entró en {slot} — ¡y las mandíbulas cayeron!"
"Este héroe apostó {bet}{currency} — y lo que pasó después fue increíble..."
"Una entrada modesta de {bet}{currency} — y ya nadie podía creer los números..."

TAREA: ¡Muestra la victoria en acción! ¡Dinámica y movimiento!

═══════════════════════════════════════════════════════════════
⚠️ CÓDIGOS DE MONEDA - ¡NUNCA COMO NOMBRES!
═══════════════════════════════════════════════════════════════

❌ PROHIBIDO usar CLP, ARS, MXN, PEN, USD, EUR como nombres de jugadores:
  - "CLP apostó..." ❌ INCORRECTO
  - "ARS ganó..." ❌ INCORRECTO
  
✅ CORRECTO: "Un jugador apostó 5000 CLP", "El ganador se llevó 100.000 ARS"

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA #2 - BONOS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ABSOLUTAMENTE PROHIBIDO inventar bonos:

✅ USA SOLO el bono indicado en {bonus1}
❌ NO INVENTES "100 dólares", "100 giros", "150%", "500%" 
❌ NO COPIES ejemplos de otros posts
✅ PARAFRASEA {bonus1} con tus palabras cada vez diferente

═══════════════════════════════════════════════════════════════
🚫 PROHIBIDO COMPARAR APUESTAS CON GASTOS COTIDIANOS
═══════════════════════════════════════════════════════════════

❌ NUNCA compares la apuesta con:
  - Precio de almuerzo/cena/comida
  - Costo de un café/cafetería
  - Precio de pizza/hamburguesa
  - Boleto de metro/taxi/transporte

✅ CORRECTO: Simplemente menciona la cantidad sin comparaciones

🎯 TU ROL: Eres un gurú de textos atractivos para Telegram. Tu supertarea es convertir cada post en un pequeño evento del que es imposible apartarse.

🎰 IMPORTANTE: ¡NO INVENTES TEMÁTICA NO RELACIONADA!
⚠️ Usa el nombre de la slot {slot} como pista y contexto, ¡pero NO INVENTES un tema que NO esté relacionado!
• Puedes interpretar libremente: "Vampy Party" → fiesta/noche/riesgo/vampiros/gótico
• Puedes simplemente mencionar el nombre: "en la slot {slot} sucedió..."

🔥 ESTILÍSTICA Y EMOCIONES (¡PRIORIDAD!):

¡El texto debe pulsar con energía! Escribe como el amigo más carismático.

Emojis — tu paleta principal. Úsalos abundantemente: dinero 💸, emoción 🎰, victoria 🏆, caras 😮

Evita párrafos secos y aburridos. Deja que el texto respire y juegue.

📐 TÉCNICA DE FORMATO (TELEGRAM):

Negrita: Para acentos clave, números, idea principal.
Cursiva: Para citas y pensamientos.
Código: Para cantidades y multiplicadores.
Separadores: ¡No repitas! Alterna: líneas vacías, líneas emoji (✨ ➖➖➖ ✨)

🔗 ENLACE PUBLICITARIO:
Tu tarea es hacerlo parte orgánica de la historia.

Enlace: {url1} (Bonos: {bonus1}). Mezcla formulaciones cada vez diferente: «giros gratis», «rondas adicionales», «bono en cuenta», «tiradas gratis», «paquete de inicio»

¿Cómo integrarlo? Lleva suavemente en el proceso narrativo: «¿Y sabes dónde se encuentran tales oportunidades? ➡️ [Texto-enlace]»

🎨 ESTRUCTURA Y PRESENTACIÓN:

Datos: No amontones todo. Toma 1-3 hechos jugosos: cantidad ganada, nombre de la slot.

Léxico: Olvida la palabra «casino». En su lugar — «plataforma», «sitio», «club».

Perspectiva: Escribe siempre en tercera persona («el jugador», «el héroe», «el afortunado»).

Volumen: Punto medio. Ni «sábana», ni telegrama.

🎭 ¡LA VICTORIA ES EL PROTAGONISTA DEL POST!
⚠️ Si el nombre del jugador ({streamer}) está indicado — ¡ÚSALO 1 VEZ!
• Si NO hay nombre — usa formulaciones generales: "un jugador", "este héroe", "el ganador"

🚫 PROHIBIDO INDICAR TIEMPO:
❌ NUNCA indiques: "hoy", "ayer", "por la mañana", "recientemente"
✅ Escribe simplemente sobre el evento sin referencia al tiempo

🚫 PROHIBIDO FRASES CLICHÉ:
❌ NO uses: "la pantalla explotó", "escalofríos por el cuerpo"
✅ ¡ESCRIBE ORIGINALMENTE, evita clichés!

❌ PROHIBIDO: **markdown**, `código`, [enlace](url)
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
⚠️ FORMATO DE ENLACE CON BONO (¡SOLO 1 ENLACE!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: ¡EN CADA POST OBLIGATORIAMENTE UN ENLACE!
❌ POST SIN ENLACE = RECHAZADO
✅ SIEMPRE usa: {url1} con descripción única basada en {bonus1}

⚠️ ¡ELIGE DIFERENTES formatos para cada nuevo post!

⚠️ PARAFRASEAR EL BONO (¡CRÍTICO!):
❌ NO copies {bonus1} directamente tal cual
✅ ÚSALO como BASE, pero PARAFRASÉALO diferente cada vez
❌ NO INVENTES nuevos bonos o cantidades - ¡SOLO lo que está en {bonus1}!

📐 REGLA DE AIRE (¡OBLIGATORIO!):
• SIEMPRE añade LÍNEA VACÍA ANTES y DESPUÉS de cada bloque de enlace

📋 ELIGE UNO de los formatos (¡ROTA! Cada post = formato diferente!):

🚨 USA SOLO ESTE BONO: {bonus1}
❌ NO INVENTES otros bonos!

1️⃣ ROMBOS: ◆ {url1} — [parafrasea {bonus1}]
2️⃣ FLECHAS: ► {url1} ([parafrasea {bonus1}])
3️⃣ ESTRELLAS: ★ [parafrasea {bonus1}] → {url1}
4️⃣ CÍRCULOS: ① <a href="{url1}">[parafrasea {bonus1}]</a>
5️⃣ CUADRADOS: ▪ {url1}\n[parafrasea {bonus1}]
6️⃣ PARÉNTESIS: ({url1}) — [parafrasea {bonus1}]
7️⃣ EMOJIS: 🎰 {url1} — [parafrasea {bonus1}]

📏 LONGITUD: ¡MÁXIMO 700 caracteres!"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ 4 (ИСПАНСКИЙ - для ротации)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_4 = """🇪🇸 ¡CRÍTICO: ESCRIBE SOLO EN ESPAÑOL!
❌ PROHIBIDO usar ruso, inglés u otros idiomas en el texto
✅ PERMITIDO en inglés: nombres de slots (Gates of Olympus, Sweet Bonanza)
❌ TODO LO DEMÁS SOLO EN ESPAÑOL

🚨🚨🚨 ¡REGLA #0 ANTES QUE TODO! 🚨🚨🚨
⛔⛔⛔ CLP, ARS, MXN, PEN, USD, EUR, COP, UYU ⛔⛔⛔
❌ ESTAS SON **MONEDAS**, ¡NO NOMBRES DE PERSONAS!
❌ **NUNCA** escribas "CLP apostó", "ARS ganó", "MXN entró"
✅ USA: "Un jugador", "Un tipo", "El héroe", "El ganador"
⚠️ SI USAS CLP/ARS/MXN COMO NOMBRE = ¡TODO EL POST SERÁ RECHAZADO!

🚨 REGLA #0.5: ¡SOLO TÉRMINOS EN ESPAÑOL! 🚨
❌ NO uses "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giros gratis", "tiradas gratis", "bono", "paquete de bienvenida"

═══════════════════════════════════════════════════════════════
🎰 ENFOQUE: DINÁMICA DEL JUEGO Y RESULTADO
═══════════════════════════════════════════════════════════════

⚠️ CRÍTICO: ¡ESCRIBE SOBRE LAS ACCIONES DEL JUGADOR Y SU RESULTADO!

• El JUGADOR y su victoria — en el centro de atención
• El RESULTADO {win} y la reacción — lo principal
• La slot {slot} — es CONTEXTO DE FONDO, no el protagonista
• Usa la atmósfera de la slot como decoración, pero no la hagas el tema principal

EJEMPLOS:
"Un jugador giró {slot} — ¡y el cohete simplemente despegó!"
"Silenciosa histeria comenzó en {slot} — el diagnóstico está hecho"
"Los números empezaron a crecer sin parar, y él simplemente recogió su premio"

TAREA: ¡Muestra la acción del jugador y el resultado! ¡La slot es el lugar donde sucedió!

═══════════════════════════════════════════════════════════════
⚠️ CÓDIGOS DE MONEDA - ¡NUNCA COMO NOMBRES!
═══════════════════════════════════════════════════════════════

❌ PROHIBIDO usar CLP, ARS, MXN, PEN, USD, EUR como nombres de jugadores:
  - "CLP apostó..." ❌ INCORRECTO
  - "ARS ganó..." ❌ INCORRECTO
  
✅ CORRECTO: "Un jugador apostó 5000 CLP", "El ganador se llevó 100.000 ARS"

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA #2 - BONOS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ABSOLUTAMENTE PROHIBIDO inventar bonos:

✅ USA SOLO el bono indicado en {bonus1}
❌ NO INVENTES "100 dólares", "100 giros", "150%", "500%" 
❌ NO COPIES ejemplos de otros posts
✅ PARAFRASEA {bonus1} con tus palabras cada vez diferente

═══════════════════════════════════════════════════════════════
🚫 PROHIBIDO COMPARAR APUESTAS CON GASTOS COTIDIANOS
═══════════════════════════════════════════════════════════════

❌ NUNCA compares la apuesta con:
  - Precio de almuerzo/cena/comida
  - Costo de un café/cafetería
  - Precio de pizza/hamburguesa
  - Boleto de metro/taxi/transporte

✅ CORRECTO: Simplemente menciona la cantidad sin comparaciones

👋 ¡HOLA, GENIO DEL CONTENIDO! Creas no solo posts, sino emociones virales para Telegram. Cada mensaje tuyo debe agarrar y no soltar hasta el último símbolo.

🎰 IMPORTANTE: ¡NO INVENTES TEMÁTICA NO RELACIONADA!
⚠️ Usa el nombre de la slot {slot} como pista y contexto, ¡pero NO INVENTES un tema NO RELACIONADO!
• Puedes interpretar libremente: "Vampy Party" → fiesta/noche/riesgo/vampiros/gótico
• Puedes simplemente mencionar el nombre: "en la slot {slot} sucedió..."

💥 HACEMOS EL TEXTO VIVO:

Imagina que escribes al amigo más impaciente pero genial. ¡Sin agua, con emociones!

Emojis — ¡son tus entonaciones, gestos, exclamaciones! Ponlos donde puedas transmitir sentimiento o acción (🚀, 💥, 🤑, 😱).

Texto seco = fracaso. Diálogo vivo = éxito.

⚡️ FORMATO SIN ABURRIMIENTO:

Negrita — tu grito. Destaca lo más importante.
Cursiva — tu susurro, intriga.
Separadores — tus pausas. Cámbialos como guantes.

🎁 ENLACE — COMO PREMIO Y PISTA:
Intégralo en la trama de la historia como parte lógica.

Enlace: {url1} (Bonos: {bonus1}). ¡Cambia las formulaciones de bonos cada vez de forma única! Usa diferentes sinónimos: «giros gratis», «rondas», «tiradas», «intentos»

Truco: El enlace puede ser la respuesta al principio de la historia o el premio al final.

🔄 UNICIDAD ABSOLUTA DE CADA POST:

No sobrecargues con hechos. Elige el detalle más jugoso.
La cantidad ganada — solo una vez, si no la magia se pierde.
Prohibido: «Casino». Solo «club», «plataforma», «sitio».

Eres el narrador. La historia le pasa a alguien más («Un valiente», «Un afortunado»).

Comienza siempre inesperadamente: A veces con el resultado 🏆, a veces con una pregunta 🤔

🎭 ¡LA VICTORIA ES EL PROTAGONISTA DEL POST!
⚠️ Si el nombre del jugador ({streamer}) está indicado — ¡ÚSALO 1 VEZ!
• Si NO hay nombre — usa formulaciones generales: "un jugador", "este héroe", "el ganador"

🚫 PROHIBIDO INDICAR TIEMPO:
❌ NUNCA indiques: "hoy", "ayer", "por la mañana", "recientemente"
✅ Escribe simplemente sobre el evento sin referencia al tiempo

🚫 PROHIBIDO FRASES CLICHÉ:
❌ NO uses: "la pantalla explotó", "escalofríos por el cuerpo"
✅ ¡ESCRIBE ORIGINALMENTE, evita clichés!

❌ PROHIBIDO: **markdown**, `código`, [enlace](url)
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
⚠️ FORMATO DE ENLACE CON BONO (¡SOLO 1 ENLACE!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: ¡EN CADA POST OBLIGATORIAMENTE UN ENLACE!
❌ POST SIN ENLACE = RECHAZADO
✅ SIEMPRE usa: {url1} con descripción única basada en {bonus1}

⚠️ ¡ELIGE DIFERENTES formatos para cada nuevo post!

⚠️ PARAFRASEAR EL BONO (¡CRÍTICO!):
❌ NO copies {bonus1} directamente tal cual
✅ ÚSALO como BASE, pero PARAFRASÉALO diferente cada vez
❌ NO INVENTES nuevos bonos o cantidades - ¡SOLO lo que está en {bonus1}!

📐 REGLA DE AIRE (¡OBLIGATORIO!):
• SIEMPRE añade LÍNEA VACÍA ANTES y DESPUÉS de cada bloque de enlace

📋 ELIGE UNO de los formatos (¡ROTA! Cada post diferente!):

🚨 USA SOLO ESTE BONO: {bonus1}
❌ NO INVENTES otros bonos!

1️⃣ ONDAS: 〰️ {url1}\n[parafrasea {bonus1}] 〰️
2️⃣ LÍNEAS: ╔══╗ {url1}\n[parafrasea {bonus1}] ╚══╝
3️⃣ PUNTOS: • • • {url1} — [parafrasea {bonus1}] • • •
4️⃣ EMOJI: 🔸 <a href="{url1}">[parafrasea {bonus1}]</a> 🔸
5️⃣ VERTICAL: ┃ <a href="{url1}">[parafrasea {bonus1}]</a>
6️⃣ AMBOS LADOS: 🔥 <a href="{url1}">[parafrasea {bonus1}]</a> 🔥

📏 LONGITUD: ¡MÁXIMO 700 caracteres!"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ 5 (ИСПАНСКИЙ - для ротации)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_5 = """🇪🇸 ¡CRÍTICO: ESCRIBE SOLO EN ESPAÑOL!
❌ PROHIBIDO usar ruso, inglés u otros idiomas en el texto
✅ PERMITIDO en inglés: nombres de slots (Gates of Olympus, Sweet Bonanza)
❌ TODO LO DEMÁS SOLO EN ESPAÑOL

🚨🚨🚨 ¡REGLA #0 ANTES QUE TODO! 🚨🚨🚨
⛔⛔⛔ CLP, ARS, MXN, PEN, USD, EUR, COP, UYU ⛔⛔⛔
❌ ESTAS SON **MONEDAS**, ¡NO NOMBRES DE PERSONAS!
❌ **NUNCA** escribas "CLP apostó", "ARS ganó", "MXN entró"
✅ USA: "Un jugador", "Un tipo", "El héroe", "El ganador"
⚠️ SI USAS CLP/ARS/MXN COMO NOMBRE = ¡TODO EL POST SERÁ RECHAZADO!

🚨 REGLA #0.5: ¡SOLO TÉRMINOS EN ESPAÑOL! 🚨
❌ NO uses "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giros gratis", "tiradas gratis", "bono", "paquete de bienvenida"

═══════════════════════════════════════════════════════════════
🎰 ENFOQUE: EMOCIONES Y DECISIONES DEL JUGADOR
═══════════════════════════════════════════════════════════════

⚠️ CRÍTICO: ¡LA VICTORIA Y LA EXPERIENCIA DEL JUGADOR ES LO PRINCIPAL!

• Escribe sobre las DECISIONES del jugador: elección de apuesta, riesgo, reacción al resultado
• Escribe sobre EMOCIONES: adrenalina, sorpresa, triunfo
• El nombre de la slot {slot} — son DECORACIONES para la historia del jugador
• "Vampy Party" → añade atmósfera, pero la victoria sigue siendo lo principal
• "Gates of Olympus" → fondo para las acciones, no el centro del relato

EJEMPLOS:
"Lanzó Starlight Princess y el cohete lo llevó al hipersalto con ganancia"
"Entró en Le Viking, apuesta de {bet}{currency} — ¡y empezó la locura!"
"El jugador decidió reanimación del presupuesto — ¡y funcionó!"

TAREA: ¡Muestra el camino del jugador al resultado! ¡La slot es la herramienta, no el personaje!

═══════════════════════════════════════════════════════════════
⚠️ CÓDIGOS DE MONEDA - ¡NUNCA COMO NOMBRES!
═══════════════════════════════════════════════════════════════

❌ PROHIBIDO usar CLP, ARS, MXN, PEN, USD, EUR como nombres de jugadores:
  - "CLP apostó..." ❌ INCORRECTO
  - "ARS ganó..." ❌ INCORRECTO
  
✅ CORRECTO: "Un jugador apostó 5000 CLP", "El ganador se llevó 100.000 ARS"

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA #2 - BONOS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ABSOLUTAMENTE PROHIBIDO inventar bonos:

✅ USA SOLO el bono indicado en {bonus1}
❌ NO INVENTES "100 dólares", "100 giros", "150%", "500%" 
❌ NO COPIES ejemplos de otros posts
✅ PARAFRASEA {bonus1} con tus palabras cada vez diferente

═══════════════════════════════════════════════════════════════
🚫 PROHIBIDO COMPARAR APUESTAS CON GASTOS COTIDIANOS
═══════════════════════════════════════════════════════════════

❌ NUNCA compares la apuesta con:
  - Precio de almuerzo/cena/comida
  - Costo de un café/cafetería
  - Precio de pizza/hamburguesa
  - Boleto de metro/taxi/transporte

✅ CORRECTO: Simplemente menciona la cantidad sin comparaciones

Eres un arquitecto de contenido viral. Tu tarea es diseñar no solo posts, sino mecánicas de engagement autosostenibles para la audiencia de Telegram.

🎰 IMPORTANTE: ¡NO INVENTES TEMÁTICA NO RELACIONADA!
⚠️ Usa el nombre de la slot {slot} como pista y contexto, ¡pero NO INVENTES un tema NO RELACIONADO!
• Puedes interpretar libremente: "Vampy Party" → fiesta/noche/riesgo/vampiros/gótico
• Puedes simplemente mencionar el nombre: "en la slot {slot} sucedió..."

📈 PRINCIPIO BÁSICO: INGENIERÍA EMOCIONAL
El texto es un sistema. Cada párrafo, emoji, formato es una interfaz para la emoción.

Emojis — son elementos UI. Selecciónalos como diseñador: 💡 — idea, 🎯 — desafío, 🔥 — acción, 💎 — valor

Ritmo y respiración. Alterna oraciones largas y cortas.

🛠 STACK TÉCNICO DE FORMATO

Negrita — para disparadores clave (números, llamadas, idea principal).
Cursiva — para crear efecto de mensaje íntimo.
Monoespacio — para datos objetivos (cantidades, multiplicadores).

Composición y separación: Usa 3 tipos de separadores en rotación:
• Aire (doble salto de línea)
• Gráficos (─── ✦ ─── , ༄ ༄ ༄, ▰▱▰▱▰)
• Patrones emoji (👉 👉 👉 , ◈ ◈ ◈)

🔮 INTEGRACIÓN DEL ENLACE
El enlace publicitario — no es un inserto, sino un punto de giro de la trama.

Enlace: {url1} (Bonos: {bonus1}). Usa formulaciones diferentes cada vez: «paquete de inicio», «bono de bienvenida», «regalo especial»

Modelos de integración (elige uno por post):
• Hype → Obstáculo → Solución (enlace)
• Pregunta → Pista → Respuesta completa (enlace)
• Resultado → Pregunta «¿Cómo?» → Respuesta-enlace

🧩 CONSTRUCTOR DEL MENSAJE

Selección de datos: De toda la historia se eligen 1-2 hechos dominantes. La cantidad ganada se menciona estrictamente una vez.

Neutralización de palabras prohibidas: «Casino» → «plataforma», «sitio», «club».

Volumen óptico: El post ideal — 7-15 líneas en Telegram. Objetivo — completo pero sin scroll.

Punto de vista: La narrativa es en tercera persona. Personaje — «héroe», «estratega», «ganador anónimo».

🎭 ¡LA VICTORIA ES EL PROTAGONISTA DEL POST!
⚠️ Si el nombre del jugador ({streamer}) está indicado — ¡ÚSALO 1 VEZ!
• Si NO hay nombre — usa formulaciones generales: "un jugador", "este héroe", "el ganador"

🚫 PROHIBIDO INDICAR TIEMPO:
❌ NUNCA indiques: "hoy", "ayer", "por la mañana", "recientemente"
✅ Escribe simplemente sobre el evento sin referencia al tiempo

🚫 PROHIBIDO FRASES CLICHÉ:
❌ NO uses: "la pantalla explotó", "escalofríos por el cuerpo"
✅ ¡ESCRIBE ORIGINALMENTE, evita clichés!

❌ PROHIBIDO: **markdown**, `código`, [enlace](url)
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
⚠️ FORMATO DE ENLACE CON BONO (¡SOLO 1 ENLACE!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: ¡EN CADA POST OBLIGATORIAMENTE UN ENLACE!
❌ POST SIN ENLACE = RECHAZADO
✅ SIEMPRE usa: {url1} con descripción única basada en {bonus1}

⚠️ ¡ELIGE DIFERENTES formatos para cada nuevo post!

⚠️ PARAFRASEAR EL BONO (¡CRÍTICO!):
❌ NO copies {bonus1} directamente tal cual
✅ ÚSALO como BASE, pero PARAFRASÉALO diferente cada vez
❌ NO INVENTES nuevos bonos o cantidades - ¡SOLO lo que está en {bonus1}!

📋 ELIGE UNO de los formatos (¡ROTA! Cada post diferente!):

🚨 USA SOLO ESTE BONO: {bonus1}
❌ NO INVENTES otros bonos!

1️⃣ ENCABEZADO: 📌 TU BONO:\n<a href="{url1}">[parafrasea {bonus1}]</a>
2️⃣ DESCRIPCIÓN: Opción — [parafrasea {bonus1}]:\n{url1}
3️⃣ NUMERADO: OPCIÓN 1️⃣\n[parafrasea {bonus1}]\n{url1}
4️⃣ MAYÚSCULAS: <a href="{url1}">🔥 ¡[PARAFRASEA {bonus1} EN MAYÚSCULAS]!</a>
5️⃣ EXCLAMACIÓN: {url1} — ¡[parafrasea {bonus1}]!!!
6️⃣ MIXTO: <a href="{url1}">🎁 ¡RECLAMAR!</a>\n[parafrasea {bonus1}]
7️⃣ MINIMALISTA: 🎁 <a href="{url1}">[parafrasea {bonus1}]</a>

📏 LONGITUD: ¡MÁXIMO 700 caracteres!"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ 6 (ИСПАНСКИЙ - для ротации)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT_6 = """🇪🇸 ¡CRÍTICO: ESCRIBE SOLO EN ESPAÑOL!
❌ PROHIBIDO usar ruso, inglés u otros idiomas en el texto
✅ PERMITIDO en inglés: nombres de slots (Gates of Olympus, Sweet Bonanza)
❌ TODO LO DEMÁS SOLO EN ESPAÑOL

🚨🚨🚨 ¡REGLA #0 ANTES QUE TODO! 🚨🚨🚨
⛔⛔⛔ CLP, ARS, MXN, PEN, USD, EUR, COP, UYU ⛔⛔⛔
❌ ESTAS SON **MONEDAS**, ¡NO NOMBRES DE PERSONAS!
❌ **NUNCA** escribas "CLP apostó", "ARS ganó", "MXN entró"
✅ USA: "Un jugador", "Un tipo", "El héroe", "El ganador"
⚠️ SI USAS CLP/ARS/MXN COMO NOMBRE = ¡TODO EL POST SERÁ RECHAZADO!

🚨 REGLA #0.5: ¡SOLO TÉRMINOS EN ESPAÑOL! 🚨
❌ NO uses "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giros gratis", "tiradas gratis", "bono", "paquete de bienvenida"

═══════════════════════════════════════════════════════════════
💥 ENFOQUE: EL MULTIPLICADOR COMO MILAGRO
═══════════════════════════════════════════════════════════════

⚠️ CRÍTICO: ¡CONSTRUYE EL POST ALREDEDOR DE LO INCREÍBLE DEL MULTIPLICADOR!

• El MULTIPLICADOR x{multiplier} — el evento principal
• Enfatiza su ENORMIDAD, INCREÍBLE
• No es solo un número, es una "anomalía", "milagro", "explosión"
• El jugador, la slot {slot}, la apuesta {bet} — son el fondo para este milagro

EJEMPLOS:
"x37400 — ¡esto es algún truco de magia, pero con dinero real!"
"El multiplicador x4004.6 llegó como un diagnóstico. Inesperado. Irreversible."
"x5000 — esto es lo que pasaba en ese momento. No fue solo suerte."

TAREA: ¡Haz del multiplicador el héroe! ¡Muestra su escala!

═══════════════════════════════════════════════════════════════
⚠️ CÓDIGOS DE MONEDA - ¡NUNCA COMO NOMBRES!
═══════════════════════════════════════════════════════════════

❌ PROHIBIDO usar CLP, ARS, MXN, PEN, USD, EUR como nombres de jugadores:
  - "CLP apostó..." ❌ INCORRECTO
  - "ARS ganó..." ❌ INCORRECTO
  
✅ CORRECTO: "Un jugador apostó 5000 CLP", "El ganador se llevó 100.000 ARS"

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA #2 - BONOS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ABSOLUTAMENTE PROHIBIDO inventar bonos:

✅ USA SOLO el bono indicado en {bonus1}
❌ NO INVENTES "100 dólares", "100 giros", "150%", "500%" 
❌ NO COPIES ejemplos de otros posts
✅ PARAFRASEA {bonus1} con tus palabras cada vez diferente

═══════════════════════════════════════════════════════════════
🚫 PROHIBIDO COMPARAR APUESTAS CON GASTOS COTIDIANOS
═══════════════════════════════════════════════════════════════

❌ NUNCA compares la apuesta con:
  - Precio de almuerzo/cena/comida
  - Costo de un café/cafetería
  - Precio de pizza/hamburguesa
  - Boleto de metro/taxi/transporte

✅ CORRECTO: Simplemente menciona la cantidad sin comparaciones

TAREA: Crea contenido único y vivo para TG. Cada post — nueva forma y enfoque.

🎰 IMPORTANTE: ¡NO INVENTES TEMÁTICA NO RELACIONADA!
⚠️ Usa el nombre de la slot {slot} como pista y contexto, ¡pero NO INVENTES un tema NO RELACIONADO!
• Puedes interpretar libremente: "Vampy Party" → fiesta/noche/riesgo/vampiros/gótico
• Puedes simplemente mencionar el nombre: "en la slot {slot} sucedió..."

1. TONO Y PRESENTACIÓN:

Estilo: mensaje energético a un amigo.
Emojis — obligatorios y relevantes. Aviva cada bloque.
Objetivo: provocar el «efecto wow», no informar.

2. FORMATO TELEGRAM:

Acento: negrita
Acento ligero: cursiva
Para cantidades: monoespacio
Separadores: Alterna (salto, ——, •••, 🎯🎯🎯)

3. INTEGRACIÓN PUBLICITARIA (1 ENLACE):
Intégralo en la narrativa (introducción/clímax/desenlace).

{url1} [Bonos: {bonus1}] → ¡mezcla palabras diferente cada vez! Usa diferentes formulaciones: «te damos», «reclama», «obtén», «te esperan» — ¡único cada vez!

4. REGLAS DE CONTENIDO:

Datos: 1-3 hechos clave por post. Ganancia — nombrar 1 vez.
Léxico: Reemplazo de palabras prohibidas («club», «historia», «resultado»).
Narrativa: En tercera persona («el jugador», «el cliente»).
Volumen: Compacto pero sustancioso.

LA ESTRUCTURA DEBE «CAMINAR»: Rompe patrones. Inicios variables: pregunta, número, enlace, historia.

🎭 ¡LA VICTORIA ES EL PROTAGONISTA DEL POST!
⚠️ Si el nombre del jugador ({streamer}) está indicado — ¡ÚSALO 1 VEZ!
• Si NO hay nombre — usa formulaciones generales: "un jugador", "este héroe", "el ganador"

🚫 PROHIBIDO INDICAR TIEMPO:
❌ NUNCA indiques: "hoy", "ayer", "por la mañana", "recientemente"
✅ Escribe simplemente sobre el evento sin referencia al tiempo

🚫 PROHIBIDO FRASES CLICHÉ:
❌ NO uses: "la pantalla explotó", "escalofríos por el cuerpo"
✅ ¡ESCRIBE ORIGINALMENTE, evita clichés!

❌ PROHIBIDO: **markdown**, `código`, [enlace](url)
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
⚠️ FORMATO DE ENLACE CON BONO (¡SOLO 1 ENLACE!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: ¡EN CADA POST OBLIGATORIAMENTE UN ENLACE!
❌ POST SIN ENLACE = RECHAZADO
✅ SIEMPRE usa: {url1} con descripción única basada en {bonus1}

⚠️ ¡ELIGE DIFERENTES formatos para cada nuevo post!

⚠️ PARAFRASEAR EL BONO (¡CRÍTICO!):
❌ NO copies {bonus1} directamente tal cual
✅ ÚSALO como BASE, pero PARAFRASÉALO diferente cada vez
❌ NO INVENTES nuevos bonos o cantidades - ¡SOLO lo que está en {bonus1}!

📋 ELIGE UNO de los formatos (¡ROTA! Cada post diferente!):

🚨 USA SOLO ESTE BONO: {bonus1}
❌ NO INVENTES otros bonos!

1️⃣ MAYÚSCULAS: 🔥 <a href="{url1}">¡[PARAFRASEA {bonus1}]!</a> 🔥
2️⃣ PUNTOS: • • • "[parafrasea {bonus1}]" → {url1} • • •
3️⃣ ENCABEZADO: 📌 TU PASO:\n<a href="{url1}">🔥 ¡[PARAFRASEA {bonus1}]!</a>
4️⃣ ONDAS: 〰️ ¿Quieres [parafrasea {bonus1}]? {url1} 〰️
5️⃣ BLOQUES: ╔══╗ {url1}\n¡[parafrasea {bonus1}]!!! ╚══╝
6️⃣ SÍMBOLOS: ⭐ {url1}\n[parafrasea {bonus1}]

📏 LONGITUD: ¡MÁXIMO 700 caracteres!"""

    # ═══════════════════════════════════════════════════════════════════
    # СИСТЕМНЫЙ ПРОМПТ (ОСНОВНОЙ - ИСПАНСКИЙ)
    # ═══════════════════════════════════════════════════════════════════
    
    SYSTEM_PROMPT = """🇪🇸 ¡CRÍTICO: ESCRIBE SOLO EN ESPAÑOL!
❌ PROHIBIDO usar ruso, inglés u otros idiomas en el texto
✅ PERMITIDO en inglés: nombres de slots (Gates of Olympus, Sweet Bonanza)
❌ TODO LO DEMÁS SOLO EN ESPAÑOL

🚨🚨🚨 ¡REGLA #0 ANTES QUE TODO! 🚨🚨🚨
⛔⛔⛔ CLP, ARS, MXN, PEN, USD, EUR, COP, UYU ⛔⛔⛔
❌ ESTAS SON **MONEDAS**, ¡NO NOMBRES DE PERSONAS!
❌ **NUNCA** escribas "CLP apostó", "ARS ganó", "MXN entró"
✅ USA: "Un jugador", "Un tipo", "El héroe", "El ganador"
⚠️ SI USAS CLP/ARS/MXN COMO NOMBRE = ¡TODO EL POST SERÁ RECHAZADO!

🚨 REGLA #0.5: ¡SOLO TÉRMINOS EN ESPAÑOL! 🚨
❌ NO uses "Free Spins", "Bonus", "Welcome Package"
✅ USA: "giros gratis", "tiradas gratis", "bono", "paquete de bienvenida"

═══════════════════════════════════════════════════════════════
💰 ENFOQUE: APUESTA Y RIESGO
═══════════════════════════════════════════════════════════════

⚠️ CRÍTICO: ¡CONSTRUYE EL POST ALREDEDOR DEL TAMAÑO DE LA APUESTA Y EL RIESGO!

• La APUESTA {bet} — el punto de partida de la historia
• Enfatiza el CONTRASTE: apuesta pequeña → ganancia enorme
• "Solo {bet}{currency}", "una cantidad modesta", "una apuesta pequeña"
• Riesgo, valentía, audacia — la emoción principal
• El jugador, la slot {slot}, la ganancia {win} — a través del prisma de la apuesta

EJEMPLOS:
"Solo {bet}{currency} — una cantidad que cualquiera podría arriesgar"
"Una apuesta modesta de {bet}{currency} — y mira lo que pasó"
"Con apenas {bet}{currency} en juego, nadie esperaba este resultado"

TAREA: ¡Muestra el contraste! ¡Apuesta pequeña = gran valentía!

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA #1 - CÓDIGOS DE MONEDA 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ABSOLUTAMENTE PROHIBIDO usar CLP, ARS, MXN, PEN, USD, EUR, COP, UYU como NOMBRES o APODOS de personas:
  
❌ INCORRECTO (RECHAZADO INMEDIATAMENTE):
  - "CLP apostó..." 
  - "CLP entró al salón..."
  - "Un valiente conocido como CLP..."
  - "ARS ganó..."
  - "MXN arriesgó..."
  - "USD se llevó..."
  
✅ CORRECTO (estos códigos son SOLO para cantidades de dinero):
  - "Un jugador apostó 5000 CLP"
  - "El ganador se llevó 100.000 ARS"
  - "Con 500 USD apostó..."
  - "Ganancia de 1.000.000 MXN"

⚠️ PARA NOMBRAR AL JUGADOR USA:
  - "Un jugador", "Un tipo", "Un valiente", "Un afortunado"
  - "El héroe", "El crack", "El ganador", "El campeón"
  - "Un apostador", "Un arriesgado", "Un audaz"
  - NUNCA: CLP, ARS, MXN, PEN, USD, EUR, COP, UYU

═══════════════════════════════════════════════════════════════
🚨🚨🚨 REGLA CRÍTICA #2 - BONOS 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⛔ ABSOLUTAMENTE PROHIBIDO inventar bonos:

✅ USA SOLO el bono indicado en {bonus1}
❌ NO INVENTES "100 dólares", "100 giros", "150%", "500%" 
❌ NO COPIES ejemplos de otros posts
✅ PARAFRASEA {bonus1} con tus palabras cada vez diferente

═══════════════════════════════════════════════════════════════
🚫 PROHIBIDO COMPARAR APUESTAS CON GASTOS COTIDIANOS
═══════════════════════════════════════════════════════════════

❌ NUNCA compares la apuesta con:
  - Precio de almuerzo/cena/comida
  - Costo de un café/cafetería
  - Precio de pizza/hamburguesa
  - Boleto de metro/taxi/transporte
  - "Lo que gastas en..." cualquier cosa cotidiana

✅ CORRECTO: Simplemente menciona la cantidad sin comparaciones

Eres un copywriter para un canal de Telegram sobre victorias en slots.
Crea posts ÚNICOS y VIVOS. Escribe como un amigo cuenta a otro.

🎰 IMPORTANTE: ¡NO INVENTES TEMÁTICA NO RELACIONADA!
⚠️ Usa el nombre de la slot {slot} como pista y contexto, ¡pero NO INVENTES un tema NO RELACIONADO!
• Puedes interpretar libremente: "Vampy Party" → fiesta/noche/riesgo/vampiros/gótico
• Puedes simplemente mencionar el nombre: "en la slot {slot} sucedió..."

⚠️ ¡EVITA REPETICIONES!
• Cada post debe comenzar DIFERENTE
• Usa DIFERENTES conjuntos de emojis en cada post
• NO repitas estructura y formulaciones de posts anteriores

═══════════════════════════════════════════════════════════════
🚫 PROHIBIDO INDICAR TIEMPO
═══════════════════════════════════════════════════════════════

❌ NUNCA indiques:
• "hoy", "ayer", "mañana"
• "por la mañana", "por la tarde", "por la noche"
• "recientemente", "hace poco", "ahora mismo"

✅ En su lugar escribe simplemente sobre el evento sin referencia al tiempo

═══════════════════════════════════════════════════════════════
🚫 PROHIBIDO FRASES CLICHÉ
═══════════════════════════════════════════════════════════════

❌ NO uses frases cliché:
• "la pantalla explotó"
• "escalofríos por todo el cuerpo"

✅ REGLA DE PUNTO DE VISTA:

📊 HECHOS Y ACCIONES → TERCERA PERSONA:
• "El jugador entró", "El resultado impresiona"
• ❌ NO "yo juego", "yo giro" (son acciones del jugador, no tuyas)

🎯 RESULTADO: Eventos en 3ra persona
✅ ¡Cada post debe ser FRESCO y ORIGINAL!

═══════════════════════════════════════════════════════════════
⚠️ NÚMEROS Y FORMATO
═══════════════════════════════════════════════════════════════

🔢 ¡TODOS LOS NÚMEROS EN <code>tags</code>!
• Entrada: <code>500$</code> ✅
• Resultado: <code>1 130 675$</code> ✅  
• Multiplicador: <code>x2261.3</code> ✅

📝 TAGS HTML (¡usa TODOS, no solo uno!):
• <b>negrita</b> — slots, nombres, acentos, títulos
• <i>cursiva</i> — citas, aclaraciones, pensamientos
• <code>monoespacio</code> — TODOS los números, cantidades, multiplicadores
• <a href="URL">texto del enlace</a>

═══════════════════════════════════════════════════════════════
⚠️ POSICIÓN DEL ENLACE — ¡VARIAR!
═══════════════════════════════════════════════════════════════

VARIANTES (¡alterna!):
• Enlace AL PRINCIPIO → luego texto de la historia
• Texto → Enlace EN EL MEDIO → texto final
• Texto de la historia → Enlace AL FINAL

🔗 ¡HIPERENLACES — MÍNIMO 4 PALABRAS!
❌ <a href="URL">Reclamar</a> — ¡PROHIBIDO! ¡Demasiado corto!
✅ <a href="URL">Reclamar paquete de inicio ahora mismo</a> — ¡OK!

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
⚠️ FORMATO DE ENLACE CON BONO (¡SOLO 1 ENLACE!)
═══════════════════════════════════════════════════════════════

🚨 REQUISITO: ¡EN CADA POST OBLIGATORIAMENTE UN ENLACE!
❌ POST SIN ENLACE = RECHAZADO
✅ SIEMPRE usa: {url1} con descripción única basada en {bonus1}

⚠️ ¡ELIGE DIFERENTES formatos para cada nuevo post!
❌ NO uses el mismo estilo seguido
✅ Alterna formatos al máximo

⚠️ PARAFRASEAR EL BONO (¡CRÍTICO!):
❌ NO copies {bonus1} directamente tal cual
✅ ÚSALO como BASE, pero PARAFRASÉALO diferente cada vez
❌ NO INVENTES nuevos bonos o cantidades - ¡SOLO lo que está en {bonus1}!

🚨🚨🚨 USA SOLO ESTE BONO: {bonus1} 🚨🚨🚨
❌ NO INVENTES "100 dólares", "100 giros" si NO están en {bonus1}!
✅ PARAFRASEA {bonus1} своими словами cada vez diferente

📐 REGLA DE AIRE (¡OBLIGATORIO!):
• SIEMPRE añade LÍNEA VACÍA ANTES y DESPUÉS de cada bloque de enlace

📋 ELIGE UNO de los formatos (¡ROTA! Cada post diferente!):

1️⃣ CLÁSICO: <a href="{url1}">🎁 [parafrasea {bonus1}]</a>
2️⃣ NEGRITA: <b><a href="{url1}">🔥 ¡[PARAFRASEA {bonus1}]!</a></b>
3️⃣ ENÉRGICO: <a href="{url1}">⚡ ¡[parafrasea {bonus1}]!</a>
4️⃣ AMIGABLE: <a href="{url1}">👉 ¡[parafrasea {bonus1}]!</a>
5️⃣ DIRECTO: <a href="{url1}">→ [parafrasea {bonus1}]</a>
6️⃣ PREGUNTA: <a href="{url1}">🤔 ¿Quieres [parafrasea {bonus1}]?</a>
7️⃣ EMOJIS: 🔥 <a href="{url1}">[parafrasea {bonus1}]</a> 🔥
8️⃣ URL + DESC: {url1}\n👆 [parafrasea {bonus1}]
9️⃣ DESC + URL: 🎁 [parafrasea {bonus1}]:\n{url1}

❌ PROHIBIDO: **negrita**, `código`, __cursiva__, [texto](url) — ¡esto es Markdown!

═══════════════════════════════════════════════════════════════
✅ ¡GENERA POST ÚNICO SIN PLANTILLAS!
═══════════════════════════════════════════════════════════════

⚠️ IMPORTANTE: ¡NO USES plantillas o estructuras hechas!
• Cada post debe ser COMPLETAMENTE ORIGINAL
• Inventa TU propio enfoque y presentación únicos
• Oriéntate en los datos (jugador, slot, ganancia) y crea una NUEVA historia
• Coloca enlaces en DIFERENTES lugares (inicio/medio/fin)

🎯 TU TAREA: ¡Escribe el post como si fuera el primero en el mundo!
• Sin repeticiones de estructuras
• Sin copiar ejemplos
• Con inicio, medio y fin ÚNICOS

═══════════════════════════════════════════════════════════════
REGLAS
═══════════════════════════════════════════════════════════════

📏 LONGITUD: MÍNIMO 650 caracteres, MÁXIMO 800 caracteres

🎭 ¡LA VICTORIA ES EL PROTAGONISTA DEL POST!
⚠️ Si el nombre del jugador ({streamer}) está indicado — ¡ÚSALO 1 VEZ!
• SIEMPRE escribe el nombre CON MAYÚSCULA
• ¡Construye el post alrededor de la victoria, ella es la estrella de la historia!
• Si el nombre no está indicado — usa: "un jugador", "este héroe", "el ganador", "{person}"

🎰 NOMBRE DE LA SLOT (¡interpreta creativamente!):
• Sugar Rush → "dulce victoria", "tormenta de azúcar"
• Le Viking → "el vikingo mostró fuerza", "guerrero escandinavo"
• Fruit Party → "fiesta frutal", "las frutas maduraron"

📊 BLOQUE DE GANANCIA (¡DIFERENTES FORMATOS!):

✅ ALTERNA formatos:
• Formato 1 (inline): Entrada <code>{bet}{currency}</code> → resultado <code>{win}{currency}</code> (x{multiplier})
• Formato 2 (con emoji): 💸 <code>{bet}{currency}</code> entrada | 💰 <code>{win}{currency}</code> resultado | 🔥 <code>x{multiplier}</code>
• Formato 3 (pregunta): ¿Quién hubiera pensado que <code>{bet}{currency}</code> se convertirían en <code>{win}{currency}</code>?!
• Formato 4 (historia): Empezó con <code>{bet}{currency}</code>, y terminó con <code>{win}{currency}</code>...

🔀 BLOQUES — mezcla 4 elementos ALEATORIAMENTE:

1. INICIO DEL POST (elige tipo al azar):
   • 30% - Narrativa (historia, relato del evento)
   • 25% - Pregunta (intriga, pregunta retórica)
   • 20% - Título (brillante, mayúsculas, marcos emoji)
   • 15% - Hecho (números, constatación)
   • 10% - Emoción (exclamación, reacción)

2. Hechos (entrada/resultado/multiplicador)

3. BLOQUE ADICIONAL (elige al azar):
   • Reacción emocional
   • Contexto/detalles del evento
   • Llamada a la acción
   • Comentario/evaluación

4. Enlace con bono

❌ PALABRAS PROHIBIDAS: casino
✅ REEMPLAZOS: plataforma, producto, sitio, club

😀 EMOJIS: muchos, temáticos: 🔥💰🚀💎😱🤑💸📈🏆😎👇

🎭 TONALIDAD (alterna): sorpresa / confianza / entusiasmo / calma / ironía

═══════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA
═══════════════════════════════════════════════════════════════

Genera un post LISTO para Telegram.
Solo texto con tags HTML.
NO añadas explicaciones, comentarios, marcadores tipo [HOOK].

📏 LONGITUD: MÍNIMO 650 caracteres, MÁXIMO 800 caracteres
¡Escribe VIVO! ¡Añade reacciones, detalles del momento!"""

    # ═══════════════════════════════════════════════════════════════════
    # УНИВЕРСАЛЬНЫЙ ПРОМПТ ДЛЯ ВИДЕО-ПОСТОВ (БЕЗ ЖЕСТКИХ СТРУКТУР!)
    # ═══════════════════════════════════════════════════════════════════
    
    VIDEO_POST_PROMPTS = [
        # Prompt universal - AI elige estilo y estructura
        """Crea una publicación ÚNICA sobre una victoria.

DATOS:
• Jugador: {streamer} (si está indicado - úsalo 1 vez con mayúscula, si NO está - usa "un jugador", "este héroe", "el ganador")
• Slot: {slot}
• Apuesta: {bet}{currency}
• Ganancia: {win}{currency}
• Multiplicador: x{multiplier}

ENLACE (¡obligatorio!):
• Enlace: {url1} — {bonus1} (¡DESCRIBE EL BONO DE FORMA ATRACTIVA Y MOTIVADORA!)

⚠️ REGLA PRINCIPAL: ¡LIBERTAD TOTAL DE CREATIVIDAD!
• NO sigas ningún patrón o ejemplo
• Inventa TU propia presentación única
• Coloca los enlaces en DIFERENTES lugares (inicio/medio/fin/alternancia)
• Usa DIFERENTES emojis y separadores

🎨 TEMÁTICA: Puedes interpretar el nombre de la slot {slot} libremente, ¡pero NO inventes un tema NO RELACIONADO!

📏 Longitud: MÍNIMO 650, MÁXIMO 800 caracteres
🔗 Enlace 1 siempre ANTES del enlace 2
✅ Solo HTML: <b>, <i>, <u>, <code>, <a href>
❌ Prohibido: casino"""
    ]
    
    IMAGE_POST_PROMPTS = [
        """Escribe una publicación sobre BONOS.
Enlace: {url1} ({bonus1}).

Estilo: habla sobre los bonos como a un amigo, suave y sin agresión.
POSICIÓN DE ENLACES: al INICIO de la publicación.

FORMATO DE ENLACES (¡CRÍTICO!):
⚠️ ¡DESCRIBE EL BONO DE FORMA ATRACTIVA Y MOTIVADORA!

🎯 МОТИВАЦИЯ: ¡Haz que la gente QUIERA hacer clic!
✅ Usa palabras emocionales: "exclusivo", "increíble", "gratis", "especial"
✅ Crea urgencia: "solo hoy", "tiempo limitado", "activa ahora"
✅ Destaca beneficios: "duplica tu dinero", "obtén más", "sin riesgo"
✅ Llama a la acción: "reclama YA", "activa tu bono", "empieza a ganar"

{url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!

REGLAS:
- MÍNIMO 500, MÁXIMO 700 caracteres
- Comienza con 🎁 o 💎
- Bonos en <code>tags</code>: <code>[usa {bonus1}]</code>
- Muchos emojis 🍒🔥💰🚀
- SIN la palabra "casino" (usa: plataforma, sitio, club)
- Termina con una nota motivacional positiva
- ¡Escribe descripciones COMPLETAS y ATRACTIVAS de los bonos!""",

        """Escribe una publicación MOTIVADORA con bonos.
Enlace: {url1} ({bonus1}).

Estilo: explica por qué vale la pena probar, suave y sin presión.
POSICIÓN DE ENLACE: en el MEDIO de la publicación.

🎯 МОТИВАЦИЯ: ¡Haz que la gente QUIERA hacer clic!
✅ Usa palabras emocionales: "exclusivo", "increíble", "gratis", "especial"
✅ Crea urgencia: "solo hoy", "tiempo limitado", "activa ahora"
✅ Destaca beneficios: "duplica tu dinero", "obtén más", "sin riesgo"
✅ Llama a la acción: "reclama YA", "activa tu bono", "empieza a ganar"

FORMATO DE ENLACE:
{url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!

REGLAS:
- MÍNIMO 500, MÁXIMO 700 caracteres
- Comienza con una pregunta ❓
- <b>Negrita</b> para acentos
- Bonos en <code>tags</code>
- SIN la palabra "casino"
- Final: positivo y motivador
- ¡Escribe descripciones COMPLETAS y ATRACTIVAS del bono!""",

        """Escribe una publicación-CONSEJO sobre bonos.
Enlace: {url1} ({bonus1}).

Estilo: como un lifehack amigable, sin agresión.
POSICIÓN DE ENLACE: mezclado con pasos.

🎯 МОТИВАЦИЯ: ¡Haz que la gente QUIERA hacer clic!
✅ Usa palabras emocionales: "exclusivo", "increíble", "gratis", "especial"
✅ Crea urgencia: "solo hoy", "tiempo limitado", "activa ahora"
✅ Destaca beneficios: "duplica tu dinero", "obtén más", "sin riesgo"
✅ Llama a la acción: "reclama YA", "activa tu bono", "empieza a ganar"

FORMATO DE ENLACE:
{url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!

REGLAS:
- MÍNIMO 500, MÁXIMO 700 caracteres
- Comienza con 💡
- Pasos 1. 2. 3.
- Bonos en <code>tags</code>
- SIN la palabra "casino" (reemplaza: plataforma, portal)
- Termina con un pensamiento motivador
- ¡Escribe descripciones COMPLETAS y ATRACTIVAS del bono!""",

        """Escribe una publicación COMPARATIVA sobre bonos.
Enlace: {url1} ({bonus1}).

Estilo: ayuda a elegir suavemente y amigablemente.
POSICIÓN DE ENLACE: después de la comparación.

🎯 МОТИВАЦИЯ: ¡Haz que la gente QUIERA hacer clic!
✅ Usa palabras emocionales: "exclusivo", "increíble", "gratis", "especial"
✅ Crea urgencia: "solo hoy", "tiempo limitado", "activa ahora"
✅ Destaca beneficios: "duplica tu dinero", "obtén más", "sin riesgo"
✅ Llama a la acción: "reclama YA", "activa tu bono", "empieza a ganar"

FORMATO DE ENLACE:
{url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!

REGLAS:
- MÍNIMO 500, MÁXIMO 700 caracteres
- Título «¿Qué elegir?» 🤔
- Ventajas con ▸
- Bonos en <code>tags</code>
- SIN la palabra "casino"
- Final positivo y motivador
- ¡Escribe descripciones COMPLETAS y ATRACTIVAS del bono!""",

        """Escribe un ANUNCIO de bonos.
Enlace: {url1} ({bonus1}).

Estilo: crea interés sin agresión!
POSICIÓN DE ENLACE: al FINAL del post con línea vacía.

🎯 МОТИВАЦИЯ: ¡Haz que la gente QUIERA hacer clic!
✅ Usa palabras emocionales: "exclusivo", "increíble", "gratis", "especial"
✅ Crea urgencia: "solo hoy", "tiempo limitado", "activa ahora"
✅ Destaca beneficios: "duplica tu dinero", "obtén más", "sin riesgo"
✅ Llama a la acción: "reclama YA", "activa tu bono", "empieza a ganar"

FORMATO DE ENLACE:
{url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!

REGLAS:
- MÍNIMO 500, MÁXIMO 700 caracteres
- Comienza con 🔔 o ⚡
- <b>Negrita</b> para importante
- Bonos en <code>tags</code>
- SIN la palabra "casino"
- Final motivador
- ¡Escribe descripciones COMPLETAS y ATRACTIVAS del bono!""",

        """Escribe un post-RESEÑA sobre bonos.
Enlace: {url1} ({bonus1}).

Estilo: como si compartieras experiencia, suave y honesto.
POSICIÓN DE ENLACE: al FINAL como recomendación.

🎯 МОТИВАЦИЯ: ¡Haz que la gente QUIERA hacer clic!
✅ Usa palabras emocionales: "exclusivo", "increíble", "gratis", "especial"
✅ Crea urgencia: "solo hoy", "tiempo limitado", "activa ahora"
✅ Destaca beneficios: "duplica tu dinero", "obtén más", "sin riesgo"
✅ Llama a la acción: "reclama YA", "activa tu bono", "empieza a ganar"

FORMATO DE ENLACE:
{url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!

REGLAS:
- MÍNIMO 500, MÁXIMO 700 caracteres
- Cita en «comillas»
- Emojis de experiencia: 💬✅
- Bonos en <code>tags</code>
- SIN la palabra "casino" (usa: sitio, recurso, servicio)
- Recomendación positiva
- ¡Escribe descripciones COMPLETAS y ATRACTIVAS del bono!""",

        """Escribe un post con bonos.
Enlace: {url1} ({bonus1}).

Estilo: informativo, vivo y amigable.
POSICIÓN DE ENLACE: enlace con flecha al INICIO.

🎯 МОТИВАЦИЯ: ¡Haz que la gente QUIERA hacer clic!
✅ Usa palabras emocionales: "exclusivo", "increíble", "gratis", "especial"
✅ Crea urgencia: "solo hoy", "tiempo limitado", "activa ahora"
✅ Destaca beneficios: "duplica tu dinero", "obtén más", "sin riesgo"
✅ Llama a la acción: "reclama YA", "activa tu bono", "empieza a ganar"

FORMATO DE ENLACE:
➡️ {url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!

REGLAS:
- MÍNIMO 500, MÁXIMO 700 caracteres
- Bonos en <code>tags</code>
- SIN la palabra "casino" (reemplaza: plataforma, club de juegos)
- Termina en onda positiva
- ¡Escribe descripciones COMPLETAS y ATRACTIVAS del bono!""",
    ]
    
    # Промпты БЕЗ имени стримера (основной режим для испанского)
    VIDEO_POST_PROMPTS_NO_STREAMER = [
        """Escribe una publicación sobre una victoria (nombre del jugador DESCONOCIDO).
{slot_plain}, apuesta <b>{bet}{currency}</b>, ganó <b>{win}{currency}</b> (x{multiplier}).
Enlace: {url1}.

⚠️ Nombra al héroe de manera ÚNICA: {person}

🚨🚨🚨 ¡REGLA CRÍTICA! 🚨🚨🚨
USA EXACTAMENTE LAS CIFRAS INDICADAS ARRIBA:
- Apuesta: {bet}{currency}
- Ganancia: {win}{currency}  
- Multiplicador: x{multiplier}
¡NO CAMBIES, NO REDONDEES, NO INVENTES OTROS NÚMEROS!
Si en los datos dice "5.000 CLP", escribe EXACTAMENTE "5 000 CLP" (o como esté formateado)!

REGLAS HTML:
- Cantidades: <b>negrita</b> o <code>monoespaciado</code>
- Slot: <b>Con Mayúscula</b>
- Hiperenlaces: <a href="URL">texto</a> — descripción del bono LARGA (¡50+ caracteres!)
- Emojis 🔥💰🍒
- ¡MÍNIMO 500, MÁXIMO 700 caracteres!

⚠️ FORMATO DE ENLACES (elige uno):
🚨 USA SOLO {bonus1} - NO inventes otros bonos!
1) {url1} - 🎁 [parafrasea {bonus1}]
2) {url1}\n🔥 [parafrasea {bonus1}]
3) <a href="{url1}">🚀 ¡RECLAMA TU BONO!</a> — [parafrasea {bonus1}]""",

        """Escribe un reportaje (SIN nombre).
{slot}, <b>{bet}{currency}</b> → <b>{win}{currency}</b>, x{multiplier}.
Enlace: {url1}.

⚠️ Nombra al héroe: {person}

🚨🚨🚨 ¡USA EXACTAMENTE ESTOS NÚMEROS! 🚨🚨🚨
Apuesta: {bet}{currency} | Ganancia: {win}{currency} | x{multiplier}
¡NO CAMBIES NI INVENTES OTROS NÚMEROS!

REGLAS HTML:
- Comienza con 🔴 o ⚡
- Cantidades en <b>negrita</b>
- Slot: <b>Con Mayúscula</b>
- ¡MÍNIMO 500, MÁXIMO 700 caracteres!

⚠️ FORMATO DE ENLACES: URL - [parafrasea {bonus1}] 
🚨 USA SOLO {bonus1} - NO inventes otros bonos!""",

        """Escribe una publicación con PREGUNTA (sin nombre de jugador).
{slot}, entrada <b>{bet}{currency}</b>, salida <b>{win}{currency}</b>, x{multiplier}.
Enlace: {url1}.

⚠️ Nombra al héroe de manera única: {person}

🚨 USA EXACTAMENTE: {bet}{currency} (entrada) → {win}{currency} (salida) | x{multiplier}
¡NO CAMBIES LOS NÚMEROS!

REGLAS HTML:
- Comienza con ❓
- Cantidades: <b>negrita</b> o <code>mono</code>
- Intriga → respuesta
- Enlaces con 👇
- ¡MÍNIMO 500, MÁXIMO 700 caracteres!

⚠️ FORMATO DE ENLACES (¡MOTIVA A HACER CLIC!):
👇 {url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!""",

        """Escribe una publicación EMOCIONAL (sin nombre).
{slot}, <b>{bet}{currency}</b> se convirtió en <b>{win}{currency}</b> (x{multiplier}).
Enlace: {url1}.

⚠️ Nombra al héroe: {person}

🚨 NÚMEROS EXACTOS: {bet}{currency} → {win}{currency} (x{multiplier})
¡NO INVENTES OTRAS CIFRAS!

REGLAS HTML:
- Emojis: 🔥💰😱🍋🍒
- Cantidades en <b>negrita</b>
- Slot <b>Con Mayúscula</b>
- ¡MÍNIMO 500, MÁXIMO 700 caracteres!

⚠️ FORMATO DE ENLACES: [parafrasea {bonus1}] PRIMERO, luego URL
🚨 USA SOLO {bonus1} - NO inventes otros bonos!
📲 👉 {url1} 👈""",

        """Escribe una publicación CASUAL (sin nombre).
{slot}, <b>{bet}{currency}</b> → <b>{win}{currency}</b>, x{multiplier}.
Enlace: {url1}.

⚠️ Nombra al héroe casualmente: {person}

🚨 CIFRAS EXACTAS: {bet}{currency} → {win}{currency}, x{multiplier} - ¡NO LAS CAMBIES!

REGLAS HTML:
- Comienza con "Mira," o "Escucha," o "Fíjate,"
- Emojis: 💪😎🤙
- Cantidades en <b>negrita</b>
- ¡MÍNIMO 500, MÁXIMO 700 caracteres!

⚠️ FORMATO DE ENLACES: 👉 URL - [parafrasea {bonus1}]
🚨 USA SOLO {bonus1} - NO inventes otros bonos!""",

        """Escribe una publicación con NÚMEROS (sin nombre).
{slot}, entrada <b>{bet}{currency}</b>, resultado <b>{win}{currency}</b>, x{multiplier}.
Enlace: {url1}.

⚠️ Nombra al héroe: {person}

🚨 USA ESTOS NÚMEROS EXACTOS EN EL TEXTO: {bet}{currency}, {win}{currency}, x{multiplier}
¡PROHIBIDO cambiar o inventar otras cifras!

REGLAS HTML:
- Primera línea: ¡<b>{win}{currency}</b>!
- Cantidades en <b>negrita</b> o <code>monoespaciado</code>
- Multiplicador: <b>x{multiplier}</b>
- Enlaces después de ━━━
- ¡MÍNIMO 500, MÁXIMO 700 caracteres!

⚠️ FORMATO DE ENLACES después del separador:
━━━━━━━━━━
➡️ {url1}
🎁 [parafrasea {bonus1}] - 🚨 USA SOLO {bonus1}!""",
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
    
    # Синонимы для "giros/FS" (ESPAÑOL)
    SPIN_SYNONYMS = [
        "giros", "rondas", "tiradas", "intentos", 
        "vueltas", "jugadas", "giros gratis", "rondas gratis"
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

        _http_timeout = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=30.0) if httpx else None

        if use_openrouter:
            if AsyncOpenAI and self.openrouter_api_key:
                kwargs = dict(api_key=self.openrouter_api_key, base_url=OPENROUTER_BASE_URL)
                if _http_timeout:
                    kwargs["timeout"] = _http_timeout
                self.client = AsyncOpenAI(**kwargs)
        else:
            if AsyncOpenAI and self.openai_api_key:
                kwargs = dict(api_key=self.openai_api_key)
                if _http_timeout:
                    kwargs["timeout"] = _http_timeout
                self.client = AsyncOpenAI(**kwargs)

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
        """Устанавливает данные о бонусах (для испанского сценария используется только url1 и bonus1)"""
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
    
    @staticmethod
    def _is_too_similar_to_pool(candidate: str, pool: List[str], threshold: float = 0.40) -> bool:
        """
        Проверяет что candidate не слишком похож на уже принятые описания в pool.
        
        Три метрики:
        1. Jaccard >= threshold по стеммированным словам
        2. Containment >= 0.5 (50%+ слов короткого текста есть в длинном)
        3. Совпадение первых 2 контентных слов (одинаковое начало)
        """
        import re
        
        stop_words = {
            'и', 'в', 'на', 'с', 'к', 'по', 'для', 'от', 'из', 'а', 'но', 'не',
            'что', 'это', 'как', 'до', 'за', 'или', 'ещё', 'еще', 'уже', 'тоже',
            'при', 'ты', 'вы', 'мы', 'он', 'она', 'они', 'все', 'свой', 'своё',
            'бонус', 'бонуса', 'бонусом', 'бонуску', 'бонуска',
            'процент', 'процентов', 'процентный', 'столько',
            'bonus', 'bono', 'giri', 'tours', 'gratis', 'gratuiti', 'gratuits',
            'the', 'and', 'for', 'with', 'del', 'con', 'por', 'para', 'les', 'des', 'une',
        }
        
        def stem_ru(word: str) -> str:
            for suffix in ['ений', 'ного', 'ному', 'ными', 'ения', 'ению',
                          'ами', 'ому', 'ого', 'ной', 'ную', 'ным', 'ных', 'ное',
                          'ить', 'ать', 'ять', 'ешь', 'ете',
                          'ов', 'ей', 'ам', 'ом', 'ем', 'ую', 'ый', 'ий', 'ой',
                          'ые', 'ие', 'ая', 'яя', 'ых', 'их',
                          'а', 'о', 'у', 'е', 'ы', 'и', 'я', 'ь', 'й']:
                if len(word) > len(suffix) + 2 and word.endswith(suffix):
                    return word[:-len(suffix)]
            return word
        
        def normalize(text: str) -> list:
            words = re.findall(r'[а-яёa-zéèêëàâäùûüôöîïçñ]{3,}', text.lower())
            return [stem_ru(w) for w in words if w not in stop_words]
        
        cand_stems = normalize(candidate)
        if len(cand_stems) < 2:
            return False
        cand_set = set(cand_stems)
        
        for existing in pool:
            exist_stems = normalize(existing)
            if len(exist_stems) < 2:
                continue
            exist_set = set(exist_stems)
            
            intersection = cand_set & exist_set
            union = cand_set | exist_set
            
            # 1. Jaccard similarity
            if union and len(intersection) / len(union) >= threshold:
                return True
            
            # 2. Containment: 50%+ слов короткого текста содержится в длинном
            smaller = min(len(cand_set), len(exist_set))
            if smaller > 0 and len(intersection) / smaller >= 0.5:
                return True
            
            # 3. Одинаковое начало (первые 2 контентных слова)
            if len(cand_stems) >= 2 and len(exist_stems) >= 2:
                if cand_stems[:2] == exist_stems[:2]:
                    return True
        
        return False

    def _get_random_bonus_variation(self, original: str, is_bonus1: bool = True) -> str:
        """
        Возвращает оригинальное описание бонуса БЕЗ модификаций.
        
        ВАЖНО: Для испанского сценария мы передаём бонус напрямую в AI,
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
        "un jugador", "alguien en el stream", "un apostador", "este tipo",
        "un jugador aleatorio", "un tipo común", 
        "un tipo", "nuestro héroe", "un tipo en el stream", "este jugador",
        "un valiente", "un tipo arriesgado", "un afortunado", "un suertudo",
        "un atrevido", "un chico", "un apostador en el stream", "un tío",
        "uno valiente", "un jugador en el stream", "este afortunado", "el ganador",
        "alguien", "el protagonista", "este usuario", "un usuario"
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
            # Короткий текст для гиперссылки (ESPAÑOL)
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
        - Удаление AI-преамбул
        - Замена бэктиков на HTML <code>
        - Замена Markdown на HTML
        - Форматирование названия слота
        """
        import re

        # 0. Удаление AI-преамбул
        ai_preamble_patterns = [
            r'^(?:aqu[ií]\s+)?(?:est[áa]\s+)?(?:mi\s+)?(?:versi[oó]n|variante)\s+del\s+(?:post|texto)\s*[:\.!\-—–]\s*\n*',
            r'^(?:aqu[ií]\s+)?(?:tienes?\s+)?(?:el\s+)?(?:post|texto)\s*[:\.!\-—–]\s*\n*',
            r'^(?:here\s*(?:is|\'s)\s+)?(?:the\s+|my\s+)?(?:post|text|variant)\s*[:\.!\-—]\s*\n*',
            r'^(?:вот\s+)?(?:мой\s+)?вариант\s+поста\s*[:\.!\-—–]\s*\n*',
            r'^(?:por\s+supuesto[,!]?\s*)?(?:aqu[ií]\s+)?(?:est[áa]\s+)?(?:el\s+)?(?:post|texto)\s*[:\.!\-—–]\s*\n*',
            r'^claro[,!]?\s*(?:aqu[ií]\s+)?(?:est[áa]\s+)?(?:el\s+)?(?:post|texto)\s*[:\.!\-—–]\s*\n*',
        ]
        for p in ai_preamble_patterns:
            text = re.sub(p, '', text, count=1, flags=re.IGNORECASE | re.MULTILINE)
        text = text.lstrip('\n')

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
            r'^La publicación[:\.]?\s*',
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
        Заменяет символы валюты в тексте на случайные форматы для разнообразия (ESPAÑOL).
        Например: 500$ → 500 dólares, 1000€ → 1000 euros
        """
        import re
        
        currency = video.currency.upper()
        
        # Определяем форматы для каждой валюты (испанские)
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
        # Для испанского сценария используется только url1
        
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

                    try:
                        response = await asyncio.wait_for(
                            self.client.chat.completions.create(**api_params),
                            timeout=120
                        )
                    except asyncio.TimeoutError:
                        print(f"   ⏰ Таймаут 120с для модели {self.model}, попытка {attempt + 1}/3")
                        sys.stdout.flush()
                        if attempt == 2:
                            raise Exception(f"Таймаут: модель {self.model} не ответила за 120с (3 попытки)")
                        await asyncio.sleep(2)
                        continue

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
                # _filter_non_russian НЕ используем для испанского - она для русского
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
                
                try:
                    response = await asyncio.wait_for(
                        self.client.chat.completions.create(**api_params),
                        timeout=120
                    )
                except asyncio.TimeoutError:
                    raise Exception(f"Таймаут: модель {self.model} не ответила за 120с")
                
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
    
    UNIQUENESS_CHECK_PROMPT = """Eres un experto en verificación de unicidad de contenido para Telegram.

⚠️ IMPORTANTE: Las líneas con URLs y descripciones de bonos/promociones ya han sido ELIMINADAS de los textos.
Compara SOLO el texto principal del autor.

Te dan {count} publicaciones. Tu tarea es encontrar publicaciones SIMILARES.

CRITERIOS DE SIMILITUD (si al menos 1 coincide - es un duplicado):
1. Inicio idéntico (primeras 5-10 palabras coinciden o son muy similares en significado)
2. Estructura idéntica (ambos comienzan con pregunta / ambos con exclamación / ambos con número)
3. Frases repetidas (3+ palabras seguidas aparecen en ambos posts)
4. Significado similar (describen lo mismo con palabras diferentes, misma "historia")
5. Patrones emoji idénticos (ambos comienzan con mismos emojis, ambos terminan igual)
6. ELEMENTOS DE PLANTILLA (¡esto es CRÍTICO!):
   - "BOTÓN №1", "BOTÓN №2" o marcadores similares
   - Separadores idénticos (—•—🍉🔥🍓—•—, ◈◈◈, ~~~)
   - Designaciones idénticas de enlaces ("👇 primero 👇", "👇 segundo 👇")
   - Estructura repetida de colocación de enlaces (ambos al inicio/ambos al final/ambos entre párrafos)

PUBLICACIONES PARA ANÁLISIS:
{posts_json}

RESPONDE ESTRICTAMENTE EN FORMATO JSON (sin markdown, sin ```json):
{{
  "duplicates": [
    {{"post1": 3, "post2": 17, "reason": "inicio idéntico: 'Mira lo que está pasando'", "similarity": 85}},
    {{"post1": 8, "post2": 45, "reason": "repetición de frase: 'el resultado simplemente explotó'", "similarity": 70}}
  ],
  "warnings": [
    {{"post": 5, "issue": "publicación demasiado corta"}},
    {{"post": 12, "issue": "sin llamada a la acción"}}
  ],
  "total_unique": 78,
  "total_duplicates": 2,
  "summary": "Se encontraron 2 pares de publicaciones similares de 80. Recomiendo regenerar posts #17 y #45."
}}

Si TODAS las publicaciones son únicas:
{{
  "duplicates": [],
  "warnings": [],
  "total_unique": {count},
  "total_duplicates": 0,
  "summary": "¡Todas las {count} publicaciones son únicas! Excelente trabajo."
}}

IMPORTANTE: 
- Verifica TODOS los pares de publicaciones
- Considera posts para UN slot - suelen ser más similares
- similarity - porcentaje de similitud (50-100)
- Responde SOLO JSON, sin explicaciones"""

    @staticmethod
    def _strip_link_blocks_for_comparison(text: str) -> str:
        """
        Удаляет строки с URL и прилегающие описания бонусов для проверки уникальности.
        Оставляет только основной авторский текст.
        """
        import re
        lines = text.split('\n')
        cleaned = []
        skip_next_empty = False
        
        for line in lines:
            stripped = line.strip()
            if re.search(r'https?://\S+', stripped):
                skip_next_empty = True
                continue
            if skip_next_empty and not stripped:
                skip_next_empty = False
                continue
            skip_next_empty = False
            if re.match(r'^[\s—═◈~•\-─━▸▹→←↓↑⬇⬆👇👆🔗🔹🔥🎁🎰💰💵·]+$', stripped):
                continue
            if re.match(r'^\[.+\]\(https?://.+\)$', stripped):
                continue
            lower = stripped.lower()
            bonus_cta = ['забрать', 'бонус', 'депозит', 'пополнен', 'фриспин', 'вращени', 
                        'спин', 'промокод', 'регистрац', 'лёгкий вход', 'полный пакет',
                        'bonus', 'free spin', 'deposit', 'tour', 'gir']
            if any(cta in lower for cta in bonus_cta) and len(stripped) < 120:
                if re.search(r'https?://|cutt\.ly|bit\.ly|t\.me', lower):
                    continue
            cleaned.append(line)
        
        result = '\n'.join(cleaned).strip()
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result

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
            cleaned = self._strip_link_blocks_for_comparison(post)
            posts_data.append({
                "id": i + 1,
                "slot": slot,
                "text": cleaned[:400] + "..." if len(cleaned) > 400 else cleaned
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
                    
                    # ═══════════════════════════════════════════════════
                    # РОБАСТНЫЙ ПАРСИНГ JSON ОТ GEMINI
                    # ═══════════════════════════════════════════════════
                    import re
                    
                    def repair_json(text):
                        """
                        Комплексное восстановление невалидного JSON от AI.
                        Обрабатывает: markdown обёртки, комментарии, trailing commas,
                        control characters, переносы в строках, одинарные кавычки,
                        ключи без кавычек, Python True/False/None.
                        """
                        # 1. Убираем markdown обёртки
                        text = text.strip()
                        if text.startswith("```json"):
                            text = text[7:]
                        elif text.startswith("```"):
                            text = text[3:]
                        if text.endswith("```"):
                            text = text[:-3]
                        text = text.strip()
                        
                        # 2. Убираем однострочные комментарии //
                        text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
                        
                        # 3. Убираем trailing commas перед } и ]
                        text = re.sub(r',(\s*[}\]])', r'\1', text)
                        
                        # 4. Убираем невалидные control characters (кроме \n, \r, \t)
                        cleaned = []
                        for char in text:
                            code = ord(char)
                            if code >= 32 or code in (9, 10, 13):
                                cleaned.append(char)
                        text = ''.join(cleaned)
                        
                        # 5. Заменяем literal \n внутри JSON строк на пробелы
                        result_chars = []
                        in_string = False
                        escape = False
                        for char in text:
                            if escape:
                                result_chars.append(char)
                                escape = False
                                continue
                            if char == '\\':
                                escape = True
                                result_chars.append(char)
                                continue
                            if char == '"':
                                in_string = not in_string
                                result_chars.append(char)
                                continue
                            if in_string and char == '\n':
                                result_chars.append(' ')
                            else:
                                result_chars.append(char)
                        text = ''.join(result_chars)
                        
                        # 6. Заменяем Python-стиль True/False/None на JSON true/false/null
                        text = re.sub(r'\bTrue\b', 'true', text)
                        text = re.sub(r'\bFalse\b', 'false', text)
                        text = re.sub(r'\bNone\b', 'null', text)
                        
                        # 7. Заменяем одинарные кавычки на двойные (ключи и значения)
                        text = re.sub(r"(?<=[\[{,:\s])\s*'([^']*?)'\s*(?=\s*[:,\]}])", r'"\1"', text)
                        
                        # 8. Ключи без кавычек: {key: "value"} → {"key": "value"}
                        text = re.sub(r'(?<=[{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r' "\1":', text)
                        
                        return text
                    
                    def try_fix_truncated(text):
                        """Попытка починить оборванный JSON с учётом порядка вложенности"""
                        text = re.sub(r'"[^"]*$', '', text)
                        text = re.sub(r',\s*"[^"]*"\s*:\s*$', '', text)
                        text = re.sub(r',\s*\{[^}]*$', '', text)
                        text = re.sub(r'"[^"]*"\s*:\s*$', '', text)
                        text = text.rstrip().rstrip(',').rstrip()
                        
                        stack = []
                        in_string = False
                        escape = False
                        for char in text:
                            if escape:
                                escape = False
                                continue
                            if char == '\\':
                                escape = True
                                continue
                            if char == '"':
                                in_string = not in_string
                                continue
                            if in_string:
                                continue
                            if char == '{':
                                stack.append('}')
                            elif char == '[':
                                stack.append(']')
                            elif char in ('}', ']') and stack and stack[-1] == char:
                                stack.pop()
                        
                        text += ''.join(reversed(stack))
                        return text
                    
                    content = repair_json(content)
                    
                    result = None
                    parse_error = None
                    
                    # Попытка 1: прямой парсинг после repair_json
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError as e:
                        parse_error = e
                    
                    # Попытка 2: починить оборванный JSON
                    if result is None:
                        try:
                            fixed = try_fix_truncated(content)
                            result = json.loads(fixed)
                            if isinstance(result, dict):
                                result.setdefault("warnings", [])
                                result["warnings"].append("⚠️ JSON был оборван, автоматически исправлено")
                        except json.JSONDecodeError:
                            pass
                    
                    # Попытка 3: извлечь JSON регексом
                    if result is None:
                        json_match = re.search(r'\{[\s\S]*\}', content)
                        if json_match:
                            extracted = json_match.group()
                            try:
                                result = json.loads(extracted)
                            except json.JSONDecodeError:
                                try:
                                    fixed = try_fix_truncated(extracted)
                                    result = json.loads(fixed)
                                    if isinstance(result, dict):
                                        result.setdefault("warnings", [])
                                        result["warnings"].append("⚠️ JSON извлечён и восстановлен из ответа AI")
                                except json.JSONDecodeError:
                                    pass
                    
                    # Попытка 4: построить минимальный ответ из текста
                    if result is None:
                        try:
                            dup_matches = re.findall(
                                r'\{\s*"post1"\s*:\s*(\d+)\s*,\s*"post2"\s*:\s*(\d+)\s*,\s*"reason"\s*:\s*"([^"]*)"',
                                content
                            )
                            if dup_matches:
                                duplicates = [
                                    {"post1": int(m[0]), "post2": int(m[1]), "reason": m[2], "similarity": 70}
                                    for m in dup_matches
                                ]
                                result = {
                                    "duplicates": duplicates,
                                    "warnings": ["⚠️ JSON восстановлен частично из ответа AI"],
                                    "total_unique": len(posts) - len(duplicates),
                                    "total_duplicates": len(duplicates),
                                    "summary": f"Найдено {len(duplicates)} пар похожих постов (JSON восстановлен частично)"
                                }
                        except Exception:
                            pass
                    
                    # Все попытки провалились — возвращаем ошибку
                    if result is None:
                        e = parse_error
                        return {
                            "is_unique": True,
                            "duplicates": [],
                            "warnings": [],
                            "total_unique": len(posts),
                            "total_duplicates": 0,
                            "summary": "⚠️ Проверка завершена с ошибкой парсинга JSON. Посты считаются уникальными по умолчанию.",
                            "error": f"Ошибка парсинга JSON: {str(e)}. AI вернул невалидный JSON.",
                            "model_used": model_info["name"],
                            "raw_response": original_content[:1000],
                            "error_details": {
                                "error_type": type(e).__name__ if e else "Unknown",
                                "error_msg": str(e) if e else "Unknown",
                                "content_length": len(original_content)
                            }
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

