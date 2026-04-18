# Contributing

Thanks for your interest in contributing to **Document Intelligence API**. This guide keeps the process smooth for everyone.

## Ground Rules

- Be respectful and constructive — see the GitHub community guidelines.
- One PR = one logical change. Keep diffs focused.
- Security issues go to [SECURITY.md](SECURITY.md), not public issues.

## Local Setup

```bash
git clone https://github.com/sick234/inteligenceapi.git
cd inteligenceapi
cp .env.example .env
# generate and paste a SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(64))"

docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api pytest -v
```

## Development Workflow

1. **Fork** the repo and create a feature branch: `git checkout -b feat/my-change`
2. **Write code** with tests that cover the new behaviour
3. **Lint + test** locally before pushing:
   ```bash
   make lint
   make test
   ```
4. **Commit** with a clear message (see below)
5. **Open a PR** against `main` — the CI pipeline (Ruff → pytest → Docker build) must pass

## Commit Messages

Prefer the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: add DOCX extraction support
fix: reject empty uploads with a 400
refactor: consolidate celery engine lifecycle
docs: document rate-limit env vars
test: cover magic-byte sniff fallback
```

Scope is optional (`feat(upload): ...`). Keep subject lines under 72 chars.

## Code Style

- **Ruff** is the linter — run `make lint` before committing.
- Type hints on public functions.
- Docstrings on modules and non-trivial functions.
- Prefer small, named helpers over deeply nested logic.
- Tests live in `tests/` and mirror the `app/` package layout.

## Opening a PR

Use the PR template that appears automatically. At minimum, describe:

- **What** changed and **why**
- **How** it was tested
- Any **screenshots / sample responses** for API-visible changes
- Linked issue (`Closes #123`) if applicable

## Areas We'd Love Help With

- Extra file formats (DOCX, EPUB, HTML)
- S3 / MinIO storage backend
- OpenTelemetry tracing
- Expanded test coverage (integration + edge cases)
- Documentation and examples

Happy hacking! 🚀
