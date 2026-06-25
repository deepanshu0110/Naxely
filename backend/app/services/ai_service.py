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


def _get_user_provider_config(user) -> tuple[str, str, str | None]:
    provider = str(getattr(user, 'ai_provider', None) or "gemini")
    cfg = PROVIDER_CONFIG.get(provider, {})
    base_url = cfg.get("base_url")

    if provider == "gemini":
        return ("gemini", settings.GEMINI_API_KEY, base_url)

    master_key = get_master_key()
    encrypted = str(user.encrypted_api_key) if not isinstance(user.encrypted_api_key, str) else user.encrypted_api_key
    iv = str(user.api_key_iv) if not isinstance(user.api_key_iv, str) else user.api_key_iv
    plaintext_key = decrypt_api_key(encrypted, iv, master_key)
    return (provider, plaintext_key, base_url)


def get_user_api_key(user: User) -> tuple[str | None, str | None, str | None]:
    tier = (
        getattr(user, 'subscription_tier', None)
        or getattr(user, 'tier', None)
        or 'free'
    ).lower()
    has_stored_key = bool(
        getattr(user, 'encrypted_api_key', None) and
        getattr(user, 'api_key_iv', None)
    )

    if not has_stored_key:
        return None, None, None

    return _get_user_provider_config(user)


def call_openai(prompt: str, system: str, api_key: str, timeout: int = 25) -> str:
    result = call_openai_compat(prompt, system, api_key, timeout, base_url="https://api.openai.com/v1", model="gpt-4o")
    if result is None:
        return ""
    return result


DEEPSEEK_UNSUPPORTED_PARAMS = {
    "logprobs", "top_logprobs", "n", "stream",
    "presence_penalty", "frequency_penalty", "user",
    "response_format",
}


def _sanitize_kwargs(kwargs: dict, base_url: str | None) -> dict:
    if base_url and "deepseek.com" in base_url:
        return {k: v for k, v in kwargs.items() if k not in DEEPSEEK_UNSUPPORTED_PARAMS}
    return kwargs


def call_openai_compat(prompt: str, system: str, api_key: str, timeout: int = 25, base_url: str | None = None, model: str | None = None) -> str | None:
    client = OpenAI(api_key=api_key, timeout=timeout, base_url=base_url)
    try:
        kwargs = _sanitize_kwargs({
            "model": model or "gpt-4o",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }, base_url)
        response = client.chat.completions.create(**kwargs)
        result = response.choices[0].message.content
    except OpenAIAuthError:
        raise ValueError("Invalid API key (HTTP 401/403)")
    except OpenAIRateLimitError:
        raise HTTPException(status_code=429, detail="AI rate limit — try again in 60 seconds")
    except OpenAIBadRequestError as e:
        detail = str(e.response.json().get("error", {}).get("message", str(e))) if e.response else str(e)
        logger.warning("AI provider returned 400 — likely unsupported parameter. Response: %s", detail)
        return None
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI timed out — report saved without AI insights")
    except Exception as e:
        logger.error("AI call failed: %s", type(e).__name__)
        return None
    finally:
        try:
            del client
        except Exception:
            pass
    if result is None:
        return None
    return result


def validate_api_key(provider: str, api_key: str) -> dict:
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        return {"valid": False, "message": f"Unknown provider: {provider}"}

    if provider == "gemini":
        return {"valid": True, "message": ""}

    try:
        if provider == "claude":
            call_claude("hi", "", api_key, timeout=10)
        else:
            call_openai_compat("hi", "", api_key, timeout=10, base_url=config["base_url"], model=config["model"])
        return {"valid": True, "message": ""}
    except HTTPException as e:
        detail = str(e.detail) if hasattr(e, "detail") else str(e)
        if "Invalid API key" in detail or "401" in detail or "Unauthorized" in detail:
            return {"valid": False, "message": "Invalid API key"}
        if "400" in detail or "Bad Request" in detail:
            logger.warning("[validate_api_key] %s returned 400: %s", provider, detail)
            return {"valid": True, "message": f"{provider} returned 400 — your key may be valid, but review API config: {detail[:200]}"}
        return {"valid": True, "message": f"{provider} key accepted (non-auth error)"}
    except ValueError as e:
        if "Invalid API key" in str(e) or "401" in str(e):
            return {"valid": False, "message": "Invalid API key"}
        return {"valid": True, "message": f"{provider} key accepted (unexpected ValueError)"}
    except Exception as e:
        estr = str(e)
        if "401" in estr or "Unauthorized" in estr or "AuthenticationError" in estr:
            return {"valid": False, "message": "Invalid API key"}
        logger.warning("[validate_api_key] %s validation error: %s", provider, estr)
        return {"valid": True, "message": f"{provider} key accepted (unexpected response)"}


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
        result = call_openai_compat(prompt, system, api_key, timeout, base_url=cfg["base_url"], model=cfg["model"])
        if result is None:
            return ""
        return result
    result = call_openai(prompt, system, api_key, timeout)
    if result is None:
        return ""
    return result


