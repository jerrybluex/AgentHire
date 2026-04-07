# AgentHire Critical Issues Remediation Plan

**Date**: 2026-04-07  
**Based on**: Comprehensive Code Review (Review ID: 2026-04-07-fullstack-audit)  
**Status**: Ready for Implementation

---

## Executive Summary

This document outlines a **4-phase remediation plan** to address 12 critical reliability and engineering issues identified in the AgentHire platform. The issues span data consistency, API semantics, security, and testing infrastructure.

**Critical Issues (Must Fix First)**: 5 issues that can cause data loss, inconsistent state, or billing errors  
**High Priority**: 3 issues affecting observability and quality assurance  
**Medium Priority**: 2 issues impacting maintainability and deployment

---

## Phase 1: Data Integrity & Security (Week 1)

**Goal**: Fix issues that can cause permanent data loss or corruption

### C1: Fix Development Secret Key Persistence
**Severity**: Critical  
**Files**: `backend/app/config.py`, `backend/app/core/security.py`, `.env.example`

**Problem**: Development environment generates random `secret_key` on each restart with `secrets.token_urlsafe(32)`. All encrypted data (contacts, agent secrets) becomes permanently unreadable after restart.

**Solution**:
1. Modify `SecuritySettings.validate_secret_key()` to fail hard if no key provided (even in dev)
2. Generate key once, store in `.env` file
3. Add decryption error handling with clear "key mismatch" error messages
4. Document key generation: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`

**Validation**:
- Test: Encrypt data → Restart server → Decrypt data (should work)
- Test: Wrong key produces clear error message, not garbled text

**Estimated Effort**: 2-3 hours

---

### C2: Fix Upload Flow Redis/Disk Consistency
**Severity**: Critical  
**Files**: `backend/app/core/cache.py`, `backend/app/api/v1/upload.py`

**Problem**: Upload system treats Redis as source of truth, but disk writes succeed independently. If Redis fails:
- `get_uploaded_chunks()` returns empty (scans Redis only)
- `complete_upload()` thinks chunks are missing
- Upload appears stuck despite chunks being on disk

**Solution**:
1. **Make disk the source of truth**: `get_uploaded_chunks()` scans disk directory
2. **Redis as cache layer only**: Cache chunk list, rebuild from disk if cache miss
3. **Add `_connected` checks**: Upload cache methods should handle Redis unavailability
4. **Atomic completion**: Verify chunks on disk before marking complete

**Code Changes**:
```python
# cache.py - get_uploaded_chunks becomes disk-first
async def get_uploaded_chunks(self, upload_id: str) -> list[int]:
    # Try Redis first (fast path)
    if self._connected:
        cached = await self._get_cached_chunk_list(upload_id)
        if cached is not None:
            return cached
    
    # Fall back to disk scan (source of truth)
    chunks = await self._scan_disk_chunks(upload_id)
    
    # Update cache if available
    if self._connected:
        await self._cache_chunk_list(upload_id, chunks)
    
    return chunks
```

**Validation**:
- Test: Upload with Redis running → Complete (success)
- Test: Upload with Redis stopped after init → Complete (success, disk-based)
- Test: Mixed scenario (some chunks cached, some not)

**Estimated Effort**: 6-8 hours

---

### C3: Fix Enterprise Quota Race Condition
**Severity**: Critical  
**Files**: `backend/app/services/enterprise_service.py`, tests

**Problem**: `record_usage()` uses read-check-write pattern:
```python
# Current (vulnerable)
current_usage = await get_sum_of_billing_records()  # Read
if current_usage + quantity > quota:  # Check
    raise QuotaExceeded
await insert_new_record()  # Write - NOT ATOMIC
```

Two concurrent requests both read 95, quota is 100, both try to add 10 → Result: 115 (exceeds quota)

**Solution**: Use database row locking
```python
# Fixed (atomic)
async with db.begin():
    # Lock the API key row
    api_key = await db.execute(
        select(EnterpriseAPIKey)
        .where(EnterpriseAPIKey.id == api_key_id)
        .with_for_update()  # Row lock
    ).scalar_one()
    
    # Recalculate under lock
    current_usage = await get_sum_of_billing_records()
    if current_usage + quantity > api_key.monthly_quota:
        raise QuotaExceeded
    
    # Insert within same transaction
    db.add(BillingRecord(...))
```

**Validation**:
- Concurrent test: 10 parallel requests, quota 15, each adding 5 → Max 3 succeed, 7 get QuotaExceeded

**Estimated Effort**: 4-6 hours

---

## Phase 2: API Reliability (Week 1-2)

### C4: Fix API HTTP Status Code Semantics
**Severity**: Critical  
**Files**: `backend/app/api/v1/enterprise.py`, `backend/app/api/v1/agents.py`, `backend/app/main.py`

**Problem**: Business failures return HTTP 201 + `success=False`:
```python
@router.post("/register", status_code=201)
async def register(data: RegisterRequest):
    if invalid_data:
        return EnterpriseResponse(success=False, error="Invalid")  # HTTP 201!
