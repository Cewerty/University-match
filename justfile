# Project commands. `just` lists them, `just <recipe>` runs one.
# CI runs the same recipes (lint.yml, tests.yml, ci.yml), so a green `just check` locally
# means the same checks pass there. Needs just >= 1.46 (https://just.systems).

set shell := ["bash", "-euo", "pipefail", "-c"]
# On Windows `bash` is often the WSL stub in System32; Git for Windows provides `sh` (it is bash)
set windows-shell := ["sh", "-euo", "pipefail", "-c"]
# The app reads .env itself; keep secrets out of recipe environments
set dotenv-load := false

# Container engine for the image recipes: `just engine=podman smoke-import` or ENGINE=podman
engine := env("ENGINE", "docker")
# Image under test: `just image=localhost/university-match:podman smoke-import` or IMAGE=...
image := env("IMAGE", "university-match:ci")
# The restrictions compose.yaml applies to every service
hardened := "--read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges"
# Pinned by digest; the same version is used in .github/workflows/rescan.yml
trivy_image := "aquasec/trivy:0.76.1@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c"
python := if os() == "windows" { "python" } else { "python3" }
# Linters run with uvx at pinned versions (no project install needed)
actionlint := "uvx --from actionlint-py==1.7.12.25 actionlint"
zizmor := "uvx zizmor==1.32.0"
pip_audit := "uvx pip-audit==2.10.1"
# Built with Go (installed locally and on GitHub runners); keep in sync with .pre-commit-config.yaml
gitleaks := "go run github.com/zricethezav/gitleaks/v8@v8.30.1"
# Keep in sync with the commitizen hook in .pre-commit-config.yaml
commitizen := "uvx --from commitizen==4.19.3 cz"
typos := "uvx typos==1.52.0"
hadolint := "uvx --from hadolint-py==2.15.1.3 hadolint"
yamllint := "uvx yamllint==1.38.0"
validate_pyproject := "uvx --from 'validate-pyproject[all]==0.27' validate-pyproject"

[private]
default:
    @just --list --unsorted

# ---- development ---------------------------------------------------------------------

# Install all dependencies
[group('dev')]
sync:
    uv sync --frozen

# Install only the dev tools (ruff, pytest): no torch, for jobs that do not need it
[group('dev')]
sync-dev:
    uv sync --frozen --only-dev

# Fail if pyproject.toml was changed without updating uv.lock
[group('dev')]
lock-check:
    uv lock --check

# Lint: `just lint --fix`, in CI `just lint --output-format=github`
[group('dev')]
lint *args:
    uv run --frozen ruff check . {{ args }}

# Format the code
[group('dev')]
fmt:
    uv run --frozen ruff format .

# Fail if the code is not formatted
[group('dev')]
fmt-check:
    uv run --frozen ruff format --check --diff .

# Fix what ruff can fix and format
[group('dev')]
fix: (lint "--fix") fmt

# Type check
[group('dev')]
typecheck:
    uv run --frozen mypy

# Run the tests: `just test tests/test_matcher.py -k cosine`
[group('dev')]
test *args:
    uv run --frozen pytest -q {{ args }}

# Run the tests with coverage (fails below fail_under in pyproject.toml)
[group('dev')]
cov:
    uv run --frozen pytest -q --cov --cov-report=term-missing

# Coverage table in Markdown, after `just cov`
[group('dev')]
coverage-summary:
    uv run --frozen coverage report --format=markdown

# Check that the migrations match the models, in a throwaway database
[group('dev')]
migrations-check:
    #!/usr/bin/env bash
    set -euo pipefail
    export DATABASE_URL=sqlite+aiosqlite:///./ci.db
    trap 'rm -f ci.db' EXIT
    uv run --frozen alembic upgrade head
    uv run --frozen alembic check

# Everything to run before a commit
[group('dev')]
check: lock-check lint fmt-check typecheck test

# Install the git hooks (pre-commit, commit-msg, pre-push)
[group('dev')]
hooks:
    uv run pre-commit install

# ---- the quality gate: workflows, configs, secrets, dependencies ---------------------

# Lint the GitHub Actions workflows: syntax and shell (actionlint), security (zizmor, .github/zizmor.yml)
[group('gate')]
workflows-lint:
    {{ actionlint }}
    {{ zizmor }} --min-severity low .github/

# Lint the Dockerfile (hadolint)
[group('gate')]
lint-dockerfile:
    {{ hadolint }} Dockerfile

# Lint every YAML file: workflows, compose, Dependabot, pre-commit (.yamllint.yaml)
[group('gate')]
yamllint:
    {{ yamllint }} --strict .

