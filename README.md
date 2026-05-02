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

## Test on iPhone (Expo Go)

- Install **Expo Go** on your iPhone.
- Put your iPhone and computer on the **same Wi‑Fi**.
- Start backend:

```powershell
cd api
copy .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Start Expo and scan the QR code in the Expo Go app.

Notes:
- The app will **auto-detect** your computer’s LAN IP for the API using the Expo dev host. If you want to force it, set `EXPO_PUBLIC_API_BASE_URL` in `mobile/.env` to `http://<your-lan-ip>:8000`.

## Test on web

```powershell
cd mobile
npm run web
```

For web, `EXPO_PUBLIC_API_BASE_URL=http://localhost:8000` is correct.
