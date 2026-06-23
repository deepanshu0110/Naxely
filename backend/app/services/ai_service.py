import asyncio
import json
import logging
import time
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException
from openai import OpenAI, APITimeoutError, AuthenticationError as OpenAIAuthError, RateLimitError as OpenAIRateLimitError, BadRequestError as OpenAIBadRequestError
from anthropic import Anthropic, APITimeoutError as AnthropicTimeoutError, AuthenticationError as AnthropicAuthError, RateLimitError as AnthropicRateLimitError
import requests

from app.core.config import settings
from app.models.user import User
from app.utils.encryption import decrypt_api_key, get_master_key
from app.services.data_service import compute_column_stats

logger = logging.getLogger(__name__)

PROVIDER_CONFIG = {
    "gemini":    {"base_url": None,                              "model": "gemini-2.0-flash"},
    "openai":    {"base_url": "https://api.openai.com/v1",       "model": "gpt-4o"},
    "claude":    {"base_url": None,                              "model": "claude-sonnet-4-6"},
    "groq":      {"base_url": "https://api.groq.com/openai/v1",  "model": "llama-3.3-70b-versatile"},
    "deepseek":  {"base_url": "https://api.deepseek.com/v1",     "model": "deepseek-chat"},
    "mistral":   {"base_url": "https://api.mistral.ai/v1",       "model": "mistral-large-latest"},
}


def get_user_api_key(user: User) -> tuple[str, str]:
    provider = str(user.ai_provider or "gemini")
    if provider == "gemini":
        from app.core.config import settings as app_settings
        server_key = app_settings.GEMINI_API_KEY
        if server_key:
            return ("gemini", server_key)
    if not user.encrypted_api_key or not user.api_key_iv:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "API_KEY_REQUIRED",
                "message": "Add your API key in Settings to use AI features",
            },
        )
    master_key = get_master_key()
    encrypted = str(user.encrypted_api_key) if not isinstance(user.encrypted_api_key, str) else user.encrypted_api_key
    iv = str(user.api_key_iv) if not isinstance(user.api_key_iv, str) else user.api_key_iv
    plaintext_key = decrypt_api_key(encrypted, iv, master_key)
    return (provider, plaintext_key)


def call_openai(prompt: str, system: str, api_key: str, timeout: int = 25) -> str:
    return call_openai_compat(prompt, system, api_key, timeout, base_url="https://api.openai.com/v1", model="gpt-4o")


