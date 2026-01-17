"""
@file: bonus_generator.py
@description: Генератор рандомных описаний бонусов и форматов ссылок
@dependencies: random
@created: 2026-01-05
"""

import random
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BonusConfig:
    """Конфигурация бонуса"""
    url: str
    original_description: str  # Оригинальное описание от пользователя
    # Парсированные значения
    freespins: Optional[int] = None
    deposit_bonus: Optional[int] = None  # Процент
    max_bonus: Optional[int] = None  # Максимальная сумма
    extra_freespins: Optional[int] = None


@dataclass 
class LinkFormat:
    """Формат блока ссылок"""
    id: str
    name: str
    template: str  # {url1}, {url2}, {bonus1}, {bonus2}


class BonusGenerator:
    """
    Генератор рандомных описаний бонусов и форматов ссылок.
    
    Принимает оригинальные описания бонусов от пользователя и генерирует
    множество вариаций для уникальности постов.
    """
    
    # ═══════════════════════════════════════════════════════════════════
    # ШАБЛОНЫ ОПИСАНИЙ БОНУСОВ
    # ═══════════════════════════════════════════════════════════════════
    
    # Для фриспинов
    FREESPIN_TEMPLATES = [
        "{count} бесплатных вращений",
        "{count} фриспинов",
        "{count} FS",
        "{count} бесплатных прокрутов",
        "{count} халявных спинов",
        "{count} вращений в подарок",
        "{count} круток бесплатно",
        "{count} спинов на халяву",
        "{count} бесплатных попыток",
        "{count} прокрутов без депозита",
        "Сотня фриспинов" if "{count}" == "100" else "{count} FS",
        "{count} free spins",
        "Пак {count} вращений",
        "{count} круток на старт",
        "{count} спинов бонусом",
    ]
    
    # Для депозитных бонусов
    DEPOSIT_TEMPLATES = [
        "{percent}% на депозит",
        "{percent}% к пополнению",
        "{percent}% на первый деп",
        "+{percent}% к балансу",
        "Буст {percent}%",
        "{percent}% бонус",
        "До {percent}% на депозит",
        "{percent}% к депозиту",
        "Бонус {percent}%",
        "+{percent}% на счёт",
        "{percent}% к банку",
        "Депозитный бонус {percent}%",
        "{percent}% приветственный",
        "{percent}% welcome bonus",
        "Увеличение депо на {percent}%",
    ]
    
    # Для максимальной суммы
    MAX_BONUS_TEMPLATES = [
        "до {amount}₽",
        "до {amount} RUB",
        "до {amount} рублей",
        "максимум {amount}₽",
        "потолок {amount}₽",
        "до {amount}",
        "{amount}₽ максимум",
        "лимит {amount}₽",
    ]
    
    # Комбинированные шаблоны (депозит + фриспины)
    COMBO_TEMPLATES = [
        "{deposit} + {freespins}",
        "{deposit}, плюс {freespins}",
        "{deposit} и ещё {freespins}",
        "{freespins} + {deposit}",
        "{deposit} + бонусом {freespins}",
        "{deposit} плюс {freespins} в подарок",
        "Пакет: {deposit} + {freespins}",
        "{deposit}, сверху {freespins}",
    ]
    
    # ═══════════════════════════════════════════════════════════════════
    # ФОРМАТЫ БЛОКОВ ССЫЛОК (15 вариантов)
    # ═══════════════════════════════════════════════════════════════════
    
    LINK_FORMATS = [
        LinkFormat(
            id="l1",
            name="Простые URL",
            template="""🔗 {url1}
🔗 {url2}"""
        ),
        LinkFormat(
            id="l2",
            name="Гиперссылки",
            template="""[{bonus1}]({url1})
[{bonus2}]({url2})"""
        ),
        LinkFormat(
            id="l3",
            name="Эмодзи + текст + URL",
            template="""🎁 {bonus1}: {url1}
🔥 {bonus2}: {url2}"""
        ),
        LinkFormat(
            id="l4",
            name="Стрелки",
            template="""→ {url1} ({bonus1})
→ {url2} ({bonus2})"""
        ),
        LinkFormat(
            id="l5",
            name="Нумерация",
            template="""1. {url1} — {bonus1}
2. {url2} — {bonus2}"""
        ),
        LinkFormat(
            id="l6",
            name="Разделитель",
            template="""——————
{url1}
{url2}"""
        ),
        LinkFormat(
            id="l7",
            name="Вертикальный",
            template="""▸ {bonus1}
{url1}

▸ {bonus2}
{url2}"""
        ),
        LinkFormat(
            id="l8",
            name="Компактный",
            template="""{url1} • {url2}"""
        ),
        LinkFormat(
            id="l9",
            name="Описательный",
            template="""Лёгкий вход: {url1}
Полный пакет: {url2}"""
        ),
        LinkFormat(
            id="l10",
            name="Вопросительный",
            template="""Хочешь {bonus1}? {url1}
Или сразу {bonus2}? {url2}"""
        ),
        LinkFormat(
            id="l11",
            name="Призыв",
            template="""👉 Забрать {bonus1}: {url1}
👉 Забрать {bonus2}: {url2}"""
        ),
        LinkFormat(
            id="l12",
            name="Квадратные скобки",
            template="""[1] {bonus1} → {url1}
[2] {bonus2} → {url2}"""
        ),
        LinkFormat(
            id="l13",
            name="Двойной эмодзи",
            template="""🎰 {bonus1}
{url1}

💰 {bonus2}
{url2}"""
        ),
        LinkFormat(
            id="l14",
            name="Минималистичный",
            template="""{url1}
{url2}"""
        ),
        LinkFormat(
            id="l15",
            name="Жирные гиперссылки",
            template="""🔹 [{bonus1}]({url1})
🔥 [{bonus2}]({url2})"""
        ),
    ]
    
    def __init__(self):
        self.bonus1_config: Optional[BonusConfig] = None
        self.bonus2_config: Optional[BonusConfig] = None
        self._used_bonus1_descriptions: List[str] = []
        self._used_bonus2_descriptions: List[str] = []
        self._used_link_formats: List[str] = []
    
    def set_bonuses(self, url1: str, bonus1_desc: str, url2: str, bonus2_desc: str):
        """
        Устанавливает конфигурацию бонусов.
        
        Args:
            url1: URL первого бонуса
            bonus1_desc: Описание первого бонуса (например: "100 FS")
            url2: URL второго бонуса
            bonus2_desc: Описание второго бонуса (например: "150% + 500 FS + 30000₽")
        """
        self.bonus1_config = BonusConfig(
            url=url1,
            original_description=bonus1_desc
        )
        self._parse_bonus(self.bonus1_config)
        
        self.bonus2_config = BonusConfig(
            url=url2,
            original_description=bonus2_desc
        )
        self._parse_bonus(self.bonus2_config)
        
        # Сброс использованных вариантов
        self._used_bonus1_descriptions = []
        self._used_bonus2_descriptions = []
        self._used_link_formats = []
    
    def _parse_bonus(self, config: BonusConfig):
        """Парсит описание бонуса и извлекает значения"""
        desc = config.original_description.lower()
        
        # Ищем фриспины
        import re
        fs_match = re.search(r'(\d+)\s*(?:fs|фриспин|вращени|спин|крут|прокрут)', desc)
        if fs_match:
            config.freespins = int(fs_match.group(1))
        
        # Ищем процент депозита
        dep_match = re.search(r'(\d+)\s*%', desc)
        if dep_match:
            config.deposit_bonus = int(dep_match.group(1))
        
        # Ищем максимальную сумму
        max_match = re.search(r'(\d[\d\s]*)\s*(?:₽|руб|rub)', desc)
        if max_match:
            config.max_bonus = int(max_match.group(1).replace(' ', ''))
        
        # Если есть два числа фриспинов, второе - дополнительные
        all_fs = re.findall(r'(\d+)\s*(?:fs|фриспин|вращени|спин|крут|прокрут)', desc)
        if len(all_fs) > 1:
            config.freespins = int(all_fs[0])
            config.extra_freespins = int(all_fs[1])
    
    def generate_bonus_description(self, config: BonusConfig, avoid_used: bool = True) -> str:
        """
        Генерирует случайное описание бонуса.
        
        Args:
            config: Конфигурация бонуса
            avoid_used: Избегать уже использованных вариантов
        """
        if not config:
            return ""
        
        variants = []
        
        # Генерируем варианты на основе парсированных данных
        if config.freespins and not config.deposit_bonus:
            # Только фриспины
            for template in self.FREESPIN_TEMPLATES:
                variants.append(template.format(count=config.freespins))
        
        elif config.deposit_bonus and not config.freespins:
            # Только депозит
            for template in self.DEPOSIT_TEMPLATES:
                variant = template.format(percent=config.deposit_bonus)
                if config.max_bonus:
                    variant += f" до {config.max_bonus}₽"
                variants.append(variant)
        
        elif config.deposit_bonus and config.freespins:
            # Комбинация
            deposit_parts = [t.format(percent=config.deposit_bonus) for t in self.DEPOSIT_TEMPLATES[:5]]
            fs_parts = [t.format(count=config.freespins) for t in self.FREESPIN_TEMPLATES[:5]]
            
            for combo in self.COMBO_TEMPLATES:
                for dep in deposit_parts:
                    for fs in fs_parts:
                        variant = combo.format(deposit=dep, freespins=fs)
                        if config.max_bonus:
                            variant += f" (до {config.max_bonus}₽)"
                        variants.append(variant)
        
        else:
            # Не удалось распарсить - используем оригинал
            variants = [config.original_description]
        
        # Фильтруем уже использованные
        if avoid_used:
            used_list = self._used_bonus1_descriptions if config == self.bonus1_config else self._used_bonus2_descriptions
            available = [v for v in variants if v not in used_list]
            if not available:
                # Все использованы - сбрасываем
                used_list.clear()
                available = variants
            
            choice = random.choice(available)
            used_list.append(choice)
            return choice
        
        return random.choice(variants)
    
    def generate_bonus1(self, avoid_used: bool = True) -> str:
        """Генерирует описание первого бонуса"""
        return self.generate_bonus_description(self.bonus1_config, avoid_used)
    
    def generate_bonus2(self, avoid_used: bool = True) -> str:
        """Генерирует описание второго бонуса"""
        return self.generate_bonus_description(self.bonus2_config, avoid_used)
    
    def get_random_link_format(self, avoid_used: bool = True) -> LinkFormat:
        """Возвращает случайный формат ссылок"""
        if avoid_used:
            available = [f for f in self.LINK_FORMATS if f.id not in self._used_link_formats]
            if not available:
                self._used_link_formats.clear()
                available = self.LINK_FORMATS
            
            choice = random.choice(available)
            self._used_link_formats.append(choice.id)
            return choice
        
        return random.choice(self.LINK_FORMATS)
    
    def generate_links_block(self, avoid_used: bool = True) -> str:
        """
        Генерирует готовый блок ссылок с бонусами.
        
        Returns:
            Отформатированный блок ссылок
        """
        if not self.bonus1_config or not self.bonus2_config:
            return ""
        
        link_format = self.get_random_link_format(avoid_used)
        bonus1 = self.generate_bonus1(avoid_used)
        bonus2 = self.generate_bonus2(avoid_used)
        
        result = link_format.template.format(
            url1=self.bonus1_config.url,
            url2=self.bonus2_config.url,
            bonus1=bonus1,
            bonus2=bonus2
        )
        
        return result
    
    def get_all_link_formats(self) -> List[LinkFormat]:
        """Возвращает все форматы ссылок"""
        return self.LINK_FORMATS
    
    def reset_used(self):
        """Сбрасывает списки использованных вариантов"""
        self._used_bonus1_descriptions.clear()
        self._used_bonus2_descriptions.clear()
        self._used_link_formats.clear()


# Тестирование
if __name__ == "__main__":
    generator = BonusGenerator()
    
    # Настраиваем бонусы
    generator.set_bonuses(
        url1="https://example1.com",
        bonus1_desc="100 FS",
        url2="https://example2.com",
        bonus2_desc="150% + 500 FS + 30000₽"
    )
    
    print("🎁 Варианты бонуса 1:")
    for i in range(5):
        print(f"  {i+1}. {generator.generate_bonus1()}")
    
    print("\n🎁 Варианты бонуса 2:")
    for i in range(5):
        print(f"  {i+1}. {generator.generate_bonus2()}")
    
    print("\n🔗 Примеры блоков ссылок:")
    for i in range(3):
        print(f"\n--- Вариант {i+1} ---")
        print(generator.generate_links_block())



