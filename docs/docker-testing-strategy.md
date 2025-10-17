# Docker Testing Strategy

## Overview
This document outlines the improved Docker testing strategy that separates test dependencies from production images while maintaining comprehensive testing coverage.

## Problems with Previous Approach
- **Production Image Bloat**: Including pytest in production images increases size and attack surface
- **Security Concerns**: Test tools in production containers create unnecessary security risks
- **Dependency Pollution**: Production environments don't need test dependencies

## Current Multi-Stage Approach

### Dockerfile Structure
```dockerfile
# Base stage - common dependencies
FROM python:3.9-slim as base
# ... install production dependencies

# Test stage - includes test dependencies
FROM base as test
# ... install pytest and test tools
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]

# Production stage - clean, minimal image
FROM base as production
# ... security hardening, non-root user
CMD ["python", "src/gateway.py"]
```

### Benefits
1. **Clean Separation**: Test and production dependencies are isolated
2. **Smaller Production Images**: No test tools in production
3. **Better Security**: Minimal attack surface in production
4. **Flexible Testing**: Can test both test and production stages

## Testing Strategy

### 1. Unit Tests (Local Development)
```bash
# Install test dependencies
pip install -r requirements-test.txt
# Run tests
python -m pytest tests/ -v
```

### 2. Docker Test Stage
```bash
# Build and run test image
docker build --target test -t meshtopo-test .
docker run --rm meshtopo-test
```

### 3. Production Image Smoke Test
```bash
# Test production image can start and import modules
docker run --rm --name smoke-test meshtopo:latest \
  python -c "import src.gateway; print('OK')"
```

### 4. Integration Testing
- Test the actual production image in a staging environment
- Verify health checks work
- Test with real MQTT and CalTopo endpoints

## GitHub Actions Integration

The CI pipeline now:
1. Builds both test and production images
2. Runs comprehensive tests in the test image
3. Performs smoke tests on the production image
4. Only pushes the production image to registry

## File Structure
```
├── requirements.txt          # Production dependencies only
├── requirements-test.txt     # Test dependencies (includes requirements.txt)
├── deploy/Dockerfile         # Multi-stage Dockerfile
└── .github/workflows/ci.yml  # Updated CI pipeline
```

## Best Practices

1. **Keep Production Images Minimal**: Only include what's needed for runtime
2. **Separate Test Dependencies**: Use requirements-test.txt for testing
3. **Multi-Stage Builds**: Leverage Docker's multi-stage feature
4. **Smoke Testing**: Verify production images can start
5. **Security First**: Use non-root users in production images
6. **Health Checks**: Include proper health check mechanisms

## Migration Notes

- Removed pytest from requirements.txt
- Created requirements-test.txt for test dependencies
- Updated Dockerfile to use multi-stage builds
- Modified GitHub Actions to test both stages appropriately