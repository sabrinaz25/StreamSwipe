# StreamSwipe
CDS Onboarding Datathon

Monorepo scaffold:
- `api`: FastAPI backend (feed, swipe capture, recommendation)
- `mobile`: Expo React Native app (filters → swipe → match)

## Run backend (Windows PowerShell)

```powershell
cd api
copy .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Backend docs: `http://localhost:8000/docs`

## Run mobile app

```powershell
cd mobile
copy .env.example .env
npm run start
```

If you’re using a physical phone, set `EXPO_PUBLIC_API_BASE_URL` in `mobile/.env` to your computer’s LAN IP:
`http://192.168.x.x:8000`
