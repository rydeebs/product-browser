'use client'

import { useQuery } from '@tanstack/react-query'
import { supabase, type Opportunity } from '@/lib/supabase'

// Types for pagination and filtering
export interface OpportunityFilters {
  page?: number
  limit?: number
  category?: string
  confidenceMin?: number
  painSeverityMin?: number
  sortBy?: 'confidence_score' | 'pain_severity' | 'created_at' | 'detected_at'
  sortOrder?: 'asc' | 'desc'
  search?: string
}

export interface PaginatedOpportunities {
  opportunities: Opportunity[]
  total: number
  page: number
  limit: number
  totalPages: number
}

// Enhanced hook with pagination and filtering
export function useOpportunities(filters?: OpportunityFilters) {
  const {
    page = 1,
    limit = 20,
    category,
    confidenceMin,
    painSeverityMin,
    sortBy = 'confidence_score',
    sortOrder = 'desc',
    search,
  } = filters || {}

  return useQuery({
    queryKey: ['opportunities', { page, limit, category, confidenceMin, painSeverityMin, sortBy, sortOrder, search }],
    queryFn: async (): Promise<PaginatedOpportunities> => {
      // Build query with count
      let query = supabase
        .from('opportunities')
        .select('*', { count: 'exact' })

      // Apply filters
      if (category && category !== 'all') {
        query = query.eq('category', category)
      }
      
      if (confidenceMin !== undefined) {
        query = query.gte('confidence_score', confidenceMin)
      }
      
      if (painSeverityMin !== undefined) {
        query = query.gte('pain_severity', painSeverityMin)
      }
      
      if (search) {
        query = query.or(`title.ilike.%${search}%,problem_summary.ilike.%${search}%`)
      }

      // Apply sorting
      query = query.order(sortBy, { ascending: sortOrder === 'asc' })

      // Apply pagination
      const from = (page - 1) * limit
      const to = from + limit - 1
      query = query.range(from, to)

      const { data, error, count } = await query

      if (error) throw error

      return {
        opportunities: data as Opportunity[],
        total: count || 0,
        page,
        limit,
        totalPages: Math.ceil((count || 0) / limit),
      }
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Simple hook for fetching all opportunities (backwards compatible)
export function useAllOpportunities() {
  return useQuery({
    queryKey: ['all-opportunities'],
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
