# Zoom Transcript Task Extractor

FastAPI приложение для обработки живых транскриптов Zoom, извлечения задач с помощью LLM и предоставления их через JSON API для интеграции с Jira.

## Функциональность

- **WebSocket сервер** для получения живых транскриптов из Zoom RTMS
- **Интеграция с LLM** (OpenAI GPT) для извлечения задач из фраз участников
- **REST API эндпоинт** `/tasks` для получения массива задач в JSON формате
- **Автоматическое извлечение** исполнителей, приоритетов и описаний задач

## Быстрый старт

### 1. Установка зависимостей

```bash
# Клонировать репозиторий
git clone <repository-url>
cd shai-la-baf

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать .env файл
# OPENAI_API_KEY=your_openai_api_key_here
# ZOOM_WEBHOOK_TOKEN=your_zoom_webhook_token_here
# HOST=0.0.0.0
# PORT=8000
```

### 3. Запуск сервера

```bash
# Автоматический запуск
./start.sh

# Или вручную
python main.py
```

Сервер будет доступен по адресу: `http://localhost:8000`

## API Эндпоинты

### WebSocket

**`/ws/transcript`** - WebSocket для получения живых транскриптов

Формат сообщения:
```json
{
  "participant_id": "user_001",
  "participant_name": "John Smith", 
  "text": "Нужно завершить отчет до пятницы",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### REST API

**`GET /tasks`** - Получить все извлеченные задачи

Ответ:
```json
[
  {
    "id": "John Smith_1705315800.123_0",
    "title": "Завершить квартальный отчет",
    "description": "Подготовить финансовый отчет за Q4 с анализом доходов",
    "assignee": "John Smith",
    "priority": "high",
    "created_at": "2024-01-15T10:30:00.123Z",
    "source_participant": "John Smith",
    "source_text": "Нужно завершить отчет до пятницы"
  }
]
```

**`DELETE /tasks`** - Очистить все задачи

**`GET /`** - Проверка статуса сервиса

## Тестирование

```bash
# Запустить тест-клиент (в отдельном терминале)
python test_client.py
```

Тест-клиент отправляет примеры транскриптов и проверяет работу API.

## Интеграция с Zoom

Для подключения к Zoom RTMS:

1. Настройте Zoom App с WebSocket поддержкой
2. Направьте транскрипты на WebSocket эндпоинт: `ws://your-server:8000/ws/transcript`
3. Убедитесь, что данные отправляются в правильном JSON формате

## Интеграция с Jira через MCP

Полученные задачи из эндпоинта `/tasks` можно использовать с MCP Jira для автоматического создания задач:

```bash
# Получить задачи
curl http://localhost:8000/tasks

# Данные готовы для передачи в Jira через MCP
```

## Структура проекта

```
shai-la-baf/
├── main.py              # Основное FastAPI приложение
├── test_client.py       # Тест-клиент для проверки
├── requirements.txt     # Python зависимости
├── .env.example        # Пример конфигурации
├── .gitignore          # Git игнорируемые файлы
├── start.sh            # Скрипт быстрого запуска
└── README.md           # Документация
```

## Зависимости

- **FastAPI** - веб-фреймворк
- **uvicorn** - ASGI сервер
- **websockets** - WebSocket поддержка
- **openai** - клиент для OpenAI API
- **python-dotenv** - работа с переменными окружения
- **pydantic** - валидация данных
- **aiohttp** - HTTP клиент для тестов

## Логирование

Все события логируются с информацией о:
- Подключениях WebSocket
- Обработке транскриптов
- Извлеченных задачах
- Ошибках обработки

## Производительность

- Асинхронная обработка всех операций
- Множественные WebSocket подключения
- Эффективное управление памятью для задач
- Настраиваемые параметры LLM

## Лицензия

MIT License