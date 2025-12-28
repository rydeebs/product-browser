import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Simple hash function (no MD5 dependency needed)
function simpleHash(str: string): string {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36)
}

interface RedditPost {
  data: {
    title: string
    selftext: string
    score: number
    num_comments: number
    created_utc: number
    permalink: string
    id: string
    author: string
    subreddit: string
  }
}

interface RedditResponse {
  data: {
    children: RedditPost[]
  }
}

async function scrapeReddit(subreddit: string): Promise<any[]> {
  const url = `https://www.reddit.com/r/${subreddit}/hot.json?limit=25`
  
  console.log(`Fetching r/${subreddit}...`)
  
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
      }
    })

    if (!response.ok) {
      console.error(`Failed to fetch r/${subreddit}: ${response.status} ${response.statusText}`)
      return []
    }

    const data: RedditResponse = await response.json()
    const posts = data.data.children

    console.log(`✓ Fetched ${posts.length} posts from r/${subreddit}`)

    return posts.map(post => {
      const p = post.data
      const content = p.title + (p.selftext ? '\n' + p.selftext : '')
      const contentHash = simpleHash(`${p.id}${p.title}`)

      return {
        platform: 'reddit',
        post_id: `reddit_${p.id}`,
        content: p.title,
        author: p.author,
        url: `https://www.reddit.com${p.permalink}`,
        metrics: {
          upvotes: p.score,
          comments: p.num_comments,
          created_utc: p.created_utc
        },
        content_hash: contentHash,
        scraped_at: new Date().toISOString(),
        processed: false
      }
    })
  } catch (error: any) {
    console.error(`Error scraping r/${subreddit}:`, error.message)
    return []
  }
}

serve(async (req) => {
  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Subreddits to scrape
    const subreddits = [
      'dogs',
      'HomeImprovement', 
      'BuyItForLife',
      'shutupandtakemymoney',
      'DidntKnowIWantedThat',
      'homegym',
      'Cooking'
    ]

    let allPosts: any[] = []

    // Scrape each subreddit with delay between requests
    for (const subreddit of subreddits) {
      const posts = await scrapeReddit(subreddit)
      allPosts = allPosts.concat(posts)
      
      // Wait 2 seconds between subreddit requests to avoid rate limiting
      if (subreddits.indexOf(subreddit) < subreddits.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 2000))
      }
    }

    console.log(`Total posts scraped: ${allPosts.length}`)

    if (allPosts.length === 0) {
      return new Response(JSON.stringify({ 
        success: true, 
        postsSaved: 0,
        message: 'No posts scraped - check logs for errors'
      }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Save to Supabase (upsert to handle duplicates)
    const { data, error } = await supabase
      .from('raw_posts')
      .upsert(allPosts, { 
        onConflict: 'post_id',
        ignoreDuplicates: false 
      })
      .select()

    if (error) {
      console.error('Database error:', error)
      throw error
    }

    console.log(`✅ Saved ${data?.length || 0} posts to database`)

    return new Response(JSON.stringify({
      success: true,
      postsSaved: data?.length || 0,
      totalScraped: allPosts.length,
      subreddits: subreddits.length
    }), {
      headers: { 'Content-Type': 'application/json' }
    })

  } catch (error: any) {
    console.error('Error in trigger-scraper:', error)
    
    return new Response(JSON.stringify({ 
      error: error.message,
      stack: error.stack 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
})
