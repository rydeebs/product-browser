import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Type definitions matching your database
export interface Opportunity {
  id: number
  title: string
  problem_summary: string
  category: string
  confidence_score: number
  pain_severity: number
  growth_pattern: string | null
  timing_score: number | null
  recommended_product: string | null
  detected_at: string
  status: string
}

export interface Evidence {
  id: number
  opportunity_id: number
  raw_post_id: number
  signal_type: string
  weight: number
  raw_posts?: RawPost
}

export interface RawPost {
  id: number
  platform: string
  post_id: string
  content: string
  author: string
  url: string
  metrics: {
    upvotes: number
    comments: number
  }
  scraped_at: string
  processed: boolean
}
