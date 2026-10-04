export function Card({ className = '', children, padded = true, as: As = 'div', ...props }) {
  return (
    <As className={`nx-surface ${padded ? 'p-5 sm:p-6' : ''} ${className}`} {...props}>
      {children}
    </As>
  )
}

export function CardHeader({ title, description, actions, className = '' }) {
  return (
    <div
      className={`mb-5 flex items-start justify-between gap-4 border-b border-ink-200 pb-4 dark:border-obsidian-line ${className}`}
    >
      <div className="min-w-0">
        <h3 className="truncate text-base font-semibold text-ink-900 dark:text-ink-100">{title}</h3>
        {description && (
          <p className="mt-0.5 text-sm text-ink-500 dark:text-obsidian-muted">{description}</p>
        )}
      </div>
      {actions && <div className="flex flex-shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}

export function StatCard({ label, value, icon: Icon, className = '' }) {
  return (
    <div className={`nx-surface flex items-center gap-4 p-5 ${className}`}>
      <div className="inline-flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-ink-100 text-ink-700 dark:bg-obsidian-cardAlt dark:text-ink-200">
        <Icon size={22} strokeWidth={1.8} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wide text-ink-500 dark:text-obsidian-muted">
          {label}
        </p>
        <p className="mt-1 text-3xl font-semibold leading-none tabular-nums text-ink-900 dark:text-ink-100">
          {value}
        </p>
      </div>
    </div>
  )
}

export default Card
