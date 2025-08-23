import React, { useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Activity,
  TrendingUp,
  Clock,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge, RiskBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useDashboardStore, useTestSuiteStats } from '@/stores/dashboard'
import { formatNumber, formatPercent, formatters } from '@/utils'
import MetricsChart from '@/components/charts/MetricsChart'
import ComplianceBreakdown from '@/components/charts/ComplianceBreakdown'
import RecentActivity from '@/components/RecentActivity'
import { apiClient } from '@/utils/api'

const Dashboard: React.FC = () => {
  const {
    realtimeMetrics,
    testSuiteResults,
    isConnected,
    lastUpdate,
    setIsConnected,
    updateMetrics,
  } = useDashboardStore()

  const testStats = useTestSuiteStats()

  // Test API connection and fetch initial data
  useEffect(() => {
    const testConnection = async () => {
      try {
        const healthResponse = await apiClient.getHealth()
        if (healthResponse.success) {
          setIsConnected(true)
          
          // Fetch initial metrics
          const metricsResponse = await apiClient.getMetrics()
          if (metricsResponse.success && metricsResponse.data) {
            updateMetrics(metricsResponse.data)
          }
        } else {
          setIsConnected(false)
        }
      } catch (error) {
        console.error('Connection test failed:', error)
        setIsConnected(false)
      }
    }

    testConnection()
    
    // Set up periodic connection checking and metrics refresh
    const interval = setInterval(testConnection, 30000) // Every 30 seconds
    
    return () => clearInterval(interval)
  }, [setIsConnected, updateMetrics])

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 },
  }

  // Calculate key metrics
  const blockRate = realtimeMetrics.block_rate
  const avgProcessingTime = realtimeMetrics.performance_metrics.avg_processing_time
  const totalPatternDetections = Object.values(realtimeMetrics.pattern_detections)
    .reduce((sum, count) => sum + count, 0)
  const totalPresidioDetections = Object.values(realtimeMetrics.presidio_detections)
    .reduce((sum, count) => sum + count, 0)

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* Hero Stats */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <Card className="gradient-primary text-white border-0">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm font-medium">Total Requests</p>
                <p className="text-3xl font-bold">
                  {formatNumber(realtimeMetrics.total_requests)}
                </p>
                <p className="text-blue-100 text-sm mt-1">
                  {realtimeMetrics.performance_metrics.requests_per_second.toFixed(1)} req/sec
                </p>
              </div>
              <div className="bg-white/20 p-3 rounded-lg">
                <Activity className="w-8 h-8" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={`text-white border-0 ${
          blockRate > 10 ? 'gradient-danger' : 
          blockRate > 5 ? 'gradient-warning' : 'gradient-success'
        }`}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white/80 text-sm font-medium">Block Rate</p>
                <p className="text-3xl font-bold">
                  {formatPercent(blockRate / 100)}
                </p>
                <p className="text-white/80 text-sm mt-1">
                  {realtimeMetrics.blocked_requests} blocked
                </p>
              </div>
              <div className="bg-white/20 p-3 rounded-lg">
                {blockRate > 10 ? <AlertTriangle className="w-8 h-8" /> : 
                 blockRate > 5 ? <Shield className="w-8 h-8" /> : 
                 <CheckCircle className="w-8 h-8" />}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">
                  Avg Risk Score
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {realtimeMetrics.avg_risk_score.toFixed(2)}
                </p>
                <div className="mt-1">
                  <RiskBadge score={realtimeMetrics.avg_risk_score} />
                </div>
              </div>
              <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-lg">
                <TrendingUp className="w-8 h-8 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">
                  Processing Time
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {avgProcessingTime.toFixed(0)}ms
                </p>
                <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
                  Average response
                </p>
              </div>
              <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-lg">
                <Clock className="w-8 h-8 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Test Suite Status */}
      {testSuiteResults.length > 0 && (
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Test Suite Status</CardTitle>
                <Badge variant="info">
                  {testStats.totalSuites} Suites
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-success-600 dark:text-success-400">
                    {testStats.passedTests}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Passed Tests
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-danger-600 dark:text-danger-400">
                    {testStats.failedTests}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Failed Tests
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-600 dark:text-primary-400">
                    {testStats.successRate.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Success Rate
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Overall Progress</span>
                  <span className="text-sm text-gray-500">
                    {testStats.passedTests + testStats.failedTests} / {testStats.totalTests}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-success-600 h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${testStats.totalTests > 0 ? 
                        (testStats.passedTests / testStats.totalTests) * 100 : 0}%`
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Charts Section */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <MetricsChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compliance Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <ComplianceBreakdown />
          </CardContent>
        </Card>
      </motion.div>

      {/* Detection Summary */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Detection Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Pattern Detections */}
              <div>
                <h4 className="font-semibold mb-4 text-gray-900 dark:text-white">
                  Pattern Detections ({totalPatternDetections})
                </h4>
                <div className="space-y-3">
                  {Object.entries(realtimeMetrics.pattern_detections)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([pattern, count]) => (
                      <div key={pattern} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                          {pattern.replace(/_/g, ' ')}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium">{count}</span>
                          <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-primary-500 h-2 rounded-full"
                              style={{
                                width: `${totalPatternDetections > 0 ? 
                                  (count / totalPatternDetections) * 100 : 0}%`
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {/* Presidio Detections */}
              <div>
                <h4 className="font-semibold mb-4 text-gray-900 dark:text-white">
                  Presidio Detections ({totalPresidioDetections})
                </h4>
                <div className="space-y-3">
                  {Object.entries(realtimeMetrics.presidio_detections)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([entity, count]) => (
                      <div key={entity} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {entity.replace(/_/g, ' ')}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium">{count}</span>
                          <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-orange-500 h-2 rounded-full"
                              style={{
                                width: `${totalPresidioDetections > 0 ? 
                                  (count / totalPresidioDetections) * 100 : 0}%`
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Activity */}
      <motion.div variants={itemVariants}>
        <RecentActivity />
      </motion.div>

      {/* Quick Actions */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <Button variant="primary">
                Run Full Test Suite
              </Button>
              <Button variant="secondary">
                View Live Stream
              </Button>
              <Button variant="outline">
                Export Audit Report
              </Button>
              <Button variant="ghost">
                System Health Check
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Footer Info */}
      <motion.div variants={itemVariants} className="text-center text-sm text-gray-500 dark:text-gray-400">
        Last updated: {formatters.relative(lastUpdate)} • 
        {isConnected ? ' Connected' : ' Disconnected'} • 
        Regulated Edition v1.1.0
      </motion.div>
    </motion.div>
  )
}

export default Dashboard