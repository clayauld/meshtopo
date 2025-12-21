# Engineering Review Status

This document tracks the progress of the engineering review and modernization roadmap outlined in `docs/engineering_review.md`.

## Phase 1: Foundational Improvements

| Initiative                                | Key Activities                                                                                       | Status                           |
| :---------------------------------------- | :--------------------------------------------------------------------------------------------------- | :------------------------------- |
| **Streamline Onboarding & Configuration** | 1. Implement the `make setup` interactive wizard.                                                    | :white_check_mark: **Completed** |
|                                           | 2. Refactor Docker Compose to use environment variables, deprecating `generate_mosquitto_config.py`. | :white_check_mark: **Completed** |
|                                           | 3. Restructure `README.md` for user/developer audience segmentation.                                 | :white_check_mark: **Completed** |
| **Enhance Robustness**                    | 1. Integrate `Pydantic` for configuration validation.                                                | :white_check_mark: **Completed** |
|                                           | 2. Enhance configuration to prioritize environment variables for secrets.                            | :white_check_mark: **Completed** |
|                                           | 3. Implement state persistence using `sqlitedict`.                                                   | :white_check_mark: **Completed** |
|                                           | 4. Set up Dependabot for automated dependency updates.                                               | :white_check_mark: **Completed** |
|                                           | 5. Schedule pre-commit autoupdate in CI pipeline.                                                    | :white_check_mark: **Completed** |

## Phase 2: Core Architectural Refactoring

| Initiative                                | Key Activities                                                                                               | Status                           |
| :---------------------------------------- | :----------------------------------------------------------------------------------------------------------- | :------------------------------- |
| **Transition to Asynchronous Core**       | 1. Refactor `gateway_app.py` to use an `asyncio` event loop.                                                 | :white_check_mark: **Completed** |
|                                           | 2. Replace `MqttClient` with an `asyncio-mqtt` implementation.                                               | :white_check_mark: **Completed** |
|                                           | 3. Replace `CalTopoReporter` with an `httpx`-based async implementation.                                     | :white_check_mark: **Completed** |
| **Implement Advanced Network Resilience** | 1. Add a configurable retry mechanism with exponential backoff and jitter to the new `httpx`-based reporter. | :white_check_mark: **Completed** |

## Phase 3: Advanced Capabilities & Optimization

| Initiative                     | Key Activities                                                  | Status                           |
| :----------------------------- | :-------------------------------------------------------------- | :------------------------------- |
| **Automate Release Lifecycle** | 1. Enforce Conventional Commits standard.                       | :white_check_mark: **Completed** |
|                                | 2. Integrate `python-semantic-release` into the CI/CD pipeline. | :white_check_mark: **Completed** |
| **Optimize CI/CD Pipeline**    | 1. Add an integration test stage using Docker Compose.          | :white_check_mark: **Completed** |
|                                | 2. Optimize `Dockerfile` layer caching.                         | :white_check_mark: **Completed** |

---

## Dependency Modernization Tracking (Section 2.2)

This table tracks the specific dependency upgrades identified in the engineering review.

| Dependency   | Target Version | Upgrade Risk | Status                           | Notes                                                   |
| :----------- | :------------- | :----------- | :------------------------------- | :------------------------------------------------------ |
| `paho-mqtt`  | 2.1.0          | **High**     | :white_check_mark: **Completed** | Migrated to `asyncio-mqtt` as part of async refactoring |
| `requests`   | 2.32.5+        | Low          | :white_check_mark: **Completed** | Replaced with `httpx` in async refactoring              |
| `PyYAML`     | 6.0.3+         | Low          | :white_check_mark: **Completed** | Updated to latest version                               |
| `Jinja2`     | 6.0.3+         | None         | :white_check_mark: **Completed** | Dependency removed (no longer needed)                   |
| `black`      | 25.9.0+        | Medium       | :white_check_mark: **Completed** | Updated and ran across codebase                         |
| `flake8`     | 7.3.0+         | Low          | :white_check_mark: **Completed** | Updated to latest version                               |
| `isort`      | 7.0.0+         | Medium       | :white_check_mark: **Completed** | Updated and ran across codebase                         |
| `mypy`       | v1.18.2+       | Medium       | :white_check_mark: **Completed** | Updated and addressed new type-checking rules           |
| `pydantic`   | Latest         | Low          | :white_check_mark: **Completed** | Integrated for configuration validation                 |
| `sqlitedict` | Latest         | Low          | :white_check_mark: **Completed** | Integrated for state persistence                        |
| `httpx`      | Latest         | N/A (New)    | :white_check_mark: **Completed** | Added as async HTTP client replacement for `requests`   |
