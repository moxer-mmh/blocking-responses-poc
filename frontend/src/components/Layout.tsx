import React, { useEffect } from 'react'
import { motion } from 'framer-motion'
import Sidebar from './Sidebar'
import Header from './Header'
import { useDashboardStore } from '@/stores/dashboard'
import { useConnection } from '@/utils/useConnection'
import { apiClient } from '@/utils/api'
import { notificationManager } from '@/utils/notifications'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isConnected, updateMetrics, addHistoricalMetric, realtimeMetrics } = useDashboardStore()
  const connectionStatus = useConnection()
  const prevMetricsRef = React.useRef(realtimeMetrics)

  // Global metrics loading - ensures header always has current data
  useEffect(() => {
    if (!connectionStatus) return

    const fetchGlobalMetrics = async () => {
      try {
        const metricsResponse = await apiClient.getMetrics()
        if (metricsResponse.success && metricsResponse.data) {
          const newMetrics = metricsResponse.data
          const prevMetrics = prevMetricsRef.current
          
          // Check for significant changes and create notifications
          if (prevMetrics.total_requests > 0) { // Only if we have previous data
            // High block rate notification
            if (newMetrics.block_rate > 20 && prevMetrics.block_rate <= 20) {
              notificationManager.onHighBlockRate(newMetrics.block_rate)
            }
            
            // New blocked requests notification
            if (newMetrics.blocked_requests > prevMetrics.blocked_requests) {
              const newBlocked = newMetrics.blocked_requests - prevMetrics.blocked_requests
              if (newBlocked >= 5) { // Only notify for significant increases
                notificationManager.addNotification({
                  type: 'warning',
                  title: 'Multiple Requests Blocked',
                  message: `${newBlocked} additional requests have been blocked due to compliance violations.`
                })
              }
            }
          }
          
          updateMetrics(newMetrics)
          
          // Add historical metric point for charts
          const historicalPoint = {
            timestamp: new Date().toISOString(),
            total_requests: newMetrics.total_requests,
            blocked_requests: newMetrics.blocked_requests,
            block_rate: newMetrics.block_rate,
            avg_risk_score: newMetrics.avg_risk_score,
            avg_processing_time: newMetrics.performance_metrics.avg_processing_time,
            requests_per_second: newMetrics.performance_metrics.requests_per_second,
          }
          addHistoricalMetric(historicalPoint)
          
          prevMetricsRef.current = newMetrics
        }
      } catch (error) {
        console.error('Failed to fetch global metrics:', error)
        notificationManager.addNotification({
          type: 'error',
          title: 'Connection Issue',
          message: 'Failed to fetch latest metrics from the server.'
        })
      }
    }

    // Initial fetch
    fetchGlobalMetrics()

    // Set up periodic refresh - more frequent for better chart granularity
    const interval = setInterval(fetchGlobalMetrics, 10000) // Every 10 seconds for smoother charts

    return () => clearInterval(interval)
  }, [connectionStatus, updateMetrics])

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />
        
        {/* Connection Status Banner */}
        {!isConnected && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-warning-100 dark:bg-warning-900/20 border-b border-warning-200 dark:border-warning-800"
          >
            <div className="px-6 py-2">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-warning-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-warning-700 dark:text-warning-400">
                    Connection to backend API is unavailable. Some features may be limited.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
        
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout