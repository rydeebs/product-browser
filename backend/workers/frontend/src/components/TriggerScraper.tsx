import { supabase } from '@/lib/supabase'
import { useState } from 'react'

export function TriggerScraper() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleTrigger = async () => {
    setLoading(true)
    setResult(null)

    try {
      const { data, error } = await supabase.functions.invoke('trigger-scraper')

      if (error) {
        setResult(`Error: ${error.message}`)
      } else {
        setResult(`Success! Scraped ${data.postsSaved || 0} posts`)
      }
    } catch (err: any) {
      setResult(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="font-semibold mb-2">Manual Scraper Trigger</h3>
      <button
        onClick={handleTrigger}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Scraping...' : 'Run Scraper Now'}
      </button>
      {result && (
        <p className={`mt-2 text-sm ${result.includes('Error') ? 'text-red-600' : 'text-green-600'}`}>
          {result}
        </p>
      )}
    </div>
  )
}

