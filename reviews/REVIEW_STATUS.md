# Security Review Status

This document consolidates and tracks the status of security issues identified across multiple reviews.

## ✅ Resolved Issues

### 1. SSRF (Server-Side Request Forgery) Vulnerability

**Severity**: MEDIUM  
**Files**:

- `review_security_audit.md` (L5-L15)
- `review-1765700805.md` (L7-L11)

**Original Issue**: The `ALLOW_NON_PROD_CALTOPO_URL` environment variable allowed arbitrary URLs without proper validation, creating SSRF risk.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: [src/caltopo_reporter.py:L44-L72](file:///home/clayauld/meshtopo/src/caltopo_reporter.py#L44-L72)

Replaced the boolean flag with `CALTOPO_ALLOWED_URL_PATTERNS` explicit allowlist:

- Test/development mode: URLs must match explicit patterns in the allowlist
- Production mode: URLs must point to `caltopo.com` or subdomains
- Uses pattern matching with wildcard support for flexible but controlled testing

**Review References**:

- `review-1765700805.md`: Marked as `[x]` resolved
- `review_src_20251213.md`: Marked as `[✔️]` with commendation for security control
- `review_security_audit.md`: Needs status update

### 2. Hardcoded Container Names

**Severity**: LOW (Nit)  
**Files**:

- `review-1765700805.md` (L30-L33)

**Original Issue**: Integration test fixture hardcoded container name `deploy-gateway-1`, making it brittle.

**Resolution**: ✅ **RESOLVED**  
**Implementation**:

- [tests/integration/test_integration.py:L116-L127](file:///home/clayauld/meshtopo/tests/integration/test_integration.py#L116-L127)
- [.github/workflows/ci.yml:L273-L281](file:///home/clayauld/meshtopo/.github/workflows/ci.yml#L273-L281)

Changed from `docker logs <container-name>` to `docker compose logs <service-name>` for more robust service log retrieval.

**Review References**:

- `review-1765700805.md`: Needs status update to mark as `[x]`

### 3. Dependency Management Conflicts

**Severity**: MAJOR  
**Files**:

- `review-1765700805.md` (L23-L28)

**Original Issue**: Conflicting dependency definitions across `pyproject.toml`, `requirements.txt`, and `requirements-dev.txt`.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: All dependencies consolidated into `pyproject.toml` as single source of truth.

**Review References**:

- `review-1765700805.md`: Marked as `[x]` resolved

### 4. Regex Replacement String Error

**Severity**: MEDIUM  
**Files**:

- `review-1765700805.md` (L15-L19)

**Original Issue**: Double backslash in regex replacement string causing literal backslash in logs.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: [src/caltopo_reporter.py:L222](file:///home/clayauld/meshtopo/src/caltopo_reporter.py#L222)

Fixed to use single backslash for proper backreference: `r"\1<REDACTED>"`

**Review References**:

- `review-1765700805.md`: Marked as `[x]` resolved

### 5. Log Injection Vulnerability

**Severity**: MEDIUM  
**Files**:

- `review_security_audit.md` (L17-L28)

**Original Issue**: Data received from MQTT broker is logged directly without sanitization, allowing potential log injection attacks.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: [src/gateway_app.py](file:///home/clayauld/meshtopo/src/gateway_app.py)

Implemented `_sanitize_for_log` method to escape control characters and non-printable characters. Applied this sanitization to all logging statements in `src/gateway_app.py` that handle external data.

**Review References**:

- `review_security_audit.md`: Marked as resolved

### 6. Fragile sys.path Manipulation

**Severity**: MINOR  
**Files**:

- `review_src_20251213.md` (L31-L34)

**Original Issue**: `src/gateway.py` uses `sys.path.insert()` for import resolution instead of proper editable install.

**Resolution**: ✅ **RESOLVED**  
**Implementation**: [src/gateway.py](file:///home/clayauld/meshtopo/src/gateway.py)

Removed `sys.path.insert` hack from `src/gateway.py` and updated `GEMINI.md` to explicitly recommend editable install (`pip install -e '.[dev]'`) for development.

**Review References**:

- `review_src_20251213.md`: Marked as resolved

### 7. Complex Callsign Resolution Logic

**Severity**: MINOR (Nit)
**Files**:

- `review_src_20251213.md` (L36-L39)

**Original Issue**: Nested if/else statements for callsign resolution make code harder to follow.

**Resolution**: ✅ **RESOLVED**
**Implementation**: [src/gateway_app.py](file:///home/clayauld/meshtopo/src/gateway_app.py)

Refactored callsign resolution logic into a new `_get_or_create_callsign` method to improve readability and reduce nesting in `_process_position_message`.

**Review References**:

- Marked as resolved in consolidated review.

### 8. Implicit Fallback Logic

**Severity**: MINOR
**Files**:

- Previously in `review_src_20251213.md`

**Original Issue**: Implicit contract between `gateway_app.py` and `caltopo_reporter.py` for group fallback logic.

**Resolution**: ✅ **RESOLVED**
**Implementation**: [src/gateway_app.py](file:///home/clayauld/meshtopo/src/gateway_app.py)

Made group fallback explicit in `gateway_app.py` and removed the implicit fallback in `caltopo_reporter.py`.

**Review References**:

- Marked as resolved in consolidated review.

### 9. Inefficient One-off HTTP Clients

**Severity**: MEDIUM
**Resolution**: ✅ **RESOLVED**
**Implementation**: Refactored `CalTopoReporter` to accept a shared `httpx.AsyncClient`. Updated `GatewayApp` to manage the client lifecycle.

### 10. Flaky Integration Tests (Fixed Sleeps)

**Severity**: MEDIUM
**Resolution**: ✅ **RESOLVED**
**Implementation**: Replaced fixed sleeps with polling loops in `tests/integration/test_integration.py`.

### 11. Unsafe Deserialization in SqliteDict

**Severity**: CRITICAL
**Resolution**: ✅ **RESOLVED**
**Implementation**: Updated `SqliteDict` usage in `src/gateway_app.py` to use `json.dumps`/`json.loads`. Added logic to reset state file if format is incompatible.

### 12. Leaking Secrets in Process List

**Severity**: MEDIUM
**Resolution**: ✅ **RESOLVED**
**Implementation**: Updated `Makefile` to use `echo ... | docker login ... --password-stdin`.

### 13. Command Injection in Makefile

**Severity**: CRITICAL
**Resolution**: ✅ **RESOLVED**
**Implementation**: Added sanitization for `$(REPO)` variable in `Makefile`.

### 14. Traefik Routing Rule Injection

**Severity**: HIGH
**Resolution**: ✅ **RESOLVED**
**Implementation**: Added sanitization for `SSL_DOMAIN` in `Makefile` before passing to docker-compose.

### 15. Unnecessary Build Tools in Production

**Severity**: LOW
**Resolution**: ✅ **RESOLVED**
**Implementation**: Updated `deploy/Dockerfile` to use multi-stage build, keeping `gcc` out of production image.

### 16. Path Traversal in Config Loading

**Severity**: LOW
**Resolution**: ✅ **RESOLVED**
**Implementation**: Added strict path validation in `src/gateway.py` to ensure config file is within application directory.

### 17. Permanent Callsign for Unknown Devices

**Severity**: MINOR
**Resolution**: ✅ **RESOLVED**
**Implementation**: Updated `_get_or_create_callsign` in `src/gateway_app.py` to NOT persist temporary mappings for unknown devices.

### 18. Inconsistent State for Denied Devices

**Severity**: MINOR
**Resolution**: ✅ **RESOLVED**
**Implementation**: Updated `_process_position_message` to defer persistence of `node_id_mapping` until after authorization check.

### 19. Potential Disk I/O Bottleneck

**Severity**: MEDIUM
**Resolution**: ✅ **RESOLVED**
**Implementation**: Implemented in-memory caching for `SqliteDict` lookups in `src/gateway_app.py`.

### 20. Hardware ID Resolution Logic Extraction

**Severity**: NIT
**Resolution**: ✅ **RESOLVED**
**Implementation**: Extracted `_resolve_hardware_id` method in `src/gateway_app.py`.

### 21. Inconsistent Log Sanitization

**Severity**: MEDIUM
**Resolution**: ✅ **RESOLVED**
**Implementation**: Applied `_sanitize_for_log` consistently across `src/gateway_app.py` including `_process_message`, `_process_position_message`, `_convert_numeric_to_id`, and `_get_or_create_callsign`.

### 22. Insecure Service Configuration in Integration Tests

**Severity**: LOW
**Resolution**: ✅ **RESOLVED**
**Implementation**: Added security warning comments to `deploy/docker-compose.integration.yml`.

## 🎯 Summary

**Total Issues Identified**: 22
**Resolved**: 22 (100%)
**Outstanding**: 0 (0%)

**Status**: ✅ **ALL ISSUES RESOLVED**
