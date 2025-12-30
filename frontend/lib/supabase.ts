import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Type definitions matching your database
export interface Opportunity {
  id: string // UUID
  title: string
  description?: string
  problem_summary: string
  keywords?: string[]
  category: string
  confidence_score: number
  trend_score?: number
  pain_severity: number
  growth_pattern: string | null
  timing_score: number | null
  evidence_count?: number
  status: string
  detected_at: string
  created_at: string
  updated_at: string
}

export interface Evidence {
  id: string // UUID
  opportunity_id: string
  post_id?: string
  raw_post_id: string
  content?: string
  signal_type: string
  weight: number
  created_at: string
  raw_posts?: RawPost
}

export interface RawPost {
  id: string // UUID
  platform: string
  post_id: string
  content: string
  author: string | null
  url: string
  metrics: {
    upvotes?: number
    comments?: number
  }
  content_hash: string
  scraped_at: string
  processed: boolean
  created_at: string
}
