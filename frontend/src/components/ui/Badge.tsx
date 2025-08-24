import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/utils'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary'
  size?: 'sm' | 'md' | 'lg'
  animate?: boolean
  children: React.ReactNode
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  animate = false,
  className,
  children,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full'
  
  const variants = {
    default: 'bg-primary-100 text-primary-800 dark:bg-primary-900/20 dark:text-primary-400',
    success: 'bg-success-100 text-success-800 dark:bg-success-900/20 dark:text-success-400',
    warning: 'bg-warning-100 text-warning-800 dark:bg-warning-900/20 dark:text-warning-400',
    danger: 'bg-danger-100 text-danger-800 dark:bg-danger-900/20 dark:text-danger-400',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    secondary: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
  }
  
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  }

  const BadgeComponent = animate ? motion.span : 'span'
  
  const motionProps = animate
    ? {
        initial: { scale: 0 },
        animate: { scale: 1 },
        whileHover: { scale: 1.05 },
        transition: { type: 'spring', stiffness: 500, damping: 15 },
      }
    : {}

  const { 
    onAnimationStart, 
    onAnimationEnd, 
    onAnimationIteration, 
    onDragStart,
    onDrag,
    onDragEnd,
    ...badgeProps 
  } = props

  return (
    <BadgeComponent
      className={cn(
        baseStyles,
        variants[variant],
        sizes[size],
        className
      )}
      {...(animate ? motionProps : {})}
      {...badgeProps}
    >
      {children}
    </BadgeComponent>
  )
}

interface StatusBadgeProps {
  status: 'pending' | 'running' | 'passed' | 'failed' | 'completed' | 'error'
  animate?: boolean
  className?: string
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  animate = false,
  className,
}) => {
  const statusConfig = {
    pending: { variant: 'secondary' as const, text: 'Pending' },
    running: { variant: 'info' as const, text: 'Running' },
    passed: { variant: 'success' as const, text: 'Passed' },
    failed: { variant: 'danger' as const, text: 'Failed' },
    completed: { variant: 'success' as const, text: 'Completed' },
    error: { variant: 'danger' as const, text: 'Error' },
  }
  
  const config = statusConfig[status]
  
  return (
    <Badge
      variant={config.variant}
      animate={animate}
      className={className}
    >
      {config.text}
    </Badge>
  )
}

interface RiskBadgeProps {
  score?: number | null
  label?: string
  animate?: boolean
  className?: string
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  score,
  label,
  animate = false,
  className,
}) => {
  const getRiskConfig = (score?: number | null) => {
    if (score === null || score === undefined) {
      return { variant: 'secondary' as const, text: label || 'N/A' }
    } else if (score < 0.3) {
      return { variant: 'success' as const, text: 'Low Risk' }
    } else if (score < 0.7) {
      return { variant: 'warning' as const, text: 'Medium Risk' }
    } else if (score < 1.0) {
      return { variant: 'danger' as const, text: 'High Risk' }
    } else {
      return { variant: 'danger' as const, text: 'Critical Risk' }
    }
  }
  
  const config = getRiskConfig(score)
  
  return (
    <Badge
      variant={config.variant}
      animate={animate}
      className={className}
    >
      {config.text}
    </Badge>
  )
}

interface ComplianceBadgeProps {
  type: string
  animate?: boolean
  className?: string
}

export const ComplianceBadge: React.FC<ComplianceBadgeProps> = ({
  type,
  animate = false,
  className,
}) => {
  const complianceColors: Record<string, string> = {
    HIPAA: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/20 dark:text-cyan-400',
    PCI_DSS: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
    GDPR: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400',
    CCPA: 'bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400',
    PII: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    PHI: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400',
  }
  
  const BadgeComponent = animate ? motion.span : 'span'
  
  const motionProps = animate
    ? {
        initial: { scale: 0 },
        animate: { scale: 1 },
        whileHover: { scale: 1.05 },
        transition: { type: 'spring', stiffness: 500, damping: 15 },
      }
    : {}

  return (
    <BadgeComponent
      className={cn(
        'inline-flex items-center px-2.5 py-1 text-sm font-medium rounded-full',
        complianceColors[type] || complianceColors.PII,
        className
      )}
      {...(animate ? motionProps : {})}
    >
      {type}
    </BadgeComponent>
  )
}