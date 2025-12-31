-- Initial schema for product gap intelligence platform

-- Raw posts table (scraped content)
CREATE TABLE IF NOT EXISTS raw_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform TEXT NOT NULL,
  post_id TEXT NOT NULL,
  content TEXT NOT NULL,
  author TEXT,
  url TEXT NOT NULL,
  metrics JSONB DEFAULT '{}',
  content_hash TEXT UNIQUE NOT NULL,
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  processed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_raw_posts_processed ON raw_posts(processed);
CREATE INDEX idx_raw_posts_platform ON raw_posts(platform);
CREATE INDEX idx_raw_posts_content_hash ON raw_posts(content_hash);

-- Opportunities table (identified product opportunities)
CREATE TABLE IF NOT EXISTS opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  problem_summary TEXT,
  keywords TEXT[],
  category TEXT,
  confidence_score INTEGER DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 100),
  trend_score INTEGER DEFAULT 0,
  pain_severity INTEGER DEFAULT 0 CHECK (pain_severity >= 0 AND pain_severity <= 10),
  growth_pattern TEXT DEFAULT 'regular',
  timing_score INTEGER DEFAULT 0 CHECK (timing_score >= 0 AND timing_score <= 10),
  evidence_count INTEGER DEFAULT 0,
  status TEXT DEFAULT 'active',
  detected_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_opportunities_confidence ON opportunities(confidence_score DESC);
CREATE INDEX idx_opportunities_trend ON opportunities(trend_score DESC);
CREATE INDEX idx_opportunities_created ON opportunities(created_at DESC);

-- Evidence table (links posts to opportunities)
CREATE TABLE IF NOT EXISTS evidence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
  post_id UUID REFERENCES raw_posts(id) ON DELETE CASCADE,
  raw_post_id UUID REFERENCES raw_posts(id) ON DELETE CASCADE,
  content TEXT,
  signal_type TEXT,
  weight NUMERIC DEFAULT 1.0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evidence_opportunity ON evidence(opportunity_id);
CREATE INDEX idx_evidence_post ON evidence(post_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_opportunities_updated_at
  BEFORE UPDATE ON opportunities
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Post analysis table (AI analysis results)
CREATE TABLE IF NOT EXISTS post_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_post_id UUID REFERENCES raw_posts(id) ON DELETE CASCADE,
  problem_summary TEXT,
  pain_severity INTEGER DEFAULT 0 CHECK (pain_severity >= 0 AND pain_severity <= 10),
  willingness_to_pay BOOLEAN DEFAULT FALSE,
  product_category TEXT,
  keywords TEXT[],
  analyzed_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_post_analysis_raw_post ON post_analysis(raw_post_id);
CREATE INDEX idx_post_analysis_pain_severity ON post_analysis(pain_severity DESC);
CREATE INDEX idx_post_analysis_category ON post_analysis(product_category);

