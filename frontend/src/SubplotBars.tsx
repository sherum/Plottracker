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
  span: number
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
  mainTheme: { id: number; topics: Topic[] } | null
  onDropTopic: (topicId: number, themeId: number, act: 'opening' | 'conflict' | 'climax' | null) => void
}

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
  mainTheme,
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
                // is only comparable within a single document.
                const ranks = topics.map((t) => topicOrderIndex.get(t.id)).filter((r): r is number => r !== undefined)
                const span = ranks.length > 0 ? Math.max(...ranks) - Math.min(...ranks) : 0
                return { ...subplot, topics, span }
              })
          )
        )
      )
      .then((withTopics) => {
        if (cancelled) return
        withTopics.sort((a, b) => b.span - a.span)
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

  if (subplots.length === 0 && !mainTheme) return null

  function jumpToAct(topics: Topic[], actKey: string) {
    const { buckets, extraBucket } = buildActBuckets(topics)
    const bucket = buckets.find((b) => b.key === actKey) ?? (extraBucket.key === actKey ? extraBucket : null)
    const firstTopic = bucket?.topics[0]
    if (firstTopic) onNavigateTopic(firstTopic.id)
  }

  function dropOnTheme(themeId: number) {
    return (topicId: number, actKey: string) => onDropTopic(topicId, themeId, actKey === 'unassigned' ? null : (actKey as 'opening' | 'conflict' | 'climax'))
  }

  const mainBuckets = mainTheme ? buildActBuckets(mainTheme.topics) : null

  return (
    <div className="subplot-bars">
      {mainTheme && mainBuckets && (
        <div className="subplot-bar-row subplot-bar-row-main">
          <span className="subplot-bar-label" title="Main">
            Main
          </span>
          <HbarVisual
            buckets={mainBuckets.buckets}
            extraBucket={mainBuckets.extraBucket}
            onSegmentClick={(actKey) => jumpToAct(mainTheme.topics, actKey)}
            onDropTopic={dropOnTheme(mainTheme.id)}
            markerTopicId={currentTopicId}
            size="small"
          />
        </div>
      )}
      {subplots.map((subplot) => {
        const { buckets, extraBucket } = buildActBuckets(subplot.topics)
        const isEmpty = subplot.topic_count === 0
        return (
          <div className={`subplot-bar-row${isEmpty ? ' subplot-bar-row-empty' : ''}`} key={subplot.id}>
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
            <HbarVisual
              buckets={buckets}
              extraBucket={extraBucket}
              onSegmentClick={(actKey) => jumpToAct(subplot.topics, actKey)}
              onDropTopic={dropOnTheme(subplot.theme_id)}
              markerTopicId={currentTopicId}
              size="small"
            />
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
        )
      })}
    </div>
  )
}

export default SubplotBars
