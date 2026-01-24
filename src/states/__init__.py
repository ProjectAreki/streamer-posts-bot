"""
@file: __init__.py
@description: FSM States для всех сценариев бота NinjaVideoBot
@dependencies: aiogram.fsm.state
@created: 2026-01-12
"""

from aiogram.fsm.state import State, StatesGroup


class GenerateLinksStates(StatesGroup):
    """Состояния для генерации ссылок"""
    waiting_for_ai_provider = State()  # 🆕 Выбор AI провайдера
    waiting_for_openai_model = State()  # 🆕 Выбор модели OpenAI
    waiting_for_generation_style = State()  # 🎨 Выбор стиля генерации текста
    waiting_for_text_obfuscation = State()  # 🎭 Выбор маскировки текста
    waiting_for_hide_slot_names = State()  # 🎯 Скрыть названия слотов
    waiting_for_links_mode = State()  # 🆕 Выбор способа ввода ссылок (генерация или готовые)
    waiting_for_custom_links = State()  # 🆕 Ввод готовых ссылок
    waiting_for_link = State()
    waiting_for_count = State()
    waiting_for_direction = State()
    waiting_for_range = State()


class BatchProcessStates(StatesGroup):
    """Состояния для пакетной обработки"""
    waiting_for_link = State()
    waiting_for_count = State()
    waiting_for_channel = State()


class AdUnifyStates(StatesGroup):
    """Состояния для уникализации рекламы и объединения с постом"""
    waiting_for_style_choice = State()  # 🆕 Выбор стиля генерации
    waiting_for_ai_provider_ads = State()  # 🆕 Выбор AI провайдера для рекламы
    waiting_for_openai_model_ads = State()  # 🆕 Выбор модели OpenAI для рекламы
    waiting_for_text_obfuscation = State()  # 🎭 Выбор маскировки текста
    waiting_for_hide_slot_names = State()  # 🎯 Скрыть названия слотов
    waiting_for_post_channel = State()
    waiting_for_start_post = State()
    waiting_for_ad_channel = State()
    waiting_for_target_channel = State()
    waiting_for_order_ads_only = State()
    waiting_for_count = State()
    # Разделяем состояние ввода количества для сценария "Только реклама"
    waiting_for_count_ads_only = State()
    # Состояния для сценария "Только реклама" с указанием ссылок
    waiting_for_first_link = State()
    waiting_for_second_link = State()
    # Путь: обработка пересланной рекламы
    waiting_for_forwarded_ad = State()
    waiting_for_target_forwarded = State()


class ChannelSelectionStates(StatesGroup):
    """Состояния для выбора канала"""
    waiting_for_channel_choice = State()
    waiting_for_channel_search = State()
    waiting_for_channel_input = State()
    # 🆕 Мульти-канальная публикация
    selecting_multiple_channels = State()  # Выбор нескольких каналов галочками
    confirming_distribution = State()  # Подтверждение распределения постов


class LinkReplaceStates(StatesGroup):
    """Состояния для сценария замены ссылок (формат B — перепубликация)."""
    waiting_for_channel = State()
    waiting_for_old1 = State()
    waiting_for_new1 = State()
    waiting_for_old2 = State()
    waiting_for_new2 = State()
    waiting_for_mode = State()
    waiting_for_confirm = State()


class LinkReplaceWithHyperlinksStates(StatesGroup):
    """Состояния для сценария замены ссылок с созданием гиперссылок."""
    waiting_for_channel = State()
    waiting_for_post_count = State()  # Выбор количества постов (25 или 40)
    waiting_for_texts_link1 = State()  # Ввод текстов для первой ссылки
    waiting_for_texts_link2 = State()  # Ввод текстов для второй ссылки
    waiting_for_format_choice = State()  # Выбор формата: гиперссылки или ссылка + текст
    showing_found_links = State()  # Показ найденных ссылок
    waiting_for_link1_decision = State()  # Решение по первой ссылке
    waiting_for_new_link1 = State()  # Ввод новой первой ссылки
    waiting_for_link1_text_decision = State()  # Менять ли текст первой ссылки?
    waiting_for_link1_format = State()  # Формат для первой ссылки
    waiting_for_link2_decision = State()  # Решение по второй ссылке
    waiting_for_new_link2 = State()  # Ввод новой второй ссылки
    waiting_for_link2_text_decision = State()  # Менять ли текст второй ссылки?
    waiting_for_link2_format = State()  # Формат для второй ссылки
    waiting_for_mode = State()
    waiting_for_confirm = State()


class BulkLinkReplaceStates(StatesGroup):
    """Состояния для массовой замены ссылок в нескольких каналах."""
    selecting_channels = State()  # Выбор каналов (мультивыбор)
    entering_links_for_channel = State()  # Ввод ссылок для текущего канала
    choosing_mode = State()  # Выбор режима (последовательно/параллельно)
    confirming = State()  # Финальное подтверждение


