interface Opportunity {
  id: string
  [key: string]: unknown
}

interface OpportunityCardProps {
  opportunity: Opportunity
}

function OpportunityCard({ opportunity }: OpportunityCardProps) {
  return (
    <div>
      <pre>{JSON.stringify(opportunity, null, 2)}</pre>
    </div>
  )
}

export { OpportunityCard }
export type { Opportunity }

