import React, { useMemo } from 'react'
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { useDashboardStore } from '@/stores/dashboard'
import { formatters } from '@/utils'

interface MetricsDataPoint {
  timestamp: string
  requests: number
  blocked: number
  blockRate: number
  avgRiskScore: number
  processingTime: number
}

const MetricsChart: React.FC = () => {
  const { realtimeMetrics } = useDashboardStore()

  // Generate time-series data based on actual metrics
  const chartData: MetricsDataPoint[] = useMemo(() => {
    const now = Date.now()
    const data: MetricsDataPoint[] = []
    
    // Use real metrics for the latest data point, and simulate minimal historical trend
    const currentRequests = realtimeMetrics.total_requests
    const currentBlocked = realtimeMetrics.blocked_requests
    const currentBlockRate = realtimeMetrics.block_rate
    const currentRiskScore = realtimeMetrics.avg_risk_score
    const currentProcessingTime = realtimeMetrics.performance_metrics.avg_processing_time
    
    // Show data points for the last 10 time periods (every 1 minute = 10 minutes total)
    for (let i = 9; i >= 0; i--) {
      const timestamp = new Date(now - (i * 60000)).toISOString() // Every minute
      
      if (i === 0) {
        // Use actual current data for the latest point
        data.push({
          timestamp: formatters.time(timestamp),
          requests: currentRequests,
          blocked: currentBlocked,
          blockRate: currentBlockRate,
          avgRiskScore: currentRiskScore,
          processingTime: currentProcessingTime,
        })
      } else if (i <= 2) {
        // Recent history with minimal variation (last 2-3 minutes)
        const requestsVariation = Math.max(0, currentRequests - i)
        const blockedVariation = Math.max(0, currentBlocked - i)
        
        data.push({
          timestamp: formatters.time(timestamp),
          requests: requestsVariation,
          blocked: blockedVariation,
          blockRate: requestsVariation > 0 ? (blockedVariation / requestsVariation) * 100 : 0,
          avgRiskScore: Math.max(0, currentRiskScore - (i * 0.1)),
          processingTime: Math.max(20, currentProcessingTime - (i * 5)),
        })
      } else {
        // Older points with minimal data (historical baseline)
        data.push({
          timestamp: formatters.time(timestamp),
          requests: 0,
          blocked: 0,
          blockRate: 0,
          avgRiskScore: 0,
          processingTime: 25,
        })
      }
    }
    
    return data
  }, [realtimeMetrics])

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            {label}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${
                entry.name === 'Block Rate' 
                  ? `${entry.value.toFixed(1)}%`
                  : entry.name === 'Processing Time'
                  ? `${entry.value}ms`
                  : entry.name === 'Avg Risk Score'
                  ? entry.value.toFixed(2)
                  : entry.value
              }`}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="requests" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="blocked" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#374151" 
            opacity={0.2} 
          />
          <XAxis
            dataKey="timestamp"
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="requests"
            stroke="#3b82f6"
            fillOpacity={1}
            fill="url(#requests)"
            strokeWidth={2}
            name="Requests"
          />
          <Area
            type="monotone"
            dataKey="blocked"
            stroke="#ef4444"
            fillOpacity={1}
            fill="url(#blocked)"
            strokeWidth={2}
            name="Blocked"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default MetricsChart