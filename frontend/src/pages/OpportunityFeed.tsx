import { useOpportunities } from '@/hooks/useOpportunities'
import { OpportunityCard } from '@/components/OpportunityCard'
import { TriggerScraper } from '@/components/TriggerScraper'

function OpportunityFeed() {
  const { data: opportunities, isLoading } = useOpportunities()

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      {/* Show this only for admin/dev */}
      <TriggerScraper />
      
      {/* Rest of your opportunities */}
      {opportunities?.map(opp => (
        <OpportunityCard key={opp.id} opportunity={opp} />
      ))}
    </div>
  )
}

export { OpportunityFeed }