def _round_stats(entry: dict) -> dict:
    """Round all float values in a column stats entry to 2 decimal places."""
    rounded = {}
    for k, v in entry.items():
        if isinstance(v, float):
            rounded[k] = round(v, 2)
        elif isinstance(v, dict):
            rounded[k] = {
                dk: round(dv, 2) if isinstance(dv, float) else dv
                for dk, dv in v.items()
            }
        else:
            rounded[k] = v
    return rounded


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
        columns_out.append(_round_stats(entry))
    return {
        "columns": columns_out,
        "date_column": stats["date_column"],
        "date_range": stats["date_range"],
    }


async def generate_summary(df: pd.DataFrame, config: dict, user: User) -> Optional[str]:
    try:
        provider, api_key, _ = get_user_api_key(user)
    except HTTPException:
        return None
    if api_key is None:
        return None

    column_stats = _build_column_stats(df, null_counts_override=config.get("_raw_null_counts"))

    metric_cols = [c for c in column_stats["columns"] if c["type"] == "metric"]

    # Build human-readable metrics context for the AI prompt
    def _fmt_val(v):
        if v is None:
            return 'N/A'
        if isinstance(v, float) and v == int(v):
            return str(int(v))
        return f'{v:,.2f}' if isinstance(v, float) else str(v)

    metric_lines = []
    for col in metric_cols[:6]:
        name = col.get('name', '')
        mean_v = col.get('mean')
        latest_v = col.get('latest_value')
        trend_pct = col.get('trend_pct_change', 0) or 0
        sign = '+' if trend_pct >= 0 else ''
        metric_lines.append(
            f"  {name}: mean={_fmt_val(mean_v)}, "
            f"latest={_fmt_val(latest_v)}, "
            f"trend={sign}{trend_pct:.1f}%"
        )
    metrics_context = '\n'.join(metric_lines) if metric_lines else '  No numeric metrics found.'

    top_col = max(metric_cols, key=lambda c: c.get('trend_pct_change') or 0) \
              if metric_cols else None
    bottom_col = min(metric_cols, key=lambda c: c.get('trend_pct_change') or 0) \
                 if metric_cols else None

    top_kpi_detail = (
        f"{top_col['name']} "
        f"(latest={_fmt_val(top_col.get('latest_value'))}, "
        f"trend={'+' if (top_col.get('trend_pct_change') or 0) >= 0 else ''}"
        f"{(top_col.get('trend_pct_change') or 0):.1f}%)"
    ) if top_col else 'N/A'

    bottom_kpi_detail = (
        f"{bottom_col['name']} "
        f"(latest={_fmt_val(bottom_col.get('latest_value'))}, "
        f"trend={'+' if (bottom_col.get('trend_pct_change') or 0) >= 0 else ''}"
        f"{(bottom_col.get('trend_pct_change') or 0):.1f}%)"
    ) if bottom_col else 'N/A'

    date_range = column_stats.get("date_range", {})
    tone = config.get("tone", "Professional")

    system_prompt = (
        "You are a senior business analyst writing a brief executive summary for a client-facing report. "
        "Your writing is direct, specific, and data-driven. "
        "You never fabricate numbers — every figure you mention must come from the data provided. "
        "You never use filler language or vague qualifiers."
    )

    user_prompt = (
        f"Write an executive summary for a data analysis report.\n\n"
        f"REPORT CONTEXT:\n"
        f"Date range: {date_range.get('from', 'N/A')} to {date_range.get('to', 'N/A')}\n"
        f"Total records: {len(df)}\n"
        f"Tone: {tone}\n\n"
        f"METRIC DATA (use these exact values — do not round or estimate):\n"
        f"{metrics_context}\n\n"
        f"Top performing metric: {top_kpi_detail}\n"
        f"Biggest concern: {bottom_kpi_detail}\n\n"
        f"STRICT WRITING RULES — violating any rule means the output is rejected:\n"
        f"1. LENGTH: 110–140 words. Not fewer than 110. Not more than 140.\n"
        f"2. STRUCTURE: Four parts in this exact order — no labels, no headers:\n"
        f"   Part 1 (Lead): The single most important finding with its specific number.\n"
        f"   Part 2 (Context): One sentence on a secondary metric or supporting data point.\n"
        f"   Part 3 (Implication): One sentence explaining what these numbers mean for the business.\n"
        f"   Part 4 (Action): One specific, concrete action the business should take now.\n"
        f"   Each part is 1-2 sentences maximum.\n"
        f"3. OPENING: Start with the single most important finding as a specific number.\n"
        f"   WRONG: 'The report reveals mixed results over the period.'\n"
        f"   WRONG: 'This analysis covers performance from January to June.'\n"
        f"   RIGHT: 'Revenue grew 33.9% over the period, reaching $9,494 in the latest reading.'\n"
        f"4. NUMBERS: Every metric you mention must include its actual value or percentage. "
        f"Never say 'slight decline' or 'significant growth' without a number.\n"
        f"5. BANNED PHRASES: Do not use any of these — 'it is recommended that', "
        f"'highlights the importance of', 'the data suggests', 'overall', 'in conclusion', "
        f"'mixed bag', 'moving forward', 'actionable', 'this report'.\n"
        f"6. VOICE: Active voice only. Third person.\n"
        f"7. ENDING: Final sentence must be one specific action the business should take.\n"
        f"8. FORMAT: Return plain text only. No headers, no bullets, no markdown.\n"
    )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, _call_ai, provider, user_prompt, system_prompt, api_key,
    )
    if not result:
        return None
    # Enforce length limit — truncate at sentence boundary if AI ignores the limit
    if result:
        words = result.split()
        if len(words) > 155:
            truncated = ' '.join(words[:140])
            last_period = truncated.rfind('.')
            result = (truncated[:last_period + 1]
                      if last_period > 40
                      else truncated + '.')
    return result


