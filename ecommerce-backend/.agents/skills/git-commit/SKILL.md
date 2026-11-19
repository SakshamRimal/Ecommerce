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

## Per-File Commit Rule

- **Commit each file individually with its own tailored Conventional Commit message**:
  - Never use a single generic commit message for multiple files.
  - Stage one file at a time (`git add <file>`) and write a unique message describing the exact change in that file.

## Pre-Commit Verification Checklist

1. **Backend Verification**:
   ```bash
   cd ecommerce-backend && uv run ruff check src tests && uv run pytest -q
   ```
2. **Frontend Verification**:
   ```bash
   cd ecommerce-frontend && npm run typecheck && npm test && npm run build
   ```
3. **Secret & Artifact Hygiene**:
   - Ensure `.env`, `.venv/`, `node_modules/`, `dist/`, and `.idea/` are never staged.

## Commit & Push Workflow

```bash
git status -s
git add <paths>
git diff --cached --stat
git commit -m "<type>(<scope>): <imperative summary>"
git push origin main
```
