import { useOpportunities } from '@/hooks/useOpportunities'
import { formatDate, formatNumber } from '@/lib/utils'
import { Link } from 'react-router-dom'

function OpportunityTable() {
  const { data: opportunities, isLoading } = useOpportunities()

  if (isLoading) return <div>Loading...</div>

  return (
    <table className="opportunity-table">
      <thead>
        <tr>
          <th>Title</th>
          <th>Confidence</th>
          <th>Trend Score</th>
          <th>Created</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {opportunities?.map(opp => (
          <tr key={opp.id}>
            <td>{opp.title}</td>
            <td>{opp.confidence_score}%</td>
            <td>{formatNumber(opp.trend_score || 0)}</td>
            <td>{formatDate(opp.created_at)}</td>
            <td>
              <Link to={`/opportunities/${opp.id}`}>View</Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export { OpportunityTable }

