import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'compact' | 'glass'
  padding?: 'sm' | 'md' | 'lg'
  hover?: boolean
  children: React.ReactNode
}

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  padding = 'md',
  hover = false,
  className,
  children,
  ...props
}) => {
  const baseStyles = 'rounded-xl border transition-all duration-200'
  
  const variants = {
    default: 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-sm',
    compact: 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-sm',
    glass: 'bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-white/20 dark:border-gray-800/20 shadow-lg',
  }
  
  const paddings = {
    sm: variant === 'compact' ? 'p-3' : 'p-4',
    md: variant === 'compact' ? 'p-4' : 'p-6',
    lg: variant === 'compact' ? 'p-6' : 'p-8',
  }
  
  const hoverStyles = hover
    ? 'hover:shadow-md hover:-translate-y-1 cursor-pointer'
    : ''

  const CardComponent = hover ? motion.div : 'div'
  
  const motionProps = hover
    ? {
        whileHover: { y: -2, scale: 1.01 },
        whileTap: { scale: 0.99 },
      }
    : {}

  const { 
    onAnimationStart, 
    onAnimationEnd, 
    onAnimationIteration, 
    onDragStart,
    onDrag,
    onDragEnd,
    ...cardProps 
  } = props

  return (
    <CardComponent
      className={cn(
        baseStyles,
        variants[variant],
        paddings[padding],
        hoverStyles,
        className
      )}
      {...(hover ? motionProps : {})}
      {...cardProps}
    >
      {children}
    </CardComponent>
  )
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn('mb-4 pb-2 border-b border-gray-200 dark:border-gray-700', className)}
      {...props}
    >
      {children}
    </div>
  )
}

interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg'
}

export const CardTitle: React.FC<CardTitleProps> = ({
  size = 'md',
  className,
  children,
  ...props
}) => {
  const sizes = {
    sm: 'text-lg font-semibold',
    md: 'text-xl font-semibold',
    lg: 'text-2xl font-bold',
  }
  
  return (
    <h3
      className={cn(
        'text-gray-900 dark:text-gray-100',
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </h3>
  )
}

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const CardContent: React.FC<CardContentProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn('text-gray-600 dark:text-gray-400', className)}
      {...props}
    >
      {children}
    </div>
  )
}

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export const CardFooter: React.FC<CardFooterProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn('mt-4 pt-4 border-t border-gray-200 dark:border-gray-700', className)}
      {...props}
    >
      {children}
    </div>
  )
}