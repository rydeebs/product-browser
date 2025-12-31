-- Additional tables for product gap intelligence platform
-- Uses IF NOT EXISTS to safely run even if tables already exist

-- competitors (Amazon products)
CREATE TABLE IF NOT EXISTS competitors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
  asin TEXT,
  title TEXT NOT NULL,
  price NUMERIC,
  rating NUMERIC,
  review_count INTEGER,
  url TEXT,
  image_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_competitors_opportunity ON competitors(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_competitors_asin ON competitors(asin);

-- market_data (TAM, search volume)
CREATE TABLE IF NOT EXISTS market_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
  tam_estimate NUMERIC,
  search_volume INTEGER,
  search_trend TEXT,
  yoy_growth NUMERIC,
  data_source TEXT,
  fetched_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_data_opportunity ON market_data(opportunity_id);

-- community_signals (Reddit quotes, YouTube mentions)
CREATE TABLE IF NOT EXISTS community_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  signal_type TEXT,
  content TEXT,
  url TEXT,
  engagement_score INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_community_signals_opportunity ON community_signals(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_community_signals_platform ON community_signals(platform);

-- scraper_metadata (track last_run_at for incremental scraping)
CREATE TABLE IF NOT EXISTS scraper_metadata (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scraper_name TEXT UNIQUE NOT NULL,
  last_run_at TIMESTAMPTZ,
  last_success_at TIMESTAMPTZ,
  records_processed INTEGER DEFAULT 0,
  status TEXT DEFAULT 'idle',
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scraper_metadata_name ON scraper_metadata(scraper_name);

-- Trigger for scraper_metadata updated_at
DROP TRIGGER IF EXISTS update_scraper_metadata_updated_at ON scraper_metadata;
CREATE TRIGGER update_scraper_metadata_updated_at
  BEFORE UPDATE ON scraper_metadata
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

