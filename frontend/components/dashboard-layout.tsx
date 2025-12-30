"use client"

import { useState, useRef, useEffect, useCallback, useMemo } from "react"
import Link from "next/link"
import {
  Search,
  Filter,
  Home,
  Heart,
  Activity,
  Baby,
  Utensils,
  Cpu,
  Mountain,
  Layers,
  TrendingUp,
  Users,
  Target,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Compass,
  Settings,
  Loader2,
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { useOpportunities, useOpportunityCounts } from "@/hooks/use-opportunities"

const categoryConfig = [
  { id: "all", name: "All Opportunities", icon: Layers, dbCategory: null },
  { id: "home", name: "Home & Living", icon: Home, dbCategory: "Home & Living" },
  { id: "pets", name: "Pets & Animals", icon: Heart, dbCategory: "Pets & Animals" },
  { id: "health", name: "Health & Fitness", icon: Activity, dbCategory: "Health & Fitness" },
  { id: "baby", name: "Baby & Parenting", icon: Baby, dbCategory: "Baby & Parenting" },
  { id: "food", name: "Food & Cooking", icon: Utensils, dbCategory: "Food & Cooking" },
  { id: "tech", name: "Tech & Gadgets", icon: Cpu, dbCategory: "Tech & Gadgets" },
  { id: "outdoor", name: "Outdoor & Sports", icon: Mountain, dbCategory: "Outdoor & Sports" },
]

const opportunities = [
  {
    id: 1,
    title: "Smart Home Energy Management for Renters",
    category: "Home & Living",
    timing: "Q1 2025",
    painLevel: "High",
    summary:
      "Renters struggle to optimize energy usage without installing permanent smart home devices. Current solutions require landlord approval or leave no trace upon move-out.",
    confidence: 87,
    painSeverity: 8.5,
    dateDetected: "Dec 15, 2024",
    badges: ["home", "trending", "high-pain"],
  },
  {
    id: 2,
    title: "Pet Anxiety Monitoring During Owner Absence",
    category: "Pets & Animals",
    timing: "Q2 2025",
    painLevel: "Medium",
    summary:
      "Pet owners experience guilt and worry about their pets when away. Traditional cameras show behavior but don't provide actionable insights or real-time anxiety alerts.",
    confidence: 73,
    painSeverity: 7.2,
    dateDetected: "Dec 12, 2024",
    badges: ["pets", "wellness", "medium-pain"],
  },
  {
    id: 3,
    title: "Personalized Meal Planning for Dietary Restrictions",
    category: "Food & Cooking",
    timing: "Q1 2025",
    painLevel: "High",
    summary:
      "People with multiple dietary restrictions spend hours planning meals that meet all requirements. Generic meal plans fail to account for taste preferences and local ingredient availability.",
    confidence: 91,
    painSeverity: 8.8,
    dateDetected: "Dec 10, 2024",
    badges: ["food", "ai-ready", "high-pain"],
  },
  {
    id: 4,
    title: "Baby Sleep Pattern Analytics for New Parents",
    category: "Baby & Parenting",
    timing: "Q3 2025",
    painLevel: "High",
    summary:
      "New parents struggle to identify sleep pattern issues and receive conflicting advice from various sources. Manual sleep tracking is unreliable during exhaustion.",
    confidence: 82,
    painSeverity: 9.1,
    dateDetected: "Dec 8, 2024",
    badges: ["baby", "urgent", "high-pain"],
  },
  {
    id: 5,
    title: "Workout Form Correction Without Personal Trainer",
    category: "Health & Fitness",
    timing: "Q2 2025",
    painLevel: "Medium",
    summary:
      "Home fitness enthusiasts risk injury from improper form but can't afford regular personal training sessions. Mirror checks are unreliable and don't catch subtle mistakes.",
    confidence: 68,
    painSeverity: 7.5,
    dateDetected: "Dec 5, 2024",
    badges: ["health", "ai-ready", "medium-pain"],
  },
  {
    id: 6,
    title: "Smart Outdoor Gear Rental Marketplace",
    category: "Outdoor & Sports",
    timing: "Q4 2025",
    painLevel: "Low",
    summary:
      "Outdoor enthusiasts buy expensive gear for occasional use or rent from shops with limited selection and high prices. Peer-to-peer options lack insurance and quality guarantees.",
    confidence: 64,
    painSeverity: 5.3,
    dateDetected: "Dec 2, 2024",
    badges: ["outdoor", "marketplace", "low-pain"],
  },
]

const badgeColors: Record<string, string> = {
  home: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  pets: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  health: "bg-green-500/20 text-green-400 border-green-500/30",
  baby: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  food: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  tech: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  outdoor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  trending: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  "high-pain": "bg-red-500/20 text-red-400 border-red-500/30",
  "medium-pain": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  "low-pain": "bg-gray-500/20 text-gray-400 border-gray-500/30",
  "ai-ready": "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
  urgent: "bg-red-500/20 text-red-400 border-red-500/30",
  marketplace: "bg-teal-500/20 text-teal-400 border-teal-500/30",
  wellness: "bg-green-500/20 text-green-400 border-green-500/30",
}

function DashboardLayout() {
  const [activeCategory, setActiveCategory] = useState("All Opportunities")
  const [searchQuery, setSearchQuery] = useState("")
  const [confidenceFilter, setConfidenceFilter] = useState("all")
  const [painFilter, setPainFilter] = useState("all")
  const [scrollPosition, setScrollPosition] = useState(0)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const carouselRef = useRef<HTMLDivElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const sidebarVideoRef = useRef<HTMLVideoElement>(null)
  const heroVideoRef = useRef<HTMLVideoElement>(null)

  // Fetch opportunities from Supabase
  const { data: supabaseOpportunities, isLoading, error } = useOpportunities()
  const { data: categoryCounts } = useOpportunityCounts()

  // Transform Supabase data to match the UI format, fallback to hardcoded data
  const transformedOpportunities = useMemo(() => {
    if (!supabaseOpportunities || supabaseOpportunities.length === 0) {
      return opportunities // fallback to hardcoded data
    }
    
    return supabaseOpportunities.map((opp) => {
      const painLevel = opp.pain_severity >= 8 ? "High" : opp.pain_severity >= 5 ? "Medium" : "Low"
      const timing = opp.timing_score && opp.timing_score >= 8 ? "Q1 2025" : 
                     opp.timing_score && opp.timing_score >= 5 ? "Q2 2025" : "Q3 2025"
      
      return {
        id: opp.id,
        title: opp.title,
        category: opp.category || "Uncategorized",
        timing,
        painLevel,
        summary: opp.problem_summary || "",
        confidence: opp.confidence_score,
        painSeverity: opp.pain_severity,
        dateDetected: new Date(opp.detected_at).toLocaleDateString("en-US", { 
          month: "short", 
          day: "numeric", 
          year: "numeric" 
        }),
        badges: [
          opp.category?.toLowerCase().split(" ")[0] || "other",
          opp.growth_pattern === "trending" ? "trending" : null,
          `${painLevel.toLowerCase()}-pain`,
        ].filter(Boolean) as string[],
      }
    })
  }, [supabaseOpportunities])

  // Build categories with dynamic counts
  const categories = useMemo(() => {
    return categoryConfig.map((cat) => ({
      ...cat,
      count: cat.dbCategory === null 
        ? (categoryCounts?.total || transformedOpportunities.length)
        : (categoryCounts?.[cat.dbCategory] || 0),
    }))
  }, [categoryCounts, transformedOpportunities.length])

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = 0.5
    }
    if (heroVideoRef.current) {
      heroVideoRef.current.playbackRate = 0.5
    }
    if (sidebarVideoRef.current) {
      sidebarVideoRef.current.playbackRate = 0.5
      sidebarVideoRef.current.play().catch((error) => {
        console.log("Sidebar video autoplay prevented:", error)
      })
    }
  }, [])

  const filteredOpportunities = transformedOpportunities.filter((opp) => {
    // Category filter
    const matchesCategory = activeCategory === "All Opportunities" || opp.category === activeCategory

    // Search filter
    const matchesSearch =
      searchQuery === "" ||
      opp.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      opp.summary.toLowerCase().includes(searchQuery.toLowerCase())

    // Confidence filter
    const matchesConfidence =
      confidenceFilter === "all" ||
      (confidenceFilter === "high" && opp.confidence >= 80) ||
      (confidenceFilter === "medium" && opp.confidence >= 50 && opp.confidence < 80) ||
      (confidenceFilter === "low" && opp.confidence < 50)

    // Pain severity filter
    const matchesPain =
      painFilter === "all" ||
      (painFilter === "high" && opp.painSeverity >= 8) ||
      (painFilter === "medium" && opp.painSeverity >= 5 && opp.painSeverity < 8) ||
      (painFilter === "low" && opp.painSeverity < 5)

    return matchesCategory && matchesSearch && matchesConfidence && matchesPain
  })

  const featuredOpportunity =
    filteredOpportunities.length > 0
      ? filteredOpportunities.reduce((prev, current) => (prev.confidence > current.confidence ? prev : current))
      : transformedOpportunities[0]

  const otherOpportunities = filteredOpportunities.filter((opp) => opp.id !== featuredOpportunity?.id)

  const scrollCarousel = (direction: "left" | "right") => {
    if (carouselRef.current) {
      const scrollAmount = 400
      carouselRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      })
    }
  }

  // Touch swipe handling for mobile carousel
  const [touchStart, setTouchStart] = useState<number | null>(null)
  const [touchEnd, setTouchEnd] = useState<number | null>(null)
  const minSwipeDistance = 50

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null)
    setTouchStart(e.targetTouches[0].clientX)
  }

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX)
  }

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return
    const distance = touchStart - touchEnd
    const isLeftSwipe = distance > minSwipeDistance
    const isRightSwipe = distance < -minSwipeDistance
    if (isLeftSwipe) {
      scrollCarousel("right")
    } else if (isRightSwipe) {
      scrollCarousel("left")
    }
  }

  return (
    <div className="min-h-screen lg:flex lg:h-screen overflow-hidden bg-gradient-to-br from-[#0a0a0a] to-[#1a1a1a] text-foreground relative">
      {/* Background video - hidden on mobile for performance */}
      <video
        ref={videoRef}
        autoPlay
        loop
        muted
        playsInline
        className="fixed inset-0 w-full h-full object-contain z-0 pt-8 hidden md:block"
        style={{
          left: "50%",
          transform: "translateX(-50%)",
        }}
      >
        <source src="/ascii-globe-video.mp4" type="video/mp4" />
      </video>

      {/* Mobile Header */}
      <header className="fixed top-0 left-0 right-0 z-50 lg:hidden bg-card/95 backdrop-blur-md border-b border-border/50 safe-area-inset-top">
        <div className="flex items-center justify-between px-4 py-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
            className="text-foreground -ml-2 h-10 w-10 active:scale-95 transition-transform"
          >
            {isMobileSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>

          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Layers className="w-4 h-4 text-primary-foreground" />
            </div>
            <h1 className="text-base font-display font-semibold text-foreground">Product Browser</h1>
          </div>

          <Button variant="ghost" size="icon" className="text-foreground -mr-2 h-10 w-10 active:scale-95 transition-transform">
            <Search className="w-5 h-5" />
          </Button>
        </div>
      </header>

      {isMobileSidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setIsMobileSidebarOpen(false)} />
      )}

      {/* Sidebar - Fixed overlay on mobile, static on desktop */}
      <aside
        className={`
          w-60 border-r border-border/50 bg-sidebar/95 backdrop-blur-sm flex-col z-50
          fixed inset-y-0 left-0 transition-transform duration-300
          hidden lg:flex lg:relative lg:translate-x-0
          ${isMobileSidebarOpen ? "!flex translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Top Section - Logo and Navigation */}
        <div className="flex-[2] flex flex-col min-h-0">
          <div className="p-6 border-b border-border/50 flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                <Layers className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-display font-semibold text-foreground">Product Browser</h1>
              </div>
            </div>
          </div>

          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {categories.map((category) => {
              const Icon = category.icon
              const isActive = activeCategory === category.name

              return (
                <button
                  key={category.id}
                  onClick={() => setActiveCategory(category.name)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                    isActive
                      ? "bg-gradient-to-r from-primary to-accent text-primary-foreground shadow-lg shadow-primary/20"
                      : "hover:bg-sidebar-accent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{category.name}</span>
                  </div>
                  <Badge
                    variant="secondary"
                    className={`text-xs ${isActive ? "bg-white/20 text-primary-foreground border-0" : "bg-muted/50"}`}
                  >
                    {category.count}
                  </Badge>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Bottom Section - Video Container */}
        <div className="flex-[1] flex flex-col p-4 border-t border-border/50 min-h-0 max-h-[200px]">
          <div className="flex-1 rounded-lg overflow-hidden bg-black/30 border border-border/30 flex items-center justify-center">
            <video
              ref={sidebarVideoRef}
              src="/sidebar-globe-video.mp4"
              autoPlay
              loop
              muted
              playsInline
              className="w-full h-full object-contain"
              onLoadStart={() => console.log("[v0] Sidebar video: load started")}
              onLoadedMetadata={() => console.log("[v0] Sidebar video: metadata loaded")}
              onLoadedData={() => console.log("[v0] Sidebar video: data loaded successfully")}
              onCanPlay={() => console.log("[v0] Sidebar video: can play")}
              onPlay={() => console.log("[v0] Sidebar video: playing")}
              onError={(e) => {
                const target = e.currentTarget as HTMLVideoElement
                console.log("[v0] Sidebar video error details:", {
                  error: target.error,
                  code: target.error?.code,
                  message: target.error?.message,
                  src: target.src,
                  currentSrc: target.currentSrc,
                  networkState: target.networkState,
                  readyState: target.readyState,
                })
              }}
            />
          </div>
        </div>
      </aside>

      {/* Main Content - Full width on mobile, flex-1 on desktop */}
      <main className="w-full lg:flex-1 flex flex-col overflow-hidden relative z-10 pt-14 pb-16 lg:pt-0 lg:pb-0">
        {/* Desktop Header */}
        <header className="border-b border-border/50 bg-card/30 backdrop-blur-sm hidden lg:block">
          <div className="p-6">
            <div className="flex items-center gap-4 w-full">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search opportunities..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-background/50 border-border/50"
                />
              </div>
              <Select defaultValue="confidence" onValueChange={(value) => setConfidenceFilter(value)}>
                <SelectTrigger className="w-48 bg-background/50 border-border/50">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="confidence">Confidence Score</SelectItem>
                  <SelectItem value="pain">Pain Severity</SelectItem>
                  <SelectItem value="date">Date Detected</SelectItem>
                </SelectContent>
              </Select>
              <Select value={painFilter} onValueChange={setPainFilter}>
                <SelectTrigger className="w-48 bg-background/50 border-border/50">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Pain Severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Pain Levels</SelectItem>
                  <SelectItem value="high">High (8-10)</SelectItem>
                  <SelectItem value="medium">Medium (5-7)</SelectItem>
                  <SelectItem value="low">Low (0-4)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </header>

        {/* Mobile Search & Filters */}
        <div className="lg:hidden px-4 py-3 bg-card/50 backdrop-blur-sm border-b border-border/50 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search opportunities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-background/50 border-border/50 h-11 text-base"
            />
          </div>
          <div className="flex gap-2">
            <Select value={painFilter} onValueChange={setPainFilter}>
              <SelectTrigger className="flex-1 bg-background/50 border-border/50 h-10 text-sm">
                <SelectValue placeholder="Pain Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Pain</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
            <Select defaultValue="confidence" onValueChange={(value) => setConfidenceFilter(value)}>
              <SelectTrigger className="flex-1 bg-background/50 border-border/50 h-10 text-sm">
                <SelectValue placeholder="Sort" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="confidence">Confidence</SelectItem>
                <SelectItem value="pain">Pain</SelectItem>
                <SelectItem value="date">Date</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto overscroll-contain">
          <div className="px-4 py-5 lg:p-6 space-y-5 lg:space-y-8 max-w-7xl mx-auto">
            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <span className="ml-3 text-muted-foreground">Loading opportunities...</span>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-20">
                <p className="text-red-400 mb-2">Failed to load opportunities</p>
                <p className="text-sm text-muted-foreground">Using sample data instead</p>
              </div>
            )}

            {/* Featured Product of the Day Section */}
            <div className="space-y-4 lg:space-y-6">
              {/* Hero Video Section */}
              <div className="relative w-full h-[280px] sm:h-[380px] lg:h-[480px] rounded-2xl overflow-hidden">
                {/* Background Video */}
                <video
                  ref={heroVideoRef}
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="absolute w-[125%] h-[125%] object-contain opacity-90 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
                >
                  <source src="/hero-video.mp4" type="video/mp4" />
                </video>
                
                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-black/30" />
                
                {/* Hero Content */}
                <div className="absolute inset-0 flex flex-col items-center justify-center p-6 lg:p-12 text-center">
                  <h1 className="text-2xl sm:text-3xl lg:text-5xl font-display font-bold text-balance bg-gradient-to-r from-white via-blue-200 to-[#444df6] bg-clip-text text-transparent drop-shadow-2xl">
                    Discover What to Build Next
                  </h1>
                  <p className="mt-3 sm:mt-4 text-sm sm:text-base lg:text-lg text-white/70 max-w-2xl leading-relaxed">
                    Real complaints. Real gaps. Real opportunities.
                  </p>
                </div>
              </div>

              {/* Logo Carousel Section */}
              <div className="flex items-center gap-6 lg:gap-10 py-4 lg:py-6">
                {/* Left Text */}
                <div className="flex-shrink-0">
                  <p className="text-xs lg:text-sm text-muted-foreground font-medium leading-tight">
                    Ideas
                    <br />
                    Scraped From
                  </p>
                </div>
                
                {/* Logo Carousel */}
                <div className="flex-1 overflow-hidden relative">
                  <div className="animate-logo-scroll flex gap-8 lg:gap-12">
                    {/* First set of logos */}
                    <img src="/logo-reddit.png" alt="Reddit" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-twitter.png" alt="Twitter" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-amazon.png" alt="Amazon" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-tiktok.png" alt="TikTok" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-instagram.png" alt="Instagram" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-youtube.png" alt="YouTube" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-pinterest.png" alt="Pinterest" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-etsy.png" alt="Etsy" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    {/* Duplicate set for seamless loop */}
                    <img src="/logo-reddit.png" alt="Reddit" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-twitter.png" alt="Twitter" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-amazon.png" alt="Amazon" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-tiktok.png" alt="TikTok" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-instagram.png" alt="Instagram" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-youtube.png" alt="YouTube" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-pinterest.png" alt="Pinterest" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                    <img src="/logo-etsy.png" alt="Etsy" className="h-6 lg:h-8 w-auto opacity-60 hover:opacity-100 transition-opacity" />
                  </div>
                </div>
              </div>

              {/* Product of the Day Title */}
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-display font-bold text-center text-balance bg-gradient-to-r from-white via-blue-200 to-[#444df6] bg-clip-text text-transparent mt-6 lg:mt-10">
                Product of the Day
              </h1>

              {/* Featured Card - optimized for mobile */}
              <Link href={`/opportunity/${featuredOpportunity.id}`} className="block group">
                <Card className="bg-card border-border/50 hover:border-primary/50 transition-all duration-300 hover:shadow-2xl hover:shadow-primary/20 cursor-pointer overflow-hidden active:scale-[0.99] lg:active:scale-100">
                  <div className="p-4 sm:p-5 lg:p-8 space-y-4 lg:space-y-6">
                    {/* Badges - horizontal scroll on mobile */}
                    <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-hide">
                      <Badge
                        variant="outline"
                        className={`${badgeColors[featuredOpportunity.category.toLowerCase().split(" ")[0]]} whitespace-nowrap flex-shrink-0`}
                      >
                        {featuredOpportunity.category}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`${badgeColors[featuredOpportunity.timing.toLowerCase().replace(" ", "-")]} whitespace-nowrap flex-shrink-0`}
                      >
                        {featuredOpportunity.timing}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={`${badgeColors[featuredOpportunity.painLevel.toLowerCase() + "-pain"]} whitespace-nowrap flex-shrink-0`}
                      >
                        {featuredOpportunity.painLevel} Pain
                      </Badge>
                      <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30 whitespace-nowrap flex-shrink-0">
                        Featured
                      </Badge>
                    </div>

                    <h2 className="text-xl sm:text-2xl lg:text-4xl font-display font-bold text-balance leading-tight text-foreground group-hover:text-primary transition-colors">
                      {featuredOpportunity.title}
                    </h2>

                    <p className="text-sm lg:text-base text-muted-foreground leading-relaxed text-pretty max-w-3xl line-clamp-3 sm:line-clamp-none">
                      {featuredOpportunity.summary}
                    </p>

                    {/* Metrics - stacked on mobile, grid on larger screens */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 lg:gap-6 pt-2 sm:pt-4">
                      <div className="flex items-center justify-between sm:block sm:space-y-3 py-2 sm:py-0 border-b sm:border-b-0 border-border/30 last:border-b-0">
                        <span className="text-muted-foreground flex items-center gap-2 text-sm">
                          <Target className="w-4 h-4" />
                          Confidence
                        </span>
                        <div className="flex items-center gap-3 sm:block">
                          <span className="font-bold text-lg text-foreground">{featuredOpportunity.confidence}%</span>
                          <Progress value={featuredOpportunity.confidence} className="h-2 w-20 sm:w-full sm:mt-2" />
                        </div>
                      </div>

                      <div className="flex items-center justify-between sm:block sm:space-y-3 py-2 sm:py-0 border-b sm:border-b-0 border-border/30 last:border-b-0">
                        <span className="text-muted-foreground flex items-center gap-2 text-sm">
                          <TrendingUp className="w-4 h-4" />
                          Pain Severity
                        </span>
                        <div className="flex items-center gap-3 sm:block">
                          <span className="font-bold text-lg text-foreground">
                            {featuredOpportunity.painSeverity}/10
                          </span>
                          <Progress value={featuredOpportunity.painSeverity * 10} className="h-2 w-20 sm:w-full sm:mt-2" />
                        </div>
                      </div>

                      <div className="flex items-center justify-between sm:block sm:space-y-3 py-2 sm:py-0">
                        <span className="text-muted-foreground flex items-center gap-2 text-sm">
                          <Users className="w-4 h-4" />
                          Market Interest
                        </span>
                        <div className="flex items-center gap-3 sm:block">
                          <span className="font-bold text-lg text-foreground">High</span>
                          <Progress value={85} className="h-2 w-20 sm:w-full sm:mt-2" />
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              </Link>

              {/* Stats Cards - horizontal scroll on mobile, grid on larger screens */}
              <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 lg:mx-0 lg:px-0 lg:grid lg:grid-cols-3 lg:gap-4 scrollbar-hide snap-x snap-mandatory">
                <Card className="bg-card border-border/50 p-4 lg:p-6 flex-shrink-0 w-[280px] sm:w-[300px] lg:w-auto snap-start">
                  <div className="space-y-3 lg:space-y-4">
                    <h3 className="text-sm font-medium text-muted-foreground">Market Trend</h3>
                    <div className="flex items-end gap-1 h-20 lg:h-24">
                      {[45, 52, 48, 61, 55, 68, 72, 78, 85, 87].map((height, i) => (
                        <div
                          key={i}
                          className="flex-1 bg-gradient-to-t from-white via-blue-300 to-[#444df6] rounded-t transition-all active:opacity-80 lg:hover:opacity-80"
                          style={{ height: `${height}%` }}
                        />
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground">Last 10 days</p>
                  </div>
                </Card>

                <Card className="bg-card border-border/50 p-4 lg:p-6 flex-shrink-0 w-[280px] sm:w-[300px] lg:w-auto snap-start">
                  <div className="space-y-3 lg:space-y-4">
                    <h3 className="text-sm font-medium text-muted-foreground">Competition Level</h3>
                    <div className="flex items-center justify-center h-20 lg:h-24">
                      <div className="relative w-24 h-24 lg:w-32 lg:h-32">
                        <svg className="w-full h-full transform -rotate-90">
                          <circle
                            cx="50%"
                            cy="50%"
                            r="40%"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            className="text-muted/20"
                          />
                          <circle
                            cx="50%"
                            cy="50%"
                            r="40%"
                            stroke="url(#gradient)"
                            strokeWidth="8"
                            fill="none"
                            strokeDasharray="251.2"
                            strokeDashoffset="163.28"
                            className="transition-all duration-1000"
                          />
                          <defs>
                            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                              <stop offset="0%" stopColor="#010df0" />
                              <stop offset="100%" stopColor="#444df6" />
                            </linearGradient>
                          </defs>
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-xl lg:text-2xl font-bold">Low</span>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground text-center">35% saturation</p>
                  </div>
                </Card>

                <Card className="bg-card border-border/50 p-4 lg:p-6 flex-shrink-0 w-[280px] sm:w-[300px] lg:w-auto snap-start">
                  <div className="space-y-3 lg:space-y-4">
                    <h3 className="text-sm font-medium text-muted-foreground">Revenue Potential</h3>
                    <div className="space-y-2.5 lg:space-y-3 pt-1 lg:pt-2">
                      <div className="space-y-1.5 lg:space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Year 1</span>
                          <span className="font-semibold">$2.5M</span>
                        </div>
                        <Progress value={50} className="h-1.5 lg:h-2" />
                      </div>
                      <div className="space-y-1.5 lg:space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Year 2</span>
                          <span className="font-semibold">$8.2M</span>
                        </div>
                        <Progress value={75} className="h-1.5 lg:h-2" />
                      </div>
                      <div className="space-y-1.5 lg:space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Year 3</span>
                          <span className="font-semibold">$15M</span>
                        </div>
                        <Progress value={100} className="h-1.5 lg:h-2" />
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </div>

            {/* More Opportunities Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-display font-bold">More Opportunities</h2>
                <div className="flex items-center gap-2">
                  <span className="text-xs lg:text-sm text-muted-foreground">
                    {filteredOpportunities.length} found
                  </span>
                  {/* Desktop carousel controls */}
                  <div className="hidden lg:flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => scrollCarousel("left")}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => scrollCarousel("right")}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Mobile: Vertical card list */}
              <div className="lg:hidden space-y-3">
                {otherOpportunities.slice(0, 10).map((opp) => (
                  <Link key={opp.id} href={`/opportunity/${opp.id}`} className="block group">
                    <Card className="bg-card border-border/50 active:border-primary/50 transition-all duration-200 cursor-pointer active:scale-[0.99]">
                      <div className="p-4 space-y-2.5">
                        {/* Badges - horizontal scroll */}
                        <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-hide">
                          {opp.badges.slice(0, 3).map((badge, idx) => (
                            <Badge key={idx} variant="outline" className={`${badgeColors[badge]} text-[10px] px-2 py-0.5 whitespace-nowrap flex-shrink-0`}>
                              {badge}
                            </Badge>
                          ))}
                        </div>
                        <h3 className="text-base font-display font-semibold text-foreground group-active:text-primary transition-colors line-clamp-2">
                          {opp.title}
                        </h3>
                        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">{opp.summary}</p>
                        
                        {/* Compact metrics row */}
                        <div className="flex items-center justify-between pt-2 border-t border-border/30">
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-1.5">
                              <Target className="w-3.5 h-3.5 text-muted-foreground" />
                              <span className="text-xs font-semibold">{opp.confidence}%</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <TrendingUp className="w-3.5 h-3.5 text-muted-foreground" />
                              <span className="text-xs font-semibold">{opp.painSeverity}/10</span>
                            </div>
                          </div>
                          <span className="text-[10px] text-muted-foreground">{opp.dateDetected}</span>
                        </div>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>

              {/* Desktop: Horizontal carousel */}
              <div className="hidden lg:block relative">
                <div 
                  className="flex gap-6 overflow-x-auto pb-4 scrollbar-hide snap-x snap-mandatory" 
                  ref={carouselRef}
                  onTouchStart={onTouchStart}
                  onTouchMove={onTouchMove}
                  onTouchEnd={onTouchEnd}
                >
                  {otherOpportunities.map((opp) => (
                    <Link key={opp.id} href={`/opportunity/${opp.id}`} className="flex-shrink-0 w-96 group">
                      <Card className="h-full bg-card border-border/50 hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:shadow-primary/10 hover:-translate-y-1 cursor-pointer snap-start">
                        <div className="p-6 space-y-4">
                          {/* Badges */}
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="outline" className={badgeColors[opp.category.toLowerCase().split(" ")[0]]}>
                              {opp.category}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={badgeColors[opp.timing.toLowerCase().replace(" ", "-")]}
                            >
                              {opp.timing}
                            </Badge>
                            <Badge variant="outline" className={badgeColors[opp.painLevel.toLowerCase() + "-pain"]}>
                              {opp.painLevel} Pain
                            </Badge>
                          </div>

                          {/* Title */}
                          <h3 className="text-xl font-display font-bold text-balance leading-tight text-foreground group-hover:text-primary transition-colors line-clamp-2">
                            {opp.title}
                          </h3>

                          {/* Summary */}
                          <p className="text-sm text-muted-foreground leading-relaxed text-pretty line-clamp-2">
                            {opp.summary}
                          </p>

                          {/* Metrics */}
                          <div className="pt-4 border-t border-border/50 space-y-3">
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">Confidence Score</span>
                                <span className="font-semibold text-foreground">{opp.confidence}%</span>
                              </div>
                              <Progress value={opp.confidence} className="h-1.5" />
                            </div>

                            <div className="flex items-center justify-between text-sm pt-2">
                              <div className="flex items-center gap-2">
                                <span className="text-muted-foreground">Pain Severity</span>
                                <span className="font-semibold text-foreground">{opp.painSeverity}/10</span>
                              </div>
                              <div className="text-muted-foreground text-xs">{opp.dateDetected}</div>
                            </div>
                          </div>
                        </div>
                      </Card>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 lg:hidden bg-card/95 backdrop-blur-md border-t border-border/50 safe-area-inset-bottom">
        <div className="flex items-center justify-around py-2">
          <button 
            className="flex flex-col items-center gap-1 px-4 py-2 text-primary"
            onClick={() => setActiveCategory("All Opportunities")}
          >
            <Home className="w-5 h-5" />
            <span className="text-[10px] font-medium">Home</span>
          </button>
          <button 
            className="flex flex-col items-center gap-1 px-4 py-2 text-muted-foreground active:text-primary transition-colors"
            onClick={() => setIsMobileSidebarOpen(true)}
          >
            <Compass className="w-5 h-5" />
            <span className="text-[10px] font-medium">Explore</span>
          </button>
          <button className="flex flex-col items-center gap-1 px-4 py-2 text-muted-foreground active:text-primary transition-colors">
            <Search className="w-5 h-5" />
            <span className="text-[10px] font-medium">Search</span>
          </button>
          <button className="flex flex-col items-center gap-1 px-4 py-2 text-muted-foreground active:text-primary transition-colors">
            <Settings className="w-5 h-5" />
            <span className="text-[10px] font-medium">Settings</span>
          </button>
        </div>
      </nav>
    </div>
  )
}

export default DashboardLayout
export { DashboardLayout }
