import { forwardRef } from 'react'

const Input = forwardRef(function Input({ className = '', error = false, ...props }, ref) {
  return (
    <input
      ref={ref}
      className={`h-9 w-full rounded-md border px-3 text-sm text-ink-900 transition-colors placeholder:text-ink-400 focus-ring dark:text-white dark:placeholder:text-ink-500 ${
        error
          ? 'border-red-400 dark:border-red-500'
          : 'border-ink-200 bg-white hover:border-ink-300 dark:border-obsidian-line dark:bg-obsidian-cardAlt dark:hover:border-ink-600'
      } ${className}`}
      {...props}
    />
  )
})

export function Label({ children, className = '' }) {
  return (
    <label className={`mb-1.5 block text-xs font-medium text-ink-700 dark:text-ink-300 ${className}`}>
      {children}
    </label>
  )
}

export function FieldError({ children }) {
  if (!children) return null
  return <p className="mt-1 text-xs text-red-600 dark:text-red-400">{children}</p>
}

export default Input
