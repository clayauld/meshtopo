# CHANGELOG

<!-- version list -->

## v1.3.0 (2026-02-23)

### Build System

- Specify container name for Azure Container App update in deploy workflow.
  ([`f3f69b7`](https://github.com/clayauld/meshtopo/commit/f3f69b743c73166c16c2bd894ce948540b24ba01))

### Features

- Upgrade minimum Python version to 3.10 across documentation, Dockerfiles, and dependencies, and
  delete the changelog.
  ([`34af72a`](https://github.com/clayauld/meshtopo/commit/34af72ad9fd221e8523f33e065578ad2139883eb))

## v1.2.0 (2026-02-23)

### Features

- Add GitHub Actions workflow for Azure Container App deployment.
  ([`1f94fb9`](https://github.com/clayauld/meshtopo/commit/1f94fb9bd2096a3b37d988e3a3132d65a1a9cde1))

### Refactoring

- Update deployment workflow to trigger on successful Release workflow completion and remove Docker
  image build steps.
  ([`d5eb6d4`](https://github.com/clayauld/meshtopo/commit/d5eb6d44e20b910394c9a31214606a3cef4ebd7f))

## v1.1.1 (2026-02-23)

### Bug Fixes

- Redact CalTopo connect keys and secrets in logs
  ([`d8d7af6`](https://github.com/clayauld/meshtopo/commit/d8d7af636f34a0a7eadca16994ae4bfd87c7097e))

- Redact CalTopo connect keys and secrets in logs
  ([`ff5ec33`](https://github.com/clayauld/meshtopo/commit/ff5ec33181742b2f9872f835ce9ea07190ad92b9))

- Redact CalTopo connect keys and secrets in logs
  ([`244d2ba`](https://github.com/clayauld/meshtopo/commit/244d2ba26aa610bd081598d0734c7534422b137d))

- Redact CalTopo connect keys and secrets in logs
  ([`0667a1b`](https://github.com/clayauld/meshtopo/commit/0667a1bb8c9d9f30682e6d81b4ce3ad729c44207))

- Redact CalTopo connect keys and secrets in logs
  ([`1264e5a`](https://github.com/clayauld/meshtopo/commit/1264e5ab85cae2909dc640e0bf303931bd25e3cc))

- Redact CalTopo connect keys and secrets in logs
  ([`01a2690`](https://github.com/clayauld/meshtopo/commit/01a2690f7a0079c03109f587e7dd8f169297c3de))

### Chores

- Re-lock dependencies, fix dependabot issues
  ([`2a69326`](https://github.com/clayauld/meshtopo/commit/2a693265ba4e212df73b79bcd1089d8f3aefe6fe))

- **deps**: Bump aiomqtt from 2.4.0 to 2.5.0
  ([`dd41798`](https://github.com/clayauld/meshtopo/commit/dd41798f8672afd7a855386ba1930d062f4431bd))

- **deps**: Bump gitpython from 3.1.45 to 3.1.46
  ([`e45b990`](https://github.com/clayauld/meshtopo/commit/e45b990c5c73053aaea3fb70b147259f8e83fa91))

- **deps**: Bump rich from 14.2.0 to 14.3.1
  ([`c957505`](https://github.com/clayauld/meshtopo/commit/c95750568eef9d770d94ed0ed551f190094cd1a0))

- **deps**: Bump rich from 14.3.1 to 14.3.2
  ([`a71a221`](https://github.com/clayauld/meshtopo/commit/a71a22150b974824e317d7134723787b111f6168))

- **deps**: Bump rich from 14.3.2 to 14.3.3
  ([`45b0c3a`](https://github.com/clayauld/meshtopo/commit/45b0c3a1352abd815bb922f69ca90784bbaa461e))

- **deps**: Bump the uv group across 1 directory with 2 updates
  ([`f7f9a66`](https://github.com/clayauld/meshtopo/commit/f7f9a66542eaa4e87e4cc18da7e4e4eb8a53b4d8))

- **deps**: Bump tomlkit from 0.13.3 to 0.14.0
  ([`dad052d`](https://github.com/clayauld/meshtopo/commit/dad052d779217f3021823fe33bb5bda87e30df0b))

- **deps**: Update pre-commit hooks
  ([`de5a7d1`](https://github.com/clayauld/meshtopo/commit/de5a7d19adee007fc6d410d85f438c28e33e0e41))

- **deps**: Update pre-commit hooks
  ([`4d600c8`](https://github.com/clayauld/meshtopo/commit/4d600c8c27f2ba5dd53b7e1dd1d68d575065f75b))

- **deps**: Update pre-commit hooks
  ([`97a61ef`](https://github.com/clayauld/meshtopo/commit/97a61efdae38029544fb9c0d73be4f50fcc81ca2))

### Documentation

- Introduce contribution guidelines and a documentation generation script, remove the changelog, and
  update the engineering review and developer tooling.
  ([`bd7d545`](https://github.com/clayauld/meshtopo/commit/bd7d5452a2b91b7d6720e6b3d75804b33e978c70))

- Introduced engineering review cycle 2
  ([`d55c793`](https://github.com/clayauld/meshtopo/commit/d55c793c27d3ddb6f6f2cb2d14a8f3c02719e3f8))

- Update engineering review with current status of docstring completion and `pyproject.toml`
  configuration.
  ([`cd710ac`](https://github.com/clayauld/meshtopo/commit/cd710ac0212394862d0c6e4159c26613d63714b2))

## v1.1.0 (2026-01-05)

### Bug Fixes

- Improve documentation coverage extraction and provide detailed diff for stale documentation checks
  ([#63](https://github.com/clayauld/meshtopo/pull/63),
  [`89471fb`](https://github.com/clayauld/meshtopo/commit/89471fb70be6828bc453e7fa71c5d2f8daf1b7fc))

### Build System

- Update project dependencies and configuration
  ([#63](https://github.com/clayauld/meshtopo/pull/63),
  [`89471fb`](https://github.com/clayauld/meshtopo/commit/89471fb70be6828bc453e7fa71c5d2f8daf1b7fc))

### Chores

- **deps**: Bump actions/github-script from 7 to 8
  ([`9cd9c6b`](https://github.com/clayauld/meshtopo/commit/9cd9c6b3f3fc8ab2455a70958e1b972ccdfaa6dc))

- **deps**: Bump actions/upload-artifact from 4 to 6
  ([`1086b41`](https://github.com/clayauld/meshtopo/commit/1086b415f74169a73f7d348a8b296d30ee5e2451))

- **deps**: Bump amannn/action-semantic-pull-request from 5 to 6
  ([`dcd9678`](https://github.com/clayauld/meshtopo/commit/dcd9678c9e811ad5b620036f43c1f5fb5cc46410))

- **deps**: Bump gitpython from 3.1.45 to 3.1.46
  ([`5af8aa2`](https://github.com/clayauld/meshtopo/commit/5af8aa22d55865ac892a6bfc7a2198a2e0d90653))

### Documentation

- Add Pydantic `__init__` methods and new config properties/methods to API docs, remove redundant
  `PersistentDict` methods, and refine doc generation.
  ([#63](https://github.com/clayauld/meshtopo/pull/63),
  [`89471fb`](https://github.com/clayauld/meshtopo/commit/89471fb70be6828bc453e7fa71c5d2f8daf1b7fc))

- Document internal helper and message processing methods across several API modules.
  ([#63](https://github.com/clayauld/meshtopo/pull/63),
  [`89471fb`](https://github.com/clayauld/meshtopo/commit/89471fb70be6828bc453e7fa71c5d2f8daf1b7fc))

- Enhance configuration and application component documentation and add config security checks.
  ([#63](https://github.com/clayauld/meshtopo/pull/63),
  [`89471fb`](https://github.com/clayauld/meshtopo/commit/89471fb70be6828bc453e7fa71c5d2f8daf1b7fc))

- Introduce contribution guidelines and a documentation generation script, remove the changelog, and
  update the engineering review and developer tooling.
  ([#63](https://github.com/clayauld/meshtopo/pull/63),
  [`89471fb`](https://github.com/clayauld/meshtopo/commit/89471fb70be6828bc453e7fa71c5d2f8daf1b7fc))

### Features

- Add API documentation generation, pre-commit hook, and CI checks for freshness and coverage.
  ([#63](https://github.com/clayauld/meshtopo/pull/63),
  [`89471fb`](https://github.com/clayauld/meshtopo/commit/89471fb70be6828bc453e7fa71c5d2f8daf1b7fc))

- Enhance Documentation Robustness and Automation
  ([#63](https://github.com/clayauld/meshtopo/pull/63),
  [`89471fb`](https://github.com/clayauld/meshtopo/commit/89471fb70be6828bc453e7fa71c5d2f8daf1b7fc))

## v1.0.0 (2025-12-31)

### Chores

- **deps**: Bump actions/cache from 4 to 5
  ([`e20f4f6`](https://github.com/clayauld/meshtopo/commit/e20f4f6bb3d84612b74ebae11850965811b711ea))

- **deps**: Bump actions/checkout from 4 to 6
  ([`223fac1`](https://github.com/clayauld/meshtopo/commit/223fac15090bddd4da6e5434c146ed115bf2583c))

- **deps**: Bump actions/setup-python from 5 to 6
  ([`a6947d3`](https://github.com/clayauld/meshtopo/commit/a6947d3708c1b240821b7abd4fb0bce5d3f8515d))

- **deps**: Bump aiomqtt from 2.1.0 to 2.4.0
  ([`0a2c15d`](https://github.com/clayauld/meshtopo/commit/0a2c15dfff562d5e67023d9dbc08b922c3696cce))

- **deps**: Bump httpx from 0.24.1 to 0.28.1
  ([`6a30738`](https://github.com/clayauld/meshtopo/commit/6a307385927330ba37f5b6f3923b96bb51e56a48))

- **deps**: Bump peter-evans/create-pull-request from 7 to 8
  ([`f3a3ac3`](https://github.com/clayauld/meshtopo/commit/f3a3ac39c368163abdb1d0dcde7c62c5b6384475))

- **deps**: Bump pydantic from 2.12.3 to 2.12.5
  ([`7a128e4`](https://github.com/clayauld/meshtopo/commit/7a128e4ae046abf36cb94d17b46050b2079d0551))

- **deps**: Bump python-semantic-release/python-semantic-release
  ([`19bb660`](https://github.com/clayauld/meshtopo/commit/19bb66088f5c646ed8980b70c2b42b8b2bf4f1a1))

- **deps**: Bump requests from 2.32.4 to 2.32.5
  ([`1e9c35e`](https://github.com/clayauld/meshtopo/commit/1e9c35edd17bb7294a13635b184048473944bd75))

- **deps-dev**: Bump pytest-asyncio from 0.21.1 to 1.2.0
  ([`00a3715`](https://github.com/clayauld/meshtopo/commit/00a3715dbd9ff3ee86c67c05e85e51eb71f94490))

### Features

- Enable environment variable overrides for MQTT and CalTopo configurations and add extensive
  CalTopo reporter tests.
  ([`e95a751`](https://github.com/clayauld/meshtopo/commit/e95a751cfdcc9581d65d14543738ed33f53ad541))

- Introduce simplified Docker Compose deployment options and integrated MQTT setup with updated
  documentation and configuration examples.
  ([`d719726`](https://github.com/clayauld/meshtopo/commit/d7197265c2f73e540a8dda172bed884ff63c7596))

- Mount `config.yaml` to mosquitto and update its healthcheck to use MQTT credentials from the
  config file.
  ([`d9881af`](https://github.com/clayauld/meshtopo/commit/d9881af49b303b226b35ec681f3766bf33032dba))

### Refactoring

- Use explicit environment variables for Mosquitto MQTT credentials and simplify its healthcheck
  command in docker-compose.
  ([`7e8485a`](https://github.com/clayauld/meshtopo/commit/7e8485ae22e99c92b1c5f1d92327ec6a3e101bc2))

## v0.1.0 (2025-12-21)

- Initial Release
