type IconName = 'more' | 'reanalyze' | 'classify' | 'delete' | 'add' | 'remove' | 'link' | 'up' | 'down' | 'main' | 'split' | 'rename'

const ICON_CLASSES: Record<IconName, string> = {
  more: 'bi-three-dots',
  reanalyze: 'bi-arrow-clockwise',
  classify: 'bi-tags',
  delete: 'bi-trash',
  add: 'bi-plus-lg',
  remove: 'bi-dash-lg',
  link: 'bi-link-45deg',
  up: 'bi-arrow-up',
  down: 'bi-arrow-down',
  main: 'bi-star',
  split: 'bi-scissors',
  rename: 'bi-pencil',
}

interface Props {
  icon: IconName
  label: string
  onClick: () => void
  active?: boolean
}

function IconButton({ icon, label, onClick, active = false }: Props) {
  return (
    <button
      type="button"
      className={`btn btn-sm btn-outline-secondary${active ? ' active' : ''}`}
      onClick={onClick}
      aria-label={label}
      aria-pressed={active}
      title={label}
    >
      <i className={`bi ${ICON_CLASSES[icon]}`} aria-hidden="true" />
    </button>
  )
}

export default IconButton
