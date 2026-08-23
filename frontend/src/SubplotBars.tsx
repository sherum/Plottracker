import { useEffect, useState } from 'react'
import { buildActBuckets } from './actBuckets'
import HbarVisual from './HbarVisual'
import IconButton from './IconButton'
import type { Topic } from './TopicCardGrid'
import './SubplotBars.css'

interface Subplot {
  id: number
  theme_id: number
  title: string
  topic_count: number
}

interface SubplotWithTopics extends Subplot {
  topics: Topic[]
  startPercent: number
  widthPercent: number
}

interface Props {
  documentId: number | null
  storyMode: boolean
  topicOrderIndex: Map<number, number>
  refreshToken: number
  currentTopicId: number | null
  onNavigateTopic: (topicId: number) => void
  addTargetSubplotId: number | null
  deleteTargetIds: Set<number>
  onClickAdd: (subplotId: number) => void
  onToggleDelete: (subplotId: number) => void
  onDropTopic: (topicId: number, themeId: number, act: 'opening' | 'conflict' | 'climax' | null) => void
}

// A bar narrower than this is unreadable and hard to hit with a click/drop,
// so short subplots are floored to this width rather than shown true-to-scale.
const MIN_SPAN_PERCENT = 8

function SubplotBars({
  documentId,
  storyMode,
  topicOrderIndex,
  refreshToken,
  currentTopicId,
  onNavigateTopic,
  addTargetSubplotId,
  deleteTargetIds,
  onClickAdd,
  onToggleDelete,
  onDropTopic,
}: Props) {
  const [subplots, setSubplots] = useState<SubplotWithTopics[]>([])

  useEffect(() => {
    if (!storyMode && documentId === null) {
      setSubplots([])
      return
    }
    let cancelled = false

    const listUrl = storyMode ? '/subplots' : `/subplots?document_id=${documentId}`
    const total = topicOrderIndex.size

    fetch(listUrl)
      .then((res) => res.json())
      .then((list: Subplot[]) =>
        Promise.all(
          list.map((subplot) =>
            fetch(`/subplots/${subplot.id}/topics`)
              .then((res) => res.json())
              .then((topics: Topic[]) => {
                // Ranked by each topic's position in the currently displayed
                // (story- or document-wide) order, since raw sequence_index
                // is only comparable within a single document. The bar is
                // placed at that same span of the whole story's timeline, so
                // its position lines up with the top overview bar above it.
                const ranks = topics.map((t) => topicOrderIndex.get(t.id)).filter((r): r is number => r !== undefined)
                if (ranks.length === 0 || total === 0) {
                  return { ...subplot, topics, startPercent: 0, widthPercent: 100 }
                }
                const minRank = Math.min(...ranks)
                const maxRank = Math.max(...ranks)
                const rawStart = (minRank / total) * 100
                const rawWidth = ((maxRank + 1 - minRank) / total) * 100
                const widthPercent = Math.max(rawWidth, MIN_SPAN_PERCENT)
                const startPercent = Math.min(rawStart, 100 - widthPercent)
                return { ...subplot, topics, startPercent, widthPercent }
              })
          )
        )
      )
      .then((withTopics) => {
        if (cancelled) return
        // Top to bottom in the order each subplot first appears in the story.
        withTopics.sort((a, b) => a.startPercent - b.startPercent)
        setSubplots(withTopics)
      })
      .catch(() => {
        if (!cancelled) setSubplots([])
      })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId, storyMode, refreshToken])

  if (subplots.length === 0) return null

  function jumpToAct(topics: Topic[], actKey: string) {
    const { buckets, extraBucket } = buildActBuckets(topics)
    const bucket = buckets.find((b) => b.key === actKey) ?? (extraBucket.key === actKey ? extraBucket : null)
    const firstTopic = bucket?.topics[0]
    if (firstTopic) onNavigateTopic(firstTopic.id)
  }

  function dropOnTheme(themeId: number) {
    return (topicId: number, actKey: string) => onDropTopic(topicId, themeId, actKey === 'unassigned' ? null : (actKey as 'opening' | 'conflict' | 'climax'))
  }

  return (
    <div className="subplot-bars">
      {subplots.map((subplot) => {
        const { buckets, extraBucket } = buildActBuckets(subplot.topics)
        const isEmpty = subplot.topic_count === 0
        return (
          <div className={`subplot-bar-row${isEmpty ? ' subplot-bar-row-empty' : ''}`} key={subplot.id}>
            <div className="subplot-bar-header">
              <span className="subplot-bar-label" title={subplot.title}>
                {subplot.title}
              </span>
              {isEmpty && (
                <span
                  className="subplot-bar-empty-badge"
                  title="No active topics. A future reanalyze may repopulate it, or you can remove it."
                >
                  empty
                </span>
              )}
              <IconButton
                icon="add"
                label={`Add topics to ${subplot.title}`}
                active={addTargetSubplotId === subplot.id}
                onClick={() => onClickAdd(subplot.id)}
              />
              <IconButton
                icon="remove"
                label={`Mark ${subplot.title} for deletion`}
                active={deleteTargetIds.has(subplot.id)}
                onClick={() => onToggleDelete(subplot.id)}
              />
            </div>
            <div className="subplot-bar-track">
              <div
                className="subplot-bar-span"
                style={{ marginLeft: `${subplot.startPercent}%`, width: `${subplot.widthPercent}%` }}
              >
                <HbarVisual
                  buckets={buckets}
                  extraBucket={extraBucket}
                  onSegmentClick={(actKey) => jumpToAct(subplot.topics, actKey)}
                  onDropTopic={dropOnTheme(subplot.theme_id)}
                  markerTopicId={currentTopicId}
                  size="small"
                />
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default SubplotBars
