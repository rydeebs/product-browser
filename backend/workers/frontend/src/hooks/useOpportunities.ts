import { useQuery } from '@tanstack/react-query'

import { supabase } from '../lib/supabase'
import type { Opportunity } from '../lib/supabase'

export function useOpportunities() {
  return useQuery({
    queryKey: ['opportunities'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('opportunities')
        .select('*')
        .order('confidence_score', { ascending: false })
      
      if (error) throw error
      return data as Opportunity[]
    }
  })
}

export function useOpportunityDetail(id: number) {
  return useQuery({
    queryKey: ['opportunity', id],
    queryFn: async () => {
      // Get opportunity
      const { data: opp, error: oppError } = await supabase
        .from('opportunities')
        .select('*')
        .eq('id', id)
        .single()
      
      if (oppError) throw oppError
      
      // Get evidence with raw posts
      const { data: evidence, error: evidenceError } = await supabase
        .from('evidence')
        .select(`
          *,
          raw_posts (*)
        `)
        .eq('opportunity_id', id)
      
      if (evidenceError) throw evidenceError
      
      return {
        opportunity: opp as Opportunity,
        evidence: evidence || []
      }
    }
  })
}
