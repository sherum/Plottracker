import ActHbar, { type HbarBucket } from './ActHbar'
import type { Topic } from './TopicCardGrid'

const ACTS = [
  { key: 'opening', label: 'Opening' },
  { key: 'conflict', label: 'Conflict' },
  { key: 'climax', label: 'Climax' },
] as const

interface Theme {
  id: number
  title: string
}

interface Props {
  topics: Topic[]
  themes: Theme[]
  onThemeClick: (themeId: number) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onToggleExcludeTopic: (id: number, excluded: boolean) => void
  onSetAct: (id: number, act: 'opening' | 'conflict' | 'climax' | null) => void
}

function PlotViewer({ topics, themes, onThemeClick, onUpdateTopic, onToggleExcludeTopic, onSetAct }: Props) {
  const themeTitleById = Object.fromEntries(themes.map((t) => [t.id, t.title]))

  const buckets: HbarBucket[] = ACTS.map((act) => {
    const bucketTopics = topics.filter((t) => t.act === act.key)
    return {
      key: act.key,
      label: act.label,
      topics: bucketTopics,
      activeTopics: bucketTopics.filter((t) => !t.excluded),
    }
  })

  const unassignedTopics = topics.filter((t) => t.act === null)
  const extraBucket: HbarBucket = {
    key: 'unassigned',
    label: 'Unassigned',
    topics: unassignedTopics,
    activeTopics: unassignedTopics.filter((t) => !t.excluded),
  }

  return (
    <ActHbar
      buckets={buckets}
      extraBucket={extraBucket}
      themeTitleById={themeTitleById}
      onThemeClick={onThemeClick}
      onUpdateTopic={onUpdateTopic}
      onToggleExcludeTopic={onToggleExcludeTopic}
      onSetAct={onSetAct}
    />
  )
}

export default PlotViewer
