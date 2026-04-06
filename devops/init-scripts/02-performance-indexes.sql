-- ============================================================
-- AgentHire Performance Indexes
-- Phase 8: Performance & Scaling
--
-- This script adds indexes to optimize common queries,
-- particularly for the Discovery API.
-- ============================================================

-- Index for job discovery by city (extracted from JSONB location)
-- This accelerates the ilike query on location->>'city'
CREATE INDEX IF NOT EXISTS idx_job_postings_city
ON job_postings ((location->>'city'))
WHERE location IS NOT NULL;

-- Index for job discovery with status and city combined
-- Useful for queries filtering by both status and city
CREATE INDEX IF NOT EXISTS idx_job_postings_status_city
ON job_postings (status, (location->>'city'))
WHERE status = 'active';

-- Composite index for seeker discovery
-- Accelerates status filter + ordering by last_active_at
CREATE INDEX IF NOT EXISTS idx_seeker_profiles_status_active
ON seeker_profiles (status, last_active_at DESC)
WHERE status = 'active';

-- Index for billing records lookup by enterprise and date range
-- Optimizes billing queries
CREATE INDEX IF NOT EXISTS idx_billing_records_enterprise_date
ON billing_records (enterprise_id, created_at DESC);

-- Index for API key lookup by enterprise (active keys only)
-- Optimizes API authentication
CREATE INDEX IF NOT EXISTS idx_enterprise_api_keys_enterprise_active
ON enterprise_api_keys (enterprise_id, status, created_at DESC)
WHERE status = 'active';

-- Index for resume_files by profile and current version
-- Optimizes getting current resume for a profile
CREATE INDEX IF NOT EXISTS idx_resume_files_profile_current
ON resume_files (profile_id, is_current DESC)
WHERE is_current = true;

-- Index for job_matches by seeker and status (pending matches)
-- Optimizes finding pending matches for a seeker
CREATE INDEX IF NOT EXISTS idx_job_matches_seeker_pending
ON job_matches (seeker_id, status, created_at DESC)
WHERE status = 'pending';

-- Index for job_matches by job and status (pending matches)
-- Optimizes finding pending matches for a job
CREATE INDEX IF NOT EXISTS idx_job_matches_job_pending
ON job_matches (job_id, status, created_at DESC)
WHERE status = 'pending';

-- Index for audit logs by table and time
-- Optimizes audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_time
ON audit_logs (table_name, changed_at DESC);

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'Performance indexes created successfully!';
END $$;
