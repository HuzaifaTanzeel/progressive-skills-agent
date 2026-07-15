# Frontend

Next.js UI for the GovTech Skills Assistant demo.

- **Chat** (`/`) — progressive Agent Skills over dummy Saudi civic workflows
- **Dashboard** (`/dashboard`) — read-only eval summary from `GET /api/admin/eval-summary`

## Setup (local)

```powershell
copy .env.local.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to the FastAPI server (default `http://localhost:8000`).

## Docker

Built via repo-root Compose (recommended):

```powershell
# from repo root
copy .env.example .env   # set OPENAI_API_KEY
docker compose up --build
```

- UI: http://localhost:3000  
- API: http://localhost:8000  

Frontend-only image:

```powershell
docker build -f frontend/Dockerfile --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 -t govtech-frontend .
docker run --rm -p 3000:3000 govtech-frontend
```

The image uses Next.js `output: "standalone"`. `NEXT_PUBLIC_API_URL` is baked in at **build** time (browser calls the host-mapped API).

See the [root README](../README.md) for full stack instructions.
