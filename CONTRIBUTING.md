# Contributing

## Setup

Install [uv](https://docs.astral.sh/uv/) and [just](https://just.systems), then:

```bash
just sync
just hooks                  # installs the pre-commit, commit-msg and pre-push hooks
just check                  # quick: lock file, ruff, formatting, mypy, tests
just gate                   # the whole quality gate, as in CI (about two minutes); run it before a pull request
```

`just gate` is the one command for humans, AI agents and CI alike: it runs every check of the pipeline below
without Docker. `just gate-image` adds the image part (build, smoke tests, Trivy) and needs Docker.
Besides uv and just, the gate needs Go (gitleaks is built with `go run` at a pinned version).

`just` lists all recipes. The [justfile](justfile) is the single place for the project's commands:
the CI workflows call its recipes (`just lint`, `just cov`, `just smoke`, ...) instead of repeating the commands,
so change a command there and not in a workflow.

The `pre-commit` hook runs `ruff check --fix`, `ruff format` and gitleaks on the staged changes.
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

One workflow, `ci.yml`, runs on every push to `main` and every pull request. It calls reusable workflows and
orders them with `needs`, so a release can never be published while any check is red:

```text
workflows-lint ─┬─ secrets, conventions
                ├─ hadolint ───────────────┐
                ├─ yamllint ── changes ────┼─ docker, podman ─┐
                └─ pyproject ─ lint, tests, dependencies ─────┴─ release ─ publish-image
```

| Job | Workflow | What |
|---|---|---|
| `workflows-lint` | `workflows-lint.yml` | first, every other job waits for it: actionlint (syntax, expressions, shellcheck) and zizmor (injections, permissions, unpinned actions; `.github/zizmor.yml`) |
| `secrets` | `secrets.yml` | gitleaks over the whole git history (the pre-commit hook can be skipped with `--no-verify`) |
| `conventions` | `conventions.yml` | Conventional Commits for every new commit (commitizen) and spelling (typos, `_typos.toml`) |
| `hadolint`, `yamllint`, `pyproject` | `config-lint.yml` | the Dockerfile before `docker`/`podman`, every YAML file (`.yamllint.yaml`) before the jobs that read compose files, `pyproject.toml` against its schema before the Python jobs |
| `lint` | `lint.yml` | `uv lock --check`, `ruff check`, `ruff format --check`, `mypy` |
| `tests` | `tests.yml` | `alembic upgrade head` + `alembic check`, `pytest` with a minimum coverage |
| `dependencies` | `dependencies.yml` | deptry (unused, missing and transitive dependencies; `[tool.deptry]`) and pip-audit (known vulnerabilities in every locked package) |
| `changes` | `ci.yml` | decides whether the image has to be built: the Dockerfile, compose files, the justfile, `main.py`, `.trivyignore.yaml` or dependencies changed |
| `docker` | `ci.yml` | always: `docker compose config` with and without the dev override and the compose security policy (`scripts/ci/check_compose_policy.py`); image checks only when `changes` says so: runs as uid 10001 with the default seccomp profile, no capabilities and a read-only root, imports and applies migrations without the bot token, carries no secrets, has no fixable CRITICAL/HIGH vulnerabilities (Trivy); the `dev` target builds |
| `podman` | `ci.yml` | build and smoke-test the image under rootless Podman |
| `release` | `ci.yml` | push to `main`, after all of the above: [python-semantic-release](https://python-semantic-release.readthedocs.io/) bumps the version in `pyproject.toml`, updates `CHANGELOG.md`, tags `vX.Y.Z` and publishes a GitHub Release |
| `publish-image` | `ci.yml` | after a release: push `ghcr.io/<owner>/university-match:vX.Y.Z` and `:latest` with an SBOM and provenance, attest it and add the digest to the release notes |

Every job runs a `just` recipe, so a failing job can be reproduced locally with the same command.
Making these checks required for merging is a repository setting (Settings → Branches → branch protection →
required status checks); it is not stored in the repository.

### Accepting a finding

When a check reports something that is not a real problem, record the decision next to the tool, with a reason:

| Tool | Where |
|---|---|
| zizmor | `.github/zizmor.yml`, or `# zizmor: ignore[<rule>]` on the line |
| yamllint | `.yamllint.yaml`, or `# yamllint disable-line rule:<rule>` |
| typos | `_typos.toml` (`[default.extend-words]` or `[files] extend-exclude`) |
| gitleaks | `.gitleaksignore` (fingerprint of the finding) |
| deptry | `[tool.deptry.per_rule_ignores]` in `pyproject.toml` |
| pip-audit | `--ignore-vuln <ID>` in the `audit` recipe of the justfile |
| Trivy | `.trivyignore.yaml` (with `expired_at`) |

Versions are never bumped by hand. A push with only `docs`/`ci`/`chore`/... commits produces no release.
Before releasing, `scripts/ci/validate_release_history.py` checks that the latest tag is still in
the history of `main`, so a rewritten history cannot produce a wrong version.

A separate workflow, `rescan.yml`, scans the newest three released images with Trivy every Monday and uploads the results to code scanning.
