import { useState } from 'react'
import HbarVisual, { type HbarBucket } from './HbarVisual'
import TopicCardGrid, { type Topic } from './TopicCardGrid'
import './Notecards.css'
import './PlotViewer.css'

export type { HbarBucket }

interface Props {
  buckets: HbarBucket[]
  extraBucket?: HbarBucket
  themeTitleById?: Record<number, string>
  onThemeClick?: (themeId: number) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onToggleExcludeTopic: (id: number, excluded: boolean) => void
  size?: 'large' | 'small'
}

function ActHbar({
  buckets,
  extraBucket,
  themeTitleById,
  onThemeClick,
  onUpdateTopic,
  onToggleExcludeTopic,
  size = 'large',
}: Props) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [hoveredTopicId, setHoveredTopicId] = useState<number | null>(null)

  const selected =
    selectedKey === null
      ? null
      : (buckets.find((b) => b.key === selectedKey) ?? (extraBucket?.key === selectedKey ? extraBucket : null))

  return (
    <div className="notecards">
      <HbarVisual
        buckets={buckets}
        extraBucket={extraBucket}
        selectedKey={selectedKey}
        onSegmentClick={setSelectedKey}
        markerTopicId={hoveredTopicId}
        size={size}
      />

      {selected === null ? (
        <p className="hbar-hint">Click a section above to see its topics.</p>
      ) : (
        <>
          <button className="back" onClick={() => setSelectedKey(null)} title="Clear the current selection">
            &larr; Clear selection
          </button>
          <TopicCardGrid
            topics={selected.topics}
            themeTitleById={themeTitleById}
            onThemeClick={onThemeClick}
            onUpdateTopic={onUpdateTopic}
            onToggleExcludeTopic={onToggleExcludeTopic}
            onHoverTopic={setHoveredTopicId}
          />
        </>
      )}
    </div>
  )
}

export default ActHbar
