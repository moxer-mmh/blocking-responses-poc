import React, { useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
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
import { useNotifications } from '@/components/ui/Notifications'
import { useDashboardStore, useTestSuiteStats } from '@/stores/dashboard'
import { formatNumber, formatPercent, formatters } from '@/utils'
import { useConnection } from '@/utils/useConnection'
import MetricsChart from '@/components/charts/MetricsChart'
import ComplianceBreakdown from '@/components/charts/ComplianceBreakdown'
import RecentActivity from '@/components/RecentActivity'
import { apiClient } from '@/utils/api'
import { AuditEvent } from '@/types'

const Dashboard: React.FC = () => {
  const {
    realtimeMetrics,
    testSuiteResults,
    lastUpdate,
    updateMetrics,
    setAuditEvents,
    setTestOutput,
    appendTestOutput,
  } = useDashboardStore()

  const isConnected = useConnection()
  const testStats = useTestSuiteStats()
  const navigate = useNavigate()
  const { success, error } = useNotifications()

  // Quick Action handlers
  const handleRunTestSuite = async () => {
    try {
      // Clear and start fresh output
      setTestOutput('🚀 Starting full test suite execution...\n')
      
      // First test simple compliance assessment to generate real data
      const testMessage = "Test SSN: 123-45-6789 for compliance blocking"
      appendTestOutput(`📝 Testing compliance with message: "${testMessage}"\n`)
      
      const assessmentResponse = await apiClient.assessRisk(testMessage)
      if (assessmentResponse.success) {
        appendTestOutput(`⚡ Risk assessment complete: Score ${assessmentResponse.data?.score}, Blocked: ${assessmentResponse.data?.blocked}\n`)
      }
      
      const response = await apiClient.runTestSuite(['basic', 'patterns', 'presidio', 'streaming'])
      if (response.success && response.data) {
        const data = response.data
        appendTestOutput(`✅ Test session started: ${data.session_id}\n`)
        appendTestOutput(`📊 Status: ${data.status}\n`)
        
        if (data.output) {
          appendTestOutput(`\n📝 Test Output:\n${data.output}\n`)
        }
        
        // Navigate to test suite page with output preserved
        navigate('/testing')
        
        // Show success notification with actual results
        const { passed, failed, total } = response.data.summary || { passed: 0, failed: 0, total: 0 }
        success(
          'Test Suite Completed!',
          `Results: ${passed} passed, ${failed} failed, ${total} total tests. Session: ${response.data.session_id}`
        )
      } else {
        error('Test Suite Failed', response.error || 'Unknown error occurred')
      }
    } catch (err) {
      error('Test Suite Error', `Failed to start test suite: ${err}`)
    }
  }

    const handleViewLiveStream = () => {
    // Navigate to stream monitor page
    navigate('/stream')
  }

  const handleExportAuditReport = async () => {
    try {
      const response = await apiClient.getAuditLogs(1000)
      if (response.success && response.data) {
        // Create CSV data
        const csvData = response.data.logs.map((event: AuditEvent) => ({
          timestamp: event.timestamp,
          event_type: event.event_type,
          compliance_type: event.compliance_type,
          risk_score: event.risk_score,
          blocked: event.blocked,
          session_id: event.session_id
        }))
        
        // Convert to CSV string
        const csvContent = [
          'Timestamp,Event Type,Compliance Type,Risk Score,Blocked,Session ID',
          ...csvData.map((row: any) => 
            `${row.timestamp},${row.event_type},${row.compliance_type},${row.risk_score},${row.blocked},${row.session_id}`
          )
        ].join('\n')
        
        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `audit-report-${new Date().toISOString().split('T')[0]}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Error exporting audit report:', error)
    }
  }

  const handleSystemHealthCheck = async () => {
    try {
      const response = await apiClient.getHealth()
      if (response.success) {
        success(
          'System Healthy',
          `Status: ${response.data?.status} | Version: ${response.data?.version} | All dependencies operational`
        )
      } else {
        error('Health Check Failed', response.error || 'Unknown error occurred')
      }
    } catch (err) {
      error('Health Check Error', `Failed to check system health: ${err}`)
    }
  }

  // Fetch initial metrics data
  useEffect(() => {
    const fetchMetrics = async () => {
      if (isConnected) {
        try {
          // Fetch metrics
          const metricsResponse = await apiClient.getMetrics()
          if (metricsResponse.success && metricsResponse.data) {
            updateMetrics(metricsResponse.data)
            
            // Add historical metric point for charting
            const historicalPoint = {
              timestamp: new Date().toISOString(),
              total_requests: metricsResponse.data.total_requests,
              blocked_requests: metricsResponse.data.blocked_requests,
              block_rate: metricsResponse.data.block_rate,
              avg_risk_score: metricsResponse.data.avg_risk_score,
              avg_processing_time: metricsResponse.data.performance_metrics.avg_processing_time,
              requests_per_second: metricsResponse.data.performance_metrics.requests_per_second,
            }
            useDashboardStore.getState().addHistoricalMetric(historicalPoint)
          }
          
          // Fetch recent audit events for dashboard components
          const auditResponse = await apiClient.getAuditLogs(50)
          if (auditResponse.success && auditResponse.data) {
            setAuditEvents(auditResponse.data.logs || [])
          }
        } catch (error) {
          console.error('Failed to fetch dashboard data:', error)
        }
      }
    }

    fetchMetrics()
    
    // Set up more frequent metrics refresh for live updates (every 5 seconds)
    const interval = setInterval(fetchMetrics, 5000) // Every 5 seconds
    
    return () => clearInterval(interval)
  }, [isConnected, updateMetrics, setAuditEvents])

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
      className="space-y-4 sm:space-y-6"
    >
      {/* Hero Stats - Responsive Grid */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6"
      >
        <Card className="gradient-primary text-white border-0">
          <CardContent className="p-4 sm:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-xs sm:text-sm font-medium">Total Requests</p>
                <p className="text-2xl sm:text-3xl font-bold">
                  {formatNumber(realtimeMetrics.total_requests)}
                </p>
                <p className="text-blue-100 text-xs sm:text-sm mt-1">
                  {realtimeMetrics.performance_metrics.requests_per_second.toFixed(1)} req/sec
                </p>
              </div>
              <div className="bg-white/20 p-2 sm:p-3 rounded-lg">
                <Activity className="w-6 h-6 sm:w-8 sm:h-8" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={`text-white border-0 ${
          blockRate > 10 ? 'gradient-danger' : 
          blockRate > 5 ? 'gradient-warning' : 'gradient-success'
        }`}>
          <CardContent className="p-4 sm:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white/80 text-xs sm:text-sm font-medium">Block Rate</p>
                <p className="text-2xl sm:text-3xl font-bold">
                  {formatPercent(blockRate / 100)}
                </p>
                <p className="text-white/80 text-xs sm:text-sm mt-1">
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

      {/* Charts Section - Responsive Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm sm:text-base">Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent className="p-3 sm:p-6">
            <div className="h-64 sm:h-80">
              <MetricsChart />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm sm:text-base">Compliance Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="p-3 sm:p-6">
            <div className="h-96 sm:h-[36rem] overflow-auto">
              <ComplianceBreakdown />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Detection Summary - Responsive Layout */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm sm:text-base">Detection Summary</CardTitle>
          </CardHeader>
          <CardContent className="p-3 sm:p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
              {/* Pattern Detections */}
              <div>
                <h4 className="font-semibold mb-4 text-gray-900 dark:text-white text-sm sm:text-base">
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
                  {totalPresidioDetections > 0 ? (
                    Object.entries(realtimeMetrics.presidio_detections)
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
                      ))
                  ) : (
                    <div className="text-sm text-gray-500 dark:text-gray-400 italic">
                      Custom pattern detection system active.<br/>
                      Advanced Presidio ML detection available in enterprise edition.
                    </div>
                  )}
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
              <Button variant="primary" onClick={handleRunTestSuite}>
                Run Full Test Suite
              </Button>
              <Button variant="secondary" onClick={handleViewLiveStream}>
                View Live Stream
              </Button>
              <Button variant="outline" onClick={handleExportAuditReport}>
                Export Audit Report
              </Button>
              <Button variant="success" onClick={handleSystemHealthCheck}>
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