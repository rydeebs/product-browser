import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useOpportunities } from '../hooks/useOpportunities'
import { 
  Home, Sparkles, PawPrint, Heart, Baby, UtensilsCrossed, 
  Cpu, Mountain, Search, SlidersHorizontal, ChevronLeft, ChevronRight 
} from 'lucide-react'
import { Progress } from '../components/ui/progress'
import { cn } from '../lib/utils'

const categories = [
  { id: 'all', name: 'All Opportunities', icon: Home },
  { id: 'new_invention', name: 'New Inventions', icon: Sparkles },
  { id: 'better_alternative', name: 'Better Alternatives', icon: Cpu },
  { id: 'cheaper_option', name: 'Cheaper Options', icon: Heart },
  { id: 'quality_improvement', name: 'Quality Improvements', icon: Mountain },
]

export function OpportunityFeed() {
  const [selectedCategory, setSelectedCategory] = useState('all')
  const { data: opportunities, isLoading, error } = useOpportunities()

  // Filter opportunities by category
  const filteredOpportunities = opportunities?.filter(opp => 
    selectedCategory === 'all' || opp.category === selectedCategory
  ) || []

  // Get category counts
  const getCategoryCount = (categoryId: string) => {
    if (categoryId === 'all') return opportunities?.length || 0
    return opportunities?.filter(o => o.category === categoryId).length || 0
  }

  // Featured opportunity (highest confidence)
  const featuredOpportunity = filteredOpportunities[0]
  
  // Rest of opportunities for carousel
  const carouselOpportunities = filteredOpportunities.slice(1)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0a0a0a] to-[#1a1a1a]">
        <div className="flex">
          <Sidebar 
            categories={categories}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            getCategoryCount={getCategoryCount}
          />
          <main className="flex-1 p-8">
            <div className="max-w-7xl mx-auto">
              <div className="animate-pulse space-y-8">
                <div className="h-12 bg-gray-800 rounded w-64"></div>
                <div className="h-96 bg-gray-800 rounded"></div>
              </div>
            </div>
          </main>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0a0a0a] to-[#1a1a1a] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg">Error loading opportunities</p>
          <p className="text-muted-foreground text-sm mt-2">{String(error)}</p>
        </div>
      </div>
    )
  }

  if (!opportunities || opportunities.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0a0a0a] to-[#1a1a1a]">
        <div className="flex">
          <Sidebar 
            categories={categories}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            getCategoryCount={getCategoryCount}
          />
          <main className="flex-1 p-8">
            <div className="max-w-7xl mx-auto">
              <EmptyState />
            </div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a0a0a] to-[#1a1a1a]">
      <div className="flex">
        <Sidebar 
          categories={categories}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
          getCategoryCount={getCategoryCount}
        />
        
        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="max-w-7xl mx-auto space-y-12">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-5xl md:text-6xl font-bold font-display bg-gradient-to-r from-white via-blue-400 to-[#444df6] bg-clip-text text-transparent">
                    Opportunity of the Day
                  </h1>
                  <p className="text-muted-foreground mt-2">
                    {filteredOpportunities.length} opportunities found
                  </p>
                </div>
                
                <div className="flex gap-3">
                  <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-gray-800/50 hover:bg-gray-800 transition-colors border border-gray-700">
                    <Search className="h-4 w-4" />
                    <span className="text-sm">Search</span>
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-gray-800/50 hover:bg-gray-800 transition-colors border border-gray-700">
                    <SlidersHorizontal className="h-4 w-4" />
                    <span className="text-sm">Filters</span>
                  </button>
                </div>
              </div>

              {/* Featured Opportunity */}
              {featuredOpportunity && (
                <FeaturedOpportunityCard opportunity={featuredOpportunity} />
              )}

              {/* Carousel */}
              {carouselOpportunities.length > 0 && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold font-serif">More Opportunities</h2>
                    <div className="flex gap-2">
                      <button className="p-2 rounded-md bg-gray-800/50 hover:bg-gray-800 transition-colors border border-gray-700">
                        <ChevronLeft className="h-4 w-4" />
                      </button>
                      <button className="p-2 rounded-md bg-gray-800/50 hover:bg-gray-800 transition-colors border border-gray-700">
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex gap-4 overflow-x-auto scrollbar-hide pb-4">
                    {carouselOpportunities.map((opp) => (
                      <OpportunityCard key={opp.id} opportunity={opp} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

// Sidebar Component
function Sidebar({ 
  categories, 
  selectedCategory, 
  onSelectCategory,
  getCategoryCount 
}: {
  categories: typeof categories
  selectedCategory: string
  onSelectCategory: (id: string) => void
  getCategoryCount: (id: string) => number
}) {
  return (
    <aside className="w-60 bg-[#0a0a0a] border-r border-gray-800 h-screen sticky top-0 overflow-y-auto">
      <div className="p-6">
        <div className="mb-8">
          <h2 className="text-xl font-bold font-display">Product Gap Intelligence</h2>
          <p className="text-xs text-muted-foreground mt-1">AI-powered opportunity detection</p>
        </div>
        
        <nav className="space-y-1">
          {categories.map((category) => {
            const Icon = category.icon
            const count = getCategoryCount(category.id)
            const isActive = selectedCategory === category.id
            
            return (
              <button
                key={category.id}
                onClick={() => onSelectCategory(category.id)}
                className={cn(
                  "w-full flex items-center justify-between px-4 py-2.5 rounded-md text-sm transition-all duration-300",
                  isActive 
                    ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg shadow-blue-500/20" 
                    : "text-muted-foreground hover:bg-gray-800/50 hover:text-white"
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4" />
                  <span>{category.name}</span>
                </div>
                <span className={cn(
                  "text-xs px-2 py-0.5 rounded-full",
                  isActive ? "bg-white/20" : "bg-gray-800"
                )}>
                  {count}
                </span>
              </button>
            )
          })}
        </nav>
      </div>
    </aside>
  )
}

// Featured Opportunity Card
function FeaturedOpportunityCard({ opportunity }: { opportunity: any }) {
  return (
    <Link 
      to={`/opportunity/${opportunity.id}`}
      className="block bg-[#1f1f1f] rounded-lg p-6 border border-gray-800 hover:-translate-y-1 hover:shadow-lg hover:shadow-blue-500/20 transition-all duration-300"
    >
      <div className="space-y-6">
        {/* Badges */}
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full px-3 py-1 text-xs font-medium border bg-blue-500/20 text-blue-400 border-blue-500/30">
            {opportunity.category.replace('_', ' ')}
          </span>
          <span className="rounded-full px-3 py-1 text-xs font-medium border bg-purple-500/20 text-purple-400 border-purple-500/30">
            Perfect Timing
          </span>
          <span className="rounded-full px-3 py-1 text-xs font-medium border bg-orange-500/20 text-orange-400 border-orange-500/30">
            Pain Level: {opportunity.pain_severity}/10
          </span>
        </div>

        {/* Title */}
        <h3 className="text-3xl font-bold font-serif leading-tight">
          {opportunity.title}
        </h3>

        {/* Problem Summary */}
        <p className="text-muted-foreground leading-relaxed">
          {opportunity.problem_summary}
        </p>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Confidence Score</span>
              <span className="font-semibold">{Math.round(Number(opportunity.confidence_score))}/100</span>
            </div>
            <Progress value={Number(opportunity.confidence_score)} gradientColor="#444df6" />
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Pain Severity</span>
              <span className="font-semibold">{opportunity.pain_severity}/10</span>
            </div>
            <Progress value={opportunity.pain_severity * 10} gradientColor="#f59e0b" />
          </div>
        </div>

        {/* Date */}
        <div className="text-xs text-muted-foreground">
          Detected {new Date(opportunity.detected_at).toLocaleDateString()}
        </div>
      </div>
    </Link>
  )
}

// Carousel Opportunity Card
function OpportunityCard({ opportunity }: { opportunity: any }) {
  return (
    <Link
      to={`/opportunity/${opportunity.id}`}
      className="flex-shrink-0 w-[380px] bg-[#1f1f1f] rounded-lg p-6 border border-gray-800 hover:-translate-y-1 hover:shadow-lg hover:shadow-blue-500/20 transition-all duration-300"
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full px-3 py-1 text-xs font-medium border bg-blue-500/20 text-blue-400 border-blue-500/30">
            {opportunity.category.replace('_', ' ')}
          </span>
        </div>

        <h4 className="text-xl font-semibold font-serif leading-tight line-clamp-2">
          {opportunity.title}
        </h4>

        <div className="space-y-3">
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Confidence</span>
              <span className="font-semibold">{Math.round(Number(opportunity.confidence_score))}/100</span>
            </div>
            <Progress value={Number(opportunity.confidence_score)} />
          </div>
          
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Pain Level</span>
              <span className="font-semibold">{opportunity.pain_severity}/10</span>
            </div>
            <Progress value={opportunity.pain_severity * 10} gradientColor="#f59e0b" />
          </div>
        </div>

        <div className="text-xs text-muted-foreground">
          {new Date(opportunity.detected_at).toLocaleDateString()}
        </div>
      </div>
    </Link>
  )
}

// Empty State
function EmptyState() {
  return (
    <div className="text-center py-24">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-500/10 mb-6">
        <Sparkles className="h-8 w-8 text-blue-400" />
      </div>
      <h3 className="text-2xl font-bold mb-2">No opportunities found yet</h3>
      <p className="text-muted-foreground mb-6">
        Run the scraper to discover product gaps from social media
      </p>
      <button className="px-6 py-3 rounded-md bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 transition-all text-white font-medium">
        Trigger Scraper Now
      </button>
    </div>
  )
}
