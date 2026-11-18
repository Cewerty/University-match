# University Match

[![CI](https://github.com/Cewerty/University-match/actions/workflows/ci.yml/badge.svg)](https://github.com/Cewerty/University-match/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Cewerty/University-match)](https://github.com/Cewerty/University-match/releases)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FCewerty%2FUniversity-match%2Fmain%2Fpyproject.toml)](pyproject.toml)

A Telegram bot that helps university students find people with similar interests.
A student registers (contact, name, faculty, group, interests), and the bot suggests
other students whose interests are semantically close, using sentence embeddings and a FAISS index.

Built solo in one week as a prototype for a university assignment.

<!--
## Demo

| Registration | Main menu | Matches | Match profile |
|---|---|---|---|
| ![Registration](docs/screenshots/registration.png) | ![Main menu](docs/screenshots/main-menu.png) | ![Matches](docs/screenshots/matches.png) | ![Match profile](docs/screenshots/match-profile.png) |

Admin panel (`/admin`):

![Admin panel](docs/screenshots/admin.png)
-->

## How it works

```text
Telegram ──► Bot process (aiogram-dialog, long polling)
                 │  HTTP GET /search/{user_id}
                 ▼
             FastAPI process ──► UserMatcher (FAISS IndexFlatIP, in memory)
                 │                    ▲ full rebuild every 60 s
                 └──► SQLite (SQLAlchemy async) ◄── SQLAdmin at /admin
```

- `main.py` runs the Telegram bot (`main.py bot`), the FastAPI app (`main.py web`), or both
  in two processes (no argument). In Docker they are separate containers.
- Registration and the main menu are `aiogram-dialog` state machines (`src/bot/states.py`).
  A middleware opens a database session for every incoming update.
  Dialog state is stored in Redis when `REDIS_URL` is set, otherwise in memory.
  Dialog data holds only plain values: ORM objects are converted into immutable value objects
  (`src/core/value_objects.py`) before they are stored.
- For matching, a user's interests are joined into one string and encoded with
  `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers). The embeddings are L2-normalized
  and stored in a FAISS `IndexFlatIP`, so the score is the cosine similarity of two users' interests,
  from −1 to 1 (`src/services/matcher.py`).
- A background task in the FastAPI process rebuilds the index from the database every 60 seconds
  (`src/web/app.py`). Embedding and search run in `asyncio.to_thread`, so the event loop is not blocked.
- The bot calls `/search/{user_id}` and shows matches whose score is above `MINIMAL_MATCH_VALUE` (0.45).
- SQLAdmin provides a web UI for users, interests, faculties and groups.

## Matching model and evaluation

The first version used `all-MiniLM-L6-v2` with a FAISS L2 index and `score = 1 − distance`.
That model is trained on English, while interests are entered in Russian, and the score had no fixed range,
so the threshold was a guess. I switched to the multilingual `paraphrase-multilingual-MiniLM-L12-v2`
with normalized embeddings and cosine similarity, and checked the change on seed data
(200 users, 21 interests, fixed random seed). Two references were used: exact overlap of interests
(Jaccard) and overlap of hand-labelled interest topics (IT, sport, art, leisure), which rewards
understanding that "Python" and "Программирование" are related.

| Setup | Spearman vs exact overlap | Spearman vs topic overlap | nDCG@5 exact | nDCG@5 topic |
|---|---|---|---|---|
| Old model, L2 (before) | 0.602 | 0.253 | **0.823** | 0.801 |
| New model, L2, not normalized | 0.545 | 0.325 | 0.795 | 0.806 |
| **New model, cosine (current)** | **0.632** | **0.419** | 0.809 | **0.819** |

The topic correlation grew by two thirds. The new model alone, without normalization, was worse:
the gain comes from the model and the cosine score together. Ranking by exact overlap became
slightly worse (nDCG@5 0.823 → 0.809), which is expected: the old model rewarded identical words.

The threshold `MINIMAL_MATCH_VALUE = 0.45` was chosen as the point that best separates pairs
with and without shared interests (keeps 76% of the first, removes 81% of the second).

## Tech stack

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- [aiogram 3](https://docs.aiogram.dev/) + [aiogram-dialog](https://aiogram-dialog.readthedocs.io/)
- [FastAPI](https://fastapi.tiangolo.com/) + [SQLAdmin](https://aminalaee.dev/sqladmin/)
- [SQLAlchemy 2](https://docs.sqlalchemy.org/en/20/) (async, aiosqlite), [Alembic](https://alembic.sqlalchemy.org/)
- [Redis](https://redis.io/) for dialog state (optional)
- [sentence-transformers](https://www.sbert.net/), [faiss-cpu](https://github.com/facebookresearch/faiss)
- loguru, ruff

## Running locally

Requirements: Python 3.12, uv, a bot token from [@BotFather](https://t.me/BotFather).

```bash
git clone https://github.com/Cewerty/University-match.git
cd University-match
uv sync

cp .env.example .env          # then set BOT_TOKEN
uv run alembic upgrade head
uv run python seed.py         # demo data: faculties, groups, interests, fake users
uv run python main.py         # bot + FastAPI on :8000
```

Then send `/start` to your bot. The admin panel is at <http://localhost:8000/admin>.

The embedding model (~460 MB) is downloaded on the first index build.

All settings are read from `.env`; see [.env.example](.env.example).

## Running with Docker

```bash
cp .env.example .env          # then set BOT_TOKEN
mkdir -p data
docker compose run --rm seed  # optional: demo data
docker compose up --build
```

Compose starts the services in order: `redis` (dialog state), the one-shot `migrate`
(`alembic upgrade head`) and `model-init` (downloads the embedding model into the `hf-cache` volume),
then `web` (FastAPI on :8000) once they finish, and `bot` once `web` answers its healthcheck.
All of them use one image, built once. The SQLite database is kept in `./data`.

Two files:

- `compose.yaml` is the base and production configuration: `docker compose -f compose.yaml up -d`.
- `compose.override.yaml` is merged automatically in development. It builds the `dev` target
  (the runtime image plus the dev dependency group) and configures `docker compose watch`: changes in `src/` and `main.py`
  are synced into the containers and the process restarts, without a rebuild. The image is rebuilt
  only when `pyproject.toml`, `uv.lock` or the `Dockerfile` change.

```bash
docker compose watch          # development loop
docker compose run --rm migrate   # after adding a migration (rebuild first: docker compose build)
```

## Development

```bash
uv run pytest                 # tests use a fake embedding model, no download
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Install the git hooks once with `uv run pre-commit install`: ruff and the commit message check run on every commit, mypy before a push. Releases, tags and the changelog are automated;
see [CONTRIBUTING.md](CONTRIBUTING.md).

The same checks run in GitHub Actions on every push and pull request.

## Project structure

```text
.
├── main.py                     # entry point: bot, FastAPI or both (`main.py bot|web`)
├── seed.py                     # fills the database with demo data (Faker, ru_RU)
├── alembic/                    # database migrations
├── tests/                      # pytest: matcher, repository, value objects, config, API
├── .github/workflows/          # CI pipeline: lint, tests, release only after both pass
├── scripts/ci/                 # release history check used by the release job
├── src/
│   ├── docs/adr/               # architecture decision records (template + ADRs)
│   ├── bot/
│   │   ├── dialogs/
│   │   │   ├── register/       # registration flow: windows, handlers, getters
│   │   │   └── main_menu/      # profile, events, search and match screens
│   │   ├── middlewares.py      # per-update database session
│   │   └── states.py           # dialog state groups
│   ├── core/
│   │   ├── config.py           # settings from environment variables
│   │   ├── database.py         # async engine and session factory
│   │   ├── models.py           # User, Faculty, Group, Interest
│   │   ├── value_objects.py    # UserProfile, MatchCandidate (serializable dialog data)
│   │   └── logger.py           # loguru setup
│   ├── services/
│   │   ├── matcher.py          # embeddings + FAISS index and search
│   │   └── repo.py             # database queries
│   └── web/
│       └── app.py              # FastAPI app, SQLAdmin views, /search endpoint
├── Dockerfile                  # targets: runtime (default) and dev
├── compose.yaml                # web, bot, migrate, model-init, seed, redis
├── compose.override.yaml       # dev image and `docker compose watch`
└── pyproject.toml
```

## Safety and privacy

The bot is meant for students of one institution, some of whom may be under 18.
Before any real launch, these are the risks I considered and where each one stands.

### Threat model

| Risk | Example | Status |
|---|---|---|
| Fake identity via someone else's contact | A user forwards another person's contact card instead of sharing their own | **Done:** only a contact whose `user_id` matches the sender is accepted (tests in `tests/test_register_contact.py`) |
| Harmful content inside the bot | Unwanted photos or messages | **Done by design:** the bot has no photos and no chat; it only introduces people, and interests are picked from a fixed list |
| Contact shared without consent | A match card shows the phone number and full name right away | **Planned:** reveal contact only after both sides accept; before that show first name, faculty and shared interests only |
| Outsiders registering | Anyone with Telegram can pick any faculty and group | **Planned:** join by a group invite code from the curator; later, if the institution agrees, verify the phone number against its student records (no passwords involved) |
| Large age gap between matched users | An adult student matched with a 15-year-old first-year student | **Planned:** match only within the same course; this narrows the gap but does not guarantee it |
| Abuse after an introduction | A user harasses their match outside the bot | **Planned:** report and block on every card; a moderator can ban users in the admin panel |
| Personal data | Phone numbers stored in plain text | **Planned:** consent screen, "delete my data" command, keep only the data needed for matching |
| Exposed internal API | `/search` and `/reindex` have no authentication | **Current rule:** the API and the admin panel are for local or private-network use only; publishing them needs authentication and HTTPS first |

### What code cannot solve

These need a decision from the institution, not a feature:

- **Who operates the service.** The institution should be the data operator: it collects consent (for minors, from their legal representatives) and decides where the data is stored.
- **Who moderates.** Reports are useless without a named person who reads them and rules for what happens next.
- **Whether minors take part at all.** If the institution cannot take on moderation, the safe answer is an 18+ audience, for example a hackathon team finder.

Until these are agreed in writing, the bot runs only on demo data.

Design decisions behind these measures are recorded as ADRs in [`src/docs/adr`](src/docs/adr), starting with [ADR 0001: the bot only introduces people, no media or chat](src/docs/adr/0001-bot-only-introduces-no-media-or-chat.md).

## Limitations and next steps

This is a one-week prototype. Known issues and what I would do next:

### Matching quality

- The index lives in the memory of the FastAPI process and is fully rebuilt every 60 seconds.
  That is fine for hundreds of users, not for a real university.

### Architecture

- SQLite is fine for a demo but not for concurrent writes.
  Next step: PostgreSQL with pgvector, which would also replace the in-memory FAISS index.
- Bot and FastAPI run as two processes of one container; the bot reaches the index over HTTP.

### Product

- Contact details are shown without mutual consent; see [Safety and privacy](#safety-and-privacy).
- The "Events" screen shows static placeholder text.

### Code

- Tests cover the core logic but not the Telegram dialogs end to end.

## License

[MIT](LICENSE)
