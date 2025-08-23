import React, { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Sun,
  Moon,
  Monitor,
  Bell,
  User,
  Settings,
  RefreshCw,
  ChevronRight,
  Menu,
} from 'lucide-react'
import { useDashboardStore } from '@/stores/dashboard'
import { formatters } from '@/utils'
import { notificationManager } from '@/utils/notifications'
import SettingsModal from '@/components/modals/SettingsModal'
import NotificationsModal from '@/components/modals/NotificationsModal'

interface HeaderProps {
  onMobileMenuToggle: () => void
}

const Header: React.FC<HeaderProps> = ({ onMobileMenuToggle }) => {
  const {
    theme,
    setTheme,
    lastUpdate,
    realtimeMetrics,
  } = useDashboardStore()
  
  const location = useLocation()
  const [showNotifications, setShowNotifications] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  
  // Use notification manager for unread count
  const [unreadCount, setUnreadCount] = useState(0)

  // Subscribe to notification manager for unread count updates
  React.useEffect(() => {
    const updateUnreadCount = () => {
      setUnreadCount(notificationManager.getUnreadCount())
    }
    
    // Initial count
    updateUnreadCount()
    
    // Subscribe to changes
    const unsubscribe = notificationManager.subscribe(() => {
      updateUnreadCount()
    })
    
    return unsubscribe
  }, [])

  const getPageInfo = () => {
    switch (location.pathname) {
      case '/':
        return {
          title: 'Dashboard',
          subtitle: 'Real-time monitoring and compliance overview',
          breadcrumb: ['Dashboard']
        }
      case '/testing':
        return {
          title: 'Test Suite',
          subtitle: 'Run compliance tests and validation',
          breadcrumb: ['Dashboard', 'Test Suite']
        }
      case '/stream':
        return {
          title: 'Stream Monitor',
          subtitle: 'Live stream analysis and monitoring',
          breadcrumb: ['Dashboard', 'Stream Monitor']
        }
      case '/audit':
        return {
          title: 'Audit Logs',
          subtitle: 'Compliance audit trail and history',
          breadcrumb: ['Dashboard', 'Audit Logs']
        }
      default:
        return {
          title: 'Compliance Dashboard',
          subtitle: 'Real-time monitoring and testing for regulated industries',
          breadcrumb: ['Dashboard']
        }
    }
  }

  const pageInfo = getPageInfo()

  const handleNotificationClick = () => {
    setShowNotifications(true)
  }

  const handleSettingsClick = () => {
    setShowSettings(true)
  }

  const handleThemeToggle = () => {
    const themes = ['light', 'dark', 'system'] as const
    const currentIndex = themes.indexOf(theme)
    const nextTheme = themes[(currentIndex + 1) % themes.length]
    setTheme(nextTheme)
  }

  const getThemeIcon = () => {
    switch (theme) {
      case 'light':
        return Sun
      case 'dark':
        return Moon
      default:
        return Monitor
    }
  }

  const ThemeIcon = getThemeIcon()

  return (
    <>
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-3 sm:px-6 py-4"
      >
        <div className="flex items-center justify-between">
          {/* Mobile Menu Button + Page Title & Breadcrumb */}
          <div className="flex items-center space-x-3 min-w-0 flex-1">
            {/* Mobile Menu Button */}
            <button
              onClick={onMobileMenuToggle}
              className="lg:hidden p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
            
            <div className="min-w-0 flex-1">
              {/* Breadcrumb - Hidden on small screens */}
              <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 mb-1">
                {pageInfo.breadcrumb.map((crumb, index) => (
                  <React.Fragment key={crumb}>
                    {index > 0 && <ChevronRight className="w-4 h-4" />}
                    <span className={index === pageInfo.breadcrumb.length - 1 ? 'text-primary-600 dark:text-primary-400 font-medium' : ''}>
                      {crumb}
                    </span>
                  </React.Fragment>
                ))}
              </div>
              {/* Page Title - Responsive sizing */}
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white truncate">
                {pageInfo.title}
              </h1>
              <p className="hidden sm:block text-sm text-gray-500 dark:text-gray-400 truncate">
                {pageInfo.subtitle}
              </p>
            </div>
          </div>

          {/* Status & Actions */}
          <div className="flex items-center space-x-2 sm:space-x-4">
            {/* Real-time Stats - Responsive display */}
            <div className="hidden lg:flex items-center space-x-6 px-4 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {realtimeMetrics.total_requests} Requests
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    realtimeMetrics.block_rate > 10
                      ? 'bg-danger-500'
                      : realtimeMetrics.block_rate > 5
                      ? 'bg-warning-500'
                      : 'bg-success-500'
                  }`}
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {realtimeMetrics.block_rate.toFixed(1)}% Blocked
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <RefreshCw className="w-3 h-3 text-gray-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {formatters.relative(lastUpdate)}
                </span>
              </div>
            </div>

            {/* Compact stats for tablet */}
            <div className="hidden md:flex lg:hidden items-center space-x-3 px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {realtimeMetrics.total_requests}
              </span>
              <div
                className={`w-2 h-2 rounded-full ${
                  realtimeMetrics.block_rate > 10
                    ? 'bg-danger-500'
                    : realtimeMetrics.block_rate > 5
                    ? 'bg-warning-500'
                    : 'bg-success-500'
                }`}
              />
            </div>

            {/* Notifications */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleNotificationClick}
              className="relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 w-3 h-3 bg-danger-500 rounded-full flex items-center justify-center"
                >
                  <span className="text-[10px] text-white font-bold">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                </motion.div>
              )}
            </motion.button>

            {/* Theme Toggle */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleThemeToggle}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title={`Current theme: ${theme}`}
            >
              <ThemeIcon className="w-5 h-5" />
            </motion.button>

            {/* Settings */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSettingsClick}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5" />
            </motion.button>

            {/* User Profile */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="flex items-center space-x-3 px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg cursor-pointer"
            >
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="hidden sm:block">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Compliance Admin
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  System Administrator
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.header>

      {/* Modal Components */}
      <SettingsModal 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)} 
      />
      <NotificationsModal 
        isOpen={showNotifications} 
        onClose={() => setShowNotifications(false)}
      />
    </>
  )
}

export default Header