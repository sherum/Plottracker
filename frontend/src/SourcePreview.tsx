import { useEffect, useState } from 'react'
import type { Topic } from './TopicCardGrid'
import './SourcePreview.css'

interface Props {
  topic: Topic | null
  mode: 'theme' | 'topic'
}

function SourcePreview({ topic, mode }: Props) {
  const [sourceText, setSourceText] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (mode !== 'topic' || !topic) return
    setLoading(true)
    fetch(`/topics/${topic.id}/source-text`)
      .then((res) => res.json())
      .then((data) => setSourceText(data.text))
      .catch(() => setSourceText('Could not load the source text.'))
      .finally(() => setLoading(false))
  }, [topic, mode])

  const value = !topic ? '' : mode === 'theme' ? topic.summary : loading ? 'Loading…' : sourceText

  const placeholder =
    mode === 'theme'
      ? 'Hover a topic icon in Theme View to preview its text here.'
      : 'The current topic’s manuscript text will appear here.'

  return <textarea className="source-preview" readOnly value={value} placeholder={placeholder} />
}

export default SourcePreview
