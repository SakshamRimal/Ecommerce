---
name: Git Commit & GitHub Push Convention
description: Use when staging, committing, and pushing changes to GitHub using Conventional Commits and pre-commit verification gates across ecommerce-backend and ecommerce-frontend.
---

# Git Commit & GitHub Push Convention

## When to use

- Creating a git commit for backend (`ecommerce-backend/`), frontend (`ecommerce-frontend/`), or infrastructure/docs changes.
- Reviewing staged files to ensure secrets, virtual environments, build artifacts, and IDE folders are excluded.
- Pushing verified commits to the `origin` GitHub remote (`git@github.com:SakshamRimal/Ecommerce.git`).

## Conventional Commit Format

Every commit message MUST follow the **Conventional Commits** specification:

```text
<type>(<optional-scope>): <imperative summary under 72 chars>

<optional body explaining the "why" and key changes as bullet points>
```

### Allowed `<type>` values

| Type | When to use |
|---|---|
| `feat` | A new user-facing or API feature (e.g., new endpoint, UI page, CLI command, concurrency lock) |
| `fix` | A bug fix, race-condition fix, or error-handling correction |
| `refactor` | Code restructuring that neither fixes a bug nor adds a feature |
| `perf` | A change that improves performance, caching, or query efficiency |
| `test` | Adding or updating unit, integration, component, or load tests |
| `docs` | Documentation, `AGENTS.md`, `README.md`, or `.agents/` skill updates |
| `build` | Dockerfiles, `docker-compose.yml`, Nginx config, `pyproject.toml`, or `package.json` |
| `chore` | Tooling, `.gitignore`, formatting, or maintenance tasks |

### Recommended `<scope>` values

- `backend`, `frontend`, `orders`, `cart`, `auth`, `catalog`, `search`, `chat`, `jobs`, `docker`, `agents`, `docs`

### Rules for Per-File Atomic Commits & Messages

1. **One file per commit (strictly distinct messages)**:
   - Never bundle all modified files into a single catch-all commit.
   - Stage and commit **each file individually** (`git add <file> && git commit -m "<type>(<scope>): <specific change in this file>"`) so every file in `git log` has its own distinct, descriptive commit message explaining what changed in that file.
2. **Imperative mood**: Write `"feat(orders): lock user cart and sort product locks at checkout"`, not `"added cart lock"` or `"adds cart lock"`.
3. **Lowercase summary after colon**: Do not capitalize the first word after `<type>(<scope>): ` unless it is a proper noun or identifier (`PostgreSQL`, `FastAPI`, `UserResponse`), and do not end the subject line with a period.
4. **File-accurate description**: The commit message must reflect the actual code, schema, test, configuration, or documentation change inside that specific file.

## Pre-Commit Verification Checklist

Never commit or push failing code or leaked secrets. Run these checks before committing:

1. **Backend Verification** (when `ecommerce-backend/` is touched):
   ```bash
   cd ecommerce-backend
   uv run ruff check src tests
   uv run pytest -q
   ```
2. **Frontend Verification** (when `ecommerce-frontend/` is touched):
   ```bash
   cd ecommerce-frontend
   npm run typecheck
   npm test
   npm run build
   ```
3. **Git Hygiene Check**:
   ```bash
   git status -s
   ```
   Verify that **none** of the following are staged:
   - `.env` or any file containing real API keys, JWT secrets, or SMTP passwords (`.env.example` is allowed)
   - `node_modules/`, `dist/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`
   - `.idea/`, `.vscode/`, `.DS_Store`

## Commit & Push Workflow

```bash
# 1. Inspect status and diff
git status -s

# 2. Stage tracked and intentional new files
git add <paths>

# 3. Verify staged file list
git diff --cached --stat

# 4. Commit with Conventional Commit message
git commit -m "<type>(<scope>): <imperative summary>" -m "- <detail 1>
- <detail 2>"

# 5. Push to GitHub remote
git push origin main
```
