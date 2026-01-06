# Product Gap Intelligence Platform

A platform that identifies product opportunities by analyzing social media posts, extracting insights using AI, and detecting trends through clustering and scoring algorithms.

## Features

- 🔍 **Multi-platform Scraping**: Reddit, Twitter/X, TikTok (coming soon)
- 🐦 **Twitter/X Integration**: Scrape via Nitter or manual input with pain signal detection
- 🤖 **AI-Powered Analysis**: Claude API integration for opportunity extraction
- 📊 **Trend Detection**: Clustering and scoring algorithms to identify high-confidence opportunities
- 🛒 **Competitor Analysis**: Amazon scraping for market research
- 📈 **Real-time Dashboard**: React-based frontend with opportunity feeds and detailed views

## Tech Stack

### Frontend
- React 19 + TypeScript
- Vite
- React Router
- TanStack Query
- Radix UI
- Supabase JS

### Backend
- Python 3.13
- Supabase Python Client
- Anthropic Claude API
- spaCy (NLP)
- BeautifulSoup (Web Scraping)

### Database
- Supabase (PostgreSQL)
- Edge Functions (Deno)

## Project Structure

```
product-browser/
├── frontend/          # React frontend application
├── backend/          # Python scrapers and workers
│   ├── scrapers/    # Social media scrapers
│   └── workers/      # AI analysis and processing
├── supabase/         # Database migrations and Edge Functions
└── docs/             # Documentation
```

## Getting Started

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.13+
- Supabase account
- Anthropic API key (for Claude)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd product-browser
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   pnpm install
   cp .env.example .env  # Add your Supabase credentials
   pnpm dev
   ```

3. **Backend Setup**
   ```bash
   cd backend/scrapers
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Install spaCy model
   python -m spacy download en_core_web_sm
   
   # Add environment variables
   cp .env.example .env  # Add Supabase and Anthropic API keys
   ```

4. **Database Setup**
   ```bash
   # Run migrations in Supabase dashboard SQL editor
   # Or use Supabase CLI:
   supabase db push
   ```

### Running the Pipeline

#### Option 1: MCP Reddit (Interactive - No API Keys Required)

Use Claude with mcp-reddit for interactive scraping:

```bash
# Install mcp-reddit
pip install mcp-reddit

# Add to Claude
claude mcp add reddit -- uvx mcp-reddit

# Then ask Claude:
# "Scrape the top 50 posts from r/SaaS"
# "Analyze pain points in r/Entrepreneur"
```

Import MCP data to Supabase:
```bash
cd backend/scrapers
python mcp_reddit_bridge.py --import --subreddit=SaaS
```

#### Option 2: PRAW (Automated - Requires Reddit API Keys)

For GitHub Actions automation:

```bash
cd backend/scrapers
python reddit_scraper.py --no-comments
```

Requires `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` from https://reddit.com/prefs/apps

#### Option 3: Twitter/X Scraping

```bash
cd backend/scrapers

# Quick add a single tweet
python twitter_scraper.py --add "https://x.com/user/status/123" "Tweet content here"

# Interactive mode
python twitter_scraper.py --manual

# Import from JSON file
python twitter_scraper.py --import-json tweets.json

# Nitter scraping (when instances available)
python twitter_scraper.py --default
python twitter_scraper.py --accounts=levelsio,nateliason
python twitter_scraper.py --search="someone should build"
```

#### Run Analysis Pipeline

```bash
cd backend/workers
python orchestrator.py
```

#### Trigger via Edge Function

```bash
curl -X POST 'https://your-project.supabase.co/functions/v1/trigger-scraper' \
  -H 'Authorization: Bearer YOUR_ANON_KEY'
```

## Environment Variables

### Frontend (`frontend/.env`)
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
```

### Backend (`backend/.env`)
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
ANTHROPIC_API_KEY=your_claude_api_key

# Reddit API (optional - for PRAW-based scraping)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

## Development

### Frontend Development
```bash
cd frontend
pnpm dev
```

### Backend Development
```bash
cd backend/scrapers
source venv/bin/activate
python reddit_scraper.py
```

## Deployment

### Frontend
Deploy to Vercel, Netlify, or any static hosting:
```bash
cd frontend
pnpm build
# Deploy dist/ folder
```

### Backend Workers
- Run as scheduled jobs (cron, GitHub Actions)
- Deploy to cloud functions (AWS Lambda, Google Cloud Functions)
- Trigger via Supabase Edge Functions

### Supabase Functions
```bash
supabase functions deploy trigger-scraper
```

## Documentation

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## License

MIT

