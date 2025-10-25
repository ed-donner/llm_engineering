'use client'

import React, { useState } from 'react'
import { cn } from '@/lib/utils'

interface CategoryBadgeProps {
  category: string
  subcategories?: string[]
  icon?: string
  size?: 'sm' | 'md' | 'lg'
  clickable?: boolean
  onClick?: () => void
  showIcon?: boolean
  showSubcategories?: boolean
  className?: string
}

// Color mapping for categories (AI/ML/GenAI focused)
const CATEGORY_COLORS: Record<string, string> = {
  'Machine Learning & Deep Learning': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  'Generative AI & LLMs': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  'Computer Vision & Image AI': 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
  'Natural Language Processing': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  'AI Research & Papers': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
  'MLOps & AI Infrastructure': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  'AI Ethics & Safety': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  'AI Tools & Frameworks': 'bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-200',
  'Data & Training': 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
  'AI Applications & Use Cases': 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
  'AI Business & Strategy': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  'Tutorials & Education': 'bg-lime-100 text-lime-800 dark:bg-lime-900 dark:text-lime-200',
  'AI Agents & MCP': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  'General Knowledge': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
}

// Default icons for categories
const CATEGORY_ICONS: Record<string, string> = {
  'Machine Learning & Deep Learning': '🤖',
  'Generative AI & LLMs': '✨',
  'Computer Vision & Image AI': '👁️',
  'Natural Language Processing': '�',
  'AI Research & Papers': '📚',
  'MLOps & AI Infrastructure': '⚙️',
  'AI Ethics & Safety': '🛡️',
  'AI Tools & Frameworks': '🔧',
  'Data & Training': '📊',
  'AI Applications & Use Cases': '�',
  'AI Business & Strategy': '�',
  'Tutorials & Education': '🎓',
  'AI Agents & MCP': '🤝',
  'General Knowledge': '🌐'
}

const SIZE_CLASSES = {
  sm: 'px-1.5 py-0.5 text-xs',
  md: 'px-2 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base'
}

export function CategoryBadge({
  category,
  subcategories = [],
  icon,
  size = 'md',
  clickable = false,
  onClick,
  showIcon = true,
  showSubcategories = true,
  className
}: CategoryBadgeProps) {
  const [isHovered, setIsHovered] = useState(false)
  const colorClass = CATEGORY_COLORS[category] || CATEGORY_COLORS['General Knowledge']
  const categoryIcon = icon || CATEGORY_ICONS[category] || '📄'
  const sizeClass = SIZE_CLASSES[size]
  const hasSubcategories = subcategories && subcategories.length > 0
  
  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span
        onClick={clickable ? onClick : undefined}
        className={cn(
          'inline-flex items-center gap-1 rounded-full font-medium transition-all',
          sizeClass,
          colorClass,
          clickable && 'cursor-pointer hover:opacity-80 hover:shadow-sm',
          className
        )}
        role={clickable ? 'button' : undefined}
        tabIndex={clickable ? 0 : undefined}
        onKeyDown={clickable && onClick ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onClick()
          }
        } : undefined}
      >
        {showIcon && <span className="text-sm">{categoryIcon}</span>}
        <span>{category}</span>
        {hasSubcategories && showSubcategories && (
          <span className="text-xs opacity-60">•{subcategories.length}</span>
        )}
      </span>
      
      {/* Subcategories tooltip on hover */}
      {hasSubcategories && showSubcategories && isHovered && (
        <div className="absolute left-0 top-full mt-1 z-50 min-w-max max-w-xs">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-2">
            <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
              Subcategories:
            </div>
            <div className="flex flex-wrap gap-1">
              {subcategories.map((sub, idx) => (
                <span
                  key={idx}
                  className="inline-block px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                  {sub}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface CategoryListProps {
  categories: string[]
  subcategoriesMap?: Record<string, string[]>
  maxVisible?: number
  onCategoryClick?: (category: string) => void
  size?: 'sm' | 'md' | 'lg'
  showIcons?: boolean
  showSubcategories?: boolean
  className?: string
}

export function CategoryList({
  categories,
  subcategoriesMap = {},
  maxVisible = 3,
  onCategoryClick,
  size = 'sm',
  showIcons = true,
  showSubcategories = true,
  className
}: CategoryListProps) {
  if (!categories || categories.length === 0) {
    return null
  }

  const visibleCategories = categories.slice(0, maxVisible)
  const hiddenCount = categories.length - maxVisible

  return (
    <div className={cn('flex flex-wrap gap-1', className)}>
      {visibleCategories.map((category, idx) => (
        <CategoryBadge
          key={idx}
          category={category}
          subcategories={subcategoriesMap[category]}
          size={size}
          clickable={!!onCategoryClick}
          onClick={() => onCategoryClick?.(category)}
          showIcon={showIcons}
          showSubcategories={showSubcategories}
        />
      ))}
      {hiddenCount > 0 && (
        <span
          className={cn(
            'inline-flex items-center rounded-full font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
            SIZE_CLASSES[size]
          )}
        >
          +{hiddenCount}
        </span>
      )}
    </div>
  )
}

interface CategoryFilterProps {
  selectedCategory: string | null
  onCategoryChange: (category: string | null) => void
  categories: string[]
  categoryIcons?: Record<string, string>
  className?: string
}

export function CategoryFilter({
  selectedCategory,
  onCategoryChange,
  categories,
  categoryIcons,
  className
}: CategoryFilterProps) {
  return (
    <div className={cn('flex flex-wrap gap-1', className)}>
      <button
        onClick={() => onCategoryChange(null)}
        className={cn(
          'px-2 py-1 text-xs rounded-full transition-colors font-medium',
          selectedCategory === null
            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
        )}
      >
        All
      </button>
      {categories.map((category) => {
        const icon = categoryIcons?.[category] || CATEGORY_ICONS[category] || '📄'
        const isSelected = selectedCategory === category
        
        return (
          <button
            key={category}
            onClick={() => onCategoryChange(isSelected ? null : category)}
            className={cn(
              'px-2 py-1 text-xs rounded-full transition-colors font-medium inline-flex items-center gap-1',
              isSelected
                ? CATEGORY_COLORS[category] || CATEGORY_COLORS['General Knowledge']
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            )}
          >
            <span className="text-sm">{icon}</span>
            <span>{category}</span>
          </button>
        )
      })}
    </div>
  )
}
