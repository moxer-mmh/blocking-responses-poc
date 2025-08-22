import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Search, 
  Filter, 
  Download, 
  Calendar,
  Eye,
  Shield,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge, ComplianceBadge, RiskBadge } from '@/components/ui/Badge'
import { formatters } from '@/utils'

const AuditLogs: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedComplianceType, setSelectedComplianceType] = useState('all')
  // const [dateRange] = useState('today')

  const mockAuditEvents = [
    {
      id: '1',
      timestamp: new Date().toISOString(),
      event_type: 'CONTENT_BLOCKED',
      session_id: 'sess_123',
      compliance_type: 'HIPAA',
      risk_score: 1.2,
      blocked: true,
      patterns_detected: ['patient_info', 'medical_record'],
      entities_detected: [
        { entity_type: 'PERSON', score: 0.95, start: 8, end: 16 },
        { entity_type: 'US_SSN', score: 0.98, start: 22, end: 33 },
      ],
      decision_reason: 'Multiple PHI entities detected with high confidence',
      content_hash: 'a1b2c3d4e5f6',
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      event_type: 'CONTENT_ASSESSED',
      session_id: 'sess_124',
      compliance_type: 'PII',
      risk_score: 0.6,
      blocked: false,
      patterns_detected: ['email_address'],
      entities_detected: [
        { entity_type: 'EMAIL_ADDRESS', score: 0.89, start: 15, end: 35 },
      ],
      decision_reason: 'Email detected but below blocking threshold',
      content_hash: 'f6e5d4c3b2a1',
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      event_type: 'SAFE_REWRITE',
      session_id: 'sess_125',
      compliance_type: 'PCI_DSS',
      risk_score: 1.5,
      blocked: true,
      patterns_detected: ['credit_card_number'],
      entities_detected: [
        { entity_type: 'CREDIT_CARD', score: 0.96, start: 20, end: 35 },
      ],
      decision_reason: 'Credit card information detected and safely rewritten',
      content_hash: 'b2a1f6e5d4c3',
    },
  ]

  const filteredEvents = mockAuditEvents.filter(event => {
    const matchesSearch = searchTerm === '' || 
      event.decision_reason.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.patterns_detected.some(p => p.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesCompliance = selectedComplianceType === 'all' || 
      event.compliance_type === selectedComplianceType

    return matchesSearch && matchesCompliance
  })

  const getEventIcon = (event: any) => {
    if (event.blocked) {
      return <Shield className="w-5 h-5 text-danger-600" />
    } else if (event.risk_score > 0.7) {
      return <AlertTriangle className="w-5 h-5 text-warning-600" />
    } else {
      return <CheckCircle className="w-5 h-5 text-success-600" />
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
            Audit Logs
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Comprehensive compliance audit trail and event history
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button variant="outline" size="sm">
            <Calendar className="w-4 h-4 mr-2" />
            Date Range
          </Button>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              {/* Search */}
              <div className="flex-1 min-w-64">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search audit logs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Compliance Type Filter */}
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <select
                  value={selectedComplianceType}
                  onChange={(e) => setSelectedComplianceType(e.target.value)}
                  className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Types</option>
                  <option value="HIPAA">HIPAA</option>
                  <option value="PCI_DSS">PCI DSS</option>
                  <option value="GDPR">GDPR</option>
                  <option value="CCPA">CCPA</option>
                  <option value="PII">PII</option>
                  <option value="PHI">PHI</option>
                </select>
              </div>

              {/* Results Count */}
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {filteredEvents.length} events
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Events List */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="space-y-4"
      >
        {filteredEvents.map((event, index) => (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index }}
          >
            <Card hover>
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  {/* Event Icon */}
                  <div className="flex-shrink-0 mt-1">
                    {getEventIcon(event)}
                  </div>

                  {/* Event Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <ComplianceBadge type={event.compliance_type} />
                        <RiskBadge score={event.risk_score} />
                        <Badge 
                          variant={event.blocked ? "danger" : "success"}
                          size="sm"
                        >
                          {event.blocked ? 'BLOCKED' : 'ALLOWED'}
                        </Badge>
                      </div>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {formatters.datetime(event.timestamp)}
                      </span>
                    </div>

                    <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                      {event.event_type.replace(/_/g, ' ')} 
                      <span className="text-gray-500 dark:text-gray-400 font-normal ml-2">
                        (Session: {event.session_id})
                      </span>
                    </h3>

                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {event.decision_reason}
                    </p>

                    {/* Detected Entities */}
                    {event.entities_detected.length > 0 && (
                      <div className="mb-3">
                        <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                          DETECTED ENTITIES
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {event.entities_detected.map((entity, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-400"
                            >
                              {entity.entity_type}
                              <span className="ml-1 text-blue-600 dark:text-blue-300">
                                {(entity.score * 100).toFixed(0)}%
                              </span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Detected Patterns */}
                    {event.patterns_detected.length > 0 && (
                      <div className="mb-3">
                        <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                          TRIGGERED PATTERNS
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {event.patterns_detected.map((pattern) => (
                            <span
                              key={pattern}
                              className="inline-flex items-center px-2 py-1 rounded text-xs bg-purple-100 dark:bg-purple-900/20 text-purple-800 dark:text-purple-400"
                            >
                              {pattern.replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                      <div className="flex items-center space-x-4">
                        <span>Risk Score: {event.risk_score.toFixed(2)}</span>
                        <span>Hash: {event.content_hash}</span>
                      </div>
                      <Button variant="ghost" size="sm">
                        <Eye className="w-3 h-3 mr-1" />
                        View Details
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}

        {filteredEvents.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="text-gray-500 dark:text-gray-400">
                <div className="text-4xl mb-4">🔍</div>
                <p className="font-medium mb-2">No audit events found</p>
                <p className="text-sm">
                  {searchTerm || selectedComplianceType !== 'all' 
                    ? 'Try adjusting your search filters'
                    : 'Audit events will appear here as the system processes requests'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </motion.div>

      {/* Load More */}
      {filteredEvents.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center"
        >
          <Button variant="outline">
            Load More Events
          </Button>
        </motion.div>
      )}
    </div>
  )
}

export default AuditLogs