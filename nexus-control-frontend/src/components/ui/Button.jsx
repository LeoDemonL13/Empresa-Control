import { forwardRef } from 'react'

const variants = {
  primary:
    'rounded-full bg-accent text-white font-semibold hover:bg-accent-strong hover:shadow-glow active:brightness-90 disabled:bg-accent/50 disabled:shadow-none',
  secondary:
    'rounded-md bg-white text-ink-700 border border-ink-200 hover:bg-ink-50 hover:border-ink-300 active:bg-ink-100 disabled:bg-ink-50 disabled:text-ink-400 dark:bg-obsidian-cardAlt dark:text-ink-200 dark:border-obsidian-line dark:hover:bg-obsidian-line dark:hover:border-ink-600 dark:disabled:bg-obsidian-card dark:disabled:text-ink-600',
  ghost:
    'rounded-md bg-transparent text-ink-700 hover:bg-ink-100 active:bg-ink-200 disabled:text-ink-400 dark:text-ink-300 dark:hover:bg-white/5 dark:active:bg-white/10 dark:disabled:text-ink-600',
  danger:
    'rounded-md bg-red-600 text-white hover:bg-red-700 active:bg-red-800 disabled:bg-red-600/50 shadow-sm dark:hover:bg-red-500',
  'danger-ghost':
    'rounded-md bg-transparent text-red-600 hover:bg-red-50 active:bg-red-100 disabled:text-red-400 dark:text-red-400 dark:hover:bg-red-950/40',
  success:
    'rounded-md bg-emerald-600 text-white hover:bg-emerald-700 active:bg-emerald-800 shadow-sm dark:hover:bg-emerald-500',
}

const sizes = {
  xs: 'h-7 px-2.5 text-xs gap-1',
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-9 px-4 text-sm gap-2',
  lg: 'h-10 px-5 text-sm gap-2',
  xl: 'h-11 px-6 text-base gap-2',
  icon: 'h-9 w-9 p-0',
  'icon-sm': 'h-8 w-8 p-0',
}

const Button = forwardRef(function Button(
  {
    variant = 'primary',
    size = 'md',
    className = '',
    children,
    type = 'button',
    loading = false,
    leftIcon,
    rightIcon,
    ...props
  },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={props.disabled || loading}
      className={`inline-flex items-center justify-center font-medium transition-all focus-ring whitespace-nowrap disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {loading ? (
        <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
          <path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        </svg>
      ) : (
        leftIcon
      )}
      {children}
      {!loading && rightIcon}
    </button>
  )
})

export default Button
