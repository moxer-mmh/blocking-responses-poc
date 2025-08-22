import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Play, RefreshCw, Download, Settings } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { StatusBadge } from '@/components/ui/Badge'

const TestSuite: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false)

  const mockTestSuites = [
    {
      id: 'basic',
      name: 'Basic Functionality',
      description: 'Core API endpoints and health checks',
      tests: 3,
      status: 'completed' as const,
      passed: 3,
      failed: 0,
    },
    {
      id: 'patterns',
      name: 'Pattern Detection',
      description: 'Regex pattern detection accuracy',
      tests: 4,
      status: 'completed' as const,
      passed: 4,
      failed: 0,
    },
    {
      id: 'presidio',
      name: 'Presidio Integration',
      description: 'Microsoft Presidio ML detection',
      tests: 3,
      status: 'running' as const,
      passed: 2,
      failed: 0,
    },
    {
      id: 'streaming',
      name: 'SSE Streaming',
      description: 'Server-Sent Events and validation',
      tests: 3,
      status: 'pending' as const,
      passed: 0,
      failed: 0,
    },
  ]

  const handleRunTests = () => {
    setIsRunning(true)
    // Simulate test run
    setTimeout(() => setIsRunning(false), 5000)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Test Suite Runner
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Execute comprehensive compliance tests and monitor results in real-time
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Configure
          </Button>
          <Button 
            variant="primary"
            loading={isRunning}
            onClick={handleRunTests}
            icon={isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          >
            {isRunning ? 'Running Tests...' : 'Run All Tests'}
          </Button>
        </div>
      </motion.div>

      {/* Test Suites Grid */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 gap-6"
      >
        {mockTestSuites.map((suite, index) => (
          <motion.div
            key={suite.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index }}
          >
            <Card hover className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle size="sm">{suite.name}</CardTitle>
                  <StatusBadge status={suite.status} animate />
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {suite.description}
                </p>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-4">
                  {/* Progress Bar */}
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-600 dark:text-gray-400">
                        Progress
                      </span>
                      <span className="font-medium">
                        {suite.passed + suite.failed} / {suite.tests}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ 
                          width: `${((suite.passed + suite.failed) / suite.tests) * 100}%` 
                        }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="bg-primary-600 h-2 rounded-full"
                      />
                    </div>
                  </div>

                  {/* Test Results */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-success-600 dark:text-success-400">
                        {suite.passed}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        Passed
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-danger-600 dark:text-danger-400">
                        {suite.failed}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        Failed
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2">
                    <Button 
                      variant="secondary" 
                      size="sm" 
                      className="flex-1"
                      disabled={isRunning}
                    >
                      <Play className="w-3 h-3 mr-1" />
                      Run
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Download className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Live Test Output */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Live Test Output</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-900 dark:bg-gray-950 rounded-lg p-4 font-mono text-sm min-h-[300px] max-h-[400px] overflow-y-auto">
              <div className="text-green-400">
                ✓ TestBasicFunctionality::test_health_endpoint PASSED
              </div>
              <div className="text-green-400">
                ✓ TestBasicFunctionality::test_metrics_endpoint PASSED  
              </div>
              <div className="text-green-400">
                ✓ TestBasicFunctionality::test_config_endpoint PASSED
              </div>
              <div className="text-green-400">
                ✓ TestPatternDetection::test_email_detection_regex PASSED
              </div>
              <div className="text-green-400">
                ✓ TestPatternDetection::test_ssn_detection_regex PASSED
              </div>
              <div className="text-green-400">
                ✓ TestPatternDetection::test_credit_card_detection PASSED
              </div>
              <div className="text-green-400">
                ✓ TestPatternDetection::test_phone_detection PASSED
              </div>
              <div className="text-yellow-400">
                → TestPresidioIntegration::test_email_detection_presidio RUNNING
              </div>
              {isRunning && (
                <div className="text-yellow-400 animate-pulse">
                  → Running compliance detection tests...
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default TestSuite