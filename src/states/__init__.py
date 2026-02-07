"""
@file: __init__.py
@description: FSM States для сценариев Streamer Posts Bot
@dependencies: aiogram.fsm.state
@created: 2026-01-12
"""

from aiogram.fsm.state import State, StatesGroup


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
    # 2. Выбор канала для публикации
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


class ItalianPostsStates(StatesGroup):
    """Состояния для сценария '100 постов на итальянском'"""
    # 1. Ввод ссылки и бонуса
    waiting_for_url1 = State()  # Ввод URL бонуса
    waiting_for_bonus1 = State()  # Описание бонуса
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


# Экспортируем все классы
__all__ = [
    'StreamerPostsStates',
    'ImagePostsStates',
    'SpanishPostsStates',
    'ItalianPostsStates',
]
