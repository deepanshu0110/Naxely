# Naxely — Agent Instructions

Naxely is an AI-powered PDF report generator: FastAPI + SQLAlchemy +
Supabase backend, React + Tailwind frontend, deployed on Render.com +
Vercel. Full specs are in `docs/` — read the relevant file before writing
any code for a given prompt.

## Shell

This is Windows PowerShell 5.1. `&&` is NOT supported and will throw a
ParserError (`Unexpected token '-m'` or similar). Always chain commands
with `;` instead, or run them as separate tool calls. Do not assume a
Unix-style shell.

## Python Environment

The project's Python venv is at:
`C:\Users\Deepanshu\OneDrive\Desktop\Apps\backend\venv`

Once it exists (set up manually before Prompt 2), it has all of
`requirements.txt` installed, including `pytest` and `pytest-asyncio`.

- NEVER search for `python`, `python3`, or `py` on PATH — there is no
  global interpreter configured, only this venv.
- ALWAYS invoke tests via the absolute path:
  `& "C:\Users\Deepanshu\OneDrive\Desktop\Apps\backend\venv\Scripts\python.exe" -m pytest tests/ -v`
- If a package is missing, install it into THIS venv specifically:
  `& "C:\Users\Deepanshu\OneDrive\Desktop\Apps\backend\venv\Scripts\python.exe" -m pip install <package>`

## Spec Documents

All product/technical specs live in `docs/01_PRD.md` through
`docs/08_DEP.md`. When a prompt says `READ: docs/X.md — Section Y`, open
that file yourself with your file-read tool and find that section before
writing any code. Never ask the user to paste document content — it's
already on disk.

## Critical Technical Rules (do not deviate without asking)

**Matplotlib backend.** `chart_service.py` must call `matplotlib.use('Agg')`
as the very first matplotlib-related line in the file, BEFORE importing
`matplotlib.pyplot`. Never import `matplotlib.pyplot` or `seaborn` at
module level anywhere else — import them inside each function, after
`use('Agg')` has already run. Without this, the server crashes trying to
open a GUI display on Render.com.

**Sync work inside async pipelines.** `chart_service.generate_sync` and
`pdf_service.build_sync` are both synchronous/blocking. When called from
`run_report_pipeline()` (an async function), they MUST be wrapped in
`loop.run_in_executor(None, ...)`. Calling them directly blocks the
FastAPI event loop for every other request during chart/PDF generation.

**Signed URLs.** Never store a Supabase signed URL in the database —
they expire in 1 hour. The DB stores the storage path only
(e.g. `reports/{user_id}/{report_id}/report.pdf`). Generate a fresh
signed URL on every GET request that returns one.

**CSV cleanup timing.** Delete the raw CSV from Supabase Storage right
after chart generation completes (SDD Section 2, step h) — not after AI
generation, not after PDF generation, not "once all processing is done."
The dataframe is already parsed into memory by that point; nothing
downstream needs the stored file.

## Workflow

- One prompt = one feature. Do not combine multiple prompts into one run.
- After each prompt completes, run the test suite before moving to the
  next prompt. Catching a broken step early is cheaper than debugging it
  three prompts later.
- For any prompt building more than one substantial file, prefer
  Subagent-Driven execution: a fresh subagent per file/component, with a
  review checkpoint between them, rather than one continuous batch run.
- If you propose deviating from something explicitly stated in the docs
  or in this file (e.g. changing CSV deletion timing, skipping
  `run_in_executor`), stop and ask before proceeding — don't silently
  pick the "safer-seeming" alternative.