# Check pyproject.toml against its schema, including the [tool.*] tables that have one
[group('gate')]
validate-pyproject:
    {{ validate_pyproject }} pyproject.toml

# All configuration linters
[group('gate')]
config-lint: lint-dockerfile yamllint validate-pyproject

# Conventional Commits in a range of commits: `just commits main..HEAD`
[group('gate')]
commits range="origin/main..HEAD":
    {{ commitizen }} check --rev-range {{ range }}

# Spelling in code, comments, names and docs (_typos.toml)
[group('gate')]
typos:
    {{ typos }}

# Secrets in the whole git history (the pre-commit hook sees only staged changes)
[group('gate')]
secrets:
    {{ gitleaks }} git --redact --no-banner --exit-code 1 .

# Unused, missing and transitive dependencies: imports vs pyproject.toml ([tool.deptry])
[group('gate')]
deptry:
    uv run --frozen deptry .

# Known vulnerabilities in all locked packages, dev group included (accepted ones: --ignore-vuln ID below)
[group('gate')]
audit:
    #!/usr/bin/env bash
    set -euo pipefail
    work=$(mktemp -d)
    trap 'rm -rf "$work"' EXIT
    uv export --frozen --format requirements-txt --no-hashes --all-groups --no-emit-project > "$work/requirements.txt"
    # --no-deps: the export is the complete pinned set; torch==...+cpu is not on PyPI and is skipped
    # (Trivy covers it in the image)
    status=0
    {{ pip_audit }} -r "$work/requirements.txt" --disable-pip --no-deps --progress-spinner off         --format markdown --output "$work/report.md" || status=$?
    # No report file is written when nothing is found
    [ -s "$work/report.md" ] || echo "No known vulnerabilities found." > "$work/report.md"
    cat "$work/report.md"
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        { echo "### pip-audit"; cat "$work/report.md"; } >> "$GITHUB_STEP_SUMMARY"
    fi
    exit "$status"

# ---- the application, without containers ---------------------------------------------

# Apply database migrations
[group('app')]
migrate:
    uv run alembic upgrade head

# Fill the database with demo data
[group('app')]
seed:
    uv run python seed.py

# Run the bot and FastAPI (:8000) in two processes
[group('app')]
run:
    uv run python main.py

# Run only the Telegram bot
[group('app')]
bot:
    uv run python main.py bot

# Run only FastAPI with the admin panel
[group('app')]
web:
    uv run python main.py web

# ---- the Docker Compose stack --------------------------------------------------------

# Create .env from the example if it does not exist
[group('docker')]
env-init:
    test -f .env || cp .env.example .env

# Write secrets/bot_token from $BOT_TOKEN (keeps an existing file when BOT_TOKEN is unset)
[group('docker')]
secret-init:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "${BOT_TOKEN:-}" ]; then
        test -f secrets/bot_token || { echo "set BOT_TOKEN, or create secrets/bot_token yourself" >&2; exit 1; }
        exit 0
    fi
    mkdir -p secrets
    printf '%s' "$BOT_TOKEN" > secrets/bot_token

# Build and start the stack (development: dev image, override file)
[group('docker')]
up: env-init secret-init
    docker compose up --build

# Development loop: sync code changes into the containers, rebuild on dependency changes
[group('docker')]
watch: env-init secret-init
    docker compose watch

# Stop the stack
[group('docker')]
down:
    docker compose down

# Service status
[group('docker')]
ps:
    docker compose ps

# Follow logs, optionally of some services: `just logs web bot`
[group('docker')]
logs *services:
    docker compose logs -f {{ services }}

# Production: the base file only, in the background
[group('docker')]
prod-up: env-init secret-init
    docker compose -f compose.yaml up -d --build

# Demo data in the app-data volume
[group('docker')]
docker-seed:
    docker compose --profile tools run --rm seed

# Apply migrations in a container (rebuild first after adding one: `docker compose build`)
[group('docker')]
docker-migrate:
    docker compose run --rm migrate

# Copy the SQLite database out of the app-data volume
[group('docker')]
db-export dest="./bot.db":
    docker compose cp web:/app/data/bot.db {{ dest }}

# Move a database from the old ./data folder into the app-data volume
[group('docker')]
db-import dir="data":
    docker compose run --rm --no-deps -v "$PWD/{{ dir }}:/old:ro" migrate cp /old/bot.db /app/data/bot.db

# ---- the image: build and checks (the `docker` and `podman` CI jobs) -----------------

# Build the production image
[group('image')]
build:
    {{ engine }} build --target runtime --tag {{ image }} .

# Build the dev target and check that its tools are there
[group('image')]
build-dev:
    {{ engine }} build --target dev --tag university-match:dev .
    {{ engine }} run --rm university-match:dev sh -c 'ruff --version && mypy --version'

