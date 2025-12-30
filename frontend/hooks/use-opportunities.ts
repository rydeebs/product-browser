'use client'

import { useQuery } from '@tanstack/react-query'
import { supabase, type Opportunity } from '@/lib/supabase'

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
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useOpportunityDetail(id: string) {
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
    },
    enabled: !!id,
  })
}

export function useOpportunityCounts() {
  return useQuery({
    queryKey: ['opportunity-counts'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('opportunities')
        .select('category')
      
      if (error) throw error
      
      const counts: Record<string, number> = {
        total: data.length,
      }
      
      data.forEach(opp => {
        counts[opp.category] = (counts[opp.category] || 0) + 1
      })
      
      return counts
    },
  })
}
