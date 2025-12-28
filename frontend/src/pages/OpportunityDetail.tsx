import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { EvidenceSection } from '@/components/EvidenceSection'
import { formatDate, formatNumber } from '@/lib/utils'

function OpportunityDetail() {
  const { id } = useParams<{ id: string }>()
  
  const { data: opportunity, isLoading } = useQuery({
    queryKey: ['opportunity', id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('opportunities')
        .select('*')
        .eq('id', id)
        .single()
      
      if (error) throw error
      return data
    },
    enabled: !!id
  })

  if (isLoading) return <div>Loading...</div>
  if (!opportunity) return <div>Opportunity not found</div>

  return (
    <div className="opportunity-detail">
      <h1>{opportunity.title}</h1>
      <div className="metadata">
        <span>Confidence: {opportunity.confidence_score}%</span>
        <span>Created: {formatDate(opportunity.created_at)}</span>
      </div>
      <div className="description">
        <p>{opportunity.description}</p>
      </div>
      <EvidenceSection opportunityId={opportunity.id} />
    </div>
  )
}

export { OpportunityDetail }

