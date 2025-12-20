# Bolt Learnings

## 2025-02-17 - Concurrent API Requests

**Learning:** `CalTopoReporter` was making sequential requests to multiple endpoints (`connect_key` and `group`), which amplified latency when one endpoint was slow or retrying.
**Action:** Use `asyncio.gather` for independent network requests to prevent blocking. Ensure `return_exceptions=True` is used to prevent one failure from cancelling others, and check results carefully.

## 2024-05-22 - JSON Parsing Performance

**Learning:** `json.loads(bytes)` is significantly slower than `json.loads(str)` in this environment (approx 20% slower). This is counter-intuitive as usually avoiding decoding is faster. It suggests the underlying `json` library implementation might be doing inefficient encoding detection or copying when handling bytes.
**Action:** Always decode bytes to string before passing to `json.loads` in this codebase, unless memory pressure is extreme (which might justify the CPU cost).

## 2024-05-22 - Logging Overhead

**Learning:** Standard Python `logging.debug(f"...")` evaluates the f-string even if debug logging is disabled. This adds measurable overhead (approx 30-40ms per 100k calls).
**Action:** Use lazy logging `logger.debug("%s", arg)` or guard with `if logger.isEnabledFor(logging.DEBUG):` in hot paths.
