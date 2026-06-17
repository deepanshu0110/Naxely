import asyncio
import functools

from supabase import create_client, Client

from app.core.config import settings

_supabase_client: Client | None = None


def _get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _supabase_client


async def _run_sync(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(func, *args, **kwargs),
    )