def call_openai_compat(prompt: str, system: str, api_key: str, timeout: int = 25, base_url: str | None = None, model: str | None = None) -> str:
    client = OpenAI(api_key=api_key, timeout=timeout, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model=model or "gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        result = response.choices[0].message.content
    except OpenAIAuthError:
        raise HTTPException(status_code=400, detail="Invalid API key — please update in Settings")
    except OpenAIRateLimitError:
        raise HTTPException(status_code=429, detail="AI rate limit — try again in 60 seconds")
    except OpenAIBadRequestError as e:
        detail = str(e.response.json().get("error", {}).get("message", str(e))) if e.response else str(e)
        logger.error("OpenAI call 400: %s", detail)
        raise HTTPException(status_code=400, detail=f"AI request failed: {detail[:200]}")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI timed out — report saved without AI insights")
    except Exception as e:
        logger.error("OpenAI call failed: %s", type(e).__name__)
        raise HTTPException(status_code=500, detail="AI generation failed")
    finally:
        del client
    if result is None:
        raise HTTPException(status_code=500, detail="AI returned empty response")
    return result


def call_claude(prompt: str, system: str, api_key: str, timeout: int = 25) -> str:
    client = Anthropic(api_key=api_key, timeout=timeout)
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        result = response.content[0].text
    except AnthropicAuthError:
        raise HTTPException(status_code=400, detail="Invalid API key — please update in Settings")
    except AnthropicRateLimitError:
        raise HTTPException(status_code=429, detail="AI rate limit — try again in 60 seconds")
    except AnthropicTimeoutError:
        raise HTTPException(status_code=504, detail="AI timed out — report saved without AI insights")
    except Exception as e:
        logger.error("Claude call failed: %s", type(e).__name__)
        raise HTTPException(status_code=500, detail="AI generation failed")
    finally:
        del client
    if not result:
        raise HTTPException(status_code=500, detail="AI returned empty response")
    return result


def call_gemini(prompt: str, system: str, api_key: str, timeout: int = 25) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 429:
                raise HTTPException(status_code=429, detail="AI rate limit — try again in 60 seconds")
            if resp.status_code == 403 or resp.status_code == 401:
                raise HTTPException(status_code=400, detail="Invalid API key — please update in Settings")
            if resp.status_code == 503:
                logger.warning("Gemini 503 attempt %d/3 — backing off", attempt + 1)
                if attempt < 2:
                    time.sleep(1 << attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise HTTPException(status_code=500, detail="AI returned empty response")
            finish_reason = candidates[0].get("finishReason", "UNKNOWN")
            result = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            logger.info("Gemini finishReason=%s result_len=%d", finish_reason, len(result))
            if not result:
                raise HTTPException(status_code=500, detail="AI returned empty response")
            return result
        except HTTPException:
            raise
        except requests.Timeout:
            logger.warning("Gemini Timeout attempt %d/3 — backing off", attempt + 1)
            if attempt < 2:
                time.sleep(1 << attempt)
            continue
        except requests.RequestException as e:
            status = e.response.status_code if e.response is not None else "N/A"
            body = e.response.text if e.response is not None else "N/A"
            logger.error("Gemini call failed: status=%s body=%s", status, body)
            raise HTTPException(status_code=500, detail="AI generation failed")
    logger.error("Gemini retry exhausted after 3 attempts")
    raise HTTPException(status_code=504, detail="AI timed out — report saved without AI insights")


def _call_ai(provider: str, prompt: str, system: str, api_key: str, timeout: int = 25) -> str:
    if provider == "claude":
        return call_claude(prompt, system, api_key, timeout)
    if provider == "gemini":
        return call_gemini(prompt, system, api_key, timeout)
    cfg = PROVIDER_CONFIG.get(provider)
    if cfg and cfg.get("base_url"):
        return call_openai_compat(prompt, system, api_key, timeout, base_url=cfg["base_url"], model=cfg["model"])
    return call_openai(prompt, system, api_key, timeout)


def _build_column_stats(df: pd.DataFrame, null_counts_override: dict | None = None) -> dict:
    stats = compute_column_stats(df)
    columns_out = []
    for col in stats["columns"]:
        entry = {
            "name": col["name"],
            "type": col["type"],
            "mean": col.get("mean"),
            "min": col.get("min"),
            "max": col.get("max"),
            "latest_value": col.get("latest_value"),
            "trend": col.get("trend", "flat"),
            "trend_pct_change": col.get("trend_pct_change", 0.0),
            "null_count": (null_counts_override or {}).get(col["name"], col["null_count"]),
            "row_count": col["row_count"],
        }
        columns_out.append(entry)
    return {
        "columns": columns_out,
        "date_column": stats["date_column"],
        "date_range": stats["date_range"],
    }


async def generate_summary(df: pd.DataFrame, config: dict, user: User) -> Optional[str]:
    try:
        provider, api_key = get_user_api_key(user)
    except HTTPException:
        return None

    column_stats = _build_column_stats(df, null_counts_override=config.get("_raw_null_counts"))
    column_stats_json = json.dumps(column_stats, default=str)

    metric_cols = [c for c in column_stats["columns"] if c["type"] == "metric"]
    if metric_cols:
        top_kpi = max(metric_cols, key=lambda c: c.get("trend_pct_change", 0) or 0)["name"]
        bottom_kpi = min(metric_cols, key=lambda c: c.get("trend_pct_change", 0) or 0)["name"]
    else:
        top_kpi = "N/A"
        bottom_kpi = "N/A"

    date_range = column_stats.get("date_range", {})
    tone = config.get("tone", "Professional")

    system_prompt = (
        "You are a professional business analyst writing executive summaries for client reports.\n"
        "Write concisely and authoritatively. Never fabricate numbers — only reference data provided."
    )

    user_prompt = (
        f"Write an executive summary for a {tone} marketing performance report.\n\n"
        f"Dataset statistics:\n{column_stats_json}\n\n"
        f"Key findings:\n"
        f"- Best performing metric: {top_kpi}\n"
        f"- Worst performing metric: {bottom_kpi}\n"
        f"- Date range: {date_range.get('from', 'N/A')} to {date_range.get('to', 'N/A')}\n"
        f"- Total rows: {len(df)}\n\n"
        f"Requirements:\n"
        f"- Exactly 150-250 words\n"
        f"- Third person (\"Revenue increased...\" not \"Your revenue...\")\n"
        f"- Mention: top performer, biggest concern, one recommended action\n"
        f"- Tone: {tone}\n"
        f"- Return ONLY the summary text, no headers or bullets"
    )

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _call_ai, provider, user_prompt, system_prompt, api_key,
    )


async def generate_nra_insights(df: pd.DataFrame, config: dict, user: User) -> list[dict]:
    try:
        provider, api_key = get_user_api_key(user)
    except HTTPException:
        return []

    column_stats = _build_column_stats(df, null_counts_override=config.get("_raw_null_counts"))
    metric_cols = [c for c in column_stats["columns"] if c["type"] == "metric"]
    kpi_stats_json = json.dumps(metric_cols, default=str)

    system_prompt = (
        "You are a data analyst generating actionable business insights.\n"
        "Return ONLY valid JSON. No preamble, no explanation."
    )

    user_prompt = (
        f"Generate NRA insights for these KPIs:\n{kpi_stats_json}\n\n"
        f"Return a JSON array where each object has:\n"
        f'{{\n'
        f'  "kpi": "metric name",\n'
        f'  "number": "one specific number-led observation",\n'
        f'  "reason": "one specific cause or explanation",\n'
        f'  "action": "one specific recommended action",\n'
        f'  "sentiment": "positive|negative|neutral",\n'
        f'  "priority": "high|medium|low"\n'
        f'}}\n\n'
        f"Rules:\n"
        f'- Every "number" field MUST start with an actual number from the data\n'
        f'- Every "action" must be specific and executable\n'
        f"- Maximum 5 insights\n"
        f"- trend and trend_pct_change measure different things and may point in different directions — this is expected, not an error. trend reflects the slope across the full period; trend_pct_change reflects only the first-to-last value change. NEVER generate an insight whose finding is that these two fields conflict, are \"contradictory\", indicate a \"calculation error\", need \"review\", \"correction\", or \"clarification\" of methodology. If they diverge, that itself is not insight-worthy — instead look for the REAL underlying business pattern (e.g. an overall upward trend with a recent dip) and only surface it as an insight if it reflects genuine business significance, not a metric-definition mismatch.\n"
        f"- Return ONLY the JSON array"
    )

    required_keys = {"kpi", "number", "reason", "action", "sentiment", "priority"}

    try:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None, _call_ai, provider, user_prompt, system_prompt, api_key,
        )
    except HTTPException:
        raise

    try:
        cleaned = raw.strip().lstrip("```json").rstrip("```").strip()
        insights = json.loads(cleaned)
        if not isinstance(insights, list):
            return []
        valid = []
        for item in insights[:5]:
            if isinstance(item, dict) and required_keys.issubset(item.keys()):
                valid.append(item)
        return valid
    except Exception:
        return []


