import { useParams, Link } from 'react-router-dom'
import { useOpportunityDetail } from '../hooks/useOpportunities'

export function OpportunityDetail() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, error } = useOpportunityDetail(Number(id))
  
  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading...</p>
      </div>
    )
  }
  
  if (error || !data) {
    return (
      <div className="text-center py-12 text-red-600">
        Error loading opportunity
      </div>
    )
  }
  
  const { opportunity, evidence } = data
  
  return (
    <div>
      <Link to="/" className="text-blue-600 hover:text-blue-800 mb-6 inline-block">
        ← Back to opportunities
      </Link>
      
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="mb-6">
          <span className="inline-block px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-800 mb-3">
            {opportunity.category}
          </span>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {opportunity.title}
          </h1>
          
          <div className="flex gap-6 text-sm">
            <div>
              <span className="text-gray-600">Confidence:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {Math.round(Number(opportunity.confidence_score))}/100
              </span>
            </div>
            <div>
              <span className="text-gray-600">Pain Severity:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {opportunity.pain_severity}/10
              </span>
            </div>
          </div>
        </div>
        
        <div className="border-t pt-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Problem Summary
          </h2>
          <p className="text-gray-700">
            {opportunity.problem_summary}
          </p>
        </div>
        
        <div className="border-t pt-6 mt-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Evidence ({evidence.length} posts)
          </h2>
          
          {evidence.length === 0 ? (
            <p className="text-gray-500">No evidence posts found.</p>
          ) : (
            <div className="space-y-4">
              {evidence.map((e: any) => (
                <div key={e.id} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-xs font-medium text-gray-500 uppercase">
                      {e.raw_posts?.platform || 'unknown'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {e.raw_posts?.metrics?.upvotes || 0} upvotes, {e.raw_posts?.metrics?.comments || 0} comments
                    </span>
                  </div>
                  <p className="text-gray-800">
                    "{e.raw_posts?.content || 'Content not available'}"
                  </p>
                  {e.raw_posts?.url && (
                    <a
                      href={e.raw_posts.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800 mt-2 inline-block"
                    >
                      View original post →
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
