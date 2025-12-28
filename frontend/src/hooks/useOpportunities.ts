import { useQuery } from '@tanstack/react-query'

import { supabase } from '@/lib/supabase'

export function useOpportunities() {
  return useQuery({
    queryKey: ['opportunities'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('opportunities')
        .select('*')
        .order('confidence_score', { ascending: false })
        .limit(20)
      
      if (error) throw error
      return data
    }
  })
}

