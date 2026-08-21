import { useEffect, useState } from 'react'
import { buildActBuckets } from './actBuckets'
import HbarVisual from './HbarVisual'
import type { Topic } from './TopicCardGrid'
import './SubplotBars.css'

interface Subplot {
  id: number
  title: string
  topic_count: number
}

interface SubplotWithTopics extends Subplot {
  topics: Topic[]
  span: number
}

interface Props {
  documentId: number | null
  refreshToken: number
  currentTopicId: number | null
  onNavigateTopic: (topicId: number) => void
}

function SubplotBars({ documentId, refreshToken, currentTopicId, onNavigateTopic }: Props) {
  const [subplots, setSubplots] = useState<SubplotWithTopics[]>([])

  useEffect(() => {
    if (documentId === null) {
      setSubplots([])
      return
    }
    let cancelled = false

    fetch(`/subplots?document_id=${documentId}`)
      .then((res) => res.json())
      .then((list: Subplot[]) =>
        Promise.all(
          list.map((subplot) =>
            fetch(`/subplots/${subplot.id}/topics`)
              .then((res) => res.json())
              .then((topics: Topic[]) => {
                const sequenceIndexes = topics.map((t) => t.sequence_index)
                const span = sequenceIndexes.length > 0 ? Math.max(...sequenceIndexes) - Math.min(...sequenceIndexes) : 0
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
  }, [documentId, refreshToken])

  if (documentId === null || subplots.length === 0) return null

  function jumpToAct(subplot: SubplotWithTopics, actKey: string) {
    const { buckets, extraBucket } = buildActBuckets(subplot.topics)
    const bucket = buckets.find((b) => b.key === actKey) ?? (extraBucket.key === actKey ? extraBucket : null)
    const firstTopic = bucket?.topics[0]
    if (firstTopic) onNavigateTopic(firstTopic.id)
  }

  return (
    <div className="subplot-bars">
      {subplots.map((subplot) => {
        const { buckets, extraBucket } = buildActBuckets(subplot.topics)
        return (
          <div className="subplot-bar-row" key={subplot.id}>
            <span className="subplot-bar-label" title={subplot.title}>
              {subplot.title}
            </span>
            <HbarVisual
              buckets={buckets}
              extraBucket={extraBucket}
              onSegmentClick={(actKey) => jumpToAct(subplot, actKey)}
              markerTopicId={currentTopicId}
              size="small"
            />
          </div>
        )
      })}
    </div>
  )
}

export default SubplotBars
