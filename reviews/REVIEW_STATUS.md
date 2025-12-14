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

## ⚠️ Outstanding Issues

### 1. Log Injection Vulnerability

**Severity**: MEDIUM  
**Files**:

-   `review_security_audit.md` (L17-L28)

**Issue**: Data received from MQTT broker is logged directly without sanitization, allowing potential log injection attacks.

**Location**: `src/gateway_app.py:L434` and throughout `_process_*` methods

**Recommendation**: Sanitize external data before logging by removing/escaping control characters and ANSI escape codes.

**Status**: ⚠️ **OPEN** - Needs implementation

### 2. Fragile sys.path Manipulation

**Severity**: MINOR  
**Files**:

-   `review_src_20251213.md` (L31-L34)

**Issue**: `src/gateway.py` uses `sys.path.insert()` for import resolution instead of proper editable install.

**Recommendation**: Replace with `pip install -e .` instructions in development guide.

**Status**: ⚠️ **OPEN** - Low priority maintainability issue

### 3. Complex Callsign Resolution Logic

**Severity**: MINOR (Nit)  
**Files**:

-   `review_src_20251213.md` (L36-L39)

**Issue**: Nested if/else statements for callsign resolution make code harder to follow.

**Recommendation**: Refactor into separate `_get_or_create_callsign()` method.

**Status**: ⚠️ **OPEN** - Low priority code clarity enhancement

### 4. Implicit Fallback Logic

**Severity**: MINOR  
**Files**:

-   `review_src_20251213.md` (L24-L27)

**Issue**: Implicit contract between `gateway_app.py` and `caltopo_reporter.py` for group fallback logic.

**Recommendation**: Make fallback logic more explicit for long-term maintainability.

**Status**: ⚠️ **OPEN** - Low priority, no immediate action required

## 📝 Review File Consolidation

### Active Review Files

1. **`review-1765700805.md`** - Async Refactor & CI/CD Overhaul (timestamp-based)
2. **`review_src_20251213.md`** - `src/` Directory Review (date-based)
3. **`review_security_audit.md`** - Security Audit Report (generic name)

### Recommendations

-   **Update** `review_security_audit.md` to mark SSRF issue as resolved
-   **Update** `review-1765700805.md` to mark hardcoded container names issue as resolved
-   Consider using consistent naming convention (suggest timestamp-based for traceability)
-   Archive older reviews once all issues are resolved or transferred to this status document

## 🎯 Summary

**Total Issues Identified**: 8  
**Resolved**: 4 (50%)  
**Outstanding**: 4 (50%)

**Critical/High Priority Outstanding**: 1 (Log Injection)  
**Low Priority Outstanding**: 3 (Maintainability improvements)
