import { useState, type DragEvent } from 'react'
import { onActivateKey } from './keyboardActivate'
import type { Topic } from './TopicCardGrid'
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
  selectedKey?: string | null
  onSegmentClick?: (key: string) => void
  onDropTopic?: (topicId: number, key: string) => void
  markerTopicId?: number | null
  size?: 'large' | 'small'
}

export const TOPIC_DRAG_MIME = 'application/x-topic-id'

function segmentWidths(counts: number[]): number[] {
  const total = counts.reduce((sum, c) => sum + c, 0)
  if (total === 0) return counts.map(() => 100 / counts.length)

  // True percentage of topics per act, except acts too small to read/click
  // are bumped to the floor - and only the other acts give up that width,
  // so the floor no longer waters down segments that should stay large.
  const truePercents = counts.map((c) => (c / total) * 100)
  const needsFloor = truePercents.map((p, i) => counts[i] > 0 && p < MIN_SEGMENT_PERCENT)
  const flooredTotal = needsFloor.filter(Boolean).length * MIN_SEGMENT_PERCENT
  const remaining = 100 - flooredTotal
  const scalableTotal = truePercents.reduce((sum, p, i) => sum + (needsFloor[i] ? 0 : p), 0)

  return truePercents.map((p, i) => {
    if (needsFloor[i]) return MIN_SEGMENT_PERCENT
    if (scalableTotal === 0) return 0
    return (p / scalableTotal) * remaining
  })
}

function topicLocation(t: Topic): string | null {
  if (t.chapter_title) return t.chapter_title
  if (t.page_number != null) return `page ${t.page_number}`
  return null
}

function HbarVisual({
  buckets,
  extraBucket,
  selectedKey = null,
  onSegmentClick,
  onDropTopic,
  markerTopicId,
  size = 'large',
}: Props) {
  const [dragOverKey, setDragOverKey] = useState<string | null>(null)
  const widths = segmentWidths(buckets.map((b) => b.activeTopics.length))

  function dropHandlers(key: string) {
    if (!onDropTopic) return {}
    return {
      onDragOver: (e: DragEvent) => {
        e.preventDefault()
        setDragOverKey(key)
      },
      onDragLeave: () => setDragOverKey((prev) => (prev === key ? null : prev)),
      onDrop: (e: DragEvent) => {
        e.preventDefault()
        setDragOverKey(null)
        const topicId = Number(e.dataTransfer.getData(TOPIC_DRAG_MIME))
        if (Number.isFinite(topicId) && topicId > 0) onDropTopic(topicId, key)
      },
    }
  }

  const allTopics = [...buckets.flatMap((b) => b.topics), ...(extraBucket?.topics ?? [])].sort(
    (a, b) => a.sequence_index - b.sequence_index
  )
  const markerIndex = markerTopicId == null ? -1 : allTopics.findIndex((t) => t.id === markerTopicId)
  const markerPercent = markerIndex === -1 || allTopics.length < 2 ? null : (markerIndex / (allTopics.length - 1)) * 100

  return (
    <div className={`hbar${size === 'small' ? ' hbar-small' : ''}`}>
      {markerPercent !== null && (
        <div className="hbar-marker" style={{ left: `${markerPercent}%` }} title="Where this topic sits in the story" />
      )}
      {buckets.map((bucket, i) => (
        <div
          key={bucket.key}
          className={`hbar-segment ${ACT_COLOR_CLASSES[i % ACT_COLOR_CLASSES.length]}${selectedKey === bucket.key ? ' active' : ''}${dragOverKey === bucket.key ? ' drag-over' : ''}`}
          style={{ width: `${widths[i]}%` }}
          onClick={onSegmentClick ? () => onSegmentClick(bucket.key) : undefined}
          role={onSegmentClick ? 'button' : undefined}
          tabIndex={onSegmentClick ? 0 : undefined}
          aria-label={bucket.label}
          onKeyDown={onSegmentClick ? onActivateKey(() => onSegmentClick(bucket.key)) : undefined}
          {...dropHandlers(bucket.key)}
        >
          <span className={`hbar-label${bucket.activeTopics.length === 0 ? ' hbar-label-empty' : ''}`}>
            {bucket.label}
          </span>
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
          className={`hbar-segment hbar-unassigned${selectedKey === extraBucket.key ? ' active' : ''}${dragOverKey === extraBucket.key ? ' drag-over' : ''}`}
          onClick={onSegmentClick ? () => onSegmentClick(extraBucket.key) : undefined}
          role={onSegmentClick ? 'button' : undefined}
          tabIndex={onSegmentClick ? 0 : undefined}
          aria-label={extraBucket.label}
          onKeyDown={onSegmentClick ? onActivateKey(() => onSegmentClick(extraBucket.key)) : undefined}
          {...dropHandlers(extraBucket.key)}
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
  )
}

export default HbarVisual
