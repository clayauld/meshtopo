## 2025-02-17 - Concurrent API Requests
**Learning:** `CalTopoReporter` was making sequential requests to multiple endpoints (`connect_key` and `group`), which amplified latency when one endpoint was slow or retrying.
**Action:** Use `asyncio.gather` for independent network requests to prevent blocking. Ensure `return_exceptions=True` is used to prevent one failure from cancelling others, and check results carefully.
