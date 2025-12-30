"use client"

import { useState, useMemo } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { TrendingUp, TrendingDown, Minus, Calendar, Search, ChevronDown } from "lucide-react"

interface TrendDataPoint {
  date: string
  value: number
}

interface KeywordTrendData {
  keyword: string
  data: TrendDataPoint[]
  current_volume: number
  growth_rate: number
  avg_volume: number
  max_volume: number
  min_volume: number
  timeframe: string
}

interface TrendsChartProps {
  data?: KeywordTrendData
  isLoading?: boolean
  error?: string | null
  onTimeframeChange?: (timeframe: string) => void
  className?: string
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M"
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K"
  }
  return num.toLocaleString()
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" })
}

export function TrendsChart({ 
  data, 
  isLoading = false, 
  error = null,
  onTimeframeChange,
  className = ""
}: TrendsChartProps) {
  const [timeframe, setTimeframe] = useState("today 3-y")
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; data: TrendDataPoint } | null>(null)

  const handleTimeframeChange = (value: string) => {
    setTimeframe(value)
    onTimeframeChange?.(value)
  }

  // Calculate chart dimensions and points
  const chartData = useMemo(() => {
    if (!data?.data || data.data.length === 0) return null

    const values = data.data.map(d => d.value)
    const maxValue = Math.max(...values)
    const minValue = Math.min(...values)
    const range = maxValue - minValue || 1

    // SVG dimensions
    const width = 100
    const height = 100
    const padding = { top: 10, right: 5, bottom: 10, left: 5 }
    const chartWidth = width - padding.left - padding.right
    const chartHeight = height - padding.top - padding.bottom

    // Generate path points
    const points = data.data.map((point, index) => {
      const x = padding.left + (index / (data.data.length - 1)) * chartWidth
      const y = padding.top + chartHeight - ((point.value - minValue) / range) * chartHeight
      return { x, y, data: point }
    })

    // Create SVG path
    const pathD = points
      .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
      .join(" ")

    // Create area path (for gradient fill)
    const areaD = `${pathD} L ${points[points.length - 1].x} ${height - padding.bottom} L ${padding.left} ${height - padding.bottom} Z`

    return { points, pathD, areaD, maxValue, minValue }
  }, [data])

  // Y-axis labels
  const yAxisLabels = useMemo(() => {
    if (!chartData) return []
    const { maxValue, minValue } = chartData
    const step = (maxValue - minValue) / 4
    return [
      formatNumber(maxValue),
      formatNumber(maxValue - step),
      formatNumber(maxValue - step * 2),
      formatNumber(maxValue - step * 3),
      formatNumber(minValue),
    ]
  }, [chartData])

  // X-axis labels (show ~5 dates)
  const xAxisLabels = useMemo(() => {
    if (!data?.data || data.data.length === 0) return []
    const step = Math.floor(data.data.length / 4)
    return [0, step, step * 2, step * 3, data.data.length - 1]
      .map(i => data.data[i]?.date)
      .filter(Boolean)
      .map(d => formatDate(d))
  }, [data])

  const GrowthIndicator = ({ rate }: { rate: number }) => {
    if (rate > 5) {
      return (
        <div className="flex items-center gap-1 text-emerald-400">
          <TrendingUp className="w-4 h-4" />
          <span className="font-bold">+{rate}%</span>
        </div>
      )
    }
    if (rate < -5) {
      return (
        <div className="flex items-center gap-1 text-red-400">
          <TrendingDown className="w-4 h-4" />
          <span className="font-bold">{rate}%</span>
        </div>
      )
    }
    return (
      <div className="flex items-center gap-1 text-muted-foreground">
        <Minus className="w-4 h-4" />
        <span className="font-bold">{rate > 0 ? "+" : ""}{rate}%</span>
      </div>
    )
  }

  if (isLoading) {
    return (
      <Card className={`bg-card border-border/50 p-6 ${className}`}>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-8 w-32" />
          </div>
          <div className="flex gap-8">
            <Skeleton className="h-16 w-24" />
            <Skeleton className="h-16 w-24" />
          </div>
          <Skeleton className="h-[200px] w-full" />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={`bg-card border-border/50 p-6 ${className}`}>
        <div className="text-center py-8">
          <Search className="w-12 h-12 mx-auto text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground">{error}</p>
        </div>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card className={`bg-card border-border/50 p-6 ${className}`}>
        <div className="text-center py-8">
          <Search className="w-12 h-12 mx-auto text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground">No trend data available</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className={`bg-card border-border/50 p-6 ${className}`}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30 px-3 py-1">
              <Search className="w-3 h-3 mr-1.5" />
              Keyword
            </Badge>
            <span className="text-lg font-semibold text-foreground">{data.keyword}</span>
          </div>
          
          <Select value={timeframe} onValueChange={handleTimeframeChange}>
            <SelectTrigger className="w-[140px] bg-background/50 border-border/50">
              <Calendar className="w-4 h-4 mr-2 text-muted-foreground" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today 3-m">3 Months</SelectItem>
              <SelectItem value="today 12-m">12 Months</SelectItem>
              <SelectItem value="today 3-y">3 Years</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Metrics */}
        <div className="flex items-center gap-8 flex-wrap">
          <div>
            <p className="text-3xl font-bold text-foreground bg-gradient-to-r from-white via-blue-200 to-[#444df6] bg-clip-text text-transparent">
              {formatNumber(data.current_volume)}
            </p>
            <p className="text-sm text-muted-foreground flex items-center gap-1">
              Volume <span className="text-xs opacity-60">(est.)</span>
            </p>
          </div>
          
          <div>
            <div className="text-2xl font-bold">
              <GrowthIndicator rate={data.growth_rate} />
            </div>
            <p className="text-sm text-muted-foreground">Growth (YoY)</p>
          </div>
        </div>

        {/* Chart */}
        <div className="relative">
          {/* Y-axis labels */}
          <div className="absolute left-0 top-0 bottom-8 w-12 flex flex-col justify-between text-xs text-muted-foreground">
            {yAxisLabels.map((label, i) => (
              <span key={i}>{label}</span>
            ))}
          </div>

          {/* Chart area */}
          <div className="ml-14 relative">
            <svg
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
              className="w-full h-[200px]"
              onMouseLeave={() => setHoveredPoint(null)}
            >
              {/* Gradient definition */}
              <defs>
                <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#444df6" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#444df6" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#ffffff" />
                  <stop offset="50%" stopColor="#93c5fd" />
                  <stop offset="100%" stopColor="#444df6" />
                </linearGradient>
              </defs>

              {/* Grid lines */}
              {[0, 25, 50, 75, 100].map((y) => (
                <line
                  key={y}
                  x1="5"
                  y1={10 + (y / 100) * 80}
                  x2="95"
                  y2={10 + (y / 100) * 80}
                  stroke="currentColor"
                  strokeOpacity="0.1"
                  strokeWidth="0.5"
                />
              ))}

              {/* Area fill */}
              {chartData && (
                <path
                  d={chartData.areaD}
                  fill="url(#chartGradient)"
                />
              )}

              {/* Line */}
              {chartData && (
                <path
                  d={chartData.pathD}
                  fill="none"
                  stroke="url(#lineGradient)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  vectorEffect="non-scaling-stroke"
                />
              )}

              {/* Hover points */}
              {chartData?.points.map((point, i) => (
                <circle
                  key={i}
                  cx={point.x}
                  cy={point.y}
                  r="2"
                  fill={hoveredPoint?.data.date === point.data.date ? "#444df6" : "transparent"}
                  stroke={hoveredPoint?.data.date === point.data.date ? "#fff" : "transparent"}
                  strokeWidth="1"
                  className="cursor-pointer"
                  onMouseEnter={() => setHoveredPoint(point)}
                />
              ))}
            </svg>

            {/* Tooltip */}
            {hoveredPoint && (
              <div
                className="absolute bg-card border border-border/50 rounded-lg shadow-xl px-3 py-2 pointer-events-none z-10"
                style={{
                  left: `${hoveredPoint.x}%`,
                  top: `${hoveredPoint.y}%`,
                  transform: "translate(-50%, -120%)",
                }}
              >
                <p className="text-xs text-muted-foreground">{formatDate(hoveredPoint.data.date)}</p>
                <p className="text-sm font-bold text-foreground">
                  {formatNumber(hoveredPoint.data.value * 100)} searches
                </p>
              </div>
            )}

            {/* X-axis labels */}
            <div className="flex justify-between mt-2 text-xs text-muted-foreground">
              {xAxisLabels.map((label, i) => (
                <span key={i}>{label}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

// Hook to fetch trend data
export function useTrendData(keyword: string, timeframe: string = "today 3-y") {
  const [data, setData] = useState<KeywordTrendData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTrends = async () => {
    if (!keyword) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_TRENDS_API_URL || 'http://localhost:8001'}/api/trends/keyword?keyword=${encodeURIComponent(keyword)}&timeframe=${encodeURIComponent(timeframe)}`
      )
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Failed to fetch trend data")
      }
      
      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch trend data")
    } finally {
      setIsLoading(false)
    }
  }

  return { data, isLoading, error, fetchTrends, setData }
}

// Demo data for when API is not available
export const demoTrendData: KeywordTrendData = {
  keyword: "Retirement savings plan",
  data: [
    { date: "2022-01-01", value: 32 },
    { date: "2022-03-01", value: 28 },
    { date: "2022-06-01", value: 35 },
    { date: "2022-09-01", value: 30 },
    { date: "2022-12-01", value: 38 },
    { date: "2023-03-01", value: 45 },
    { date: "2023-06-01", value: 35 },
    { date: "2023-09-01", value: 38 },
    { date: "2024-01-01", value: 42 },
    { date: "2024-04-01", value: 80 },
    { date: "2024-07-01", value: 55 },
    { date: "2024-10-01", value: 65 },
    { date: "2025-01-01", value: 72 },
    { date: "2025-04-01", value: 58 },
    { date: "2025-07-01", value: 90 },
    { date: "2025-08-01", value: 54 },
    { date: "2025-10-01", value: 150 },
  ],
  current_volume: 8100,
  growth_rate: 179,
  avg_volume: 5400,
  max_volume: 15000,
  min_volume: 2800,
  timeframe: "today 3-y"
}