class ScenarioStates(StatesGroup):
    """Состояния для сценария генерации переписок в чате"""
    waiting_for_channel = State()  # Выбор канала назначения
    waiting_for_source_channel = State()  # Выбор канала-источника скриншотов
    waiting_for_casino_name = State()  # Ввод названия казино
    waiting_for_message_count = State()  # Ввод количества сообщений
    waiting_for_interval = State()  # Ввод интервала между сообщениями
    waiting_for_characters = State()  # Выбор активных персонажей
    waiting_for_confirmation = State()  # Подтверждение и запуск
    showing_status = State()  # Показ статуса выполнения
    processing = State()  # Процесс обработки


class ReferenceChannelStates(StatesGroup):
    """Состояния для управления референс-каналами"""
    main_menu = State()  # Главное меню
    adding_channel = State()  # Добавление канала
    waiting_for_channel_input = State()  # Ожидание ввода канала
    uploading_html = State()  # Ожидание HTML-файла
    scanning_channel = State()  # Процесс сканирования
    viewing_statistics = State()  # Просмотр статистики


class ScheduledLinkStates(StatesGroup):
    """Состояния для замены ссылок в отложенных сообщениях."""
    selecting_account = State()  # Выбор аккаунта
    selecting_channel = State()  # Выбор канала
    entering_old1 = State()  # Ввод старой ссылки 1
    entering_new1 = State()  # Ввод новой ссылки 1
    entering_old2 = State()  # Ввод старой ссылки 2
    entering_new2 = State()  # Ввод новой ссылки 2
    confirming = State()  # Подтверждение


class AccountUploadStates(StatesGroup):
    """Состояния для загрузки аккаунтов через .session файлы."""
    waiting_for_session_file = State()  # Ожидание .session файла


class NewContentStates(StatesGroup):
    """Состояния для сценария 'Новый Контент' - упрощенная генерация контента"""
    waiting_for_base_link = State()  # Ввод базовой ссылки
    waiting_for_direction = State()  # Выбор направления (вниз/вверх/оба)
    waiting_for_range = State()  # Ввод диапазона (±100-10000)
    waiting_for_count = State()  # Ввод количества постов
    waiting_for_target_channel = State()  # Выбор канала назначения
    waiting_for_first_link = State()  # Ввод первой ссылки
    waiting_for_second_link = State()  # Ввод второй ссылки
    waiting_for_style_choice = State()  # Выбор стиля текста


class StreamerPostsStates(StatesGroup):
    """Состояния для сценария '100 постов стримеров'"""
    # 1. Ввод ссылок и бонусов
    waiting_for_url1 = State()  # Ввод URL первого бонуса
    waiting_for_bonus1 = State()  # Описание первого бонуса
    waiting_for_url2 = State()  # Ввод URL второго бонуса
    waiting_for_bonus2 = State()  # Описание второго бонуса
    # 2. Выбор канала для публикации
    waiting_for_target_channel = State()  # Выбор канала для публикации
    # 3. Выбор источника видео
    choosing_video_source = State()  # Выбор источника видео
    waiting_for_source_channel = State()  # Ввод канала-источника видео
    waiting_for_post_link = State()  # Ввод ссылки на конкретный пост
    waiting_for_post_count = State()  # Ввод количества постов
    choosing_ai_model = State()  # Выбор AI модели для генерации
    scanning_source_channel = State()  # Сканирование канала
    waiting_for_scan_direction = State()  # Выбор направления сканирования
    waiting_for_video_range = State()  # Диапазон видео из канала
    waiting_for_videos = State()  # Получение видео файлов
    waiting_for_video_metadata = State()  # Ввод метаданных видео
    entering_metadata_for_channel = State()  # Ввод метаданных для видео из канала
    # 4. Картинки
    waiting_for_images = State()  # Получение картинок
    choosing_image_source = State()  # Выбор источника картинок
    waiting_for_image_channel = State()  # Канал с картинками
    # 5. Генерация и публикация
    preview_and_publish = State()  # Превью и кнопка публикации
    confirming = State()  # Подтверждение
    processing = State()  # Публикация
    # 6. Проверка уникальности (Сторожевой AI)
    waiting_for_uniqueness_check = State()  # Выбор модели проверки
    showing_uniqueness_results = State()  # Показ результатов проверки
    regenerating_duplicates = State()  # Перегенерация дублей


