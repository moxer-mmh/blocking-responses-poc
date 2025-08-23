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
  const { updateMetrics, addHistoricalMetric, realtimeMetrics } = useDashboardStore()
  const connectionStatus = useConnection()
  const prevMetricsRef = React.useRef(realtimeMetrics)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false)

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false)
  }

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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Sidebar */}
      <Sidebar isOpen={isMobileMenuOpen} onClose={closeMobileMenu} />
      
      {/* Main Content */}
      <div className="flex flex-col flex-1 lg:ml-0">
        {/* Header */}
        <Header onMobileMenuToggle={toggleMobileMenu} />
        
        {/* Page Content */}
        <main className="flex-1 px-3 sm:px-6 p-3 sm:p-4 lg:p-6 overflow-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  )
}

export default Layout