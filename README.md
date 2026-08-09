# AI-Agent-Framework

Фреймворк для создания AI-агентов на Python с поддержкой **Tool Calling**, потоковой выдачи ответа, сохранения истории диалогов и интеграции с различными LLM-провайдерами.

Проект построен вокруг **LangChain** и следует принципам Clean Architecture, SOLID и dependency injection. Архитектура отделяет HTTP/API-слой, application-логику агента, инструменты, инфраструктуру хранения данных и конкретных LLM-провайдеров.

---

## Содержание

* [Возможности](#возможности)
* [Архитектура](#архитектура)
* [Как работает агент](#как-работает-агент)
* [Tool Calling](#tool-calling)
* [Streaming](#streaming)
* [Структура проекта](#структура-проекта)
* [Основные паттерны](#основные-паттерны)
* [LLM Providers](#llm-providers)
* [Инструменты](#инструменты)
* [Хранение истории](#хранение-истории)
* [Dependency Injection](#dependency-injection)
* [Error Handling](#error-handling)
* [Logging](#logging)
* [Тестирование](#тестирование)
* [Запуск проекта](#запуск-проекта)
* [API](#api)
* [Пример работы](#пример-работы)
* [Упрощения проекта](#упрощения-проекта)
* [Преимущества архитектуры](#преимущества-архитектуры)

---

# Возможности

Проект предоставляет готовый application flow для работы с AI-агентом:

* интеграция с LLM через LangChain;
* поддержка Tool Calling;
* автоматический цикл:

```text
User
 ↓
LLM
 ↓
Tool Call
 ↓
Tool
 ↓
Tool Result
 ↓
LLM
 ↓
Final Answer
```

* несколько последовательных вызовов инструментов;
* ограничение количества итераций агента;
* потоковая выдача ответа через HTTP;
* сохранение истории conversation;
* сохранение пользовательских и AI-сообщений;
* сохранение token usage, если провайдер его предоставляет;
* структурированное логирование через `structlog`;
* централизованная обработка ошибок;
* Dependency Injection;
* Unit of Work;
* Repository;
* разделение application/domain/infrastructure concerns;
* тестирование инструментов и AgentExecutor.

---

# Архитектура

Основной flow приложения:

```text
                    HTTP
                     │
                     ▼
              ┌─────────────┐
              │ Controller  │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │ AgentService│
              └──────┬──────┘
                     │
                     ▼
             ┌──────────────┐
             │ AgentExecutor│
             └──────┬───────┘
                    │
             ┌──────┴───────┐
             │              │
             ▼              ▼
           LLM           Tools
             │              │
             └──────┬───────┘
                    │
                    ▼
               Final Answer
                    │
                    ▼
                 Service
                    │
                    ▼
              Unit of Work
                    │
                    ▼
                Database
```

При этом HTTP-слой не знает деталей работы LLM или инструментов.

Controller отвечает только за HTTP:

```text
HTTP Request
     ↓
AgentService
     ↓
StreamingResponse
```

---

# Как работает агент

Основной orchestration находится в `AgentExecutor`.

Он получает:

```python
AgentRequest(
    messages=history,
)
```

После этого запускается цикл:

```text
1. Передать историю модели
2. Получить ответ модели
3. Проверить tool_calls
4. Если tool_calls отсутствуют:
       вернуть финальный ответ
5. Если tool_calls присутствуют:
       выполнить инструменты
6. Добавить ToolMessage в историю
7. Повторить запрос к модели
```

У агента существует ограничение:

```python
MAX_ITERATIONS = 10
```

Это защищает приложение от бесконечного цикла:

```text
LLM → Tool → LLM → Tool → ...
```

---

# Tool Calling

Инструменты регистрируются через `ToolRegistry`.

Например:

```text
ToolRegistry
 ├── calculator
 └── current_datetime
```

При создании `AgentExecutor` инструменты передаются модели:

```python
provider.get_model().bind_tools(registry.tools)
```

Это важный момент.

**Модель сама принимает решение, когда ей необходим инструмент.**

Например пользователь отправляет:

```text
Сколько будет 24 * 16?
```

Модель может сформировать:

```text
tool_call:
    name = calculator
    arguments = {
        "expression": "24 * 16"
    }
```

После этого `AgentExecutor`:

1. получает `tool_call`;
2. находит инструмент в `ToolRegistry`;
3. вызывает его;
4. получает результат `384`;
5. создаёт `ToolMessage`;
6. отправляет результат обратно модели.

Получается:

```text
User
 │
 ▼
LLM
 │
 │ tool_call: calculator
 ▼
Calculator
 │
 │ 384
 ▼
ToolMessage
 │
 ▼
LLM
 │
 ▼
"Результат: 384"
```

---

# Важный момент: модель не выполняет инструменты самостоятельно

LLM только **предлагает вызов инструмента**.

Например:

```json
{
  "name": "calculator",
  "arguments": {
    "expression": "24 * 16"
  }
}
```

Само выполнение происходит внутри приложения:

```python
tool = self._registry.get(tool_name)

result = await tool.ainvoke(arguments)
```

Это позволяет приложению контролировать:

* какие инструменты доступны;
* какие аргументы были переданы;
* факт вызова;
* результат;
* ошибки;
* количество итераций.

---

# Streaming

Проект использует streaming на уровне LangChain.

`AgentExecutor` получает события через:

```python
self._model.astream_events(
    state.messages,
    version="v2",
)
```

Из событий извлекаются `on_chat_model_stream`.

Полученные chunks передаются через `asyncio.Queue`.

Схематично:

```text
LLM
 │
 │ token
 ▼
astream_events()
 │
 ▼
asyncio.Queue
 │
 ▼
AgentExecution.stream
 │
 ▼
AgentService
 │
 ▼
StreamingResponse
 │
 ▼
HTTP Client
```

Таким образом клиент получает ответ частями, а не ждёт формирования всего ответа целиком.

Endpoint возвращает:

```python
StreamingResponse(
    result.stream,
    media_type="text/plain",
)
```

Также в response передаётся:

```text
X-Conversation-ID
```

чтобы клиент мог продолжить существующий conversation.

---

# AgentExecution

Между `AgentExecutor` и `AgentService` используется отдельный контракт:

```python
@dataclass(slots=True)
class AgentExecution:
    stream: AsyncIterator[str]

    get_result: Callable[
        [],
        Awaitable[AgentFinalResult],
    ]
```

Это позволяет разделить два процесса:

### Streaming

```python
async for token in execution.stream:
    ...
```

### Получение финального результата

```python
result = await execution.get_result()
```

Финальный результат содержит:

```python
AgentFinalResult(
    message=...,
    metrics=...,
)
```

А метрики:

```python
AgentRunMetrics(
    iterations=...,
    execution_time=...,
    token_usage=...,
)
```

Это позволяет одновременно поддерживать streaming и получение итоговых метрик выполнения.

---

# Структура проекта

Основная структура:

```text
app/
│
├── agents/
│   ├── executor.py
│   ├── service.py
│   └── state.py
│
├── tools/
│   ├── calculator.py
│   ├── datetime.py
│   └── registry.py
│
├── providers/
│   ├── base.py
│   └── ...
│
├── protocols/
│   ├── llm.py
│   └── uow.py
│
├── models/
│   ├── agent.py
│   └── llm.py
│
├── repository.py
├── uow.py
├── database.py
├── dependencies.py
├── controllers.py
├── models.py
└── exceptions.py
│
tests/
│
├── agents/
│   └── test_executor.py
│
├── tools/
│   ├── test_calculator.py
│   └── test_datetime.py
│
└── services/
```

---

# Основные паттерны

## Dependency Injection

Зависимости передаются извне через FastAPI `Depends` и dependency-функции.

Например:

```text
Controller
    ↓
AgentService
    ↓
AgentExecutor
    ↓
ModelProvider
    ↓
LLM
```

Конкретные реализации не создаются непосредственно внутри бизнес-логики.

---

## Repository

Работа с БД изолирована в `ConversationRepository`.

Он отвечает за:

* создание conversation;
* получение conversation;
* получение сообщений;
* добавление сообщений;
* преобразование истории в LangChain messages.

Application-слой не должен самостоятельно писать SQL-запросы.

---

## Unit of Work

`UnitOfWork` управляет жизненным циклом database session и транзакцией.

Основной flow:

```text
async with uow:
    repository operation
    repository operation

        ↓

    commit()
```

Если возникает исключение:

```text
exception
   ↓
rollback()
```

После завершения session закрывается.

Таким образом ответственность за commit/rollback централизована.

---

## Factory

`UnitOfWorkFactory` используется для создания новых Unit of Work:

```python
uow_factory()
```

Это особенно важно для streaming.

HTTP-запрос может продолжаться после того, как первая DB-транзакция уже завершена, поэтому для сохранения финального ответа создаётся отдельный UOW.

---

## Protocol

Абстракции представлены через Python Protocol.

Например:

```text
Application
     │
     ▼
Protocol
     ▲
     │
Concrete implementation
```

Это уменьшает связанность application-слоя с инфраструктурой.

---

## Strategy / Provider abstraction

LLM подключается через `ModelProviderProtocol`.

AgentExecutor работает с provider abstraction, а не с конкретной реализацией модели.

Условно:

```text
AgentExecutor
      │
      ▼
ModelProviderProtocol
      │
 ┌────┴─────┐
 ▼          ▼
Provider A  Provider B
```

Благодаря этому orchestration агента не зависит напрямую от конкретного LLM backend.

---

# Clean Architecture

Проект не является академически строгой реализацией Clean Architecture со всеми возможными слоями и интерфейсами.

Используется **прагматичный вариант**:

```text
API
 │
 ▼
Application
 │
 ▼
Agent orchestration
 │
 ├── LLM abstraction
 ├── Tools abstraction
 └── Persistence abstraction
```

Главная цель — контролировать зависимости и не смешивать:

* HTTP;
* agent orchestration;
* LLM;
* tools;
* database;
* configuration.

---

# SOLID

В проекте применяются основные идеи SOLID.

### Single Responsibility

Например:

```text
Controller
    → HTTP

AgentService
    → application flow + conversation persistence

AgentExecutor
    → agent loop

ToolRegistry
    → поиск инструментов

Repository
    → persistence

UnitOfWork
    → transaction lifecycle
```

### Open/Closed

Новый инструмент можно добавить через `ToolRegistry`, не переписывая основной agent loop.

### Dependency Inversion

Application-код зависит от abstractions/protocols, а не от конкретных реализаций инфраструктуры.

---

# Инструменты

Сейчас агент работает с инструментами:

### `calculator`

Вычисляет математические выражения.

Например:

```text
24 * 16
```

возвращает:

```text
384
```

### `current_datetime`

Возвращает текущее время.

Важно понимать архитектурное ограничение:

**наличие инструмента не означает наличие доступа модели к интернету.**

Если модели не предоставлен web search tool, агент не сможет самостоятельно выполнить поиск в интернете.

Точно так же если пользователь запрещает использовать конкретный инструмент, модель может просто ответить без него. Это не является `ToolNotFoundError`: ошибка `ToolNotFoundError` возникает только тогда, когда **модель фактически запросила tool call с именем, которого нет в `ToolRegistry`**.

---

# ToolRegistry

`ToolRegistry` является точкой управления доступными инструментами.

Условно:

```text
AgentExecutor
      │
      ▼
ToolRegistry
      │
 ┌────┴──────────────┐
 ▼                   ▼
calculator      current_datetime
```

AgentExecutor не содержит условной логики:

```python
if tool_name == "calculator":
    ...
elif tool_name == "datetime":
    ...
```

Вместо этого используется registry.

Это упрощает расширение системы.

---

# Error Handling

Для важных ошибок используются собственные исключения.

Например:

```text
ToolNotFoundError
ToolExecutionError
MaxIterationsExceededError
```

### ToolNotFoundError

Возникает, если модель запросила инструмент, которого нет в registry.

```text
LLM
 ↓
tool_call: unknown_tool
 ↓
ToolRegistry
 ↓
ToolNotFoundError
```

### ToolExecutionError

Возникает, если зарегистрированный инструмент существует, но его выполнение завершилось ошибкой.

### MaxIterationsExceededError

Возникает при превышении:

```python
MAX_ITERATIONS = 10
```

Это защита от бесконечного Tool Calling loop.

---

# Logging

Для логирования используется `structlog`.

Логи представлены структурированными событиями.

Например:

```json
{
    "event": "agent.started",
    "message_count": 1
}
```

При вызове инструмента:

```json
{
    "event": "tool.call",
    "tool": "calculator",
    "arguments": {
        "expression": "24 * 16"
    },
    "tool_call_id": "..."
}
```

После выполнения:

```json
{
    "event": "tool.result",
    "tool": "calculator",
    "result": "384",
    "tool_call_id": "..."
}
```

Это позволяет определить, действительно ли модель вызвала инструмент.

Для завершения агента логируются:

```text
agent.completed
```

с метриками:

* iterations;
* execution_time;
* token_usage.

---

# Хранение истории

Conversation хранится в PostgreSQL.

Основная структура:

```text
Conversation
    │
    └── Message
          ├── USER
          └── ASSISTANT
```

При новом запросе:

```text
HTTP request
      ↓
conversation
      ↓
save USER message
      ↓
load history
      ↓
AgentExecutor
      ↓
save ASSISTANT message
```

История преобразуется в LangChain messages:

```text
USER
 ↓
HumanMessage

ASSISTANT
 ↓
AIMessage
```

Таким образом LLM получает контекст предыдущего разговора.

---

# Token Usage

Модель может возвращать информацию о количестве использованных токенов.

В проекте предусмотрена модель:

```python
TokenUsage(
    prompt_tokens=...,
    completion_tokens=...,
    total_tokens=...,
)
```

Она входит в:

```python
AgentRunMetrics
```

Однако поддержка token usage зависит от конкретного LLM provider.

Поэтому поле является nullable:

```python
token_usage: TokenUsage | None
```

Если провайдер не предоставляет соответствующую информацию, значение остаётся `None`.

---

# Тестирование

Тесты находятся в директории:

```text
tests/
```

Основные категории:

```text
tests/
├── tools/
├── agents/
└── services/
```

## Tools

Проверяется непосредственно поведение инструментов:

```text
calculator
current_datetime
```

## AgentExecutor

Проверяется agent loop:

```text
LLM
 ↓
tool call
 ↓
tool execution
 ↓
ToolMessage
 ↓
LLM повторно
 ↓
final response
```

То есть тестируется не только отдельный вызов модели, но и основная orchestration-логика агента.

---

# Запуск проекта

## Требования

Необходимы:

* Docker;
* Docker Compose;
* Python 3.12+ для локального запуска тестов.

---

## Запуск через Docker Compose

Запустить проект:

```bash
docker compose up --build
```

После запуска API будет доступен по адресу:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

OpenAPI:

```text
http://localhost:8000/openapi.json
```

---

# Переменные окружения

Конфигурация хранится в `.env`.

Пример основных параметров:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_chat

LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:3b
OLLAMA_HOST=http://ollama:11434
```

Конкретный набор переменных зависит от выбранного provider.

Секреты не должны храниться непосредственно в Git.

---

# Запуск тестов

Создать и активировать virtual environment:

```powershell
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Установить зависимости:

```powershell
pip install -r requirements.txt
```

Запустить:

```powershell
pytest
```

Для более подробного вывода:

```powershell
pytest -v
```

---

# API

Основной endpoint агента:

```http
POST /api/v1/agent/chat
```

Request:

```json
{
    "conversation_id": null,
    "message": "Сколько будет 24 * 16?"
}
```

Если `conversation_id` отсутствует:

```text
создаётся новая conversation
```

В ответе передаётся поток:

```text
Результат умножения 24 на 16 равен 384.
```

И header:

```text
X-Conversation-ID: 1
```

Полученный ID можно использовать для продолжения разговора:

```json
{
    "conversation_id": 1,
    "message": "А теперь прибавь к этому 100"
}
```

---

# Пример работы

Пользователь:

```text
Сколько будет 24 * 16?
```

Модель формирует:

```text
calculator(
    expression="24 * 16"
)
```

AgentExecutor передаёт запрос в registry:

```text
ToolRegistry
    ↓
calculator
```

Инструмент возвращает:

```text
384
```

Результат передаётся модели:

```text
ToolMessage:
384
```

Модель формирует финальный ответ:

```text
Результат умножения 24 на 16 — 384.
```

Клиент получает ответ через streaming.

В логах при этом можно увидеть:

```text
agent.model_response
tool.call
tool.result
agent.model_response
agent.completed
agent.response_saved
```

---

# Полный жизненный цикл запроса

```text
                 HTTP POST
                     │
                     ▼
              AgentController
                     │
                     ▼
               AgentService
                     │
              ┌──────┴──────┐
              │             │
              ▼             ▼
         PostgreSQL      History
              │             │
              └──────┬──────┘
                     ▼
                AgentRequest
                     │
                     ▼
               AgentExecutor
                     │
                     ▼
                    LLM
                     │
             ┌───────┴────────┐
             │                │
       final answer       tool_call
             │                │
             │                ▼
             │            ToolRegistry
             │                │
             │                ▼
             │              Tool
             │                │
             │                ▼
             │           ToolMessage
             │                │
             │                ▼
             │               LLM
             │                │
             └────────┬───────┘
                      ▼
                 final answer
                      │
                      ▼
                  Streaming
                      │
                      ▼
                 AgentService
                      │
                      ▼
                  UnitOfWork
                      │
                      ▼
                  PostgreSQL
```

---

# Упрощения проекта

Проект намеренно не пытается реализовать абсолютно все возможности LangChain или построить максимально сложную agent architecture.

Основные упрощения:

### 1. Один основной AgentExecutor

Вместо сложной системы нескольких специализированных агентов используется один executor, управляющий Tool Calling loop.

Это делает архитектуру проще для понимания и отладки.

### 2. Ограниченный Tool Registry

Инструменты регистрируются централизованно и доступны агенту через один registry.

### 3. Ограниченное количество итераций

Используется фиксированное:

```python
MAX_ITERATIONS = 10
```

Это простое и надёжное ограничение.

### 4. Streaming финального ответа

В текущей реализации streaming ориентирован на выдачу ответа модели клиенту.

Сам Tool Calling остаётся внутренним процессом агента.

То есть пользователь видит:

```text
final answer → stream
```

а не внутренние:

```text
tool call
tool result
```

### 5. Token usage зависит от provider

Проект предусматривает сохранение token usage, но не пытается искусственно вычислять его, если LLM provider эти данные не предоставляет.

---

# Преимущества

## Разделение ответственности

Каждый компонент выполняет свою задачу:

```text
Controller
    → HTTP

AgentService
    → application flow

AgentExecutor
    → agent orchestration

ToolRegistry
    → tools

Provider
    → LLM

Repository
    → persistence

UnitOfWork
    → transactions
```

---

## Независимость AgentExecutor от конкретного LLM

Executor работает с:

```python
ModelProviderProtocol
```

а не с конкретным Ollama/OpenAI SDK.

Это позволяет не распространять provider-specific детали по application-коду.

---

## Управляемый Tool Calling

Вызов инструмента проходит через контролируемый pipeline:

```text
LLM
 ↓
ToolRegistry
 ↓
Tool
 ↓
ToolMessage
 ↓
LLM
```

Приложение контролирует каждый этап.

---

## Streaming без изменения application contract

`AgentExecution` отделяет streaming от финального результата.

Поэтому сервис может:

```python
async for token in execution.stream:
    yield token
```

а после завершения получить:

```python
await execution.get_result()
```

и сохранить:

* финальный ответ;
* iterations;
* execution time;
* token usage.

---

## Транзакционная целостность

За commit/rollback отвечает Unit of Work.

Application-коду не требуется вручную управлять транзакциями.

```text
success
   ↓
commit

exception
   ↓
rollback
```

---

## Наблюдаемость

Структурированные логи позволяют увидеть не только финальный ответ, но и внутреннее поведение агента:

```text
agent.started
     ↓
agent.model_response
     ↓
tool.call
     ↓
tool.result
     ↓
agent.model_response
     ↓
agent.completed
     ↓
agent.response_saved
```

Это особенно важно для debugging Tool Calling.

---

# Итоговая концепция

Проект представляет собой компактную архитектуру AI Agent Framework:

```text
             ┌──────────────────┐
             │      FastAPI     │
             └────────┬─────────┘
                      │
                      ▼
             ┌──────────────────┐
             │   AgentService   │
             └────────┬─────────┘
                      │
                      ▼
             ┌──────────────────┐
             │  AgentExecutor   │
             └───────┬───┬──────┘
                     │   │
             ┌───────┘   └────────┐
             ▼                    ▼
       Model Provider        ToolRegistry
             │                    │
             ▼               ┌────┴─────┐
            LLM               ▼          ▼
                         calculator   datetime
             │
             ▼
        AgentResponse
             │
             ▼
        StreamingResponse
             │
             ▼
           Client

             + PostgreSQL
             + Repository
             + UnitOfWork
             + structlog
             + custom exceptions
```

Главная идея проекта — **не просто вызвать LLM, а построить контролируемый application-level цикл вокруг модели**:

```text
LLM
 ↓
Decision
 ↓
Tool Calling
 ↓
Tool Execution
 ↓
Tool Result
 ↓
LLM
 ↓
Final Response
```

При этом HTTP, persistence, инструменты, LLM provider и orchestration остаются разделёнными между собой.

Это позволяет получить относительно небольшую, но уже полноценную основу для разработки AI-агентов на Python с использованием современного стека LangChain и FastAPI.
