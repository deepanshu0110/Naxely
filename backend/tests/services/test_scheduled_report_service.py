import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import patch, MagicMock


class TestCopyUploadToScheduledSource:
    USER_ID = "user-abc"
    FILE_EXT = "csv"

    @pytest.mark.asyncio
    async def test_copies_csv_from_permanent_to_scheduled_sources(self):
        from app.services.scheduled_report_service import copy_upload_to_scheduled_source

        fake_csv_bytes = b"col1,col2\n1,2\n3,4"

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.download.return_value = fake_csv_bytes
        mock_storage.storage.from_.return_value.upload.return_value = None

        with patch("app.services.scheduled_report_service._get_supabase", return_value=mock_storage):
            result = await copy_upload_to_scheduled_source(
                upload_id="upload-123",
                scheduled_report_id="sr-abc-123",
                user_id=self.USER_ID,
                file_ext=self.FILE_EXT,
            )

        assert result == "scheduled-sources/sr-abc-123.csv"

        # Reads from uploads/ bucket with permanent/ path
        mock_storage.storage.from_.assert_any_call("uploads")
        mock_storage.storage.from_.return_value.download.assert_called_once_with(
            f"permanent/{self.USER_ID}/upload-123.{self.FILE_EXT}",
        )
        mock_storage.storage.from_.return_value.upload.assert_called_once_with(
            "scheduled-sources/sr-abc-123.csv",
            fake_csv_bytes,
            {"content-type": "text/csv"},
        )

    @pytest.mark.asyncio
    async def test_raises_on_missing_storage_file(self):
        from app.services.scheduled_report_service import copy_upload_to_scheduled_source

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.download.side_effect = Exception(
            "The resource was not found",
        )

        with patch("app.services.scheduled_report_service._get_supabase", return_value=mock_storage):
            with pytest.raises(Exception, match="The resource was not found"):
                await copy_upload_to_scheduled_source(
                    upload_id="missing-upload",
                    scheduled_report_id="sr-abc",
                    user_id=self.USER_ID,
                    file_ext=self.FILE_EXT,
                )

    @pytest.mark.asyncio
    async def test_scheduled_source_survives_one_off_cleanup(self):
        """The scheduled-sources/ copy must persist even after a one-off report
        deletes the uploads/ copy (Guard 2)."""
        from app.services.scheduled_report_service import copy_upload_to_scheduled_source

        fake_csv_bytes = b"a,b\n1,2"

        mock_storage = MagicMock()
        mock_storage.storage.from_.return_value.download.return_value = fake_csv_bytes
        mock_storage.storage.from_.return_value.upload.return_value = None

        with patch("app.services.scheduled_report_service._get_supabase", return_value=mock_storage):
            await copy_upload_to_scheduled_source(
                upload_id="upload-123",
                scheduled_report_id="sr-persist-1",
                user_id=self.USER_ID,
                file_ext=self.FILE_EXT,
            )

        # remove() should NOT be called — the CSV persists
        remove_calls = [
            call for call in mock_storage.storage.method_calls
            if call[0].startswith("from_.return_value.remove")
        ]
        assert len(remove_calls) == 0, "scheduled-source CSV was deleted unexpectedly"
