import { useOpportunities } from '../hooks/useOpportunities'
import { Link } from 'react-router-dom'

export function OpportunityFeed() {
  const { data: opportunities, isLoading, error } = useOpportunities()
  
  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading opportunities...</p>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading opportunities</p>
        <p className="text-sm text-gray-500 mt-2">{String(error)}</p>
      </div>
    )
  }
  
  if (!opportunities || opportunities.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No opportunities found yet.</p>
        <p className="text-sm text-gray-500 mt-2">Run the scraper to collect data!</p>
      </div>
    )
  }
  
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          {opportunities.length} Opportunities Found
        </h2>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {opportunities.map((opp) => (
          <Link
            key={opp.id}
            to={`/opportunity/${opp.id}`}
            className="block bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <span className="inline-block px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 mb-2">
                  {opp.category}
                </span>
                <h3 className="text-lg font-semibold text-gray-900 leading-tight">
                  {opp.title}
                </h3>
              </div>
            </div>
            
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Confidence</span>
                <span className="font-semibold text-gray-900">
                  {Math.round(Number(opp.confidence_score))}/100
                </span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Pain Severity</span>
                <span className="font-semibold text-gray-900">
                  {opp.pain_severity}/10
                </span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${Number(opp.confidence_score)}%` }}
                />
              </div>
            </div>
            
            <div className="mt-4 text-xs text-gray-500">
              Detected {new Date(opp.detected_at).toLocaleDateString()}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
