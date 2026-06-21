import logging

from app.core.supabase_helpers import _get_supabase, _run_sync
from app.services.report_service import get_upload

logger = logging.getLogger(__name__)


async def copy_upload_to_scheduled_source(upload_id: str, scheduled_report_id: str) -> str:
    upload = await get_upload(upload_id)
    if not upload:
        raise ValueError(f"Upload {upload_id} not found")

    file_url = upload["file_url"]

    csv_bytes = await _run_sync(
        _get_supabase().storage.from_("uploads").download, file_url,
    )

    dest_path = f"scheduled-sources/{scheduled_report_id}.csv"
    await _run_sync(
        _get_supabase().storage.from_("scheduled-sources").upload,
        dest_path,
        csv_bytes,
        {"content-type": "text/csv"},
    )

    return dest_path
