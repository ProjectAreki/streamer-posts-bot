# Конфигурация Cursor для Streamer Posts Bot

## MCP серверы

Этот проект использует следующие MCP (Model Context Protocol) серверы:

### 1. Memory Server
**Назначение:** Сохранение контекста проекта между сессиями

```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"]
}
```

**Возможности:**
- Сохранение важной информации о проекте
- Восстановление контекста после перезапуска
- Улучшение качества ответов AI

### 2. Context7 Server
**Назначение:** Получение актуальной документации для библиотек

```json
{
  "command": "npx",
  "args": ["-y", "@upaya07/mcp-server-context7"]
}
```

**Возможности:**
- Актуальная документация по API
- Примеры кода для библиотек
- Помощь в настройке и конфигурации

### 3. Browser Extension Servers
**Назначение:** Тестирование веб-интерфейсов

**Возможности:**
- Навигация по веб-страницам
- Тестирование frontend кода
- Проверка UI/UX

## Установка

MCP серверы устанавливаются автоматически через `npx` при первом использовании.

### Требования:
- Node.js 16+ и npm
- Доступ к интернету для загрузки пакетов

## Конфигурационный файл

Основной файл конфигурации: `.cursor/mcp_config.json`

## Использование

После настройки MCP серверы будут доступны автоматически в Cursor AI.

### Memory Server - примеры команд:

**Сохранить информацию:**
```
Запомни: проект использует OpenRouter для AI генерации, основные модели - Qwen и Gemini Flash
```

**Получить информацию:**
```
Что ты помнишь о настройках AI в этом проекте?
```

### Context7 - примеры запросов:

```
Покажи актуальную документацию по aiogram 3.x
```

```
Как правильно использовать FSM в aiogram 3?
```

## Отладка

Если MCP сервер не работает:

1. Проверьте установку Node.js: `node --version`
2. Проверьте доступ к npm: `npm --version`
3. Попробуйте установить вручную: `npm install -g @modelcontextprotocol/server-memory`
4. Проверьте логи Cursor

## Дополнительная информация

- [MCP Protocol](https://modelcontextprotocol.io/)
- [Memory Server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
- [Context7 Server](https://github.com/upaya07/mcp-server-context7)
