import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  TestTube2,
  Activity,
  FileText,
  Shield,
} from 'lucide-react'
import { cn } from '@/utils'
import { useDashboardStore } from '@/stores/dashboard'

const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
    description: 'Overview and metrics',
  },
  {
    name: 'Test Suite',
    href: '/testing',
    icon: TestTube2,
    description: 'Run compliance tests',
  },
  {
    name: 'Stream Monitor',
    href: '/stream',
    icon: Activity,
    description: 'Live stream analysis',
  },
  {
    name: 'Audit Logs',
    href: '/audit',
    icon: FileText,
    description: 'Compliance audit trail',
  },
]

const Sidebar: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const location = useLocation()
  const { isConnected } = useDashboardStore()

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="lg:hidden fixed inset-0 z-40 bg-gray-600 bg-opacity-75"
            onClick={onClose}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.div
        initial={{ x: -300 }}
        animate={{ 
          x: 0,
        }}
        className={cn(
          "flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700",
          // Desktop: Always visible, fixed width
          "lg:flex lg:w-64",
          // Mobile/Tablet: Hidden by default, overlay when open
          isOpen 
            ? "fixed inset-y-0 left-0 z-50 w-64 flex lg:hidden"
            : "hidden lg:flex"
        )}
      >
      {/* Logo/Brand */}
      <div className="flex items-center justify-center h-16 px-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="flex items-center justify-center w-8 h-8 bg-primary-600 rounded-lg">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">
              Compliance
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Dashboard
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          const Icon = item.icon

          return (
            <motion.div
              key={item.name}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
            >
              <NavLink
                to={item.href}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 group',
                    isActive
                      ? 'bg-primary-100 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )
                }
              >
                <Icon
                  className={cn(
                    'w-5 h-5 mr-3 transition-colors duration-200',
                    isActive
                      ? 'text-primary-600 dark:text-primary-400'
                      : 'text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300'
                  )}
                />
                <div>
                  <div className="font-medium">{item.name}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {item.description}
                  </div>
                </div>
              </NavLink>
            </motion.div>
          )
        })}
      </nav>

      {/* Connection Status */}
      <div className="px-3 py-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div
            className={cn(
              'w-2 h-2 rounded-full',
              isConnected
                ? 'bg-success-500'
                : 'bg-danger-500 animate-pulse'
            )}
          />
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {isConnected ? 'Connected' : 'Disconnected'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Backend API
            </p>
          </div>
        </div>
      </div>

      {/* Version Info */}
      <div className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center">
          <span>Regulated Edition</span>
          <span>v1.1.0</span>
        </div>
      </div>
    </motion.div>
    </>
  )
}

export default Sidebar