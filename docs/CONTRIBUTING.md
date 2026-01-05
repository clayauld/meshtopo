# Contributing to Meshtopo

Thank you for your interest in contributing to Meshtopo! We welcome contributions from the community to help make this project better.

This document outlines the standards and guidelines for contributing to this repository.

## 1. Pull Request Naming Convention

We enforce a strict naming convention for Pull Requests to ensure our history is clean and semantic.

**Format:** `<type>: <description>`

**Types:**

* `feat`: A new feature
* `fix`: A bug fix
* `docs`: Documentation only changes
* `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
* `refactor`: A code change that neither fixes a bug nor adds a feature
* `perf`: A code change that improves performance
* `test`: Adding missing tests or correcting existing tests
* `chore`: Changes to the build process or auxiliary tools and libraries

**Examples:**

* `feat: add support for Meshtastic telemetry packets`
* `fix: resolve retry loop off-by-one error`
* `docs: update architecture diagram in design.md`

## 2. Code Style & Standards

We use the following tools to enforce code quality. You must ensure your code passes these checks before submitting.

### Python Style

* **Formatter:** We use **Black**.
* **Linter:** We use **Flake8**.
* **Imports:** Sorted by **isort**.

### Type Hinting

* All new code must be fully type-hinted.
* We use **mypy** for static type checking.

### Docstrings

* We follow the **Google Python Style Guide** for docstrings.
* Every public class and method must have a docstring explaining "Why" and "How".
* Example:

```python
def calculate_distance(p1: tuple, p2: tuple) -> float:
    """
    Calculate the haversine distance between two points.

    Args:
        p1: Tuple of (lat, lon) for point 1.
        p2: Tuple of (lat, lon) for point 2.

    Returns:
        float: Distance in kilometers.
    """
```

## 3. Testing

* **Requirement:** All new features must include unit tests.
* **Framework:** We use `pytest` and `pytest-asyncio`.
* **Mocks:** Use `unittest.mock` or `pytest-mock` to isolate external dependencies (HTTP, MQTT, Disk).
* **Coverage:** We aim for >90% code coverage.

## 4. Development Workflow

1. **Setup:**

    ```bash
    make setup
    pip install -e ".[dev]"
    ```

2. **Run Tests:**

    ```bash
    pytest
    ```

3. **Pre-commit:**
    Install pre-commit hooks to automatically check your code before you commit:

    ```bash
    pre-commit install
    ```

4. **Submit:**
    Push your branch and open a PR matching the naming convention.

## 5. Security

* **Secrets:** Never commit secrets/passwords. Use `SecretStr` in Pydantic models.
* **Serialization:** Do not use `pickle`. Use `json` for serialization.
* **Input:** Always sanitize untrusted input before logging using `utils.sanitize_for_log`.
