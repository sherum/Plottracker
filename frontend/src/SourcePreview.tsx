import { useEffect, useState } from 'react'
import IconButton from './IconButton'
import type { Topic } from './TopicCardGrid'
import './SourcePreview.css'

interface Segment {
  id: number
  text: string
  sequence_index: number
}

interface Props {
  topic: Topic | null
  mode: 'theme' | 'topic'
  onSplitTopic?: (topicId: number, segmentId: number) => void
}

function SourcePreview({ topic, mode, onSplitTopic }: Props) {
  const [segments, setSegments] = useState<Segment[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (mode !== 'topic' || !topic) return
    setLoading(true)
    fetch(`/topics/${topic.id}/segments`)
      .then((res) => res.json())
      .then((data) => setSegments(data))
      .catch(() => setSegments([]))
      .finally(() => setLoading(false))
  }, [topic, mode])

  if (mode === 'theme') {
    return (
      <textarea
        className="source-preview"
        readOnly
        value={topic?.summary ?? ''}
        placeholder="Hover a topic icon in Theme View to preview its text here."
      />
    )
  }

  if (!topic) {
    return (
      <div className="source-preview source-preview-empty">
        The current topic’s manuscript text will appear here.
      </div>
    )
  }

  return (
    <div className="source-preview">
      {loading && <p>Loading…</p>}
      {!loading &&
        segments.map((segment, i) => (
          <div key={segment.id}>
            {i > 0 && onSplitTopic && (
              <div className="source-preview-split-gap">
                <IconButton
                  icon="split"
                  label="Split topic here"
                  onClick={() => onSplitTopic(topic.id, segment.id)}
                />
              </div>
            )}
            <p className="source-preview-paragraph">{segment.text}</p>
          </div>
        ))}
    </div>
  )
}

export default SourcePreview