def detect_anomalies(df: pd.DataFrame) -> list[dict]:
    anomalies = []
    for col_name in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col_name]):
            continue
        col_data = df[col_name].dropna()
        if len(col_data) < 3:
            continue
        mean = col_data.mean()
        std = col_data.std()
        if std == 0:
            continue
        z_scores = (col_data - mean) / std
        outlier_mask = z_scores.abs() > 2
        for idx in col_data[outlier_mask].index:
            value = float(df.loc[idx, col_name])
            z = round(float(z_scores.loc[idx]), 2)
            anomalies.append({
                "column": str(col_name),
                "row_index": int(idx),
                "value": value,
                "z_score": z,
                "mean": round(float(mean), 2),
                "std": round(float(std), 2),
                "deviation": z,
                "expected": f"{round(mean - 2 * std, 2)} – {round(mean + 2 * std, 2)}",
                "message": f"{str(col_name)} value {value:.2f} is {abs(z):.1f}x the standard deviation from the mean",
            })
            if len(anomalies) >= 5:
                return anomalies
    return anomalies


def detect_trends(df: pd.DataFrame, date_col: str | None = None) -> list[dict]:
    trends = []
    for col_name in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col_name]):
            continue
        col_data = df[col_name].dropna()
        if len(col_data) < 2:
            continue
        values = col_data.values.astype(float)
        x = np.arange(len(values))
        slope = float(np.polyfit(x, values, 1)[0])
        if slope > 0.01:
            trend = "increasing"
        elif slope < -0.01:
            trend = "decreasing"
        else:
            trend = "flat"
        first_value = float(values[0])
        last_value = float(values[-1])
        if first_value == 0:
            pct_change = 0.0
        else:
            pct_change = round(((last_value - first_value) / abs(first_value)) * 100, 2)
        trends.append({
            "column": str(col_name),
            "trend": trend,
            "pct_change": pct_change,
        })
    return trends