def _dedup_insights_by_kpi(insights: list[dict]) -> list[dict]:
    """
    Keep only the first (highest-priority) insight per unique kpi.
    The LLM is prompted for priority ordering so first-occurrence
    is the most important card for that metric.
    """
    seen: set[str] = set()
    deduped: list[dict] = []
    for card in insights:
        kpi_key = card.get("kpi", "").strip().lower()
        if kpi_key and kpi_key not in seen:
            seen.add(kpi_key)
            deduped.append(card)
    return deduped


async def generate_nra_insights(df: pd.DataFrame, config: dict, user: User) -> list[dict]:
    try:
        provider, api_key, _ = get_user_api_key(user)
    except HTTPException:
        return []
    if api_key is None:
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
        f"- Each \"kpi\" value must be unique — do NOT generate two insights for the same metric.\n"
        f"- Do not create multiple insights for \"Units Sold\" or \"Revenue\" variants.\n"
        f"- Vary priority: include at least one \"high\", one \"medium\", one \"low\".\n"
        f"- Choose the single most actionable insight per metric column.\n"
        f"- Return ONLY the JSON array\n"
        f"- All string values must be non-empty. Never return null or empty string for kpi, number, reason, or action fields."
    )

    def _is_valid_insight(item: dict) -> bool:
        required = {"kpi", "number", "reason", "action"}
        if not required <= item.keys():
            return False
        return all(
            isinstance(item.get(k), str) and item.get(k, "").strip()
            for k in required
        )

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
        insights = _dedup_insights_by_kpi(insights)
        return [item for item in insights[:5] if isinstance(item, dict) and _is_valid_insight(item)]
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
    # Deduplicate by (column, value) so repeated outlier values don't flood the report
    seen = set()
    deduped = []
    for anomaly in anomalies:
        col = str(anomaly.get('column', ''))
        val = anomaly.get('value')
        try:
            val_key = str(round(float(val), 4)) if val is not None else ''
        except (TypeError, ValueError):
            val_key = str(val)
        key = (col, val_key)
        if key not in seen:
            seen.add(key)
            deduped.append(anomaly)
    return deduped[:10]


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
