import logging

from app.core.supabase_helpers import _get_supabase, _run_sync

logger = logging.getLogger(__name__)


async def copy_upload_to_scheduled_source(
    upload_id: str, scheduled_report_id: str, user_id: str, file_ext: str,
) -> str:
    source_path = f"permanent/{user_id}/{upload_id}.{file_ext}"
    dest_path = f"scheduled-sources/{scheduled_report_id}.csv"

    csv_bytes = await _run_sync(
        _get_supabase().storage.from_("uploads").download, source_path,
    )

    await _run_sync(
        _get_supabase().storage.from_("scheduled-sources").upload,
        dest_path,
        csv_bytes,
        {"content-type": "text/csv"},
    )

    return dest_path
