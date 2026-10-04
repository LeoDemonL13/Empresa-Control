export default function SysLabel({ children, live = false, className = '' }) {
  return (
    <span className={`nx-label inline-flex items-center gap-1.5 ${className}`}>
      {live && <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-accent" />}
      {children}
    </span>
  )
}
