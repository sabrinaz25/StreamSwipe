# StreamSwipe API (FastAPI)

## Quick start (Windows PowerShell)

```powershell
cd api
copy .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Open docs at `http://localhost:8000/docs`.
