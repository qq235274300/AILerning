# Repository Guidelines

## Project Structure & Module Organization

This repository is a small Python project centered on `day-01/`. The main FastAPI entry point is `day-01/main.py`, which exposes `/chat` and `/chat/stream`. LLM client logic and chat history live in `day-01/llm.py`; Pydantic response/request models are in `day-01/models.py`; prompts, tool schemas, and tool implementations are split across `prompt.py`, `tool_definitions.py`, and `tools.py`. Browser-facing static UI currently lives in `day-01/index.html`. Experimental or older examples are under `day-01/Test/`.

Do not commit local runtime artifacts such as `day-01/.env`, `.venv/`, `.vscode/`, or `__pycache__/`.

## Build, Test, and Development Commands

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn python-dotenv openai pydantic pydantic-ai instructor nest-asyncio
python .\day-01\main.py
```

`python .\day-01\main.py` starts the local API at `http://127.0.0.1:8000`. If you prefer Uvicorn reload during development, run from `day-01/`:

```powershell
uvicorn main:app --reload
```

There is no committed `requirements.txt` yet. When adding or changing dependencies, update a dependency manifest in the same change.

## Coding Style & Naming Conventions

Use Python 3.11+ style with 4-space indentation. Keep modules focused: request/response schemas belong in `models.py`, OpenAI tool definitions in `tool_definitions.py`, and executable tool logic in `tools.py`. Prefer snake_case for functions and variables, PascalCase for Pydantic models, and descriptive endpoint names such as `chat_api` or `chat_stream`.

Keep comments short and useful. Existing comments include Chinese notes; preserve them when editing nearby code and use the language that best matches the surrounding context.

## Testing Guidelines

Tests and experiments currently live in `day-01/Test/`. Name new tests `test_*.py` or `*_test.py` so they can be discovered by common Python tooling. Prefer small tests around Pydantic validation, tool routing, and FastAPI endpoints. If adding pytest, run:

```powershell
python -m pytest .\day-01\Test
```

Avoid tests that require real OpenAI API calls unless they are explicitly marked as integration tests.

## Commit & Pull Request Guidelines

Recent commits use short, direct messages, sometimes in Chinese, such as `使用fastapi 网页提问带历史信息` and `LLM.PY中完成support ticket生成`. Keep commits focused and describe the functional change.

Pull requests should include a brief summary, commands run, any required environment variables, and screenshots or request/response examples when UI or API behavior changes.

## Security & Configuration

Store secrets only in `day-01/.env`; never hard-code API keys. Document required variables, such as `OPENAI_API_KEY`, when adding setup instructions.
