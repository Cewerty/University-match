# CHANGELOG

<!-- version list -->

## v0.2.0 (2026-11-18)

### Bug Fixes

- Repair startup, reindexing, search status and config parsing
  ([`c3818df`](https://github.com/Cewerty/University-match/commit/c3818dfe70a52df6fc78c153d64160a117292f2b))

- **bot**: Translate registration prompts to Russian
  ([`07468b1`](https://github.com/Cewerty/University-match/commit/07468b101362d373910914a63b083264808ec1c8))

- **db**: Squash broken migrations and run Alembic against DATABASE_URL
  ([`5a18208`](https://github.com/Cewerty/University-match/commit/5a182081744510d1becfca6d84658847403607e2))

### Features

- **bot**: Keep dialog state in Redis using serializable value objects
  ([`1390b07`](https://github.com/Cewerty/University-match/commit/1390b070319469fd42d8f675aee1b132aa62cb08))

- **matcher**: Use multilingual embeddings with cosine similarity
  ([`d4ec990`](https://github.com/Cewerty/University-match/commit/d4ec990e6053c2707fcacc91c54477e2d6aeaaf6))


## v0.1.1 (2026-11-18)

- Initial Release
