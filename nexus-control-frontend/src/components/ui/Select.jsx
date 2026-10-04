import { forwardRef } from 'react'

const Select = forwardRef(function Select({ className = '', children, ...props }, ref) {
  return (
    <select
      ref={ref}
      className={`h-9 w-full rounded-md border border-ink-200 bg-white px-2.5 text-sm text-ink-900 transition-colors hover:border-ink-300 focus-ring dark:border-obsidian-line dark:bg-obsidian-cardAlt dark:text-white dark:hover:border-ink-600 ${className}`}
      {...props}
    >
      {children}
    </select>
  )
})

export default Select
