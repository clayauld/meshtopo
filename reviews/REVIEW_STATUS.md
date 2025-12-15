# Security Review Status

This document consolidates and tracks the status of security issues identified across multiple reviews.

## ✅ Resolved Issues

### 1. SSRF (Server-Side Request Forgery) Vulnerability

**Severity**: MEDIUM  
**Files**:

-   `review_security_audit.md` (L5-L15)
-   `review-1765700805.md` (L7-L11)

**Original Issue**: The `ALLOW_NON_PROD_CALTOPO_URL` environment variable allowed arbitrary URLs without proper validation, creating SSRF risk.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: [src/caltopo_reporter.py:L44-L72](file:///home/clayauld/meshtopo/src/caltopo_reporter.py#L44-L72)

Replaced the boolean flag with `CALTOPO_ALLOWED_URL_PATTERNS` explicit allowlist:

-   Test/development mode: URLs must match explicit patterns in the allowlist
-   Production mode: URLs must point to `caltopo.com` or subdomains
-   Uses pattern matching with wildcard support for flexible but controlled testing

**Review References**:

-   `review-1765700805.md`: Marked as `[x]` resolved
-   `review_src_20251213.md`: Marked as `[✔️]` with commendation for security control
-   `review_security_audit.md`: Needs status update

### 2. Hardcoded Container Names

**Severity**: LOW (Nit)  
**Files**:

-   `review-1765700805.md` (L30-L33)

**Original Issue**: Integration test fixture hardcoded container name `deploy-gateway-1`, making it brittle.

**Resolution**: ✅ **RESOLVED**  
**Implementation**:

-   [tests/integration/test_integration.py:L116-L127](file:///home/clayauld/meshtopo/tests/integration/test_integration.py#L116-L127)
-   [.github/workflows/ci.yml:L273-L281](file:///home/clayauld/meshtopo/.github/workflows/ci.yml#L273-L281)

Changed from `docker logs <container-name>` to `docker compose logs <service-name>` for more robust service log retrieval.

**Review References**:

-   `review-1765700805.md`: Needs status update to mark as `[x]`

### 3. Dependency Management Conflicts

**Severity**: MAJOR  
**Files**:

-   `review-1765700805.md` (L23-L28)

**Original Issue**: Conflicting dependency definitions across `pyproject.toml`, `requirements.txt`, and `requirements-dev.txt`.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: All dependencies consolidated into `pyproject.toml` as single source of truth.

**Review References**:

-   `review-1765700805.md`: Marked as `[x]` resolved

### 4. Regex Replacement String Error

**Severity**: MEDIUM  
**Files**:

-   `review-1765700805.md` (L15-L19)

**Original Issue**: Double backslash in regex replacement string causing literal backslash in logs.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: [src/caltopo_reporter.py:L222](file:///home/clayauld/meshtopo/src/caltopo_reporter.py#L222)

Fixed to use single backslash for proper backreference: `r"\1<REDACTED>"`

**Review References**:

-   `review-1765700805.md`: Marked as `[x]` resolved

### 5. Log Injection Vulnerability

**Severity**: MEDIUM  
**Files**:

-   `review_security_audit.md` (L17-L28)

**Original Issue**: Data received from MQTT broker is logged directly without sanitization, allowing potential log injection attacks.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: [src/gateway_app.py](file:///home/clayauld/meshtopo/src/gateway_app.py)

Implemented `_sanitize_for_log` method to escape control characters and non-printable characters. Applied this sanitization to all logging statements in `src/gateway_app.py` that handle external data.

**Review References**:

-   `review_security_audit.md`: Marked as resolved

### 6. Fragile sys.path Manipulation

**Severity**: MINOR  
**Files**:

-   `review_src_20251213.md` (L31-L34)

**Original Issue**: `src/gateway.py` uses `sys.path.insert()` for import resolution instead of proper editable install.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: [src/gateway.py](file:///home/clayauld/meshtopo/src/gateway.py)

Removed `sys.path.insert` hack from `src/gateway.py` and updated `GEMINI.md` to explicitly recommend editable install (`pip install -e '.[dev]'`) for development.

**Review References**:

-   `review_src_20251213.md`: Marked as resolved

### 7. Complex Callsign Resolution Logic

**Severity**: MINOR (Nit)
**Files**:

-   `review_src_20251213.md` (L36-L39)

**Original Issue**: Nested if/else statements for callsign resolution make code harder to follow.

**Resolution**: ✅ **RESOLVED**
**Implementation**: [src/gateway_app.py](file:///home/clayauld/meshtopo/src/gateway_app.py)

Refactored callsign resolution logic into a new `_get_or_create_callsign` method to improve readability and reduce nesting in `_process_position_message`.

**Review References**:

-   Marked as resolved in consolidated review.

### 8. Implicit Fallback Logic

**Severity**: MINOR
**Files**:

-   Previously in `review_src_20251213.md`

**Original Issue**: Implicit contract between `gateway_app.py` and `caltopo_reporter.py` for group fallback logic.

**Resolution**: ✅ **RESOLVED**
**Implementation**: [src/gateway_app.py](file:///home/clayauld/meshtopo/src/gateway_app.py)

Made group fallback explicit in `gateway_app.py` and removed the implicit fallback in `caltopo_reporter.py`.

**Review References**:

-   Marked as resolved in consolidated review.

## ⚠️ Outstanding Issues

### 1. Inefficient One-off HTTP Clients

**Severity**: MEDIUM
**Files**:

-   `src/caltopo_reporter.py` (L129)

**Original Issue**: Inefficient `httpx.AsyncClient` instantiation creates unnecessary overhead by creating a new client for each request, preventing connection pooling.

**Recommendation**: Modify `CalTopoReporter` to manage a shared `httpx.AsyncClient` instance tied to the application lifecycle.

**Status**: ⚠️ **OPEN**

### 2. Flaky Integration Tests (Fixed Sleeps)

**Severity**: MEDIUM
**Files**:

-   `tests/integration/test_integration.py` (L182)

**Original Issue**: Use of fixed `time.sleep()` for waiting on async events leads to flaky tests on slow systems.

**Recommendation**: Replace fixed sleep with polling loop that checks for expected condition with a timeout.

**Status**: ⚠️ **OPEN**

## 🎯 Summary

**Total Issues Identified**: 20
**Resolved**: 8 (40%)
**Outstanding**: 12 (60%)

**Status**: ⚠️ **OPEN ISSUES REMAINING**

**Status**: ⚠️ **OPEN**

### 7. Unsafe Deserialization in SqliteDict

**Severity**: CRITICAL
**Files**:

-   `src/gateway_app.py`

**Original Issue**: `SqliteDict` uses unsafe `pickle` serialization by default, which can lead to RCE if untrusted data is deserialized.

**Recommendation**: Explictly use JSON serialization: `encode=json.dumps, decode=json.loads`.

**Status**: ⚠️ **OPEN**

### 8. Leaking Secrets in Process List

**Severity**: MEDIUM
**Files**:

-   `Makefile` (L202)

**Original Issue**: `docker login` passes password via command line `-p`, visible in process list.

**Recommendation**: Use `--password-stdin`.

**Status**: ⚠️ **OPEN**

### 9. Command Injection in Makefile

**Severity**: CRITICAL
**Files**:

-   `Makefile` (L136)

**Original Issue**: Unsanitized usage of `$(REPO)` and `$(GITHUB_REPOSITORY)` in shell commands.

**Recommendation**: Sanitize variables before use.

**Status**: ⚠️ **OPEN**

### 10. Traefik Routing Rule Injection

**Severity**: HIGH
**Files**:

-   `deploy/docker-compose.yml` (L51)

**Original Issue**: Unsanitized `SSL_DOMAIN` usage in Traefik labels allow rule injection.

**Recommendation**: Sanitize `SSL_DOMAIN`.

**Status**: ⚠️ **OPEN**

### 11. Unnecessary Build Tools in Production

**Severity**: LOW
**Files**:

-   `deploy/Dockerfile` (L8-10)

**Original Issue**: `gcc` installed in production image, increasing attack surface.

**Recommendation**: Use multi-stage build to keep compiler out of final image.

**Status**: ⚠️ **OPEN**

### 12. Path Traversal in Config Loading

**Severity**: LOW
**Files**:

-   `src/gateway.py` (L29)

**Original Issue**: Unsanitized command-line argument used as config file path.

**Recommendation**: Validate/sanitize input path.

**Status**: ⚠️ **OPEN**