```

**Impact**: 
- Frontends see HTTP 201, cache the response, don't retry
- Monitoring systems (Pingdom, Datadog) see 2xx, mark as healthy
- API clients following REST conventions are broken

**Solution**:
1. **Validation errors**: `HTTPException(400, detail={"error": "validation", "fields": {...}})`
2. **Not found**: `HTTPException(404, detail={"error": "not_found"})`
3. **Quota exceeded**: `HTTPException(429, headers={"Retry-After": "3600"})`
4. **Server errors**: `HTTPException(500)` or let exception handlers convert
5. Reserve `success=False` only for partial success (200 OK with warnings)

**Endpoints to Fix**:
- `enterprise.py`: Lines 182, 221, 251, 325, 333, 342, 348, 482, 504, 540
- `agents.py`: Check all success=False returns
- Add global exception handler for QuotaExceededError → 429

**Validation**:
- Test: Invalid registration → 400
- Test: Non-existent enterprise → 404
- Test: Quota exceeded → 429 with Retry-After header

**Estimated Effort**: 8-10 hours

---

### C5: Database Migration Governance
**Severity**: Critical  
**Files**: `backend/app/core/database.py`, `backend/app/main.py`

**Problem**: `create_all()` on startup:
- Only creates tables, can't handle schema changes
- Causes "works on my machine" schema drift
- Conflicts with Alembic migrations

**Solution**:
1. **Remove from production**: `if not settings.is_production: await init_db()`
2. **Testing only**: Add flag `TESTING_AUTO_CREATE=true` for test environments
3. **CI enforcement**: Add step that fails if migrations are missing
4. **Documentation**: Update DEVELOPMENT.md with migration workflow

**Migration Workflow**:
```bash
# After changing models
alembic revision --autogenerate -m "description"
alembic upgrade head
# Commit migration file
```

**Estimated Effort**: 3-4 hours

---

## Phase 3: Observability & Testing (Week 2)

### H1: Fix Rate Limit Return Values
**Severity**: High  
**Files**: `backend/app/core/rate_limit.py`

**Problem**: `get_current_usage()` returns:
```python
{
    "minute": {"used": 45, "limit": 60, ...},      # Wrong limit (should be 60/120/300)
    "hour": {"used": 500, "limit": 3600, ...},     # Returns seconds!
    "day": {"used": 2000, "limit": 86400, ...}     # Returns seconds!
}
```

**Solution**:
```python
async def get_current_usage(self, request, enterprise_id=None, plan="pay_as_you_go"):
    config = TIER_LIMITS.get(plan, DEFAULT_LIMITS)
    
    return {
        "minute": {"used": minute_usage, "limit": config.requests_per_minute, ...},
        "hour": {"used": hour_usage, "limit": config.requests_per_hour, ...},
        "day": {"used": day_usage, "limit": config.requests_per_day, ...},
    }
```

**Estimated Effort**: 1-2 hours

---

### H2: Replace Placeholder Tests with Real Tests
**Severity**: High  
**Files**: `tests/unit/`, `tests/integration/`

**Current State**:
- `test_models.py`: MagicMock instead of real ORM instances
- `test_services.py`: `pytest.skip("placeholder")` on most tests
- `test_upload.py`: Tests constants, not upload flow
- `test_health.py`: All tests skipped
- No concurrent tests for quota

**Tests to Add**:

**Backend**:
1. **Upload Integration**: `test_upload_full_flow.py`
   - init → chunk[0] → chunk[1] → status → complete
   - Test Redis failure mid-upload (should still complete)
   - Test cancel cleanup

2. **Quota Concurrency**: `test_quota_concurrent.py`
   - Use `asyncio.gather()` or `threading` to simulate race
   - Verify quota never exceeded

3. **API Semantics**: `test_api_error_codes.py`
   - Each endpoint: invalid input → 400, not found → 404, quota → 429

4. **Encryption**: `test_encryption_roundtrip.py`
   - Encrypt → Decrypt with same key (success)
   - Decrypt with different key (clear error)

5. **Rate Limit Values**: `test_rate_limit_values.py`
   - Assert returned limits match TIER_LIMITS

**Estimated Effort**: 16-20 hours

---

### M1: Frontend Test Infrastructure
**Severity**: Medium  
**Files**: `frontend/package.json`, new test files

**Current State**: Zero tests. No test script in package.json.

**Setup**:
1. Install: `jest`, `@testing-library/react`, `@testing-library/user-event`, `msw` (mock service worker)
2. Configure: `jest.config.js`, `jest.setup.js`
3. Utilities: `frontend/src/test/utils.tsx` with render helpers
4. MSW handlers for API mocking

**First Tests**:
1. `api.test.ts`: Test API client error handling (401, 403, 500)
2. `dashboard.test.tsx`: Test loading states, error boundaries, data display
3. `enterprise/register.test.tsx`: Test form validation, submission, error display

**Estimated Effort**: 6-8 hours

---

## Phase 4: Maintainability (Week 2-3)

### M2: Codebase Cleanup
**Severity**: Medium

**Remove from repo**:
- `htmlcov/` - Add to .gitignore
- `.coverage` - Already in .gitignore, remove from index
- `backend/agenthire.db` - Add to .gitignore
- `*.log` files - Ensure in .gitignore
- `uploads/` - Create on startup, don't commit

**Cleanup commands**:
```bash
git rm -r --cached htmlcov/ .coverage backend/agenthire.db uploads/
echo "*.log" >> .gitignore
echo "uploads/" >> .gitignore
```

**Estimated Effort**: 1 hour

---

### M3: Frontend API Configuration
**Severity**: Medium  
**Files**: `frontend/next.config.ts`, `frontend/src/lib/api.ts`

**Problem**: Hardcoded `http://localhost:8000` in Next.js rewrites.

