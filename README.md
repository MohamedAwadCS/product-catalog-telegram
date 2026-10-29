# Product Catalog Telegram

This is a small product catalog. The admin creates products from a Telegram bot (one photo with the product name as the caption), and anyone can view them on a Next.js catalog page, in the browser or inside Telegram as a TMA.

Stack: FastAPI, PostgreSQL, MinIO, aiogram 3, Next.js (App Router), nginx, Docker.

## How to run

1. Copy `.env.example` to `.env` and fill it in (bot token from @BotFather, your Telegram id as `ADMIN_ID`, any random string as `WEBHOOK_SECRET`).

2. To get it started use this command in your terminal:
   ```
   docker compose up -d --build
   ```
3. Telegram needs a public https address, so start a tunnel to nginx:
   ```
   cloudflared tunnel --url http://localhost:8080
   ```
4. Put the tunnel address in `.env` as both `WEBHOOK_URL` and `CATALOG_URL`, then use these commands:
   ```
   docker compose up -d --force-recreate api
   docker compose restart nginx
   docker compose run --rm api uv run --no-sync python scripts/set_telegram_webhook.py
   ```
5. Send `/start` to the bot.

The catalog is at `http://localhost:8080`, and the MinIO console is at `http://localhost:9001`.

## Architecture

```
Telegram ──► tunnel ──► nginx :8080 ─┬─► api (2 copies) ──► PostgreSQL (products)
browser / Mini App ─────────────────┘                    └► MinIO (photos)
                                     └─► frontend (2 copies, Next.js)
```

- nginx sends `/webhook`, `/health`, `/ready` and `/products` to the api, and everything else to the frontend.
- `migrate` runs once before the api starts. It creates the table and the bucket.
- The bot runs inside the api (the webhook route), so there is no separate bot process.

## Decisions

- **Photo first, then the database row.** Postgres and MinIO can't share a transaction. If something fails in between, the worst case is an unused photo in MinIO, never a product with a missing photo.
- **No duplicates.** The photo key is built from Telegram's `file_unique_id`, and the insert uses `ON CONFLICT DO NOTHING`. If Telegram sends the same message twice, or two api copies get it at the same time, the result is still one product and one photo.
- **Schema setup is a separate step (`migrate`).** If every api copy created the table at startup, they could race each other.
- **Webhook, not polling.** Telegram only allows one polling connection per bot, so polling can't run on more than one instance.
- **Webhook secret.** The webhook checks Telegram's secret header, so nobody can send fake updates pretending to be the admin.
- **Stateless bot.** The name and photo come in one message, so the bot doesn't need to remember anything between messages, which means there's no need for Redis.
- **Pool checks connections.** `check_connection` replaces dead connections, so the api keeps working after Postgres restarts.
- **nginx connect timeout of 2s.** If an api copy dies, nginx moves the request to the other copy after 2s instead of waiting much longer.

## Reliability tests I ran

- Same product sent 4 times at the same moment to 2 api copies: 1 product, 1 photo.
- Forwarded the same photo to the bot twice: 1 product.
- Fake update from a non-admin user: ignored.
- Restarted Postgres, then MinIO, while the api was running: kept working (after adding `check_connection`).
- Stopped Postgres between the photo upload and the insert: the request failed, the retry worked, and there was still only 1 photo.
- Stopped one api copy: 40/40 requests through nginx still worked (slowest 2.2s), and creating a product in Telegram still worked.
- `docker compose down` then `up`: all products and photos were still there.

To scale up: `docker compose up -d --scale api=3 --scale frontend=3`, then `docker compose restart nginx`.

## Known limits

- The quick tunnel address changes every time it restarts, so `.env` and the webhook need updating.
- A photo left over from a failed request that is never retried stays in MinIO (no cleanup job).
- nginx looks up the api copies when it starts, so restart nginx after recreating them.
- The bot replies "Product saved" even when the product already existed.
