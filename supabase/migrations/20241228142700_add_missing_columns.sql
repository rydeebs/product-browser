-- Add missing columns to existing tables
-- Run this if you already have the base schema

-- Add missing columns to opportunities table
ALTER TABLE opportunities 
ADD COLUMN IF NOT EXISTS problem_summary TEXT,
ADD COLUMN IF NOT EXISTS category TEXT,
ADD COLUMN IF NOT EXISTS pain_severity INTEGER DEFAULT 0 CHECK (pain_severity >= 0 AND pain_severity <= 10),
ADD COLUMN IF NOT EXISTS growth_pattern TEXT DEFAULT 'regular',
ADD COLUMN IF NOT EXISTS timing_score INTEGER DEFAULT 0 CHECK (timing_score >= 0 AND timing_score <= 10),
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active',
ADD COLUMN IF NOT EXISTS detected_at TIMESTAMPTZ;

-- Ensure trend_score exists (in case it was missing)
ALTER TABLE opportunities 
ADD COLUMN IF NOT EXISTS trend_score INTEGER DEFAULT 0;

-- Add missing columns to evidence table
-- Note: Keep post_id for backward compatibility, but use raw_post_id going forward
ALTER TABLE evidence
ADD COLUMN IF NOT EXISTS raw_post_id UUID REFERENCES raw_posts(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS signal_type TEXT,
ADD COLUMN IF NOT EXISTS weight NUMERIC DEFAULT 1.0;

-- If post_id doesn't exist, add it for backward compatibility
ALTER TABLE evidence
ADD COLUMN IF NOT EXISTS post_id UUID REFERENCES raw_posts(id) ON DELETE CASCADE;

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_opportunities_pain_severity ON opportunities(pain_severity DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_category ON opportunities(category);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_evidence_raw_post ON evidence(raw_post_id);

