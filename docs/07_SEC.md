
# SEC — Security Specification Document
## Naxely: AI-Powered Report Generator
> Version: 1.0 | Date: June 2026 | Status: Final

---

## 1. AUTHENTICATION SECURITY

### 1.1 JWT Token Handling
- Tokens issued by Supabase Auth using **HS256** (HMAC-SHA256) with shared secret
- ⚠️ NOT RS256 — the SEC doc previously stated RS256 incorrectly. Supabase uses HS256.
- Backend validation uses `python-jose`:
  ```python
  from jose import jwt, JWTError
  def verify_supabase_jwt(token: str) -> dict:
      try:
          payload = jwt.decode(
              token,
              settings.SUPABASE_JWT_SECRET,  # from env vars
              algorithms=["HS256"],           # HS256 not RS256
              options={"verify_aud": False}   # Supabase doesn't set audience
          )
          return payload
      except JWTError:
          raise HTTPException(status_code=401, detail="Invalid token")
  ```
- Frontend: Store JWT in memory only (Zustand store) — NEVER in localStorage or cookies
- Token refresh: Supabase client handles auto-refresh silently
- Token expiry: 1 hour (Supabase default)
- On logout: Clear token from memory + call Supabase signOut()

### 1.2 Google OAuth Security
- Use Supabase's built-in Google OAuth (handles PKCE flow)
- Never handle OAuth tokens manually in frontend code
- Redirect URI whitelist: only `https://Naxely.io/auth/callback`

### 1.3 Email/Password Rules
- Minimum password length: 8 characters
- Supabase handles password hashing (bcrypt)
- Rate limiting on login: 5 failed attempts → 15 minute lockout (Supabase built-in)
- Password reset: Email link only, expires in 1 hour

### 1.4 Session Management
- No "remember me" — session lives as long as browser tab is open
- Inactive timeout: 24 hours (Supabase session)
- Force logout on: password change, account deletion, suspicious activity

---

## 2. API KEY ENCRYPTION

### 2.1 Algorithm
- Algorithm: AES-256-GCM (authenticated encryption)
- Key derivation: MASTER_ENCRYPTION_KEY (64 hex chars = 32 bytes) from environment
- IV: 12 random bytes, unique per encryption operation
- Auth tag: 16 bytes (GCM standard)

### 2.2 Encryption Flow
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64

# CRITICAL: MASTER_ENCRYPTION_KEY is stored as 64 hex chars in env vars
# AESGCM requires bytes — always convert with bytes.fromhex() before use
# Example: "a1b2c3..." (64 hex chars) → 32 bytes
def get_master_key() -> bytes:
    hex_key = os.environ["MASTER_ENCRYPTION_KEY"]
    if len(hex_key) != 64:
        raise ValueError("MASTER_ENCRYPTION_KEY must be exactly 64 hex characters (32 bytes)")
    return bytes.fromhex(hex_key)