# Check both compose configurations against the container security policy
[group('image')]
compose-policy: env-init secret-init
    #!/usr/bin/env bash
    set -euo pipefail
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' EXIT
    docker compose config --format json > "$tmp/compose.dev.json"
    docker compose -f compose.yaml config --format json > "$tmp/compose.prod.json"
    {{ python }} scripts/ci/check_compose_policy.py "$tmp/compose.prod.json" "$tmp/compose.dev.json"

# Seccomp and AppArmor must be active on the host for the default profiles to apply
[group('image')]
host-security:
    #!/usr/bin/env bash
    set -euo pipefail
    opts=$(docker info --format '{{{{json .SecurityOptions}}')
    echo "Docker security options: $opts"
    [ -z "${GITHUB_STEP_SUMMARY:-}" ] || echo "Docker security options: $opts" >> "$GITHUB_STEP_SUMMARY"
    echo "$opts" | grep -q seccomp

# The app imports under the compose restrictions, without a bot token
[group('image')]
smoke-import:
    {{ engine }} run --rm {{ hardened }} {{ image }} python -c "import main, src.web.app"

# The bot refuses to start without a token
[group('image')]
smoke-no-token:
    #!/usr/bin/env bash
    set -euo pipefail
    if out=$({{ engine }} run --rm {{ hardened }} {{ image }} python main.py bot 2>&1); then
        echo "the bot started without a token"; exit 1
    fi
    echo "$out" | grep -q "BOT_TOKEN is not set"

# PyTorch is the CPU build
[group('image')]
smoke-torch-cpu:
    {{ engine }} run --rm {{ image }} python -c "import torch; assert not torch.cuda.is_available(); assert torch.__version__.endswith('+cpu'), torch.__version__; print(torch.__version__)"

# Runs as uid 10001 that can write its data and nothing else
[group('image')]
smoke-user:
    {{ engine }} run --rm {{ image }} sh -c 'test "$(id -u)" = 10001 && touch /app/data/probe /cache/huggingface/probe && ! touch /app/probe 2>/dev/null && ! touch /app/main.py 2>/dev/null && echo "uid $(id -u): data and model cache writable, code read-only"'

# Seccomp 2 = filter mode (the default profile applies); no capabilities; no privilege gain
[group('image')]
smoke-seccomp:
    {{ engine }} run --rm {{ hardened }} {{ image }} sh -c 'grep -E "^(Seccomp|NoNewPrivs|CapEff):" /proc/self/status && grep -Eq "^Seccomp:[[:space:]]+2$" /proc/self/status && grep -Eq "^NoNewPrivs:[[:space:]]+1$" /proc/self/status && grep -Eq "^CapEff:[[:space:]]+0+$" /proc/self/status'

# Migrations apply to a fresh named volume on a read-only root (it must take the image's ownership)
[group('image')]
smoke-migrate:
    {{ engine }} run --rm {{ hardened }} -v ci-app-data:/app/data {{ image }} alembic upgrade head

# No .env or secrets/ in the image, no secret-looking variable in any layer
[group('image')]
smoke-no-secrets:
    #!/usr/bin/env bash
    set -euo pipefail
    {{ engine }} run --rm {{ image }} sh -c 'test ! -e /app/.env && test ! -e /app/secrets'
    if {{ engine }} history --no-trunc --format '{{{{.CreatedBy}}' {{ image }} | grep -Ei '(token|password|secret)[A-Z_]*='; then
        echo "a layer sets a secret-looking variable"; exit 1
    fi

# All the smoke tests
[group('image')]
smoke: smoke-import smoke-no-token smoke-torch-cpu smoke-user smoke-seccomp smoke-migrate smoke-no-secrets

# Trivy: full report, then fail on CRITICAL/HIGH vulnerabilities that have a fix (.trivyignore.yaml)
[group('image')]
scan:
    #!/usr/bin/env bash
    set -euo pipefail
    work=$(mktemp -d)
    trap 'rm -rf "$work"' EXIT
    docker save {{ image }} -o "$work/image.tar"
    trivy() {
        docker run --rm -v "$work:/scan" -v "$PWD/.trivyignore.yaml:/trivyignore.yaml:ro" \
            -v trivy-cache:/root/.cache {{ trivy_image }} image --input /scan/image.tar --scanners vuln \
            --ignorefile /trivyignore.yaml "$@"
    }
    trivy --format table --output /scan/trivy.txt
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        { echo "### Vulnerabilities (all severities)"; echo '```'; head -c 500000 "$work/trivy.txt"; echo '```'; } >> "$GITHUB_STEP_SUMMARY"
    fi
    trivy --skip-db-update --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 --format table
