# Going live — wiring real data

The app ships on stubs (seed products, no keys). To make it search **real,
buyable clothes with accurate visual tags**, you flip six environment variables
on Render. No code changes.

## Step 1 — get two keys

- **SerpApi** (real products) — serpapi.com → Dashboard → copy the **Private API
  Key**. Note the free monthly search allowance on their pricing page; each user
  search = 1 SerpApi credit returning ~60 products.
- **Anthropic** (the visual scan) — console.anthropic.com → add billing credit →
  **API Keys → Create Key**. From the console's model list, note a
  **Haiku-class** model ID (cheapest for bulk image tagging). Model IDs change —
  use whatever the console currently lists; don't copy an old one.

## Step 2 — set six variables on Render

Render → **clothesfinder-api** → **Environment** → set these, **Save Changes**
once (auto-redeploys):

| Key | Value |
|-----|-------|
| `CF_INVENTORY` | `shopping_api` |
| `CF_SHOPPING_API_URL` | `https://serpapi.com/search` |
| `CF_SHOPPING_API_KEY` | *your SerpApi key* |
| `CF_TAGGER` | `vlm` |
| `CF_LLM_API_KEY` | *your Anthropic key* |
| `CF_LLM_MODEL` | *the Haiku-class model ID* |

Keys go in the Render dashboard only — never committed to the repo.

## What every CF_ switch does

| Variable | Controls | Options |
|----------|----------|---------|
| `CF_INVENTORY` | where products come from | `seed` (22 demo items) · `shopping_api` (real, via SerpApi, allowlist-filtered) |
| `CF_TAGGER` | how products get tagged | `rules` (keyword-guess from title) · `vlm` (vision model scans the photo + reads the description) |
| `CF_EMBEDDER` | how things become comparable vectors | `stub` (match on tags) · `lykdat` (fashion model for photo-similarity) |
| `CF_QUERY_PARSER` | how the typed search is understood | `rules` (keywords) · `llm` (handles phrasing, negation, occasion) |
| `CF_REPO_BACKEND` | where products are stored | `memory` (RAM, resets on restart) · `postgres` (DB + vector search, durable tag cache) |
| `CF_SHOPPING_API_URL` / `_KEY` | SerpApi endpoint + key | read when `CF_INVENTORY=shopping_api` |
| `CF_LLM_API_KEY` / `CF_LLM_MODEL` | Anthropic key + model | read when `CF_TAGGER=vlm` or `CF_QUERY_PARSER=llm` |
| `CF_LYKDAT_API_KEY` | Lykdat key | only when `CF_EMBEDDER=lykdat` — not needed for the above |
| `CF_CORS_ORIGINS` | which sites may call the API | set to the Vercel frontend origin |
| `CF_ENV` | dev/prod labelling | `prod` on Render |

## Notes & gotchas

- **You don't need Lykdat** for real products + accurate tags. The vision tagger
  (`CF_TAGGER=vlm`) plus the stub embedder is enough. Lykdat is only for a future
  "find this exact look from a photo" feature.
- **First search is slower** — new products get scanned (a few seconds for ~60,
  bounded to 8 concurrent calls). Tags are **cached per product** after that.
- **The cache is in RAM** — it resets when Render sleeps or redeploys. For a
  durable tag cache, move to `CF_REPO_BACKEND=postgres` (add a Render Postgres,
  run `alembic upgrade head`, ingest). See the main README.
- **SerpApi cost** — 1 credit per search. A busy app burns the free tier fast;
  the long-term cheap/earning path is affiliate feeds (Awin/CJ) ingested into
  Postgres once, not a live API call per query.
- **SerpApi field mapping** (already in code): retailer = `source`,
  price = `extracted_price`, link = `product_link`, image = `thumbnail`.

## Verify (don't assume)

After it's live, run a real query and inspect: the products should be real and
buyable (real `product_link`s), from trusted retailers only, with tags that
match the photos. If tags look off, the lever is the `CF_LLM_MODEL` (try a
stronger one) or the prompt in `backend/app/services/tagger.py`.
