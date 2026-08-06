# AI-Agent-Framework

AI-Agent-Framework — backend-приложение на FastAPI для создания AI-агентов с поддержкой Tool Calling на базе LangChain. Проект построен по принципам Clean Architecture и ориентирован на расширяемость: новые модели, инструменты, хранилища и бизнес-логика могут подключаться без изменения существующего кода.

---

# Возможности

- AI Agent на базе LangChain
- Tool Calling
- Реестр инструментов (Tool Registry)
- Подключение нескольких LLM-провайдеров
    - Ollama
    - OpenAI
- Dependency Injection
- Repository Pattern
- Unit of Work
- PostgreSQL
- Docker Compose
- Полностью асинхронный стек

---

# Технологии

- Python 3.12
- FastAPI
- LangChain
- PostgreSQL
- SQLAlchemy 2.0 (Async)
- asyncpg
- Pydantic v2
- Docker
- Docker Compose

---

# Архитектура

Проект разделен на независимые слои.

```
HTTP

↓

Controllers

↓

Agent Service

↓

Agent Executor

↓

LLM + Tool Calling

↓

Tools
```

Работа с базой данных полностью изолирована:

```
Service

↓

Unit Of Work

↓

Repository

↓

SQLAlchemy
```

---

# Структура проекта

```
app/

├── agents/
│   ├── executor.py
│   ├── models.py
│   ├── service.py
│   └── state.py
│
├── controllers.py
├── dependencies.py
├── models.py
│
├── llm/
│   ├── ollama.py
│   └── openai.py
│
├── protocols/
│   └── llm.py
│
├── repository.py
├── schemas.py
├── uow.py
│
├── tools/
│   ├── calculator.py
│   ├── datetime.py
│   └── registry.py
│
└── database.py

routers/
    api_v1_router.py

settings/
    settings.py

main.py
```

---

# Используемые архитектурные паттерны

## Repository

Изолирует доступ к данным.

```text
Service

↓

Repository

↓

PostgreSQL
```

Repository ничего не знает о FastAPI и бизнес-логике.

---

## Unit of Work

Каждая бизнес-операция выполняется внутри собственной транзакции.

```text
async with uow_factory() as uow:
    ...
```

UoW отвечает за:

- создание AsyncSession;
- commit;
- rollback;
- освобождение ресурсов.

---

## Dependency Injection

Все зависимости создаются через `dependencies.py`.

Например:

- LLM
- Repository
- UnitOfWork
- AgentExecutor
- ToolRegistry

Это позволяет легко заменять реализации без изменения бизнес-логики.

---

## Factory

Создание LLM происходит через фабрику.

В зависимости от настроек приложение автоматически выбирает:

- Ollama
- OpenAI

Без изменения остального кода.

---

## Strategy

Каждый LLM-клиент реализует единый интерфейс.

Например:

```
OpenAILLMClient

или

OllamaLLMClient
```

AgentExecutor не зависит от конкретной модели.

---

## SOLID

Проект следует принципам SOLID.

### Single Responsibility

Каждый класс отвечает только за одну задачу.

Например:

- AgentExecutor — выполнение агента;
- Repository — работа с БД;
- ToolRegistry — регистрация инструментов.

---

### Open/Closed

Добавление нового инструмента или новой модели не требует изменения существующего кода.

---

### Liskov Substitution

Любой клиент LLM может заменить другой благодаря общему протоколу.

---

### Interface Segregation

Используются небольшие специализированные протоколы.

---

### Dependency Inversion

Высокоуровневые компоненты зависят только от абстракций.

---

# Tool Calling

Инструменты реализуются через LangChain.

Каждый инструмент наследуется от `BaseTool`.

Пример:

- Calculator Tool
- DateTime Tool

Все инструменты регистрируются в `ToolRegistry`.

Во время выполнения агент самостоятельно принимает решение, требуется ли вызов инструмента.

---

# Agent

Агент реализован собственным циклом исполнения.

```
Human

↓

LLM

↓

Tool?

↓

Да

↓

Tool

↓

LLM

↓

Ответ
```

AgentExecutor полностью изолирован от:

- HTTP
- FastAPI
- PostgreSQL

Он отвечает исключительно за выполнение агентного цикла.

---

# База данных

Используется PostgreSQL.

Основные сущности:

## Conversation

Хранит информацию о диалоге.

## Message

Хранит сообщения пользователя и модели.

---

# Конфигурация

Все настройки находятся в `.env`.

Пример:

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=agent_db

APP_HOST=0.0.0.0
APP_PORT=8000

LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:3b

OLLAMA_HOST=http://ollama:11434/v1

OPENAI_API_KEY=
```

---

# Запуск проекта

## 1. Клонировать репозиторий

```bash
git clone <repository_url>

cd AI-Agent-Framework
```

---

## 2. Создать файл `.env`

Заполнить параметры подключения к базе данных и выбранной модели.

---

## 3. Запустить Docker

```bash
docker compose up --build
```

---

## 4. Скачать модель Ollama

После первого запуска контейнеров выполнить:

```bash
docker exec -it ai-chat-ollama bash
```

Далее внутри контейнера:

```bash
ollama pull qwen2.5:3b
```

Проверить:

```bash
ollama list
```

---

## 5. Проверить API

Swagger:

```
http://localhost:8000/docs
```

Adminer:

```
http://localhost:8080
```

---

# Принципы разработки

Во всем проекте соблюдаются следующие принципы:

- OOP
- SOLID
- DRY
- KISS
- Dependency Injection
- Repository Pattern
- Unit of Work
- Factory Pattern
- Strategy Pattern

---

# Текущее состояние проекта

На данный момент реализовано:

- инфраструктура FastAPI;
- асинхронная работа с PostgreSQL;
- Repository + Unit of Work;
- подключение нескольких LLM-провайдеров;
- AI Agent;
- Tool Calling;
- реестр инструментов;
- Dependency Injection;
- Docker Compose.

Архитектура подготовлена для дальнейшего развития и масштабирования без нарушения существующих компонентов.