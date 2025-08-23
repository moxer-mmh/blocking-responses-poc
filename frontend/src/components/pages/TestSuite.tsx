import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Play, RefreshCw, Download, Settings } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { StatusBadge } from '@/components/ui/Badge'
import { useConnection } from '@/utils/useConnection'
import { apiClient } from '@/utils/api'

const TestSuite: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false)
  const [testSuites, setTestSuites] = useState<any[]>([
    {
      id: 'basic',
      name: 'Basic Functionality', 
      description: 'Core API endpoints and health checks',
      tests: 3,
      status: 'completed',
      passed: 3,
      failed: 0,
    },
    {
      id: 'patterns',
      name: 'Pattern Detection',
      description: 'Regex pattern detection accuracy', 
      tests: 4,
      status: 'completed',
      passed: 4,
      failed: 0,
    },
    {
      id: 'presidio',
      name: 'Presidio Integration',
      description: 'Microsoft Presidio ML detection',
      tests: 3,
      status: 'running',
      passed: 2,
      failed: 0,
    },
    {
      id: 'streaming',
      name: 'SSE Streaming',
      description: 'Server-Sent Events and validation',
      tests: 3,
      status: 'pending',
      passed: 0,
      failed: 0,
    }
  ])
  const [testOutput, setTestOutput] = useState<string>('')
  const isConnected = useConnection()

  // Load test suites on component mount
  useEffect(() => {
    loadTestSuites()
  }, [isConnected])

  const loadTestSuites = async () => {
    if (!isConnected) return
    
    try {
      const response = await apiClient.getAllTestSuites()
      if (response.success && response.data) {
        setTestSuites(response.data.suites || [])
      }
    } catch (error) {
      console.error('Error loading test suites:', error)
    }
  }

  const handleRunTests = async () => {
    if (!isConnected) return
    
    setIsRunning(true)
    setTestOutput('🚀 Starting test suite execution...\n')
    
    try {
      const response = await apiClient.runTestSuite(['basic', 'patterns'])
      if (response.success && response.data) {
        const data = response.data
        setTestOutput(prev => prev + `✅ Test session started: ${data.session_id}\n`)
        setTestOutput(prev => prev + `📊 Status: ${data.status}\n`)
        
        if (data.output) {
          setTestOutput(prev => prev + `\n📝 Test Output:\n${data.output}\n`)
        }
        
        // Reload test suites to update status
        await loadTestSuites()
      } else {
        setTestOutput(prev => prev + `❌ Error: ${response.error}\n`)
      }
    } catch (error) {
      setTestOutput(prev => prev + `💥 Exception: ${error}\n`)
    } finally {
      setIsRunning(false)
    }
  }

  const handleRunSingleSuite = async (suiteId: string) => {
    if (!isConnected) return
    
    setTestOutput(`🔄 Running ${suiteId} suite...\n`)
    
    try {
      const response = await apiClient.runTestSuite([suiteId])
      if (response.success && response.data) {
        const data = response.data
        setTestOutput(prev => prev + `✅ ${suiteId} completed: ${data.status}\n`)
        if (data.output) {
          setTestOutput(prev => prev + data.output + '\n')
        }
      }
    } catch (error) {
      setTestOutput(prev => prev + `❌ ${suiteId} failed: ${error}\n`)
    }
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

      {/* Connection Status Warning */}
      {!isConnected && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4"
        >
          <div className="flex items-center space-x-3">
            <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
            <span className="text-amber-800 dark:text-amber-200 font-medium">
              Connection to backend API is unavailable. Some features may be limited.
            </span>
          </div>
        </motion.div>
      )}

      {/* Test Suites Grid */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 gap-6"
      >
        {testSuites.map((suite: any, index: number) => (
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
                      onClick={() => handleRunSingleSuite(suite.id)}
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
              {testOutput ? (
                <pre className="text-green-400 whitespace-pre-wrap">
                  {testOutput}
                </pre>
              ) : (
                <div className="text-gray-500">
                  Test output will appear here when tests are running...
                </div>
              )}
              {isRunning && !testOutput && (
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