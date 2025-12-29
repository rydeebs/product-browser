"use client"

import { useState, useRef, useEffect } from "react"
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
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"

const categories = [
  { id: "all", name: "All Opportunities", icon: Layers, count: 47 },
  { id: "home", name: "Home & Living", icon: Home, count: 12 },
  { id: "pets", name: "Pets & Animals", icon: Heart, count: 8 },
  { id: "health", name: "Health & Fitness", icon: Activity, count: 6 },
  { id: "baby", name: "Baby & Parenting", icon: Baby, count: 5 },
  { id: "food", name: "Food & Cooking", icon: Utensils, count: 9 },
  { id: "tech", name: "Tech & Gadgets", icon: Cpu, count: 4 },
  { id: "outdoor", name: "Outdoor & Sports", icon: Mountain, count: 3 },
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

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = 0.5
    }
    if (sidebarVideoRef.current) {
      console.log("[v0] Sidebar video ref exists:", !!sidebarVideoRef.current)
      console.log("[v0] Sidebar video src:", sidebarVideoRef.current?.src)
      console.log("[v0] Sidebar video readyState:", sidebarVideoRef.current?.readyState)
      console.log("[v0] Sidebar video networkState:", sidebarVideoRef.current?.networkState)
      console.log("[v0] Sidebar video error:", sidebarVideoRef.current?.error)

      sidebarVideoRef.current.playbackRate = 0.5
      sidebarVideoRef.current.play().catch((error) => {
        console.log("[v0] Sidebar video autoplay prevented:", error)
      })
    } else {
      console.log("[v0] Sidebar video ref is null!")
    }
  }, [])

  const filteredOpportunities = opportunities.filter((opp) => {
    // Category filter
    const matchesCategory = activeCategory === "All Opportunities" || opp.category === activeCategory

    // Search filter - check against searchQuery, not activeCategory
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
      : opportunities[0]

  const otherOpportunities = filteredOpportunities.filter((opp) => opp.id !== featuredOpportunity.id)

  console.log("[v0] Filtered opportunities count:", filteredOpportunities.length)
  console.log("[v0] Other opportunities count:", otherOpportunities.length)
  console.log("[v0] Featured opportunity:", featuredOpportunity?.title)

  const scrollCarousel = (direction: "left" | "right") => {
    if (carouselRef.current) {
      const scrollAmount = 400
      carouselRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      })
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gradient-to-br from-[#0a0a0a] to-[#1a1a1a] text-foreground relative">
      <video
        ref={videoRef}
        autoPlay
        loop
        muted
        playsInline
        className="fixed inset-0 w-full h-full object-contain z-0 pt-8"
        style={{
          left: "50%",
          transform: "translateX(-50%)",
        }}
      >
        <source src="/ascii-globe-video.mp4" type="video/mp4" />
      </video>

      <header className="fixed top-0 left-0 right-0 z-50 lg:hidden bg-card/90 backdrop-blur-md border-b border-border/50">
        <div className="flex items-center justify-between p-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
            className="text-foreground"
          >
            {isMobileSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Layers className="w-4 h-4 text-primary-foreground" />
            </div>
            <h1 className="text-base font-display font-semibold text-foreground">OpportunityOS</h1>
          </div>

          <Button variant="ghost" size="icon" className="text-foreground">
            <Search className="w-5 h-5" />
          </Button>
        </div>
      </header>

      {isMobileSidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setIsMobileSidebarOpen(false)} />
      )}

      <aside
        className={`
          w-60 border-r border-border/50 bg-sidebar/95 backdrop-blur-sm flex flex-col relative z-50
          lg:relative lg:translate-x-0
          fixed inset-y-0 left-0 transition-transform duration-300
          ${isMobileSidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Top Half - Logo and Navigation */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="p-6 border-b border-border/50 flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                <Layers className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-display font-semibold text-foreground">OpportunityOS</h1>
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

        {/* Bottom Half - Video Container */}
        <div className="flex-1 flex flex-col p-4 border-t border-border/50 min-h-0">
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

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative z-10 pt-16 lg:pt-0">
        {/* Header - hidden on mobile */}
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

        <div className="lg:hidden p-4 bg-card/30 backdrop-blur-sm border-b border-border/50">
          <Input
            placeholder="Search opportunities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-background/50 border-border/50"
          />
          <div className="flex gap-2 mt-2">
            <Select value={painFilter} onValueChange={setPainFilter}>
              <SelectTrigger className="flex-1 bg-background/50 border-border/50 text-xs">
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
              <SelectTrigger className="flex-1 bg-background/50 border-border/50 text-xs">
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

        <div className="flex-1 overflow-y-auto">
          <div className="p-4 lg:p-6 space-y-6 lg:space-y-8 max-w-7xl mx-auto">
            {/* Featured Product of the Day Section */}
            <div className="space-y-4 lg:space-y-6">
              <h1 className="text-2xl lg:text-4xl font-display font-bold text-center text-balance bg-gradient-to-r from-white via-blue-200 to-[#444df6] bg-clip-text text-transparent px-4">
                Product of the Day
              </h1>

              {/* Featured Card - optimized for mobile */}
              <Link href={`/opportunity/${featuredOpportunity.id}`} className="block">
                <Card className="group bg-card border-border/50 hover:border-primary/50 transition-all duration-300 hover:shadow-2xl hover:shadow-primary/20 cursor-pointer overflow-hidden">
                  <div className="p-4 lg:p-8 space-y-4 lg:space-y-6">
                    <div className="flex flex-wrap gap-2">
                      <Badge
                        variant="outline"
                        className={badgeColors[featuredOpportunity.category.toLowerCase().split(" ")[0]]}
                      >
                        {featuredOpportunity.category}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={badgeColors[featuredOpportunity.timing.toLowerCase().replace(" ", "-")]}
                      >
                        {featuredOpportunity.timing}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={badgeColors[featuredOpportunity.painLevel.toLowerCase() + "-pain"]}
                      >
                        {featuredOpportunity.painLevel} Pain
                      </Badge>
                      <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                        Featured
                      </Badge>
                    </div>

                    <h2 className="text-2xl lg:text-4xl font-display font-bold text-balance leading-tight text-foreground group-hover:text-primary transition-colors">
                      {featuredOpportunity.title}
                    </h2>

                    <p className="text-sm lg:text-base text-muted-foreground leading-relaxed text-pretty max-w-3xl">
                      {featuredOpportunity.summary}
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6 pt-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground flex items-center gap-2">
                            <Target className="w-4 h-4" />
                            Confidence Score
                          </span>
                          <span className="font-bold text-lg text-foreground">{featuredOpportunity.confidence}%</span>
                        </div>
                        <Progress value={featuredOpportunity.confidence} className="h-2" />
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" />
                            Pain Severity
                          </span>
                          <span className="font-bold text-lg text-foreground">
                            {featuredOpportunity.painSeverity}/10
                          </span>
                        </div>
                        <Progress value={featuredOpportunity.painSeverity * 10} className="h-2" />
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            Market Interest
                          </span>
                          <span className="font-bold text-lg text-foreground">High</span>
                        </div>
                        <Progress value={85} className="h-2" />
                      </div>
                    </div>
                  </div>
                </Card>
              </Link>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
                <Card className="bg-card border-border/50 p-6">
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-muted-foreground">Market Trend</h3>
                    <div className="flex items-end gap-1 h-24">
                      {[45, 52, 48, 61, 55, 68, 72, 78, 85, 87].map((height, i) => (
                        <div
                          key={i}
                          className="flex-1 bg-gradient-to-t from-white via-blue-300 to-[#444df6] rounded-t transition-all hover:opacity-80"
                          style={{ height: `${height}%` }}
                        />
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground">Last 10 days</p>
                  </div>
                </Card>

                <Card className="bg-card border-border/50 p-6">
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-muted-foreground">Competition Level</h3>
                    <div className="flex items-center justify-center h-24">
                      <div className="relative w-32 h-32">
                        <svg className="w-full h-full transform -rotate-90">
                          <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            className="text-muted/20"
                          />
                          <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="url(#gradient)"
                            strokeWidth="8"
                            fill="none"
                            strokeDasharray={`${2 * Math.PI * 56}`}
                            strokeDashoffset={`${2 * Math.PI * 56 * (1 - 0.35)}`}
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
                          <span className="text-2xl font-bold">Low</span>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground text-center">35% saturation</p>
                  </div>
                </Card>

                <Card className="bg-card border-border/50 p-6">
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-muted-foreground">Revenue Potential</h3>
                    <div className="space-y-3 pt-2">
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Year 1</span>
                          <span className="font-semibold">$2.5M</span>
                        </div>
                        <Progress value={50} className="h-2" />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Year 2</span>
                          <span className="font-semibold">$8.2M</span>
                        </div>
                        <Progress value={75} className="h-2" />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Year 3</span>
                          <span className="font-semibold">$15M</span>
                        </div>
                        <Progress value={100} className="h-2" />
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl lg:text-2xl font-display font-bold">More Opportunities</h2>
                <span className="text-xs lg:text-sm text-muted-foreground">
                  {filteredOpportunities.length} opportunities found
                </span>
              </div>

              <div className="lg:hidden space-y-4">
                {otherOpportunities.slice(0, 10).map((opp) => (
                  <Link key={opp.id} href={`/opportunity/${opp.id}`} className="block">
                    <Card className="group bg-card border-border/50 hover:border-primary/50 transition-all duration-300 cursor-pointer">
                      <div className="p-4 space-y-3">
                        <div className="flex flex-wrap gap-1.5">
                          {opp.badges.map((badge, idx) => (
                            <Badge key={idx} variant="outline" className={`${badgeColors[badge]} text-xs px-2 py-0.5`}>
                              {badge}
                            </Badge>
                          ))}
                        </div>
                        <h3 className="text-lg font-display font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">
                          {opp.title}
                        </h3>
                        <p className="text-xs text-muted-foreground line-clamp-2">{opp.summary}</p>
                        <div className="grid grid-cols-2 gap-3 pt-2">
                          <div className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-muted-foreground">Confidence</span>
                              <span className="font-semibold">{opp.confidence}%</span>
                            </div>
                            <Progress value={opp.confidence} className="h-1.5" />
                          </div>
                          <div className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-muted-foreground">Pain</span>
                              <span className="font-semibold">{opp.painSeverity}/10</span>
                            </div>
                            <Progress value={opp.painSeverity * 10} className="h-1.5" />
                          </div>
                        </div>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>

              <div className="hidden lg:block relative">
                <div className="flex gap-6 overflow-x-auto pb-4 scrollbar-hide snap-x snap-mandatory" ref={carouselRef}>
                  {otherOpportunities.map((opp) => (
                    <Link key={opp.id} href={`/opportunity/${opp.id}`} className="flex-shrink-0 w-96">
                      <Card className="group h-full bg-card border-border/50 hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:shadow-primary/10 hover:-translate-y-1 cursor-pointer snap-start">
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
    </div>
  )
}

export default DashboardLayout
export { DashboardLayout }
