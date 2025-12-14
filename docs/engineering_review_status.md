# Engineering Review Status

This document tracks the progress of the engineering review and modernization roadmap outlined in `docs/engineering_review.md`.

## Phase 1: Foundational Improvements

| Initiative                                | Key Activities                                                                                       | Status                           |
| :---------------------------------------- | :--------------------------------------------------------------------------------------------------- | :------------------------------- |
| **Streamline Onboarding & Configuration** | 1. Implement the `make setup` interactive wizard.                                                    | :white_check_mark: **Completed** |
|                                           | 2. Refactor Docker Compose to use environment variables, deprecating `generate_mosquitto_config.py`. | :white_check_mark: **Completed** |
|                                           | 3. Restructure `README.md` for user/developer audience segmentation.                                 | :white_check_mark: **Completed** |
| **Enhance Robustness**                    | 1. Integrate `Pydantic` for configuration validation.                                                | :white_check_mark: **Completed** |
|                                           | 2. Implement state persistence using `sqlitedict`.                                                   | :white_check_mark: **Completed** |
|                                           | 3. Set up Dependabot for automated dependency updates.                                               | :white_check_mark: **Completed** |

## Phase 2: Core Architectural Refactoring

| Initiative                                | Key Activities                                                                                               | Status                   |
| :---------------------------------------- | :----------------------------------------------------------------------------------------------------------- | :----------------------- |
| **Transition to Asynchronous Core**       | 1. Refactor `gateway_app.py` to use an `asyncio` event loop.                                                 | :red_circle: **Pending** |
|                                           | 2. Replace `MqttClient` with an `asyncio-mqtt` implementation.                                               | :red_circle: **Pending** |
|                                           | 3. Replace `CalTopoReporter` with an `httpx`-based async implementation.                                     | :red_circle: **Pending** |
| **Implement Advanced Network Resilience** | 1. Add a configurable retry mechanism with exponential backoff and jitter to the new `httpx`-based reporter. | :red_circle: **Pending** |

## Phase 3: Advanced Capabilities & Optimization

| Initiative                     | Key Activities                                                  | Status                           |
| :----------------------------- | :-------------------------------------------------------------- | :------------------------------- |
| **Automate Release Lifecycle** | 1. Enforce Conventional Commits standard.                       | :red_circle: **Pending**         |
|                                | 2. Integrate `python-semantic-release` into the CI/CD pipeline. | :red_circle: **Pending**         |
| **Optimize CI/CD Pipeline**    | 1. Add an integration test stage using Docker Compose.          | :red_circle: **Pending**         |
|                                | 2. Optimize `Dockerfile` layer caching.                         | :white_check_mark: **Completed** |
