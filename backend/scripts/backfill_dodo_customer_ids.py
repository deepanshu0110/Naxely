"""One-time backfill: fetch dodo_customer_id from Dodo API for existing users.

Usage:
    set DODO_API_KEY=sk_live_...  (PowerShell)
    & "backend/venv/Scripts/python.exe" backend/scripts/backfill_dodo_customer_ids.py

Or set the key in .env as DODO_API_KEY=sk_live_...
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
import httpx

os.environ.setdefault("ENVIRONMENT", "development")
from app.core.config import settings

sync_url = str(settings.DATABASE_URL).replace("+asyncpg", "+psycopg2")
engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")

DODO_API_KEY = settings.DODO_API_KEY or os.environ.get("DODO_API_KEY")
if not DODO_API_KEY:
    print("ERROR: DODO_API_KEY not found. Set it via env var or in .env")
    sys.exit(1)

BASE_URL = (
    "https://api.dodopayments.com"
    if settings.DODO_ENVIRONMENT == "live"
    else "https://api.test.dodopayments.com"
)

headers = {
    "Authorization": f"Bearer {DODO_API_KEY}",
    "Content-Type": "application/json",
}

with engine.connect() as conn:
    rows = conn.execute(
        text("""
            SELECT id, email, dodo_subscription_id
            FROM users
            WHERE dodo_subscription_id IS NOT NULL AND dodo_customer_id IS NULL
        """)
    ).fetchall()

if not rows:
    print("No users need backfill.")
    sys.exit(0)

print(f"Found {len(rows)} user(s) to backfill...")
backfilled = 0
failed = 0

for user_id, email, sub_id in rows:
    try:
        resp = httpx.get(
            f"{BASE_URL}/subscriptions/{sub_id}",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        customer_id = data.get("customer_id")
        if not customer_id:
            print(f"  - {email}: no customer_id in sub {sub_id}")
            failed += 1
            continue

        with engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE users
                    SET dodo_customer_id = :cid, updated_at = NOW()
                    WHERE id = :uid AND dodo_customer_id IS NULL
                """),
                {"cid": customer_id, "uid": str(user_id)},
            )
        print(f"  + {email}: sub={sub_id} -> customer_id={customer_id}")
        backfilled += 1

    except Exception as e:
        print(f"  ! {email} (sub={sub_id}): {e}")
        failed += 1

print(f"\nDone. Backfilled: {backfilled}, Failed: {failed}")