**Solution**:
```typescript
// frontend/src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**Environment documentation**:
- `.env.example`: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- README: Document production deployment needs real URL

**Estimated Effort**: 1-2 hours

---

## Implementation Schedule

### Week 1: Critical Data Integrity
| Day | Task | Owner | Deliverable |
|-----|------|-------|-------------|
| 1 | C1: Secret Key | TBD | PR with fixed key management |
| 1-2 | C2: Upload Consistency | TBD | PR with disk-first upload |
| 2-3 | C3: Quota Race | TBD | PR with row locking |
| 3-4 | C4: API Semantics | TBD | PR with proper HTTP codes |
| 4-5 | C5: Migrations | TBD | PR with create_all removed |

### Week 2: API Reliability & Testing
| Day | Task | Owner | Deliverable |
|-----|------|-------|-------------|
| 5-6 | H1: Rate Limit | TBD | PR with correct limits |
| 6-8 | H2: Real Tests | TBD | PR with 70%+ real coverage |
| 8-9 | M1: Frontend Tests | TBD | PR with test infrastructure |

### Week 3: Polish
| Day | Task | Owner | Deliverable |
|-----|------|-------|-------------|
| 10 | M2: Cleanup | TBD | Clean repo, no artifacts |
| 10 | M3: API Config | TBD | Environment-based config |
| 11-12 | Integration | TBD | Full regression testing |

---

## Testing Strategy

### Automated Tests Required
1. **Unit tests**: Individual function behavior (encryption, validation)
2. **Integration tests**: API endpoint to database flow
3. **Concurrent tests**: Multiple simultaneous requests (quota, race conditions)
4. **Resilience tests**: Redis failure, database locks

### Manual Verification
1. **Secret key**: Encrypt → Restart → Decrypt (cycle 3 times)
2. **Upload**: 1GB file upload, kill Redis mid-way, verify completion
3. **Quota**: Script to hammer API, verify hard stop at limit
4. **Error codes**: Use curl to verify 400/404/429 responses

---

## Success Criteria

- [ ] Encrypted data persists across 10 server restarts
- [ ] Upload completes successfully even with Redis disabled
- [ ] Quota never exceeds limit under concurrent load (test: 100 threads, quota 50)
- [ ] All error responses return correct HTTP status codes (verified by test suite)
- [ ] Test coverage >70% with real assertions (no mocks that don't verify behavior)
- [ ] Frontend test suite runs and passes
- [ ] No runtime artifacts in repository
- [ ] Production deployment uses explicit environment variables

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| C3 fix causes deadlock | Medium | High | Use timeouts on locks, monitor for lock waits |
| C2 changes break existing uploads | Medium | High | Feature flag, gradual rollout, extensive testing |
| C4 changes break frontend | High | High | Coordinate with frontend team, version API or update simultaneously |
| Test writing takes longer than expected | High | Medium | Prioritize critical path tests (upload, quota), defer edge cases |

---

## Related Documents

- Original code review: (attached to this plan)
- `DEVELOPMENT.md`: Update with migration workflow
- `.env.example`: Document all required environment variables
- `backend/app/core/security.py`: Encryption documentation
- `backend/app/core/rate_limit.py`: Rate limit tier documentation

---

**Next Step**: Begin Phase 1 with C1 (Secret Key) - smallest change, highest impact on development stability.
