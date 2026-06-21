import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import patch, MagicMock


class TestCopyUploadToScheduledSource:
    @pytest.mark.asyncio
    async def test_copies_csv_to_scheduled_sources(self):
        from app.services.scheduled_report_service import copy_upload_to_scheduled_source

        mock_upload = {
            "id": "upload-123",
            "file_url": "uploads/user-abc/upload-123/raw.csv",
            "filename": "data.csv",
        }

        fake_csv_bytes = b"col1,col2\n1,2\n3,4"

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.download.return_value = fake_csv_bytes
        mock_storage.storage.from_.return_value.upload.return_value = None

        with patch("app.services.scheduled_report_service.get_upload", return_value=mock_upload):
            with patch("app.services.scheduled_report_service._get_supabase", return_value=mock_storage):
                result = await copy_upload_to_scheduled_source(
                    upload_id="upload-123",
                    scheduled_report_id="sr-abc-123",
                )

        assert result == "scheduled-sources/sr-abc-123.csv"

        mock_storage.storage.from_.assert_any_call("uploads")
        mock_storage.storage.from_.assert_any_call("scheduled-sources")

        mock_storage.storage.from_.return_value.download.assert_called_once_with(
            "uploads/user-abc/upload-123/raw.csv",
        )
        mock_storage.storage.from_.return_value.upload.assert_called_once_with(
            "scheduled-sources/sr-abc-123.csv",
            fake_csv_bytes,
            {"content-type": "text/csv"},
        )

    @pytest.mark.asyncio
    async def test_raises_on_missing_upload(self):
        from app.services.scheduled_report_service import copy_upload_to_scheduled_source

        with patch("app.services.scheduled_report_service.get_upload", return_value=None):
            with pytest.raises(ValueError, match="Upload missing-upload not found"):
                await copy_upload_to_scheduled_source(
                    upload_id="missing-upload",
                    scheduled_report_id="sr-abc",
                )

    @pytest.mark.asyncio
    async def test_persisted_csv_not_deleted_after_copy(self):
        """CSV in scheduled-sources/ must not be deleted after copy
        (unlike uploads/ which is deleted after chart generation)."""
        from app.services.scheduled_report_service import copy_upload_to_scheduled_source

        mock_upload = {
            "id": "upload-123",
            "file_url": "uploads/user-abc/upload-123/raw.csv",
        }

        fake_csv_bytes = b"a,b\n1,2"

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.download.return_value = fake_csv_bytes
        mock_storage.storage.from_.return_value.upload.return_value = None
        mock_storage.storage.from_.return_value.remove.return_value = None

        with patch("app.services.scheduled_report_service.get_upload", return_value=mock_upload):
            with patch("app.services.scheduled_report_service._get_supabase", return_value=mock_storage):
                await copy_upload_to_scheduled_source(
                    upload_id="upload-123",
                    scheduled_report_id="sr-persist-1",
                )

        # remove() should NOT be called — the CSV persists
        remove_calls = [
            call for call in mock_storage.storage.method_calls
            if call[0].startswith("from_.return_value.remove")
        ]
        assert len(remove_calls) == 0, "scheduled-source CSV was deleted unexpectedly"
