-- ============================================
-- Daily Pulse PK: Supabase Database Schema
-- Copy and paste this into Supabase SQL Editor
-- ============================================

-- 1. Posts Table (every post made across all platforms)
CREATE TABLE IF NOT EXISTS posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    platform TEXT NOT NULL,          -- 'telegram', 'twitter', 'reddit'
    content TEXT NOT NULL,
    image_path TEXT DEFAULT '',
    status TEXT DEFAULT 'posted',    -- 'posted', 'failed', 'scheduled'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Alerts Table (dashboard notifications)
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    level TEXT NOT NULL,             -- 'INFO', 'WARNING', 'CRITICAL'
    module TEXT NOT NULL,            -- Which module raised the alert
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Metrics Table (subscriber counts, daily stats)
CREATE TABLE IF NOT EXISTS metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    metric_name TEXT NOT NULL,       -- 'subscriber_count', 'posts_today', etc.
    value FLOAT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Error Logs Table (self-healing tracking)
CREATE TABLE IF NOT EXISTS error_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    module TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    auto_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================
-- Indexes for fast dashboard queries
-- ============================================
CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(resolved, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_errors_module ON error_logs(module, created_at DESC);

-- ============================================
-- Row Level Security (RLS) - Enable for safety
-- ============================================
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

-- Allow the anon key to read/write (since this is a private bot)
CREATE POLICY "Allow all for anon" ON posts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON alerts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON metrics FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON error_logs FOR ALL USING (true) WITH CHECK (true);
