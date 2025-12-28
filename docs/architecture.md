# Product Gap Intelligence Platform - Architecture

## Overview

This platform identifies product opportunities by analyzing social media posts, extracting insights using AI, and detecting trends through clustering and scoring algorithms.

## Architecture Components

### Frontend (React + TypeScript + Vite)

- **Location**: `frontend/`
- **Tech Stack**:
  - React 19
  - TypeScript
  - Vite
  - React Router
  - TanStack Query (React Query)
  - Radix UI components
  - Supabase JS client

- **Structure**:
  - `src/pages/` - Page components (OpportunityFeed, OpportunityDetail, Login)
  - `src/components/` - Reusable components (OpportunityCard, OpportunityTable, EvidenceSection)
  - `src/hooks/` - Custom React hooks (useOpportunities, useAuth)
  - `src/lib/` - Utilities and Supabase client

### Backend

#### Scrapers (`backend/scrapers/`)

- **reddit_scraper.py**: Scrapes Reddit posts using JSON API
- **twitter_scraper.py**: (To be implemented) Twitter/X scraping
- **tiktok_scraper.py**: (To be implemented) TikTok scraping
- **db_client.py**: Supabase Python client for database operations

#### Workers (`backend/workers/`)

- **ai_analyzer.py**: Uses Claude API to analyze posts and extract opportunities
- **nlp_processor.py**: spaCy-based keyword extraction and entity recognition
- **trend_detector.py**: Clustering and scoring algorithms for trend detection
- **amazon_scraper.py**: Competitor analysis by scraping Amazon
- **orchestrator.py**: Main pipeline orchestrator that runs the full workflow

### Database (Supabase PostgreSQL)

#### Tables

1. **raw_posts**: Stores scraped social media posts
   - Platform, content, metrics, URLs
   - Deduplication via content_hash
   - Processing status tracking

2. **opportunities**: Identified product opportunities
   - Title, description, keywords
   - Confidence and trend scores
   - Evidence count

3. **evidence**: Links posts to opportunities
   - Many-to-many relationship
   - Supports opportunity validation

### Supabase Edge Functions

- **trigger-scraper**: Deno-based Edge Function that triggers scraping
  - Can be called via HTTP or scheduled
  - Handles CORS and authentication

## Data Flow

1. **Scraping Phase**
   - Scrapers collect posts from social media platforms
   - Posts saved to `raw_posts` table with `processed = false`

2. **Analysis Phase**
   - Orchestrator fetches unprocessed posts
   - AI analyzer extracts opportunities from posts
   - NLP processor extracts keywords and entities

3. **Trend Detection Phase**
   - Opportunities are clustered by similarity
   - Confidence scores calculated based on evidence
   - Trend scores calculated based on frequency

4. **Storage Phase**
   - Opportunities saved to `opportunities` table
   - Evidence links created in `evidence` table
   - Posts marked as `processed = true`

5. **Frontend Display**
   - React Query hooks fetch opportunities
   - Opportunities displayed with confidence scores
   - Evidence sections show supporting posts

## Environment Variables

### Frontend (`.env`)
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
```

### Backend (`backend/.env`)
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
ANTHROPIC_API_KEY=your_claude_api_key
```

## Deployment

### Frontend
```bash
cd frontend
pnpm install
pnpm build
# Deploy to Vercel, Netlify, etc.
```

### Backend Workers
- Can run locally: `python backend/workers/orchestrator.py`
- Can be deployed as scheduled jobs (cron, GitHub Actions, etc.)
- Can be triggered via Supabase Edge Functions

### Supabase Functions
```bash
supabase functions deploy trigger-scraper
```

## Future Enhancements

- [ ] Twitter/X scraper implementation
- [ ] TikTok scraper implementation
- [ ] Real-time opportunity notifications
- [ ] User authentication and personalized feeds
- [ ] Advanced trend analysis with time-series data
- [ ] Competitor price tracking
- [ ] Market size estimation