def encrypt_api_key(plaintext: str, master_key: bytes) -> tuple[str, str]:
    """Returns (encrypted_b64, iv_b64)"""
    iv = os.urandom(12)
    aesgcm = AESGCM(master_key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
    return base64.b64encode(ciphertext).decode(), base64.b64encode(iv).decode()

def decrypt_api_key(encrypted_b64: str, iv_b64: str, master_key: bytes) -> str:
    """Returns plaintext API key"""
    ciphertext = base64.b64decode(encrypted_b64)
    iv = base64.b64decode(iv_b64)
    aesgcm = AESGCM(master_key)
    return aesgcm.decrypt(iv, ciphertext, None).decode()

# Generate a valid key (run once, save to env):
# python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.3 Key Storage Rules
- encrypted_api_key + api_key_iv stored in users table
- MASTER_ENCRYPTION_KEY ONLY in Render.com environment variables
- MASTER_ENCRYPTION_KEY NEVER in: git repo, logs, API responses, frontend code
- Key rotation: If MASTER_ENCRYPTION_KEY is compromised, re-encrypt all keys with new master key
- Key preview: Only show last 4 characters to user ("...abcd") — never full key

### 2.4 API Key Usage
- Decrypted in memory only during report generation
- Never logged (log sanitiser strips keys from all log lines)
- Never included in error messages returned to frontend
- Discarded from memory immediately after AI API call completes

---

## 3. DATA SECURITY

### 3.1 User Data (CSV Files)
- Uploaded to Supabase Storage (private bucket) via FastAPI backend (streamed in memory)
- Files stored at: `uploads/{user_id}/{upload_id}/raw.csv` — uses upload_id NOT report_id (report doesn't exist yet)
- Access: Only via service key (backend)
- Retention: CSV deleted from storage immediately after report generation completes
- Never stored in database rows (only storage path stored in uploads.file_url)

### 3.2 Generated Reports (PDFs)
- Stored at path: `reports/{user_id}/{report_id}/report.pdf` (path stored in DB, NOT signed URL)
- Signed URL generated FRESH on every GET /reports or GET /reports/{id} request (1-hour expiry)
- Never cache signed URLs in the database — they expire and go stale
- Shareable links: Separate token-based access (share_token in DB)
- Retention: Kept for 90 days after creation, then auto-deleted

### 3.3 Temp Files (Report Generation)
- Charts and intermediate files written to `/tmp/Naxely/{report_id}/`
- Directory deleted immediately after PDF is built and uploaded
- Render.com ephemeral disk — automatically wiped on restart

### 3.4 Database Security
- Row Level Security (RLS) enabled on all tables
- Users can only access their own rows (enforced at Supabase level)
- Backend uses SUPABASE_SERVICE_KEY (bypasses RLS intentionally for backend operations)
- SUPABASE_SERVICE_KEY never exposed to frontend
- Frontend only has SUPABASE_ANON_KEY (limited permissions)

---

## 4. TRANSPORT SECURITY

### 4.1 HTTPS
- All endpoints: HTTPS only
- HTTP requests auto-redirected to HTTPS (Vercel + Render handle this)
- HSTS header: max-age=31536000; includeSubDomains

### 4.2 CORS
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://Naxely.io", "https://www.Naxely.io"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
# Development only: add http://localhost:5173
# NEVER add "*" in production
```

### 4.3 Security Headers (FastAPI)
```python
# Add to all responses
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self'
```

---

## 5. PAYMENT SECURITY

### 5.1 Webhook Verification
```python
import hmac, hashlib

def verify_dodo_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```
- Reject webhook if signature invalid (return 400)
- Accept webhook only from Dodo Payments IP ranges
- Idempotency: Check dodo_event_id before processing (prevent duplicate processing)

### 5.2 Payment Data
- Never store card numbers, CVV, or any PAN data
- Dodo Payments handles all card data (PCI compliant as MoR)
- Only store: dodo_customer_id, dodo_subscription_id, tier, tier_expires_at

---

## 6. INPUT VALIDATION & SANITISATION

### 6.1 File Upload Validation
```python
ALLOWED_MIME_TYPES = ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_upload(file):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "Only CSV and XLSX files are allowed")
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Maximum size is 10MB")
```

### 6.2 CSV Content Validation
- Scan for formula injection: reject cells starting with =, +, -, @
- No macro execution — Pandas read_csv() is safe (no formula evaluation)
- Max 50,000 rows enforced after parsing
- Column names sanitised before use in SQL queries (no raw column names in queries)

### 6.3 API Key Validation
```python
VALID_KEY_PATTERNS = {
    "openai": r"^sk-[a-zA-Z0-9\-_]{20,}$",
    "claude": r"^sk-ant-[a-zA-Z0-9\-_]{20,}$"
}
```

### 6.4 General Input Rules
- All string inputs: strip whitespace, max length enforced
- Report titles: max 255 chars, HTML entities escaped
- Brand colours: validated as valid hex (#RRGGBB format)
- URLs (Sheets): validated as Google Sheets URL before processing
- All Pydantic schemas enforce types strictly

---

## 7. PRIVACY

### 7.1 What We Store
| Data | Where | Retention |
|---|---|---|
| Email, name, avatar | users table | Until account deletion |
| Encrypted API key | users table | Until deleted by user |
| Report config (no raw data) | reports table | 90 days |
| PDF output | Supabase Storage | 90 days |
| Raw CSV | Supabase Storage | Deleted after processing |
| Payment events | payment_events table | 7 years (legal requirement) |

### 7.2 What We NEVER Store
- Raw CSV data in database (only file URL)
- Plain text API keys
- Card numbers or payment details
- Passwords (Supabase handles hashing)
- Browser fingerprints or tracking pixels

### 7.3 Data Deletion
- User deletes account → immediate: soft delete user row, delete all reports + PDFs from Storage
- Automated cleanup: Cron job runs nightly, hard-deletes soft-deleted records older than 30 days
- CSV files deleted immediately post-processing regardless

---

## 8. THREAT MODEL

| Threat | Risk | Mitigation |
|---|---|---|
| Stolen API key | High | AES-256-GCM encryption, never in logs or responses |
| SQL injection | Medium | SQLAlchemy ORM, parameterised queries only |
| CSV formula injection | Medium | Cell content validation before processing |
| JWT forgery | Low | Supabase RS256 signing, verified on every request |
| CSRF | Low | JWT bearer token auth (not cookies) — CSRF not applicable |
| Webhook replay attack | Medium | Idempotency key check (dodo_event_id unique constraint) |
| File path traversal | Medium | report_id is UUID — no user input in file paths |
| Rate limit bypass | Low | Rate limiting per user_id (not IP, harder to bypass) |
| Brute force login | Medium | Supabase built-in lockout after 5 failures |
| Data exfiltration | Medium | RLS policies, service key only on backend |
| Shared report access | Low | Token is 64 random chars, expires in 30 days |

---

*End of SEC*


---
