# Notes API: DevSecOps practice target

A small Flask + PostgreSQL REST API. **The app is the given.** Everything around it is your job:
the Dockerfile, docker-compose, GitHub Actions workflows, scanning, signing and hardening.

The app contains deliberate security flaws. See `PLANTED_FLAWS.md` **after** your first scan run.

## What the app does

Users register and log in (bearer token), then create, list, read and delete private notes.
There are also a few unauthenticated endpoints. See `openapi.yaml` for the full contract.

## Facts you need to containerize it

| Thing | Value |
|-------|-------|
| Python | 3.11+ (tested on 3.13) |
| Install | `pip install -r requirements.txt` |
| Production entrypoint | `gunicorn --bind 0.0.0.0:8000 wsgi:app` |
| Port | 8000 |
| Health endpoint | `GET /health` (returns 503 if the DB is unreachable) |
| Env vars | `DATABASE_URL`, `SECRET_KEY` (see `.env.example`) |
| Database | PostgreSQL. Tables are created at startup, so there are no migrations |
| Default DB | If `DATABASE_URL` is unset it falls back to a local SQLite file |

Note what happens at startup if Postgres isn't ready yet. Figure out what that means for compose.

## Run locally (no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov=notesapp
ruff check .
python wsgi.py          # dev server on :8000, SQLite
```

Tests run on SQLite, so they need no database. Writing an integration job that runs against a
real Postgres service container is a good extra.

## Your roadmap

Do these in order and commit after each step. Get a stage working and failing correctly
before moving on. A scanner that can never fail the build proves nothing.

### Milestone 1: containerize
- Write a multi-stage `Dockerfile`: small base image, non-root user, no build tools in the final
  image, a `HEALTHCHECK`, pinned base image (tag *and* digest).
- Write a `.dockerignore`. Check what ends up in the image (`docker history`, `docker run ... ls`).
- Write `docker-compose.yml` with the app + Postgres, using a DB healthcheck and `depends_on`.

### Milestone 2: shift-left scans (GitHub Actions)
- Secrets: Gitleaks with full history.
- SCA: Trivy fs, or `pip-audit`.
- SAST: Semgrep and/or CodeQL.
- Upload results as SARIF so they appear in the repo's Security tab.
- Add least-privilege `permissions:` per job and `concurrency` to cancel superseded runs.

### Milestone 3: build and test
- Lint (ruff), unit tests with coverage, a coverage threshold, and a Python version matrix.
- Cache dependencies. Upload test and coverage reports as artifacts.
- Optional: an integration test job with a Postgres service container.

### Milestone 4: image build, scan and DAST
- Build the image with Buildx and layer caching. Lint the Dockerfile with Hadolint.
- Scan the image with Trivy and generate an SBOM (Syft or Trivy).
- Start the container, wait for `/health`, then run OWASP ZAP: baseline first, then an API scan
  using `openapi.yaml`. Know the difference between passive and active scanning.

### Milestone 5: publish and sign
- Push to GHCR **only** on `main`/tags and only if every earlier stage passed.
- Sign with Cosign keyless (GitHub OIDC), signing by **digest**, not tag.
- Attach the SBOM as an attestation, and optionally SLSA build provenance.
- Prove it: `cosign verify` the image from your own machine.

### Milestone 6: AI in the pipeline
- Add a job that takes the scan reports and posts a PR comment: findings grouped by severity,
  plain-language explanation, suggested fix.
- Design questions to answer: what data may leave the pipeline? What if a scanned file contains
  a prompt injection? Can the model ever dismiss a finding on its own? (Suggested answer: no.)

### Milestone 7: harden and operate
- Pin every action to a commit SHA, with Dependabot or Renovate keeping them fresh.
- Branch protection with required checks, and a `pre-commit` hook running Gitleaks.
- GitHub Environments with a manual approval before publishing.
- OpenSSF Scorecard, license scanning of dependencies, a release workflow with a changelog.
- Fix the planted flaws, re-run, and watch the pipeline go from red to green.

## Rules of the game

1. Write your own first draft of every workflow, then get review from AI, not the other way round.
2. Every finding gets a written decision: fix, accept, or false positive, with the reason.
3. Break your own pipeline on purpose (a leaked secret, a bad dependency) and confirm it goes red.
