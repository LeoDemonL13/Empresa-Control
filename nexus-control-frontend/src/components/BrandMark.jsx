export default function BrandMark({ subtitle = 'CONTROL', size = 'md' }) {
  const logo = size === 'lg' ? 'h-14 w-14' : 'h-10 w-10'
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <img
        src="./logo_sidebar.png"
        alt="Nexus Obsidian"
        className={`${logo} shrink-0 rounded-xl object-contain`}
        draggable={false}
      />
      <div className="min-w-0 leading-none">
        <div className="truncate text-[13px] font-black tracking-[0.08em] text-white">
          NEXUS <span className="text-brand-400">OBSIDIAN</span>
        </div>
        <div className="mt-1 font-mono text-[8px] font-semibold tracking-[0.16em] text-ink-400">
          {subtitle}
        </div>
      </div>
    </div>
  )
}
