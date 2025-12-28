import { useQuery } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { formatDate } from '@/lib/utils'

interface EvidenceSectionProps {
  opportunityId: string
}

function EvidenceSection({ opportunityId }: EvidenceSectionProps) {
  const { data: evidence, isLoading } = useQuery({
    queryKey: ['evidence', opportunityId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('evidence')
        .select('*')
        .eq('opportunity_id', opportunityId)
        .order('created_at', { ascending: false })
      
      if (error) throw error
      return data
    }
  })

  if (isLoading) return <div>Loading evidence...</div>
  if (!evidence || evidence.length === 0) return <div>No evidence found</div>

  return (
    <div className="evidence-section">
      <h2>Supporting Evidence</h2>
      <div className="evidence-list">
        {evidence.map(ev => (
          <div key={ev.id} className="evidence-item">
            <div className="evidence-header">
              <span className="platform">{ev.platform}</span>
              <span className="date">{formatDate(ev.created_at)}</span>
            </div>
            <p className="evidence-content">{ev.content}</p>
            {ev.url && (
              <a href={ev.url} target="_blank" rel="noopener noreferrer">
                View Source
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export { EvidenceSection }

