# CHANGELOG

<!-- version list -->

## v0.3.0 (2026-11-19)

### Features

- **core**: Read secrets from *_FILE and require the bot token only in the bot
  ([`61742f9`](https://github.com/Cewerty/University-match/commit/61742f99887018fd3d1731fd51fa4a15517e3228))

### Refactoring

- Run the bot and the web server separately from main.py
  ([`7b6a996`](https://github.com/Cewerty/University-match/commit/7b6a996d5394b937b43d9721ee501e14a3572a90))


## v0.2.3 (2026-11-18)

### Bug Fixes

- **bot**: Do not crash when a callback's message is no longer accessible
  ([`c7df7eb`](https://github.com/Cewerty/University-match/commit/c7df7eb0f8a03cb16053e9915b372737befa7987))

### Refactoring

- Fix the logger return type and a missing return in seed.py
  ([`f30fb98`](https://github.com/Cewerty/University-match/commit/f30fb9800c0e8b1638bba5d0deb78042ab2fa481))

- **bot**: Fix type annotations of the registration getters
  ([`e3a4960`](https://github.com/Cewerty/University-match/commit/e3a496049229fc4cc7fc15c8720346650aace275))

- **bot**: Match the Multiselect callback signature
  ([`41a0d7d`](https://github.com/Cewerty/University-match/commit/41a0d7dcbad55bf4aee82bc28cad811adf6c4eab))

- **repo**: Return None explicitly and fix annotations
  ([`b8815a0`](https://github.com/Cewerty/University-match/commit/b8815a0745d618edd6daa373e42511046721e9e9))

- **web**: Type the admin column formatters
  ([`892a751`](https://github.com/Cewerty/University-match/commit/892a75162116c3becd7dcf70f29e6239c149fe1d))


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
