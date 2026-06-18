# GitHub Actions Secrets — Reference

> **WARNING: NEVER commit these secrets to git.** Add all via GitHub → Settings → Secrets and variables → Actions.

| Secret Name | What It Is | Where to Find It | Used By |
|---|---|---|---|
| `SUPABASE_URL` | Supabase project URL | Supabase Dashboard → Settings → API → Project URL | Backend CI (test env) |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Supabase Dashboard → Settings → API → service_role key | Backend CI (test env) |
| `MASTER_ENCRYPTION_KEY` | 64-hex-char encryption key for API key storage | Generate locally: `python -c "import secrets; print(secrets.token_hex(32))"` | Backend CI (test env) |
| `RENDER_DEPLOY_HOOK_URL` | Render deploy trigger URL | Render.com → Your Service → Settings → Deploy Hook → Copy URL | Backend CI (deploy step) |
| `VITE_SUPABASE_URL` | Supabase project URL (same as SUPABASE_URL) | Supabase Dashboard → Settings → API → Project URL | Frontend CI (build env) |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous/public key | Supabase Dashboard → Settings → API → anon public key | Frontend CI (build env) |
| `VITE_API_BASE_URL` | Production backend API base URL | Your Render custom domain: `https://api.Naxely.io` | Frontend CI (build env) |
