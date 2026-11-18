# CHANGELOG

<!-- version list -->

## v0.2.2 (2026-11-18)

### Bug Fixes

- **bot**: Remove dating wording from the welcome message
  ([`9a7de60`](https://github.com/Cewerty/University-match/commit/9a7de605fee06ec68ed8910c49b1d21c4d246a1b))


## v0.2.1 (2026-11-18)

### Bug Fixes

- **bot**: Accept only the sender's own contact at registration
  ([`3d759e2`](https://github.com/Cewerty/University-match/commit/3d759e236f6b340e0f5df7e9e304c3bc4beeaf98))


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


## v0.1.1 (2026-04-15)

University prototype, as submitted. Built on 24-26 November 2025; the SOCKS5 proxy support and the
expanded welcome dialog were added on 15 April 2026. Tagged and published as a release on
18 November 2026, see the [v0.1.1 release notes](https://github.com/Cewerty/University-match/releases/tag/v0.1.1).
