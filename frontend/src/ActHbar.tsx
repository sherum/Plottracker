import { useState } from 'react'
import TopicCardGrid, { type Topic } from './TopicCardGrid'
import './Notecards.css'
import './PlotViewer.css'

const MIN_SEGMENT_PERCENT = 10
const ACT_COLOR_CLASSES = ['hbar-act-0', 'hbar-act-1', 'hbar-act-2']

export interface HbarBucket {
  key: string
  label: string
  topics: Topic[]
  activeTopics: Topic[]
}

interface Props {
  buckets: HbarBucket[]
  extraBucket?: HbarBucket
  themeTitleById?: Record<number, string>
  onThemeClick?: (themeId: number) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onToggleExcludeTopic: (id: number, excluded: boolean) => void
  onSetAct?: (id: number, act: 'opening' | 'conflict' | 'climax' | null) => void
  size?: 'large' | 'small'
}

function segmentWidths(counts: number[]): number[] {
  const total = counts.reduce((sum, c) => sum + c, 0)
  if (total === 0) return counts.map(() => 100 / counts.length)

  const raw = counts.map((c) => Math.max((c / total) * 100, c > 0 ? MIN_SEGMENT_PERCENT : 0))
  const rawTotal = raw.reduce((sum, w) => sum + w, 0)
  return raw.map((w) => (w / rawTotal) * 100)
}

function topicLocation(t: Topic): string | null {
  if (t.chapter_title) return t.chapter_title
  if (t.page_number != null) return `page ${t.page_number}`
  return null
}

function ActHbar({
  buckets,
  extraBucket,
  themeTitleById,
  onThemeClick,
  onUpdateTopic,
  onToggleExcludeTopic,
  onSetAct,
  size = 'large',
}: Props) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [hoveredTopicId, setHoveredTopicId] = useState<number | null>(null)
  const widths = segmentWidths(buckets.map((b) => b.activeTopics.length))

  const selected =
    selectedKey === null
      ? null
      : (buckets.find((b) => b.key === selectedKey) ?? (extraBucket?.key === selectedKey ? extraBucket : null))

  const allTopics = [...buckets.flatMap((b) => b.topics), ...(extraBucket?.topics ?? [])].sort(
    (a, b) => a.sequence_index - b.sequence_index
  )
  const hoveredIndex = hoveredTopicId === null ? -1 : allTopics.findIndex((t) => t.id === hoveredTopicId)
  const markerPercent =
    hoveredIndex === -1 || allTopics.length < 2 ? null : (hoveredIndex / (allTopics.length - 1)) * 100

  return (
    <div className="notecards">
      <div className={`hbar${size === 'small' ? ' hbar-small' : ''}`}>
        {markerPercent !== null && (
          <div className="hbar-marker" style={{ left: `${markerPercent}%` }} title="Where this topic sits in the story" />
        )}
        {buckets.map((bucket, i) => (
          <div
            key={bucket.key}
            className={`hbar-segment ${ACT_COLOR_CLASSES[i % ACT_COLOR_CLASSES.length]}${selectedKey === bucket.key ? ' active' : ''}`}
            style={{ width: `${widths[i]}%` }}
            onClick={() => setSelectedKey(bucket.key)}
          >
            <span className="hbar-label">{bucket.label}</span>
            <div className="hbar-tooltip">
              <strong>{bucket.label}</strong>
              <ul>
                {bucket.activeTopics.slice(0, 5).map((t) => {
                  const location = topicLocation(t)
                  return (
                    <li key={t.id}>
                      {t.title}
                      {location && <span className="hbar-tooltip-location"> — {location}</span>}
                    </li>
                  )
                })}
              </ul>
              {bucket.activeTopics.length === 0 && <span>No topics yet</span>}
              {bucket.activeTopics.length > 5 && <span>+{bucket.activeTopics.length - 5} more</span>}
            </div>
          </div>
        ))}
        {extraBucket && extraBucket.activeTopics.length > 0 && (
          <div
            className={`hbar-segment hbar-unassigned${selectedKey === extraBucket.key ? ' active' : ''}`}
            onClick={() => setSelectedKey(extraBucket.key)}
          >
            <span className="hbar-label">?</span>
            <div className="hbar-tooltip">
              <strong>{extraBucket.label}</strong>
              <ul>
                {extraBucket.activeTopics.slice(0, 5).map((t) => {
                  const location = topicLocation(t)
                  return (
                    <li key={t.id}>
                      {t.title}
                      {location && <span className="hbar-tooltip-location"> — {location}</span>}
                    </li>
                  )
                })}
              </ul>
            </div>
          </div>
        )}
      </div>

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
            onSetAct={onSetAct}
            onHoverTopic={setHoveredTopicId}
          />
        </>
      )}
    </div>
  )
}

export default ActHbar
