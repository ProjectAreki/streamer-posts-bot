#!/usr/bin/env python3
"""
Автоматический скрипт деплоя на сервер

Использование:
    python auto_deploy.py

Требования:
    - Настроенный SSH доступ к серверу
    - Переменные окружения SERVER_HOST, SERVER_USER, SERVER_PATH
"""

import os
import sys
import subprocess
from pathlib import Path

# Цвета для вывода
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_step(step_num, total_steps, message):
    """Вывод шага деплоя"""
    print(f"\n{YELLOW}[{step_num}/{total_steps}]{NC} {message}")

def print_success(message):
    """Вывод успешного сообщения"""
    print(f"{GREEN}[OK] {message}{NC}")

def print_error(message):
    """Вывод ошибки"""
    print(f"{RED}[ERROR] {message}{NC}")

def run_command(command, description="", check=True):
    """Выполнение команды с выводом"""
    if description:
        print(f"   {description}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Ошибка выполнения команды: {e}")
            if e.stderr:
                print(e.stderr)
        return False

def main():
    """Основная функция деплоя"""
    
    # Исправляем кодировку для Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print(f"\n{GREEN}{'='*60}{NC}")
    print(f"{GREEN}   Автоматический Deploy - Streamer Posts Bot{NC}")
    print(f"{GREEN}{'='*60}{NC}\n")
    
    # Получаем параметры сервера
    server_host = os.getenv('SERVER_HOST')
    server_user = os.getenv('SERVER_USER', 'root')
    server_path = os.getenv('SERVER_PATH', '/root/streamer_posts_bot')
    ssh_key = os.getenv('SSH_KEY_PATH', '')
    
    # Если параметры не заданы, спрашиваем у пользователя
    if not server_host:
        print("Параметры сервера не найдены в переменных окружения.")
        print("Введите данные для подключения:\n")
        
        server_host = input("Хост сервера (например, 123.456.789.0): ").strip()
        if not server_host:
            print_error("Хост сервера обязателен!")
            return 1
        
        server_user = input(f"Пользователь [{server_user}]: ").strip() or server_user
        server_path = input(f"Путь к проекту [{server_path}]: ").strip() or server_path
        ssh_key = input("Путь к SSH ключу (Enter для пропуска): ").strip()
    
    # Формируем SSH команду
    ssh_base = f"ssh"
    if ssh_key:
        ssh_base += f" -i {ssh_key}"
    ssh_base += f" {server_user}@{server_host}"
    
    print(f"\n{YELLOW}Параметры деплоя:{NC}")
    print(f"   Сервер: {server_user}@{server_host}")
    print(f"   Путь: {server_path}")
    print(f"   SSH ключ: {ssh_key if ssh_key else 'по умолчанию'}")
    
    confirm = input(f"\n{YELLOW}Продолжить? (y/n): {NC}").strip().lower()
    if confirm not in ['y', 'yes', 'д', 'да']:
        print("Деплой отменен")
        return 0
    
    total_steps = 5
    
    # Шаг 1: Проверка подключения
    print_step(1, total_steps, "Проверка подключения к серверу...")
    if not run_command(f"{ssh_base} 'echo Connected'", "Подключение к серверу", check=False):
        print_error("Не удалось подключиться к серверу!")
        print("\nПроверьте:")
        print("  1. Правильность хоста и пользователя")
        print("  2. SSH ключ и права доступа")
        print("  3. Доступность сервера")
        return 1
    print_success("Подключение установлено")
    
    # Шаг 2: Проверка git на сервере
    print_step(2, total_steps, "Обновление кода с GitHub...")
    
    commands = [
        f"cd {server_path}",
        "git fetch origin",
        "git pull origin main"
    ]
    
    cmd = f"{ssh_base} '{'; '.join(commands)}'"
    if not run_command(cmd, "Выполнение git pull", check=False):
        print_error("Не удалось обновить код!")
        return 1
    print_success("Код обновлен")
    
    # Шаг 3: Установка зависимостей
    print_step(3, total_steps, "Проверка зависимостей...")
    
    commands = [
        f"cd {server_path}",
        "source venv/bin/activate 2>/dev/null || true",
        "pip install -r requirements.txt --quiet"
    ]
    
    cmd = f"{ssh_base} '{'; '.join(commands)}'"
    if not run_command(cmd, "Установка зависимостей", check=False):
        print(f"{YELLOW}⚠️  Возможны проблемы с зависимостями{NC}")
    else:
        print_success("Зависимости обновлены")
    
    # Копируем новые скрипты
    print(f"\n{YELLOW}   Копирование новых файлов...{NC}")
    files_to_check = [
        "find_missing_posts.py",
        "check_recent_posts.py",
        "BUGFIX_GEMINI_JSON_PARSING.md",
        "QUICK_FIX_GUIDE.md"
    ]
    for file in files_to_check:
        cmd = f"{ssh_base} 'test -f {server_path}/{file} && echo \"   {file}: OK\" || echo \"   {file}: NOT FOUND\"'"
        run_command(cmd, check=False)
    
    # Шаг 4: Перезапуск бота
    print_step(4, total_steps, "Перезапуск бота...")
    
    # Пробуем разные способы перезапуска
    restart_methods = [
        # Systemd
        ("systemctl restart streamer-posts-bot", "через systemd"),
        # PM2
        ("pm2 restart bot", "через PM2"),
        # Supervisor
        ("supervisorctl restart streamer-posts-bot", "через supervisor"),
        # Screen/manual
        (f"pkill -f bot.py && cd {server_path} && nohup python bot.py > logs/bot.log 2>&1 &", "вручную")
    ]
    
    restarted = False
    for cmd_template, method in restart_methods:
        cmd = f"{ssh_base} 'sudo {cmd_template} 2>/dev/null || {cmd_template} 2>/dev/null'"
        if run_command(cmd, f"Попытка перезапуска {method}", check=False):
            print_success(f"Бот перезапущен {method}")
            restarted = True
            break
    
    if not restarted:
        print(f"{YELLOW}[!] Автоматический перезапуск не удался{NC}")
        print("   Выполните вручную на сервере:")
        print(f"   ssh {server_user}@{server_host}")
        print(f"   cd {server_path} && python bot.py")
    
    # Шаг 5: Проверка статуса
    print_step(5, total_steps, "Проверка статуса бота...")
    
    commands = [
        f"cd {server_path}",
        "ps aux | grep -E '[p]ython.*bot.py' || echo 'Bot process not found'"
    ]
    
    cmd = f"{ssh_base} '{'; '.join(commands)}'"
    run_command(cmd, "Поиск процесса бота", check=False)
    
    # Финальное сообщение
    print(f"\n{GREEN}{'='*60}{NC}")
    print(f"{GREEN}   Деплой завершен!{NC}")
    print(f"{GREEN}{'='*60}{NC}\n")
    
    print("Просмотр логов на сервере:")
    print(f"   {ssh_base} 'tail -f {server_path}/logs/bot.log'")
    
    print("\nПроверка статуса:")
    print(f"   {ssh_base} 'cd {server_path} && ps aux | grep bot.py'")
    
    print(f"\n{YELLOW}Рекомендуется:{NC}")
    print("   1. Проверить логи на наличие ошибок")
    print("   2. Протестировать бота в Telegram")
    print("   3. Убедиться что проверка уникальности работает")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Деплой прерван пользователем{NC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
