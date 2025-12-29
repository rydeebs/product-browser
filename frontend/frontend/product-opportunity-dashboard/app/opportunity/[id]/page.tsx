"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, TrendingUp, Zap, Clock, Target, Menu, X, ChevronDown } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { XAxis, YAxis, CartesianGrid, ResponsiveContainer, Area, AreaChart } from "recharts"

export default function OpportunityDetailPage() {
  const router = useRouter()
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    evidence: true,
    product: true,
    whyNow: true,
    signals: true,
  })

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  // Mock data - in real app, fetch based on [id]
  const opportunity = {
    title: "Smart Pet Water Fountain with Health Monitoring",
    badges: [
      { label: "Pets & Animals", color: "blue" },
      { label: "Perfect Timing", color: "purple" },
      { label: "Severe Pain", color: "orange" },
      { label: "Proven Founder Fit", color: "green" },
    ],
    summary:
      "Pet owners struggle to monitor their pets' hydration and detect early signs of health issues through drinking behavior. Current water fountains lack smart features that could provide valuable health insights and peace of mind.",
    metrics: {
      opportunityScore: { value: 9, label: "Exceptional", color: "green" },
      problemSeverity: { value: 9, label: "Severe Pain", color: "red" },
      feasibility: { value: 6, label: "Challenging", color: "blue" },
      whyNow: { value: 9, label: "Perfect Timing", color: "orange" },
    },
    marketData: [
      { month: "Jan", volume: 45000, growth: 5 },
      { month: "Feb", volume: 48000, growth: 6.7 },
      { month: "Mar", volume: 52000, growth: 8.3 },
      { month: "Apr", volume: 58000, growth: 11.5 },
      { month: "May", volume: 67000, growth: 15.5 },
      { month: "Jun", volume: 81000, growth: 20.9 },
    ],
    businessFit: {
      revenue: { level: 4, description: "High revenue potential ($50-100M market)" },
      difficulty: { level: 5, description: "Moderate hardware complexity" },
      goToMarket: { level: 8, description: "Clear channels via pet stores & Amazon" },
    },
    evidence: [
      {
        platform: "Reddit",
        subreddit: "r/pets",
        content:
          "My cat has kidney disease and I wish there was a way to track how much water she's drinking without constantly checking. Early detection could have saved us so much heartache.",
        engagement: { upvotes: 2847, comments: 342 },
        link: "https://reddit.com/...",
      },
      {
        platform: "Twitter",
        handle: "@petparent_life",
        content:
          "Just spent $5k on emergency vet bills because we didn't notice our dog wasn't drinking enough water. Why isn't there a smart fountain that alerts you?",
        engagement: { likes: 1523, retweets: 284 },
        link: "https://twitter.com/...",
      },
      {
        platform: "TikTok",
        creator: "veterinaryclinic",
        content:
          "80% of pet health issues we see could be prevented with better hydration monitoring. Video shows common symptoms pet owners miss.",
        engagement: { views: 2400000, likes: 156000 },
        link: "https://tiktok.com/...",
      },
    ],
    product: {
      features: [
        "AI-powered drinking pattern analysis",
        "Health anomaly detection and alerts",
        "App dashboard with hydration trends",
        "Veterinarian-approved metrics",
        "Multi-pet tracking capability",
        "Stainless steel, dishwasher-safe design",
      ],
      manufacturing: "Partner with established pet product manufacturers in Asia, focus on software differentiation",
      pricePoint: "$129-149 (premium positioning below $200 threshold)",
      differentiation:
        "First fountain with veterinary-grade health monitoring, leveraging AI for early disease detection rather than just filtration",
    },
    whyNow: {
      trends: [
        "Pet humanization trend: 67% of US households own pets, spending on pet health up 40% since 2020",
        "Preventive pet healthcare movement gaining traction",
        "Smart home device adoption at all-time high",
        "Pet insurance coverage increasing, incentivizing preventive monitoring",
        "Veterinary shortage creating demand for at-home monitoring tools",
      ],
    },
    communitySignals: {
      reddit: {
        subreddits: 8,
        members: 2500000,
        score: 8,
        description: "High engagement in r/pets, r/dogs, r/cats with hydration concerns",
      },
      twitter: {
        mentions: 15000,
        engagement: 450000,
        score: 7,
        description: "Steady stream of frustration with existing solutions",
      },
      tiktok: {
        views: 8500000,
        videos: 234,
        score: 7,
        description: "Pet health content highly viral, esp. preventive care topics",
      },
    },
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] to-[#1a1a1a] text-foreground">
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
              <TrendingUp className="w-4 h-4 text-primary-foreground" />
            </div>
            <h1 className="text-base font-display font-semibold text-foreground">OpportunityOS</h1>
          </div>

          <Button variant="ghost" size="icon" onClick={() => router.push("/")} className="text-foreground">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </div>
      </header>

      {isMobileSidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setIsMobileSidebarOpen(false)} />
      )}

      <div className="relative z-10 flex pt-16 lg:pt-0">
        <aside
          className={`
            w-60 border-r border-border/50 bg-sidebar/95 backdrop-blur-sm flex flex-col h-[calc(100vh-4rem)] lg:h-screen
            lg:relative lg:translate-x-0 lg:sticky lg:top-0
            fixed inset-y-16 lg:inset-y-0 left-0 transition-transform duration-300 z-50
            ${isMobileSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
          `}
        >
          {/* Logo */}
          <div className="p-6 border-b border-border/50">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => router.push("/")}>
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-display font-semibold text-foreground">OpportunityOS</h1>
              </div>
            </div>
          </div>

          {/* Navigation would go here - reuse from dashboard */}
          <div className="flex-1 p-4 text-sm text-muted-foreground">
            <p>Dashboard navigation...</p>
          </div>

          {/* Video in bottom half */}
          <div className="flex-1 flex flex-col p-4 border-t border-border/50 min-h-0">
            <div className="flex-1 rounded-lg overflow-hidden bg-black/30 border border-border/30 flex items-center justify-center">
              <video
                src="/sidebar-globe-video.mp4"
                autoPlay
                loop
                muted
                playsInline
                className="w-full h-full object-contain"
                onLoadedMetadata={(e) => {
                  e.currentTarget.playbackRate = 0.5
                }}
              />
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-4 lg:p-8 space-y-6 lg:space-y-8">
            <Button
              variant="ghost"
              onClick={() => router.push("/")}
              className="gap-2 text-muted-foreground hover:text-foreground hidden lg:flex"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to opportunities
            </Button>

            {/* Header Section */}
            <div className="space-y-3 lg:space-y-4">
              <h1 className="font-display text-3xl lg:text-5xl xl:text-6xl font-bold text-foreground leading-tight">
                {opportunity.title}
              </h1>

              <div className="flex flex-wrap gap-2">
                {opportunity.badges.map((badge, i) => (
                  <Badge
                    key={i}
                    className={`rounded-full px-3 py-1 text-xs font-medium border ${
                      badge.color === "blue"
                        ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                        : badge.color === "purple"
                          ? "bg-purple-500/20 text-purple-400 border-purple-500/30"
                          : badge.color === "orange"
                            ? "bg-orange-500/20 text-orange-400 border-orange-500/30"
                            : "bg-green-500/20 text-green-400 border-green-500/30"
                    }`}
                  >
                    {badge.label}
                  </Badge>
                ))}
              </div>

              <p className="text-base lg:text-lg text-muted-foreground leading-relaxed max-w-4xl">
                {opportunity.summary}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 lg:gap-4">
              {/* Opportunity Score */}
              <Card className="p-6 bg-card/50 backdrop-blur-sm border-border/50 border-l-4 border-l-green-500">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-muted-foreground">Opportunity Score</h3>
                    <Target className="w-5 h-5 text-green-400" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-bold text-foreground">
                      {opportunity.metrics.opportunityScore.value}
                    </span>
                    <span className="text-xl text-muted-foreground">/10</span>
                  </div>
                  <p className="text-sm font-semibold text-green-400">{opportunity.metrics.opportunityScore.label}</p>
                  <Progress
                    value={opportunity.metrics.opportunityScore.value * 10}
                    gradientColor="rgb(74, 222, 128)"
                    className="h-2"
                  />
                </div>
              </Card>

              {/* Problem Severity */}
              <Card className="p-6 bg-card/50 backdrop-blur-sm border-border/50 border-l-4 border-l-red-500">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-muted-foreground">Problem Severity</h3>
                    <Zap className="w-5 h-5 text-red-400" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-bold text-foreground">
                      {opportunity.metrics.problemSeverity.value}
                    </span>
                    <span className="text-xl text-muted-foreground">/10</span>
                  </div>
                  <p className="text-sm font-semibold text-red-400">{opportunity.metrics.problemSeverity.label}</p>
                  <Progress
                    value={opportunity.metrics.problemSeverity.value * 10}
                    gradientColor="rgb(239, 68, 68)"
                    className="h-2"
                  />
                </div>
              </Card>

              {/* Feasibility */}
              <Card className="p-6 bg-card/50 backdrop-blur-sm border-border/50 border-l-4 border-l-blue-500">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-muted-foreground">Feasibility</h3>
                    <TrendingUp className="w-5 h-5 text-blue-400" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-bold text-foreground">{opportunity.metrics.feasibility.value}</span>
                    <span className="text-xl text-muted-foreground">/10</span>
                  </div>
                  <p className="text-sm font-semibold text-blue-400">{opportunity.metrics.feasibility.label}</p>
                  <Progress
                    value={opportunity.metrics.feasibility.value * 10}
                    gradientColor="rgb(59, 130, 246)"
                    className="h-2"
                  />
                </div>
              </Card>

              {/* Why Now */}
              <Card className="p-6 bg-card/50 backdrop-blur-sm border-border/50 border-l-4 border-l-orange-500">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-muted-foreground">Why Now</h3>
                    <Clock className="w-5 h-5 text-orange-400" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-bold text-foreground">{opportunity.metrics.whyNow.value}</span>
                    <span className="text-xl text-muted-foreground">/10</span>
                  </div>
                  <p className="text-sm font-semibold text-orange-400">{opportunity.metrics.whyNow.label}</p>
                  <Progress
                    value={opportunity.metrics.whyNow.value * 10}
                    gradientColor="rgb(249, 115, 22)"
                    className="h-2"
                  />
                </div>
              </Card>
            </div>

            {/* Market Intelligence */}
            <Card className="p-4 lg:p-6 bg-card/50 backdrop-blur-sm border-border/50">
              <h2 className="font-display text-xl lg:text-2xl font-bold mb-4 lg:mb-6">Market Intelligence</h2>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <p className="text-sm text-muted-foreground">Search Volume</p>
                  <p className="text-3xl font-bold">81,000</p>
                  <p className="text-xs text-muted-foreground">monthly searches</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">6-Month Growth</p>
                  <p className="text-3xl font-bold text-green-400">+80%</p>
                  <p className="text-xs text-muted-foreground">accelerating trend</p>
                </div>
              </div>

              <div className="h-48 lg:h-64 overflow-x-auto">
                <div className="min-w-[500px] h-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={opportunity.marketData}>
                      <defs>
                        <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#444df6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#444df6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                      <XAxis dataKey="month" stroke="#666" />
                      <YAxis stroke="#666" />
                      <Area
                        type="monotone"
                        dataKey="volume"
                        stroke="#444df6"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorVolume)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </Card>

            {/* Evidence Section */}
            <div className="space-y-4">
              <button
                onClick={() => toggleSection("evidence")}
                className="w-full flex items-center justify-between lg:cursor-default"
              >
                <h2 className="font-display text-xl lg:text-2xl font-bold">Community Signals (Social Posts)</h2>
                <ChevronDown
                  className={`w-5 h-5 transition-transform lg:hidden ${expandedSections.evidence ? "rotate-180" : ""}`}
                />
              </button>

              {(expandedSections.evidence || window.innerWidth >= 1024) && (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                  {opportunity.evidence.map((post, i) => (
                    <Card
                      key={i}
                      className="p-6 bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/50 transition-colors"
                    >
                      <Badge className="mb-3 bg-primary/20 text-primary border-primary/30">{post.platform}</Badge>
                      <p className="text-sm italic text-muted-foreground mb-4 leading-relaxed">"{post.content}"</p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
                        {post.engagement.upvotes && <span>↑ {post.engagement.upvotes.toLocaleString()}</span>}
                        {post.engagement.comments && <span>💬 {post.engagement.comments}</span>}
                        {post.engagement.likes && <span>❤️ {post.engagement.likes.toLocaleString()}</span>}
                        {post.engagement.views && <span>👁️ {post.engagement.views.toLocaleString()}</span>}
                      </div>
                      <a
                        href={post.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline"
                      >
                        View original →
                      </a>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Recommended Product */}
            <div className="space-y-4">
              <button
                onClick={() => toggleSection("product")}
                className="w-full flex items-center justify-between lg:cursor-default"
              >
                <h2 className="font-display text-xl lg:text-2xl font-bold">Recommended Product</h2>
                <ChevronDown
                  className={`w-5 h-5 transition-transform lg:hidden ${expandedSections.product ? "rotate-180" : ""}`}
                />
              </button>

              {(expandedSections.product || window.innerWidth >= 1024) && (
                <Card className="p-4 lg:p-6 bg-card/50 backdrop-blur-sm border-border/50">
                  <div className="space-y-6">
                    <div>
                      <h3 className="font-semibold mb-3 text-primary">Key Features</h3>
                      <ul className="space-y-2">
                        {opportunity.product.features.map((feature, i) => (
                          <li key={i} className="flex items-start gap-3">
                            <span className="text-primary mt-1">•</span>
                            <span className="text-sm text-muted-foreground">{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-2">Manufacturing Approach</h3>
                      <p className="text-sm text-muted-foreground">{opportunity.product.manufacturing}</p>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-2">Target Price Point</h3>
                      <p className="text-sm text-muted-foreground">{opportunity.product.pricePoint}</p>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-2">Differentiation</h3>
                      <p className="text-sm text-muted-foreground">{opportunity.product.differentiation}</p>
                    </div>
                  </div>
                </Card>
              )}
            </div>

            {/* Why Now Section */}
            <div className="space-y-4">
              <button
                onClick={() => toggleSection("whyNow")}
                className="w-full flex items-center justify-between lg:cursor-default"
              >
                <h2 className="font-display text-xl lg:text-2xl font-bold">Why Now?</h2>
                <ChevronDown
                  className={`w-5 h-5 transition-transform lg:hidden ${expandedSections.whyNow ? "rotate-180" : ""}`}
                />
              </button>

              {(expandedSections.whyNow || window.innerWidth >= 1024) && (
                <div className="space-y-4">
                  {opportunity.whyNow.trends.map((trend, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/10"
                    >
                      <Clock className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-muted-foreground leading-relaxed">{trend}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Community Signals Breakdown */}
            <div className="space-y-4">
              <button
                onClick={() => toggleSection("signals")}
                className="w-full flex items-center justify-between lg:cursor-default"
              >
                <h2 className="font-display text-xl lg:text-2xl font-bold">Community Signals Breakdown</h2>
                <ChevronDown
                  className={`w-5 h-5 transition-transform lg:hidden ${expandedSections.signals ? "rotate-180" : ""}`}
                />
              </button>

              {(expandedSections.signals || window.innerWidth >= 1024) && (
                <div className="space-y-6">
                  {/* Reddit */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-semibold">Reddit</h3>
                        <p className="text-xs text-muted-foreground">
                          {opportunity.communitySignals.reddit.subreddits} subreddits •{" "}
                          {opportunity.communitySignals.reddit.members.toLocaleString()}+ members
                        </p>
                      </div>
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-bold">{opportunity.communitySignals.reddit.score}</span>
                        <span className="text-sm text-muted-foreground">/10</span>
                      </div>
                    </div>
                    <Progress value={opportunity.communitySignals.reddit.score * 10} className="h-2 mb-2" />
                    <p className="text-sm text-muted-foreground">{opportunity.communitySignals.reddit.description}</p>
                  </div>

                  {/* Twitter */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-semibold">Twitter/X</h3>
                        <p className="text-xs text-muted-foreground">
                          {opportunity.communitySignals.twitter.mentions.toLocaleString()} mentions •{" "}
                          {opportunity.communitySignals.twitter.engagement.toLocaleString()} total engagement
                        </p>
                      </div>
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-bold">{opportunity.communitySignals.twitter.score}</span>
                        <span className="text-sm text-muted-foreground">/10</span>
                      </div>
                    </div>
                    <Progress value={opportunity.communitySignals.twitter.score * 10} className="h-2 mb-2" />
                    <p className="text-sm text-muted-foreground">{opportunity.communitySignals.twitter.description}</p>
                  </div>

                  {/* TikTok */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-semibold">TikTok</h3>
                        <p className="text-xs text-muted-foreground">
                          {opportunity.communitySignals.tiktok.videos} videos •{" "}
                          {opportunity.communitySignals.tiktok.views.toLocaleString()} views
                        </p>
                      </div>
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-bold">{opportunity.communitySignals.tiktok.score}</span>
                        <span className="text-sm text-muted-foreground">/10</span>
                      </div>
                    </div>
                    <Progress value={opportunity.communitySignals.tiktok.score * 10} className="h-2 mb-2" />
                    <p className="text-sm text-muted-foreground">{opportunity.communitySignals.tiktok.description}</p>
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
