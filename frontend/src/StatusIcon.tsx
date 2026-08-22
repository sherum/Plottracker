import type { ReactNode } from 'react'
import { onActivateKey } from './keyboardActivate'

type StatusIconName = 'theme' | 'excluded'

const ICON_CLASSES: Record<StatusIconName, string> = {
  theme: 'bi-tag-fill',
  excluded: 'bi-eye-slash',
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
      <i className={`bi ${ICON_CLASSES[icon]}`} aria-hidden="true" />
      {children}
    </span>
  )
}

export default StatusIcon
