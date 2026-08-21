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
  markerTopicId?: number | null
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

function HbarVisual({ buckets, extraBucket, selectedKey = null, onSegmentClick, markerTopicId, size = 'large' }: Props) {
  const widths = segmentWidths(buckets.map((b) => b.activeTopics.length))

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
          className={`hbar-segment ${ACT_COLOR_CLASSES[i % ACT_COLOR_CLASSES.length]}${selectedKey === bucket.key ? ' active' : ''}`}
          style={{ width: `${widths[i]}%` }}
          onClick={onSegmentClick ? () => onSegmentClick(bucket.key) : undefined}
          role={onSegmentClick ? 'button' : undefined}
          tabIndex={onSegmentClick ? 0 : undefined}
          aria-label={bucket.label}
          onKeyDown={onSegmentClick ? onActivateKey(() => onSegmentClick(bucket.key)) : undefined}
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
          onClick={onSegmentClick ? () => onSegmentClick(extraBucket.key) : undefined}
          role={onSegmentClick ? 'button' : undefined}
          tabIndex={onSegmentClick ? 0 : undefined}
          aria-label={extraBucket.label}
          onKeyDown={onSegmentClick ? onActivateKey(() => onSegmentClick(extraBucket.key)) : undefined}
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
