import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Square, Settings, Send } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge, RiskBadge } from '@/components/ui/Badge'

const StreamMonitor: React.FC = () => {
  const [isStreaming, setIsStreaming] = useState(false)
  const [message, setMessage] = useState('Tell me about patient John Doe with SSN 123-45-6789')

  const mockStreamData = {
    tokens: [
      { text: 'I', risk: 0.0, timestamp: '14:32:01.123' },
      { text: ' can', risk: 0.0, timestamp: '14:32:01.156' },
      { text: ' help', risk: 0.1, timestamp: '14:32:01.189' },
      { text: ' with', risk: 0.1, timestamp: '14:32:01.223' },
      { text: ' patient', risk: 0.7, timestamp: '14:32:01.256' },
      { text: ' information', risk: 0.8, timestamp: '14:32:01.289' },
      { text: '.', risk: 0.3, timestamp: '14:32:01.323' },
      { text: ' John', risk: 0.9, timestamp: '14:32:01.356' },
      { text: ' Doe', risk: 1.1, timestamp: '14:32:01.389', blocked: true },
    ]
  }

  const handleStartStream = () => {
    setIsStreaming(true)
    // Simulate streaming
    setTimeout(() => setIsStreaming(false), 3000)
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
            Live Stream Monitor
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Real-time visualization of token streaming and compliance decisions
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Stream Settings
          </Button>
          <Button 
            variant={isStreaming ? "danger" : "primary"}
            onClick={() => isStreaming ? setIsStreaming(false) : handleStartStream()}
            icon={isStreaming ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          >
            {isStreaming ? 'Stop Stream' : 'Start Stream'}
          </Button>
        </div>
      </motion.div>

      {/* Message Input */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle size="sm">Test Message</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-3">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Enter a message to test compliance streaming..."
                className="flex-1 p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                rows={3}
              />
              <Button 
                variant="primary" 
                disabled={!message.trim() || isStreaming}
                onClick={handleStartStream}
                icon={<Send className="w-4 h-4" />}
              >
                Stream
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Token Visualization */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle size="sm">Token Flow</CardTitle>
                <Badge variant={isStreaming ? "info" : "secondary"}>
                  {isStreaming ? "Streaming" : "Idle"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 min-h-[300px]">
                <AnimatePresence mode="popLayout">
                  {mockStreamData.tokens.map((token, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20, scale: 0.8 }}
                      animate={{ opacity: 1, x: 0, scale: 1 }}
                      exit={{ opacity: 0, x: 20, scale: 0.8 }}
                      transition={{ 
                        delay: isStreaming ? index * 0.3 : 0,
                        duration: 0.2 
                      }}
                      className={`
                        flex items-center justify-between p-3 rounded-lg border-l-4
                        ${token.blocked 
                          ? 'border-red-500 bg-red-50 dark:bg-red-900/20' 
                          : token.risk >= 0.7
                          ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20'
                          : token.risk >= 0.3
                          ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                          : 'border-green-500 bg-green-50 dark:bg-green-900/20'
                        }
                      `}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="font-mono text-sm font-medium">
                          "{token.text}"
                        </span>
                        {token.blocked && (
                          <Badge variant="danger" size="sm">
                            BLOCKED
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <RiskBadge score={token.risk} />
                        <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                          {token.timestamp}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                
                {!isStreaming && mockStreamData.tokens.length === 0 && (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <div className="text-4xl mb-4">🎯</div>
                    <p className="font-medium mb-2">No stream active</p>
                    <p className="text-sm">Start a stream to see token-by-token analysis</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Decision Timeline */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle size="sm">Decision Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 min-h-[300px]">
                <div className="flex items-start space-x-4">
                  <div className="flex flex-col items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full" />
                    <div className="w-px h-8 bg-gray-200 dark:bg-gray-700" />
                  </div>
                  <div className="flex-1 pb-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">Stream Started</span>
                      <span className="text-xs text-gray-500">14:32:01.123</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Processing message: "{message.slice(0, 50)}..."
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="flex flex-col items-center">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                    <div className="w-px h-8 bg-gray-200 dark:bg-gray-700" />
                  </div>
                  <div className="flex-1 pb-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">Risk Threshold Exceeded</span>
                      <span className="text-xs text-gray-500">14:32:01.356</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Token "John" scored 0.9, approaching block threshold
                    </p>
                    <div className="flex space-x-2 mt-2">
                      <Badge variant="warning" size="sm">PHI Detected</Badge>
                      <Badge variant="info" size="sm">Name Pattern</Badge>
                    </div>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="flex flex-col items-center">
                    <div className="w-3 h-3 bg-red-500 rounded-full" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">Stream Blocked</span>
                      <span className="text-xs text-gray-500">14:32:01.389</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Token "Doe" pushed cumulative score to 1.1, exceeding threshold
                    </p>
                    <div className="flex space-x-2 mt-2">
                      <Badge variant="danger" size="sm">BLOCKED</Badge>
                      <Badge variant="warning" size="sm">HIPAA Violation</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Risk Score Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardHeader>
            <CardTitle size="sm">Real-time Risk Scoring</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-32 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-center justify-center">
              <p className="text-gray-500 dark:text-gray-400">
                Risk score visualization will appear here during streaming
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default StreamMonitor