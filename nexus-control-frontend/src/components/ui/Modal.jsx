import { X } from 'lucide-react'

export default function Modal({ open, onClose, title, description, children, className = 'max-w-md' }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className={`w-full animate-scale-in overflow-hidden rounded-xl border border-ink-200 bg-white shadow-modal dark:border-obsidian-line dark:bg-obsidian-card ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 border-b border-ink-200 p-5 dark:border-obsidian-line">
          <div>
            <h3 className="text-base font-semibold text-ink-900 dark:text-white">{title}</h3>
            {description && <p className="mt-0.5 text-sm text-ink-500 dark:text-obsidian-muted">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-ink-400 hover:bg-ink-100 hover:text-ink-700 dark:hover:bg-white/5 dark:hover:text-white"
          >
            <X size={18} />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto scrollbar-thin p-5">{children}</div>
      </div>
    </div>
  )
}
