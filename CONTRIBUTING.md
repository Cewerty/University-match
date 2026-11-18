# Contributing

## Setup

Install [uv](https://docs.astral.sh/uv/) and [just](https://just.systems), then:

```bash
just sync
just hooks                  # installs the pre-commit, commit-msg and pre-push hooks
just check                  # lock file, ruff, formatting, mypy, tests: the same checks as CI
```

`just` lists all recipes. The [justfile](justfile) is the single place for the project's commands:
the CI workflows call its recipes (`just lint`, `just cov`, `just smoke`, ...) instead of repeating the commands,
so change a command there and not in a workflow.

The `pre-commit` hook runs `ruff check --fix` and `ruff format`.
The `pre-push` hook runs `just typecheck` (mypy; slower, so not on every commit).
The `commit-msg` hook checks the commit message format with Commitizen.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/), in English, imperative mood:

```text
<type>(<optional scope>): <description>

feat(matcher): use multilingual embeddings
fix(web): return 503 while the index is warming up
docs: describe the matching evaluation
```

| Type | Use for | Release | In CHANGELOG |
|---|---|---|---|
| `feat` | new behaviour | minor | yes |
| `fix` | bug fix | patch | yes |
| `perf` | performance improvement | patch | yes |
| `refactor` | code change without behaviour change | none | yes |
| `test` | tests only | none | no |
| `docs` | documentation only | none | no |
| `ci` | GitHub Actions, release tooling | none | no |
| `build` | dependencies, Docker | none | no |
| `chore` | everything else | none | no |
| `style` | formatting only | none | no |

Useful scopes: `bot`, `web`, `matcher`, `core`, `db`, `docker`.

**Breaking changes:** add `!` after the type (`feat(web)!: ...`) or a `BREAKING CHANGE:` footer.
While the version is `0.x`, a breaking change bumps the minor version (`0.2.0 → 0.3.0`);
moving to `1.0.0` is a deliberate manual decision (set `major_on_zero = true` in `pyproject.toml`).

## CI and releases

One workflow, `ci.yml`, runs on every push to `main` and every pull request. Its jobs depend on each other,
so a release can never be published while any check is red:

| Job | When | What |
|---|---|---|
| `lint` | always | `uv lock --check`, `ruff check`, `ruff format --check`, `mypy` (defined in `lint.yml`) |
| `tests` | always | `alembic upgrade head` + `alembic check`, `pytest` with a minimum coverage (defined in `tests.yml`) |
| `changes` | always | decides whether the image has to be built: the Dockerfile, compose files, `main.py`, `.trivyignore.yaml` or dependencies changed |
| `docker` | always; image checks only when `changes` says so | hadolint, `docker compose config` with and without the dev override, and the compose security policy (`scripts/ci/check_compose_policy.py`); then build the image, check that it runs as uid 10001 with the default seccomp profile, no capabilities and a read-only root, imports and applies migrations without the bot token, carries no secrets and has no fixable CRITICAL/HIGH vulnerabilities (Trivy); build the `dev` target |
| `podman` | always; image checks only when `changes` says so | build and smoke-test the image under rootless Podman |
| `release` | push to `main`, after `lint`, `tests`, `docker` and `podman` pass | [python-semantic-release](https://python-semantic-release.readthedocs.io/): bumps the version in `pyproject.toml`, updates `CHANGELOG.md`, tags `vX.Y.Z` and publishes a GitHub Release |
| `publish-image` | after a release | push `ghcr.io/<owner>/university-match:vX.Y.Z` and `:latest` with an SBOM and provenance, attest it and add the digest to the release notes |

Versions are never bumped by hand. A push with only `docs`/`ci`/`chore`/... commits produces no release.
Before releasing, `scripts/ci/validate_release_history.py` checks that the latest tag is still in
the history of `main`, so a rewritten history cannot produce a wrong version.

A separate workflow, `rescan.yml`, scans the newest three released images with Trivy every Monday and uploads the results to code scanning.
