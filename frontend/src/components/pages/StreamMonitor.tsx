import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Square, Send, Download } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge, RiskBadge } from '@/components/ui/Badge'
import { useConnection } from '@/utils/useConnection'
import { useNotifications } from '@/components/ui/Notifications'

interface StreamToken {
  text: string
  risk: number
  timestamp: string
  blocked?: boolean
  entities?: string[]
  patterns?: string[]
}

interface StreamEvent {
  id: number
  type: string
  timestamp: string
  description: string
  risk?: number
  entities?: string[]
  patterns?: string[]
}

const StreamMonitor: React.FC = () => {
  const [isStreaming, setIsStreaming] = useState(false)
  const [message, setMessage] = useState('Tell me about patient John Doe with SSN 123-45-6789')
  const [tokens, setTokens] = useState<StreamToken[]>([])
  const [events, setEvents] = useState<StreamEvent[]>([])
  const [currentResponse, setCurrentResponse] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [riskScores, setRiskScores] = useState<number[]>([])
  const evtSourceRef = useRef<EventSource | null>(null)
  const isConnected = useConnection()
  const { success, error, warning, info } = useNotifications()

  useEffect(() => {
    return () => {
      if (evtSourceRef.current) {
        evtSourceRef.current.close()
      }
    }
  }, [])

  const handleStartStream = async () => {
    if (!message.trim()) {
      warning('Invalid Input', 'Please enter a message to stream')
      return
    }

    setIsStreaming(true)
    setTokens([])
    setEvents([])
    setCurrentResponse('')
    setRiskScores([])
    
    try {
      // Get API key from localStorage
      const apiKey = localStorage.getItem('openai_api_key')
      
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          delay_tokens: 5,
          delay_ms: 100,
          risk_threshold: 1.0,
          ...(apiKey && { api_key: apiKey })
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      info('Stream Started', `Processing: "${message.slice(0, 50)}${message.length > 50 ? '...' : ''}"`)

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataContent = line.slice(6)
            
            // Handle [DONE] message
            if (dataContent === '[DONE]') {
              setIsStreaming(false)
              continue
            }
            
            try {
              const data = JSON.parse(dataContent)
              
              if (data.type === 'chunk') {
                const timestamp = new Date().toLocaleTimeString() + '.' + Date.now().toString().slice(-3)
                setTokens(prev => [...prev, {
                  text: data.content,
                  risk: data.risk_score || 0,
                  timestamp,
                  entities: data.entities || [],
                  patterns: data.patterns || []
                }])
                setCurrentResponse(prev => prev + data.content)
                setRiskScores(prev => [...prev, data.risk_score || 0])
              }
              
              if (data.type === 'risk_alert') {
                const timestamp = new Date().toLocaleTimeString() + '.' + Date.now().toString().slice(-3)
                setEvents(prev => [...prev, {
                  id: prev.length + 1,
                  type: 'risk_alert',
                  timestamp,
                  description: `High risk detected: ${data.content}`,
                  risk: data.risk_score,
                  entities: data.entities,
                  patterns: data.patterns
                }])
                warning('Risk Alert', `Token "${data.content}" scored ${data.risk_score?.toFixed(2)}`)
              }
              
              if (data.type === 'blocked') {
                const timestamp = new Date().toLocaleTimeString() + '.' + Date.now().toString().slice(-3)
                setTokens(prev => prev.map((token, idx) => 
                  idx === prev.length - 1 ? { ...token, blocked: true } : token
                ))
                setEvents(prev => [...prev, {
                  id: prev.length + 1,
                  type: 'blocked',
                  timestamp,
                  description: `Stream blocked: ${data.reason}`,
                  risk: data.risk_score
                }])
                error('Stream Blocked', data.reason || 'Content violated compliance policies')
                setIsStreaming(false)
                break
              }
              
              if (data.type === 'completed') {
                setSessionId(data.session_id)
                const timestamp = new Date().toLocaleTimeString() + '.' + Date.now().toString().slice(-3)
                setEvents(prev => [...prev, {
                  id: prev.length + 1,
                  type: 'completed',
                  timestamp,
                  description: `Stream completed successfully`
                }])
                success('Stream Completed', `Session ${data.session_id} finished successfully`)
                setIsStreaming(false)
                break
              }
              
            } catch (e) {
              console.warn('Failed to parse SSE data:', line)
            }
          }
        }
      }
    } catch (err) {
      error('Stream Error', `Failed to start stream: ${err}`)
      setIsStreaming(false)
    }
  }

  const handleStopStream = () => {
    if (evtSourceRef.current) {
      evtSourceRef.current.close()
      evtSourceRef.current = null
    }
    setIsStreaming(false)
    info('Stream Stopped', 'Stream manually stopped by user')
  }

  const handleExportSession = () => {
    if (!sessionId && tokens.length === 0) {
      warning('No Data', 'No stream session data to export')
      return
    }

    const exportData = {
      sessionId: sessionId || 'unsaved',
      message,
      timestamp: new Date().toISOString(),
      tokens,
      events,
      response: currentResponse,
      riskScores,
      maxRisk: Math.max(...riskScores, 0),
      tokenCount: tokens.length
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `stream-session-${sessionId || Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    success('Export Complete', `Session data exported as stream-session-${sessionId || Date.now()}.json`)
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
          {!isStreaming && tokens.length > 0 && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleExportSession}
              icon={<Download className="w-4 h-4" />}
            >
              Export Session
            </Button>
          )}
          <Button 
            variant={isStreaming ? "danger" : "primary"}
            onClick={() => isStreaming ? handleStopStream() : handleStartStream()}
            icon={isStreaming ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            disabled={isStreaming ? false : !message.trim()}
          >
            {isStreaming ? 'Stop Stream' : 'Start Stream'}
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
                  {tokens.map((token, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20, scale: 0.8 }}
                      animate={{ opacity: 1, x: 0, scale: 1 }}
                      exit={{ opacity: 0, x: 20, scale: 0.8 }}
                      transition={{ 
                        delay: isStreaming ? index * 0.1 : 0,
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
                        {token.entities && token.entities.length > 0 && (
                          <div className="flex space-x-1">
                            {token.entities.map((entity, idx) => (
                              <Badge key={idx} variant="warning" size="sm">
                                {typeof entity === 'string' ? entity : ((entity as any)?.entity_type || 'Unknown')}
                              </Badge>
                            ))}
                          </div>
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
                
                {!isStreaming && tokens.length === 0 && (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <div className="text-4xl mb-4">🎯</div>
                    <p className="font-medium mb-2">No stream active</p>
                    <p className="text-sm">Start a stream to see token-by-token analysis</p>
                  </div>
                )}

                {isStreaming && tokens.length === 0 && (
                  <div className="flex items-center justify-center h-48 text-blue-500">
                    <div className="text-center">
                      <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
                      <p>Starting stream...</p>
                    </div>
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
              <div className="space-y-4 min-h-[300px] max-h-[400px] overflow-y-auto">
                {events.length > 0 ? (
                  events.map((event, index) => (
                    <div key={event.id} className="flex items-start space-x-4">
                      <div className="flex flex-col items-center">
                        <div className={`w-3 h-3 rounded-full ${
                          event.type === 'blocked' ? 'bg-red-500' :
                          event.type === 'risk_alert' ? 'bg-yellow-500' :
                          event.type === 'completed' ? 'bg-green-500' :
                          'bg-blue-500'
                        }`} />
                        {index < events.length - 1 && (
                          <div className="w-px h-8 bg-gray-200 dark:bg-gray-700" />
                        )}
                      </div>
                      <div className="flex-1 pb-4">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium capitalize">
                            {event.type.replace('_', ' ')}
                          </span>
                          <span className="text-xs text-gray-500 font-mono">
                            {event.timestamp}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {event.description}
                        </p>
                        {event.entities && event.entities.length > 0 && (
                          <div className="flex space-x-1 mt-2">
                            {event.entities.map((entity, idx) => (
                              <Badge key={idx} variant="warning" size="sm">
                                {typeof entity === 'string' ? entity : ((entity as any)?.entity_type || 'Unknown')}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {event.patterns && event.patterns.length > 0 && (
                          <div className="flex space-x-1 mt-2">
                            {event.patterns.map((pattern, idx) => (
                              <Badge key={idx} variant="info" size="sm">
                                {pattern}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {event.risk !== undefined && (
                          <div className="mt-2">
                            <RiskBadge score={event.risk} />
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : !isStreaming ? (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <div className="text-4xl mb-4">📋</div>
                    <p className="font-medium mb-2">No events yet</p>
                    <p className="text-sm">Start streaming to see decision timeline</p>
                  </div>
                ) : (
                  <div className="text-center py-12 text-blue-500">
                    <div className="animate-pulse text-2xl mb-4">⏳</div>
                    <p>Waiting for stream events...</p>
                  </div>
                )}
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
            <div className="flex items-center justify-between">
              <CardTitle size="sm">Real-time Risk Scoring</CardTitle>
              {riskScores.length > 0 && (
                <div className="flex items-center space-x-4 text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600 dark:text-gray-400">Current:</span>
                    <RiskBadge score={riskScores[riskScores.length - 1]} />
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600 dark:text-gray-400">Max:</span>
                    <RiskBadge score={Math.max(...riskScores)} />
                  </div>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {riskScores.length > 0 ? (
              <div className="space-y-4">
                {/* Simple Risk Score Chart */}
                <div className="h-32 bg-gray-50 dark:bg-gray-800 rounded-lg p-4 relative overflow-hidden">
                  <div className="absolute inset-0 p-4">
                    <div className="relative h-full">
                      {/* Risk threshold line */}
                      <div className="absolute inset-x-4 top-4 border-t-2 border-red-300 border-dashed"></div>
                      <span className="absolute right-2 top-2 text-xs text-red-500">Risk Threshold (1.0)</span>
                      
                      {/* Risk score line */}
                      <svg className="w-full h-full" preserveAspectRatio="none" viewBox={`0 0 ${Math.max(riskScores.length - 1, 1)} 2`}>
                        <polyline
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="0.05"
                          className="text-blue-500"
                          points={riskScores.map((score, index) => `${index},${2 - Math.min(score, 2)}`).join(' ')}
                        />
                        {riskScores.map((score, index) => (
                          <circle
                            key={index}
                            cx={index}
                            cy={2 - Math.min(score, 2)}
                            r="0.03"
                            className={score >= 1.0 ? "fill-red-500" : score >= 0.7 ? "fill-orange-500" : "fill-blue-500"}
                          />
                        ))}
                      </svg>
                    </div>
                  </div>
                </div>
                
                {/* Session Statistics */}
                <div className="grid grid-cols-4 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {tokens.length}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Tokens</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {tokens.filter(t => t.blocked).length}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Blocked</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {riskScores.filter(s => s >= 0.7).length}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">High Risk</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {currentResponse.length}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Characters</div>
                  </div>
                </div>

                {/* Current Response Preview */}
                {currentResponse && (
                  <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Current Response:</div>
                    <div className="text-sm font-mono text-gray-900 dark:text-white max-h-20 overflow-y-auto">
                      {currentResponse}
                      {isStreaming && <span className="animate-pulse">▋</span>}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-32 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <p className="text-gray-500 dark:text-gray-400">
                  {isStreaming ? "Waiting for risk data..." : "Risk score visualization will appear here during streaming"}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default StreamMonitor