class ContentWithAdsStates(StatesGroup):
    """Состояния для сценария 'Контент + Реклама'"""
    # Шаг 1: Генерация ссылок на контент
    waiting_for_base_link = State()  # Базовая ссылка на пост
    waiting_for_direction = State()  # Направление (вверх/вниз/оба)
    waiting_for_range = State()  # Диапазон (±100-10000)
    waiting_for_post_count = State()  # Количество постов
    waiting_for_win_block_option = State()  # Что делать с блоком выигрыша
    # Шаг 2: Канал с рекламой
    waiting_for_ads_channel = State()  # Канал с рекламой
    waiting_for_ads_start_post = State()  # С какого поста брать рекламу
    # Шаг 3: Целевой канал
    waiting_for_target_channel = State()  # Куда публиковать
    # Финал
    waiting_for_confirmation = State()  # Подтверждение
    processing = State()  # Обработка


class ImagePostsStates(StatesGroup):
    """Состояния для сценария '🖼 Посты с картинками' (20 постов на основе тем)"""
    # 1. Ввод ссылок и бонусов
    waiting_for_url1 = State()  # Ввод URL первого бонуса
    waiting_for_bonus1 = State()  # Описание первого бонуса
    waiting_for_url2 = State()  # Ввод URL второго бонуса
    waiting_for_bonus2 = State()  # Описание второго бонуса
    # 2. Управление темами
    topics_menu = State()  # Меню управления темами
    viewing_topics = State()  # Просмотр доступных тем
    adding_custom_topic = State()  # Добавление своей темы
    generating_new_topics = State()  # Генерация новых тем AI
    selecting_topics = State()  # Выбор тем для генерации
    confirming_reset_topics = State()  # Подтверждение сброса статистики тем
    # 3. Выбор модели и настроек
    choosing_text_model = State()  # Выбор модели для текста
    choosing_image_model = State()  # Выбор модели для картинок (Nano Banana)
    # 4. Генерация
    generating_posts = State()  # Генерация постов
    generating_images = State()  # Генерация картинок
    # 5. Превью и публикация
    preview_posts = State()  # Превью сгенерированных постов
    viewing_single_post = State()  # Просмотр одного поста
    regenerating_image = State()  # Перегенерация картинки
    regenerating_text = State()  # Перегенерация текста
    # 6. Выбор канала и публикация
    waiting_for_target_channel = State()  # Выбор канала
    confirming_publish = State()  # Подтверждение публикации
    publishing = State()  # Процесс публикации


class SpanishPostsStates(StatesGroup):
    """Состояния для сценария '100 постов на испанском'"""
    # 1. Ввод ссылок и бонусов
    waiting_for_url1 = State()  # Ввод URL первого бонуса
    waiting_for_bonus1 = State()  # Описание первого бонуса
    waiting_for_url2 = State()  # Ввод URL второго бонуса
    waiting_for_bonus2 = State()  # Описание второго бонуса
    # 2. Выбор валюты (НОВОЕ!)
    waiting_for_currency = State()  # Выбор валюты (USD, EUR, CLP, MXN, ARS, COP)
    # 3. Выбор канала для публикации
    waiting_for_target_channel = State()  # Выбор канала для публикации
    # 4. Выбор источника видео
    choosing_video_source = State()  # Выбор источника видео
    waiting_for_source_channel = State()  # Ввод канала-источника видео
    waiting_for_post_link = State()  # Ввод ссылки на конкретный пост
    waiting_for_post_count = State()  # Ввод количества постов
    choosing_ai_model = State()  # Выбор AI модели для генерации
    scanning_source_channel = State()  # Сканирование канала
    waiting_for_scan_direction = State()  # Выбор направления сканирования
    waiting_for_video_range = State()  # Диапазон видео из канала
    waiting_for_videos = State()  # Получение видео файлов
    waiting_for_video_metadata = State()  # Ввод метаданных видео
    entering_metadata_for_channel = State()  # Ввод метаданных для видео из канала
    # 5. Картинки
    waiting_for_images = State()  # Получение картинок
    choosing_image_source = State()  # Выбор источника картинок
    waiting_for_image_channel = State()  # Канал с картинками
    # 6. Генерация и публикация
    preview_and_publish = State()  # Превью и кнопка публикации
    confirming = State()  # Подтверждение
    processing = State()  # Публикация
    # 7. Проверка уникальности (Сторожевой AI)
    waiting_for_uniqueness_check = State()  # Выбор модели проверки
    showing_uniqueness_results = State()  # Показ результатов проверки
    regenerating_duplicates = State()  # Перегенерация дублей


# Экспортируем все классы
__all__ = [
    'GenerateLinksStates',
    'BatchProcessStates',
    'AdUnifyStates',
    'ChannelSelectionStates',
    'LinkReplaceStates',
    'LinkReplaceWithHyperlinksStates',
    'BulkLinkReplaceStates',
    'ScenarioStates',
    'ReferenceChannelStates',
    'ScheduledLinkStates',
    'AccountUploadStates',
    'NewContentStates',
    'StreamerPostsStates',
    'ContentWithAdsStates',
    'ImagePostsStates',
    'SpanishPostsStates',  # Новый класс
]
