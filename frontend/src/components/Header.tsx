import React from 'react'
import { motion } from 'framer-motion'
import {
  Sun,
  Moon,
  Monitor,
  Bell,
  User,
  Settings,
  RefreshCw,
} from 'lucide-react'
import { useDashboardStore } from '@/stores/dashboard'
import { formatters } from '@/utils'

const Header: React.FC = () => {
  const {
    theme,
    setTheme,
    lastUpdate,
    realtimeMetrics,
  } = useDashboardStore()

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
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4"
    >
      <div className="flex items-center justify-between">
        {/* Page Title & Breadcrumb */}
        <div className="flex items-center space-x-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Compliance Dashboard
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Real-time monitoring and testing for regulated industries
            </p>
          </div>
        </div>

        {/* Status & Actions */}
        <div className="flex items-center space-x-4">
          {/* Real-time Stats */}
          <div className="hidden md:flex items-center space-x-6 px-4 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg">
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

          {/* Notifications */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Bell className="w-5 h-5" />
            {realtimeMetrics.blocked_requests > 0 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 w-3 h-3 bg-danger-500 rounded-full flex items-center justify-center"
              >
                <span className="text-[10px] text-white font-bold">
                  {realtimeMetrics.blocked_requests > 9 ? '9+' : realtimeMetrics.blocked_requests}
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
  )
}

export default Header