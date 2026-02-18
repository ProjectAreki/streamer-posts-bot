"""
@file: caption_parser.py
@description: Парсер данных из подписей к видео в Telegram
@dependencies: re
@created: 2026-01-05
"""

import re
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class ParsedCaption:
    """Распарсенные данные из подписи"""
    slot: str = ""
    win: float = 0.0  # Изменено на float для поддержки дробных сумм
    bet: float = 0.0  # Изменено на float для поддержки ставок < 1 (0.8 USD и т.д.)
    streamer: str = ""
    multiplier: float = 0.0
    currency: str = "RUB"  # Валюта: RUB, USD, EUR и т.д.
    
    def __post_init__(self):
        if self.bet > 0 and self.win > 0 and self.multiplier == 0:
            self.multiplier = round(self.win / self.bet, 1)
    
    def is_valid(self) -> bool:
        """Проверяет что есть минимум слот, ставка и выигрыш"""
        return bool(self.slot and self.bet > 0 and self.win > 0)


class CaptionParser:
    """
    Парсер подписей к видео.
    
    Поддерживаемые форматы:
    
    Формат 1 (построчный):
        слот Rip City
        выигрыш 644580.00 р
        ставка 300 р
    
    Формат 2 (с двоеточием):
        Слот: Gates of Olympus
        Выигрыш: 125 000₽
        Ставка: 500₽
    
    Формат 3 (компактный):
        Gates of Olympus | 500₽ → 125000₽
    
    Формат 4 (с эмодзи):
        🎰 Sweet Bonanza
        💰 89 000 р
        💵 200 р
    """
    
    # Паттерны для извлечения данных
    PATTERNS = {
        # Слот
        'slot': [
            r'[сc]лот[:\s]+([^\n\r]+)',  # слот/cлот Rip City (кириллица/латиница)
            r'ranura[:\s]+([^\n\r]+)',  # ranura: Mvertos Mvltiplier Megaways (испанский)
            r'[Ss]lot[:\s]+([^\n\r]+)',  # Slot: Dragon Hero (итальянский/английский)
            r'🎰\s*([^\n\r]+)',  # 🎰 Sweet Bonanza
            r'игра[:\s]+([^\n\r]+)',  # игра: ...
            r'продукт[:\s]+([^\n\r]+)',  # продукт: ...
        ],
        # Выигрыш
        'win': [
            r'выигрыш[:\s]*[$₽€£\s]*([\d\s,.]+)',  # выигрыш $ 6609.50 или выигрыш 644580.00
            r'ganancia[:\s]*[$₽€£\s]*([\d\s,.]+)',  # Ganancia: 498.095$ (испанский)
            r'[Vv]incita[:\s]*[$₽€£\s]*([\d\s,.]+)',  # Vincita: 505 € (итальянский)
            r'💰\s*[$₽€£\s]*([\d\s,.]+)',  # 💰 $ 89 000
            r'получил[:\s]*[$₽€£\s]*([\d\s,.]+)',  # получил $ 125000
            r'забрал[:\s]*[$₽€£\s]*([\d\s,.]+)',  # забрал $ 125000
            r'вин[:\s]*[$₽€£\s]*([\d\s,.]+)',  # вин: $ 125000
            r'win[:\s]*[$₽€£\s]*([\d\s,.]+)',  # win: $ 125000
            r'→\s*[$₽€£\s]*([\d\s,.]+)',  # → $ 125000
        ],
        # Ставка
        'bet': [
            r'[сc]тавка[:\s]*[$₽€£\s]*([\d\s,.]+)',  # ставка/cтавка 1 USD (кириллица/латиница)
            r'apuesta[:\s]*[$₽€£\s]*([\d\s,.]+)',  # Apuesta: 100$ (испанский)
            r'[Pp]untata[:\s]*[$₽€£\s]*([\d\s,.]+)',  # Puntata: 50 € (итальянский)
            r'💵\s*[$₽€£\s]*([\d\s,.]+)',  # 💵 $ 200
            r'вход[:\s]*[$₽€£\s]*([\d\s,.]+)',  # вход: $ 500
            r'бет[:\s]*[$₽€£\s]*([\d\s,.]+)',  # бет: $ 500
            r'bet[:\s]*[$₽€£\s]*([\d\s,.]+)',  # bet: $ 500
        ],
        # Стример (опционально)
        'streamer': [
            r'стример[:\s]+([^\n\r|]+)',  # стример: Жека
            r'👤\s*([^\n\r|]+)',  # 👤 Жека
            r'игрок[:\s]+([^\n\r|]+)',  # игрок: ...
            r'ни[кk][:\s]+([^\n\r|]+)',  # ник/нik: Gena88 (кириллица/латиница)
            r'nick[:\s]+([^\n\r|]+)',  # nick: Gena88
            r'@([A-Za-z0-9_]+)',  # @username (Telegram username, только английский)
            r'^([А-Яа-яA-Za-z0-9_]{2,20})\s*[|:]',  # Gena88 | или Жека: или Gena88:
            r'^([А-Яа-яA-Za-z0-9_]{2,20})\s+',  # Gena88 или Жека в начале строки
            r'([А-Яа-яA-Za-z0-9_]{2,20})\s*$',  # Gena88 или Жека в конце строки (если нет других данных)
            r'([А-Яа-яA-Za-z0-9_]{2,20})\s*[|]\s*[А-Яа-яA-Za-z]',  # Имя | Слот (в начале данных)
        ],
        # Множитель (опционально)
        'multiplier': [
            r'[xхXХ]([\d.,]+)',  # x250 или Х6609 (русская и английская X)
            r'множитель[:\s]*([\d.,]+)',  # множитель: 250
            r'📊\s*[xхXХ]?([\d.,]+)',  # 📊 x250
        ],
    }
    
    @classmethod
    def parse(cls, caption: str) -> ParsedCaption:
        """
        Парсит подпись и извлекает данные.
        
        Args:
            caption: Текст подписи к видео
            
        Returns:
            ParsedCaption с извлечёнными данными
        """
        if not caption:
            return ParsedCaption()
        
        # Убираем markdown форматирование (**text** -> text)
        caption_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', caption)
        # Убираем другие markdown теги
        caption_clean = re.sub(r'`([^`]+)`', r'\1', caption_clean)
        caption_clean = re.sub(r'_([^_]+)_', r'\1', caption_clean)
        
        # Замена кириллических символов-двойников на цифры (OCR/копирование)
        # Только в контексте чисел: "З 641 490" -> "3 641 490", "О" рядом с цифрами -> "0"
        caption_clean = re.sub(r'(?<=\d)[\sЗз](?=\d)', lambda m: ' ' if m.group().isspace() else '3', caption_clean)
        caption_clean = re.sub(r'(?<=[\s:$₽€£])З(?=[\s\d])', '3', caption_clean)
        caption_clean = re.sub(r'(?<=[\s:$₽€£])з(?=[\s\d])', '3', caption_clean)
        caption_clean = re.sub(r'(?<=\d)О(?=\d)', '0', caption_clean)
        caption_clean = re.sub(r'(?<=\d)о(?=\d)', '0', caption_clean)
        
        text = caption_clean.lower()
        result = ParsedCaption()
        
        # Извлекаем слот
        for pattern in cls.PATTERNS['slot']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.slot = match.group(1).strip()
                # Убираем лишние символы в конце
                result.slot = re.sub(r'[₽рp\d\s]+$', '', result.slot).strip()
                break
        
        # Извлекаем выигрыш
        for pattern in cls.PATTERNS['win']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                win_str = match.group(1)
                result.win = cls._parse_number(win_str)
                break
        
        # Извлекаем ставку
        for pattern in cls.PATTERNS['bet']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bet_str = match.group(1)
                result.bet = cls._parse_number(bet_str)
                break
        
        # Извлекаем стримера (опционально) - поддержка русских и английских ников
        # Список запрещённых слов, которые НЕ являются никами стримеров
        FORBIDDEN_STREAMER_WORDS = {
            'ставка', 'ставки', 'слот', 'слоты', 'выигрыш', 'выигрыша', 'выиграл',
            'игра', 'игры', 'бонус', 'бонуса', 'бонусы', 'спин', 'спины', 'спинов',
            'руб', 'рубль', 'рублей', 'рублях', 'usd', 'eur', 'euro', 'евро', 'доллар',
            'множитель', 'мульт', 'итог', 'итого', 'результат', 'победа', 'вход',
            'депозит', 'баланс', 'профит', 'прибыль', 'сумма', 'bet', 'win', 'slot',
            'игрок', 'стример', 'ник', 'nick', 'name', 'казино', 'casino',
            'фриспины', 'фриспин', 'freespin', 'freespins', 'free', 'spin',
            # Испанские слова (чтобы не путать с никами)
            'apuesta', 'ganancia', 'ranura',
            # Итальянские слова (чтобы не путать с никами)
            'puntata', 'vincita', 'scommessa', 'giocatore', 'slot',
            # ⚠️ КРИТИЧНО: КОДЫ ВАЛЮТ НЕ МОГУТ БЫТЬ НИКАМИ!
            'clp', 'ars', 'mxn', 'pen', 'cop', 'uyu', 'gbp', 'rub',
            'usd', 'eur',  # дублируем в нижнем регистре для полной уверенности
        }
        
        for pattern in cls.PATTERNS['streamer']:
            match = re.search(pattern, caption, re.IGNORECASE)  # Используем оригинальный caption для сохранения регистра
            if match:
                streamer_candidate = match.group(1).strip()
                # Убираем лишние символы в начале
                streamer_candidate = re.sub(r'^[:\s|]+', '', streamer_candidate).strip()
                # Очищаем от чисел и валюты в конце ТОЛЬКО если они идут после пробела
                # Это позволяет сохранить ники типа "Player$" или "Gena88", но удалить "Gena88 500$"
                # Сначала убираем числа и валюту после пробела в конце
                streamer_candidate = re.sub(r'\s+[\d\s₽$€£.,]+$', '', streamer_candidate).strip()
                # Затем убираем только числа в самом конце (без букв перед ними)
                # Но сохраняем ники типа "Gena88" или "Player123"
                if re.search(r'[А-Яа-яA-Za-z]', streamer_candidate):
                    # Если есть буквы, оставляем как есть (ник может содержать цифры)
                    pass
                else:
                    # Если нет букв, значит это не ник
                    streamer_candidate = ""
                
                # ВАЖНО: Проверяем что это не служебное слово (ставка, слот и т.д.)
                if streamer_candidate.lower() in FORBIDDEN_STREAMER_WORDS:
                    continue  # Пропускаем это совпадение, ищем дальше
                
                # ⚠️ КРИТИЧЕСКАЯ ПРОВЕРКА: Исключаем множители типа X1265, Х6609
                # Паттерн: начинается с X или Х (русская/английская) и далее только цифры
                if re.match(r'^[xхXХ]\d+$', streamer_candidate):
                    continue  # Это множитель, пропускаем!
                
                # ⚠️🚨 АБСОЛЮТНЫЙ ЗАПРЕТ: Коды валют (3 заглавные латинские буквы)
                # CLP, ARS, MXN, USD, EUR, GBP, RUB, COP, PEN, UYU и т.д.
                if re.match(r'^[A-Z]{3}$', streamer_candidate):
                    continue  # Это код валюты, НЕ НИК! Пропускаем!
                
                # ⚠️ Исключаем чистые числа или числа с символами: 202, 512, 1265
                if re.match(r'^\d+[.,]?\d*$', streamer_candidate):
                    continue  # Это число, пропускаем!
                
                # ⚠️ Исключаем паттерны типа "Eye of Spartacus" (названия слотов из данных)
                # Если в названии есть " of ", это скорее всего слот
                if ' of ' in streamer_candidate.lower():
                    continue  # Это название слота, пропускаем!
                
                # Проверяем что это не пусто и не похоже на число/валюту
                # Должен содержать хотя бы одну букву (русскую или английскую)
                if streamer_candidate and len(streamer_candidate) >= 2:
                    # Проверяем что есть хотя бы одна буква (не только цифры и символы)
                    if re.search(r'[А-Яа-яA-Za-z]', streamer_candidate):
                        # Проверяем что это не похоже на число/валюту
                        if not re.match(r'^[\d\s₽$€£.,]+$', streamer_candidate):
                            # ⚠️ ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Убеждаемся что это не название слота
                            # Если кандидат совпадает с уже найденным слотом - пропускаем
                            if result.slot and streamer_candidate.lower() == result.slot.lower():
                                continue  # Это название слота, пропускаем!
                            
                            result.streamer = streamer_candidate
                            break
        
        # Извлекаем множитель (опционально)
        for pattern in cls.PATTERNS['multiplier']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    result.multiplier = float(match.group(1).replace(',', '.'))
                except Exception:
                    pass
                break
        
        # Вычисляем множитель если не указан
        if result.multiplier == 0 and result.bet > 0 and result.win > 0:
            result.multiplier = round(result.win / result.bet, 1)
        
        # Извлекаем валюту из строк выигрыша и ставки
        # Приоритет: явное указание валюты рядом с числами (выигрыш/ставка)
        # Используем очищенную версию без markdown
        caption_for_currency = caption_clean
        
        # Ищем валюту в строках с выигрышем и ставкой
        # Паттерны: "выигрыш 1235 USD", "ставка 1 USD", "выигрыш 2 262 700 руб", "выигрыш 10000.00 евро"
        # Также испанские: "Apuesta: 100$", "Ganancia: 498.095$"
        currency_found = False
        
        # 1. Ищем USD (явное указание включая "доллар")
        if re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:USD|\$|доллар)', caption_for_currency, re.IGNORECASE):
            result.currency = 'USD'
            currency_found = True
        # 2. Ищем EUR (явное указание включая "евро")
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:EUR|€|евро)', caption_for_currency, re.IGNORECASE):
            result.currency = 'EUR'
            currency_found = True
        # 3. Ищем GBP (явное указание включая "фунт")
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:GBP|£|фунт)', caption_for_currency, re.IGNORECASE):
            result.currency = 'GBP'
            currency_found = True
        # 4. Ищем CLP (чилийское песо)
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:CLP)', caption_for_currency, re.IGNORECASE):
            result.currency = 'CLP'
            currency_found = True
        # 5. Ищем MXN (мексиканское песо)
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:MXN)', caption_for_currency, re.IGNORECASE):
            result.currency = 'MXN'
            currency_found = True
        # 6. Ищем ARS (аргентинское песо)
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:ARS|ARG)', caption_for_currency, re.IGNORECASE):
            result.currency = 'ARS'
            currency_found = True
        # 7. Ищем COP (колумбийское песо)
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:COP)', caption_for_currency, re.IGNORECASE):
            result.currency = 'COP'
            currency_found = True
        # 8. Ищем PEN (перуанское соль)
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:PEN)', caption_for_currency, re.IGNORECASE):
            result.currency = 'PEN'
            currency_found = True
        # 9. Ищем UYU (уругвайское песо)
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:UYU)', caption_for_currency, re.IGNORECASE):
            result.currency = 'UYU'
            currency_found = True
        # 10. Ищем RUB (руб, р, RUB, ₽, рубл)
        elif re.search(r'(?:выигрыш|ставка|ganancia|apuesta|vincita|puntata|win|bet)[:\s]*[\d\s,.]+\s*(?:руб|рубл|р\b|RUB|₽)', caption_for_currency, re.IGNORECASE):
            result.currency = 'RUB'
            currency_found = True
        
        # Если не нашли в строках выигрыша/ставки, ищем во всем тексте
        if not currency_found:
            # СНАЧАЛА проверяем символы валюты (приоритет выше чем слова)
            if '$' in caption_for_currency or re.search(r'\d+\s*\$\s*|\$\s*\d+', caption_for_currency):
                result.currency = 'USD'
                currency_found = True
            elif '€' in caption_for_currency or re.search(r'\d+\s*€\s*|€\s*\d+', caption_for_currency):
                result.currency = 'EUR'
                currency_found = True
            elif '£' in caption_for_currency or re.search(r'\d+\s*£\s*|£\s*\d+', caption_for_currency):
                result.currency = 'GBP'
                currency_found = True
            elif '₽' in caption_for_currency or re.search(r'\d+\s*₽\s*|₽\s*\d+', caption_for_currency):
                result.currency = 'RUB'
                currency_found = True
            # Затем проверяем слова
            elif re.search(r'\b(?:USD|доллар)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'USD'
            elif re.search(r'\b(?:EUR|евро)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'EUR'
            elif re.search(r'\b(?:GBP|фунт)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'GBP'
            elif re.search(r'\b(?:CLP)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'CLP'
            elif re.search(r'\b(?:MXN)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'MXN'
            elif re.search(r'\b(?:ARS|ARG)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'ARS'
            elif re.search(r'\b(?:COP)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'COP'
            elif re.search(r'\b(?:PEN)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'PEN'
            elif re.search(r'\b(?:UYU)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'UYU'
            elif re.search(r'\b(?:руб|рубл|р\b|RUB)\b', caption_for_currency, re.IGNORECASE):
                result.currency = 'RUB'
            # По умолчанию USD для испанского сценария (если ничего не найдено, но есть числа)
            elif re.search(r'\d+', caption_for_currency):
                result.currency = 'USD'  # По умолчанию USD для испанского сценария
            # Иначе RUB (для русского сценария)
        
        return result
    
    @staticmethod
    def _parse_number(s: str) -> float:
        """Парсит число из строки (возвращает float для поддержки дробных сумм)"""
        # Убираем пробелы
        s = s.replace(' ', '')
        
        # Определяем формат числа:
        # Если есть несколько точек/запятых - это разделители тысяч
        # Если одна точка/запятая и после нее 1-2 цифры - это десятичный разделитель
        
        dot_count = s.count('.')
        comma_count = s.count(',')
        
        # Случай 1: несколько точек (разделители тысяч) - удаляем их
        # Пример: 17.086.780 или 19.000 (испанский формат)
        if dot_count > 1:
            s = s.replace('.', '')
        # Случай 2: одна точка и несколько запятых (точка - десятичная, запятые - тысячи)
        # Пример: 1,234,567.89
        elif dot_count == 1 and comma_count > 0:
            s = s.replace(',', '')  # Удаляем запятые-разделители
            # Точка остается как десятичный разделитель
        # Случай 3: несколько запятых (разделители тысяч) - удаляем их
        # Пример: 1,234,567
        elif comma_count > 1:
            s = s.replace(',', '')
        # Случай 4: одна запятая (может быть десятичным разделителем или разделителем тысяч)
        elif comma_count == 1:
            # Если после запятой 1-2 цифры - это десятичный разделитель
            # Иначе - это разделитель тысяч
            parts = s.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                s = s.replace(',', '.')  # Десятичный разделитель
            else:
                s = s.replace(',', '')  # Разделитель тысяч
        # Случай 5: одна точка (может быть десятичным разделителем или разделителем тысяч)
        elif dot_count == 1:
            parts = s.split('.')
            if len(parts) == 2:
                # Если после точки 3 цифры - это разделитель тысяч (испанский формат: 19.000)
                if len(parts[1]) == 3:
                    s = s.replace('.', '')  # Разделитель тысяч
                # Если после точки 1-2 цифры - это десятичный разделитель
                elif len(parts[1]) <= 2:
                    # Точка как десятичный разделитель - оставляем
                    pass
                else:
                    # Больше 3 цифр - скорее всего разделитель тысяч
                    s = s.replace('.', '')
            else:
                # Несколько частей - разделитель тысяч
                s = s.replace('.', '')
        
        # Убираем всё кроме цифр и точки
        cleaned = re.sub(r'[^\d.]', '', s)
        try:
            return float(cleaned) if cleaned else 0.0
        except Exception:
            return 0.0
