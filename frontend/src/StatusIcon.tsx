import type { ReactNode } from 'react'
import { onActivateKey } from './keyboardActivate'

type StatusIconName = 'theme' | 'excluded'

const PATHS: Record<StatusIconName, JSX.Element> = {
  theme: (
    <>
      <path d="M8.7 2H3a1 1 0 0 0-1 1v5.7a1 1 0 0 0 .3.7l6.3 6.3a1 1 0 0 0 1.4 0l4.7-4.7a1 1 0 0 0 0-1.4L8.4 2.3A1 1 0 0 0 8.7 2Z" />
      <circle cx="4.75" cy="4.75" r="0.75" fill="currentColor" stroke="none" />
    </>
  ),
  excluded: (
    <>
      <path d="M1.5 8S4 3.5 8 3.5 14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8Z" />
      <circle cx="8" cy="8" r="1.6" />
      <path d="M2.5 2.5l11 11" />
    </>
  ),
}

interface Props {
  icon: StatusIconName
  label: string
  onClick?: () => void
  children?: ReactNode
}

function StatusIcon({ icon, label, onClick, children }: Props) {
  return (
    <span
      className={`status-icon${onClick ? ' status-icon-link' : ''}`}
      title={label}
      aria-label={label}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? onActivateKey(onClick) : undefined}
    >
      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
        {PATHS[icon]}
      </svg>
      {children}
    </span>
  )
}

export default StatusIcon
