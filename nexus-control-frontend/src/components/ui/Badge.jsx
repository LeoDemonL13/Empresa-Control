const tones = {
  neutral: 'bg-ink-100 text-ink-700 ring-ink-200 dark:bg-white/5 dark:text-ink-300 dark:ring-white/10',
  brand: 'bg-brand-50 text-brand-800 ring-brand-200 dark:bg-brand-900/40 dark:text-brand-200 dark:ring-brand-700/60',
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:ring-emerald-700/60',
  warning: 'bg-amber-50 text-amber-800 ring-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:ring-amber-700/60',
  danger: 'bg-red-50 text-red-700 ring-red-200 dark:bg-red-900/30 dark:text-red-300 dark:ring-red-700/60',
  info: 'bg-sky-50 text-sky-700 ring-sky-200 dark:bg-sky-900/30 dark:text-sky-300 dark:ring-sky-700/60',
}

const dots = {
  neutral: 'bg-ink-400',
  brand: 'bg-brand-500',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-red-500',
  info: 'bg-sky-500',
}

export default function Badge({ tone = 'neutral', children, leftIcon, className = '', dot = false, mono = false }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
        mono ? 'font-mono text-[10px] uppercase tracking-widest' : ''
      } ${tones[tone] || tones.neutral} ${className}`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dots[tone] || dots.neutral}`} />}
      {leftIcon}
      {children}
    </span>
  )
}
