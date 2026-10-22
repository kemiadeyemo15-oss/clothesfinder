# clothesfinder — handoff / continuation notes

Written 2026-10-23. Read this + `README.md` + `GOING-LIVE.md` to continue.

## What it is
Hyper-specific clothing search, **text-first and image-first**, over a *curated*
set of trusted retailers (no SHEIN/Temu/marketplace junk). Text and image both
collapse to one intermediate (structured attributes + embedding) → one ranker.

## Live right now
- **Site (frontend):** https://clothesfinder.vercel.app  (Vercel, React/Vite)
- **API (backend):** https://clothesfinder-api.onrender.com  (Render, FastAPI, Docker)
- **Repo:** https://github.com/kemiadeyemo15-oss/clothesfinder  (branch `main`)
- **Status:** WORKING with **real products** via SerpApi. Confirmed live searches
  return real buyable items (Aritzia, Reformation, & Other Stories, Mango,
  Everlane…) with prices, shipping estimates, junk excluded.

## Accounts / services (owner: kemiadeyemo15-oss)
- GitHub: kemiadeyemo15-oss/clothesfinder (Claude GitHub App installed for push).
- Render: service `clothesfinder-api`, free tier, Docker, auto-deploys on push to main.
- Vercel: project root `frontend`, env `VITE_API_URL=https://clothesfinder-api.onrender.com`.
- SerpApi key + Anthropic key: set in the **Render dashboard** env (never in repo).

## Current runtime config (Render env vars)
- `CF_INVENTORY=shopping_api`  → real products from SerpApi (`CF_SHOPPING_API_URL=https://serpapi.com/search`, `CF_SHOPPING_API_KEY=…`)
- `CF_TAGGER=vlm` (+ `CF_LLM_API_KEY`, `CF_LLM_MODEL`) → Claude-vision tagging of products *(set by user; not yet externally confirmed as firing vs title-fallback)*
- `CF_EMBEDDER=stub` → matches on structured tags (fine; Lykdat not needed yet)
- `CF_REPO_BACKEND=memory` → in-RAM, resets on restart/sleep
- `CF_QUERY_PARSER=rules`, `CF_ENV=prod`, `CF_CORS_ORIGINS=["https://clothesfinder.vercel.app"]`
- Full `CF_` reference + what each switch does: see `GOING-LIVE.md`.

## Architecture (every external dep behind an interface, chosen by env var)
`backend/app/`: config.py · schemas.py · domain.py · core/{vocab,allowlist} ·
services/{query, tagger, embeddings, inventory, retrieval, ranking, search_service,
repository, repository_pg} · api/{routes_search, routes_health} · main.py · ingest.py.
Postgres+pgvector path exists (models.py, alembic/, repository_pg.py) for when you
move off memory. `frontend/`: Vite+React+TS, house-style theme.

## What was done tonight
Built full repo, pushed, deployed backend (Render) + frontend (Vercel), fixed CORS,
added SerpApi inventory with title-tagging, added Claude-vision tagger (CF_TAGGER=vlm),
and fixed a bug where strict retailer matching returned 0 real results (now
normalised, case/punctuation-insensitive). Consolidated a duplicate tagger module
introduced by a parallel process.

## PENDING — pick up here (highest impact first)
1. **UK locale (recommended, ~1 line).** SerpApi defaults to US → prices are likely
   USD shown with a "£" sign, and retailers skew US. In
   `backend/app/services/inventory.py` (ShoppingApiInventory.fetch), add SerpApi
   params `gl=uk`, `hl=en`, `location=United Kingdom`, and ideally `currency=GBP`.
   Gives UK retailers + real GBP prices.
2. **Currency correctness.** Product.currency is hard-"GBP"; map it from SerpApi's
   returned currency, or lock the locale per #1. Display assumes GBP.
3. **Widen the allowlist.** Only 12 shops in `backend/app/data/allowlist.json` →
   modest result counts. Add reputable UK retailers (M&S, Reiss, Whistles, Next,
   ASOS, Zara, Massimo Dutti, Nordstrom…) with honest `ship_days` estimates.
4. **Confirm vision tagging.** Verify `CF_TAGGER=vlm` is really firing (not falling
   back to title rules). Inspect per-product tags; check `CF_LLM_MODEL` is a current
   vision-capable model from the Anthropic console (Haiku-class = cheapest).
5. **Durable storage + tag cache.** Move to `CF_REPO_BACKEND=postgres` (add Render
   Postgres, `alembic upgrade head`, run `python -m app.ingest "<terms>"`), so tags
   persist (the in-RAM cache resets when Render sleeps) and vector search scales.
6. **Image-first search (optional).** `CF_EMBEDDER=lykdat` for true "find this exact
   look from a photo". Lykdat docs were unreachable 2026-10-23 — confirm endpoints
   from their dashboard; code has placeholders in `services/embeddings.py`.
7. **Economics.** SerpApi = 1 credit/search (free tier burns fast). Long-term cheap
   + commission path = affiliate feeds (Awin/CJ, needs approved publisher accounts)
   ingested into Postgres once, not a live API call per query.

## Gotchas
- Render free tier sleeps after ~15 min idle → first request ~30–50s (cold start).
- In-memory tag cache + catalogue reset on redeploy/sleep (→ #5).
- Keys live only in Render/Vercel dashboards; never commit them.
- SerpApi field mapping already handled: retailer=`source`, price=`extracted_price`,
  link=`product_link`, image=`thumbnail`.

## How to run locally (zero keys)
`cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
then `cd frontend && npm install && npm run dev`. Defaults to seed/stub/memory.
Tests: `cd backend && pip install -r requirements-dev.txt && pytest -q`.
