"""
sheets_service.py -- Google Sheets data ingestion for Naxely.

Uses Sheets API v4 via google-api-python-client (already installed).
Auth: service account credentials from GOOGLE_SERVICE_ACCOUNT_JSON env var.
No gspread needed.

Usage:
    creds = build_credentials(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
    df = fetch_sheet_as_df(sheet_id, creds)
"""

from __future__ import annotations

import json
import logging
import re

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SHEETS_URL_PATTERN = re.compile(
    r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)"
)


def extract_sheet_id(url: str) -> str:
    match = SHEETS_URL_PATTERN.search(url)
    if not match:
        raise ValueError(
            f"Invalid Google Sheets URL: {url!r}. "
            "Expected format: https://docs.google.com/spreadsheets/d/<ID>/..."
        )
    return match.group(1)


def get_service_account_email(sa_json: str) -> str | None:
    if not sa_json:
        return None
    try:
        data = json.loads(sa_json)
        return data.get("client_email")
    except (json.JSONDecodeError, AttributeError):
        return None


def build_credentials(sa_json: str):
    if not sa_json or not sa_json.strip():
        raise ValueError(
            "Google Sheets integration is not configured. "
            "GOOGLE_SERVICE_ACCOUNT_JSON is empty."
        )
    try:
        sa_info = json.loads(sa_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid GOOGLE_SERVICE_ACCOUNT_JSON: {e}") from e

    return service_account.Credentials.from_service_account_info(
        sa_info, scopes=SCOPES
    )


def fetch_sheet_as_df(sheet_id: str, credentials) -> pd.DataFrame:
    try:
        service = build("sheets", "v4", credentials=credentials)
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range="A1:ZZ100000")
            .execute()
        )
    except HttpError as e:
        status = e.resp.status
        if status == 403:
            email = credentials.service_account_email if hasattr(credentials, 'service_account_email') else "the Naxely service account"
            raise PermissionError(
                f"Cannot access this sheet. Please share it with {email} "
                f"(Viewer access is sufficient)."
            ) from e
        elif status == 404:
            raise ValueError(
                "Sheet not found. Check the URL and make sure the sheet exists."
            ) from e
        else:
            raise RuntimeError(
                f"Google Sheets API error ({status}): {e.reason}"
            ) from e

    rows = result.get("values", [])
    if not rows:
        raise ValueError("The sheet appears to be empty (no data found).")
    if len(rows) < 2:
        raise ValueError(
            "The sheet must have at least a header row and one data row."
        )

    headers = rows[0]
    data_rows = rows[1:]

    padded = [row + [""] * (len(headers) - len(row)) for row in data_rows]

    df = pd.DataFrame(padded, columns=headers)
    logger.info(
        f"sheets_service: fetched sheet_id={sheet_id} "
        f"rows={len(df)} cols={list(df.columns)}"
    )
    return df
