# clothesfinder

Hyper-specific clothing search — **text-first and image-first** — over a
*curated* set of trusted retailers. No SHEIN, no marketplace scams, no 50-day
shipping: junk is excluded by construction, not filtered afterwards.

Both inputs collapse to one intermediate (`Attributes` + a shared embedding),
then hit one ranker — so neither path is bolted on. Every external dependency
(embeddings, inventory, LLM parsing, database) sits behind an interface chosen
by env var, so the app **runs on stubs with zero keys** and flips to real
services one at a time.

```
 text  ─► parse ─┐
                 ├─► Attributes ─► embed ─► retrieve ─► rank ─► results
 image ─► parse ─┘   (shared vocab)  (one space)  (+ allowlist, trust)
```

## Stack
- **Backend** — FastAPI (Python), Postgres + pgvector, async SQLAlchemy, Alembic.
- **Frontend** — React + Vite + TypeScript.
- **Embeddings** — Lykdat (hosted) behind an interface; stub for dev.
- **Inventory** — shopping-search API + allowlist filter; seed JSON for dev.
- **Deploy** — Render (API + Postgres) + Vercel (frontend).

## Run locally (zero keys)
```bash
# backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload            # http://127.0.0.1:8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev                              # http://127.0.0.1:5173
```
Defaults = in-memory repo + stub embedder + seed inventory. `GET /health` shows
which impls are active.

Full Postgres path locally: `docker compose -f infra/docker-compose.yml up --build`.

## The three real services (flip one at a time via `backend/.env`)
| Subsystem | Env | Dev → Prod | You provide |
|-----------|-----|-----------|-------------|
| Inventory | `CF_INVENTORY` | `seed` → `shopping_api` | API key + URL (e.g. SerpApi) |
| Embeddings | `CF_EMBEDDER` | `stub` → `lykdat` | Lykdat key + confirm endpoints |
| Text parsing | `CF_QUERY_PARSER` | `rules` → `llm` | LLM key (optional) |
| Storage | `CF_REPO_BACKEND` | `memory` → `postgres` | a Postgres w/ pgvector |

Each has a `=== SWAP POINT ===` / `TODO` in code marking exactly what to fill.
Signatures don't change, so nothing downstream breaks.

## Deploy (ship it)

**1. Repo** — push this to GitHub.

**2. Backend + DB on Render** — New → Blueprint, point at the repo. `infra/render.yaml`
provisions a free Postgres (pgvector) and the API, runs `alembic upgrade head`
on deploy, and exposes `/health`. It ships on **stubs** first (works immediately).

**3. Frontend on Vercel** — import the repo, root `frontend/`. Set
`VITE_API_URL` to the Render API URL. `vercel.json` handles the Vite build + SPA
routing.

**4. Wire CORS** — set `CF_CORS_ORIGINS=["https://<your>.vercel.app"]` on Render.

**5. Flip real services** — add `CF_SHOPPING_API_KEY`/`_URL` and set
`CF_INVENTORY=shopping_api`; add `CF_LYKDAT_API_KEY` and set `CF_EMBEDDER=lykdat`.
Redeploy. Run the ingest job (`python -m app.ingest "<terms>"`) to populate the
index if you move to the Postgres/feeds path.

Secrets are set in the Render/Vercel dashboards — never commit them.

## Tests
```bash
cd backend && pip install -r requirements-dev.txt && pytest -q
```
CI (`.github/workflows/ci.yml`) runs ruff + pytest on the backend and builds the
frontend on every push/PR.

## Honest gaps (not bugs)
- Image path extracts **colour** for real today; category/material/silhouette
  need the embedding model's tagging (swap point in `services/query.py`).
- `ship_days` is a maintained per-retailer estimate, verified from each
  retailer's stated delivery — not a promise.
- Seed catalogue is 22 items: a harness, not coverage. Real inventory comes from
  the shopping API / feeds.
- Affiliate feed access (the eventual economics) needs approved publisher
  accounts — the real external blocker, independent of this code.
