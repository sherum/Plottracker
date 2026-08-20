type IconName = 'load' | 'reanalyze' | 'classify' | 'delete'

const PATHS: Record<IconName, JSX.Element> = {
  load: (
    <>
      <path d="M8 2v7.5M5 7l3 3 3-3" />
      <path d="M3 11.5v1.5a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1.5" />
    </>
  ),
  reanalyze: (
    <>
      <path d="M12.5 4.5A5 5 0 1 0 13.5 8" />
      <path d="M13.5 2.5v3h-3" />
    </>
  ),
  classify: (
    <>
      <path d="M8.7 2H3a1 1 0 0 0-1 1v5.7a1 1 0 0 0 .3.7l6.3 6.3a1 1 0 0 0 1.4 0l4.7-4.7a1 1 0 0 0 0-1.4L8.4 2.3A1 1 0 0 0 8.7 2Z" />
      <circle cx="4.75" cy="4.75" r="0.75" fill="currentColor" stroke="none" />
    </>
  ),
  delete: (
    <>
      <path d="M3 4.5h10M6.5 4.5v-1a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v1" />
      <path d="M4.5 4.5 5.2 13a1 1 0 0 0 1 .9h3.6a1 1 0 0 0 1-.9l.7-8.5" />
    </>
  ),
}

interface Props {
  icon: IconName
  label: string
  onClick: () => void
}

function IconButton({ icon, label, onClick }: Props) {
  return (
    <button className="icon-btn" onClick={onClick} aria-label={label} title={label}>
      <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
        {PATHS[icon]}
      </svg>
    </button>
  )
}

export default IconButton
