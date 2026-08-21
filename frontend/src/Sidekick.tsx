import { useState } from 'react'
import { useToast } from './ToastContext'
import type { Topic } from './TopicCardGrid'
import './Sidekick.css'

interface Selection {
  subplotId: number
  subplotTitle: string
  selectedTopicIds: Set<number>
}

interface Props {
  topics: Topic[]
  currentTopicId?: number | null
  currentThemeId?: number | null
  onActionsPerformed?: () => void
  onSubplotCreated?: (subplotId: number) => void
  selection?: Selection | null
  onFinishSelection?: () => Promise<{ count: number; title: string }>
}

function Sidekick({
  topics,
  currentTopicId,
  currentThemeId,
  onActionsPerformed,
  onSubplotCreated,
  selection,
  onFinishSelection,
}: Props) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [asking, setAsking] = useState(false)
  const { showError } = useToast()

  async function ask() {
    const trimmed = question.trim()
    if (!trimmed) return

    if (selection && onFinishSelection && /^done[.!]*$/i.test(trimmed)) {
      setAsking(true)
      setAnswer(null)
      try {
        const { count, title } = await onFinishSelection()
        setAnswer(`Added ${count} topic${count === 1 ? '' : 's'} to "${title}".`)
        setQuestion('')
      } catch {
        showError('Could not save the topic selection. Please try again.')
      } finally {
        setAsking(false)
      }
      return
    }

    setAsking(true)
    setAnswer(null)
    try {
      const response = await fetch('/sidekick/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: trimmed,
          topic_ids: topics.map((t) => t.id),
          current_topic_id: currentTopicId ?? null,
          current_theme_id: currentThemeId ?? null,
        }),
      })
      if (!response.ok) throw new Error()
      const data = await response.json()
      setAnswer(data.answer)
      setQuestion('')
      if (data.actions?.length > 0) onActionsPerformed?.()
      if (data.created_subplot_id != null) onSubplotCreated?.(data.created_subplot_id)
    } catch {
      showError('The sidekick could not answer that. Please try again.')
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="sidekick">
      <div className="sidekick-answer-area">
        {answer ? (
          <p className="sidekick-answer">{answer}</p>
        ) : selection ? (
          <p className="hbar-hint">
            Selecting topics for “{selection.subplotTitle}” — {selection.selectedTopicIds.size} selected. Toggle
            topics in the plot viewer, then type “done” below.
          </p>
        ) : (
          <p className="hbar-hint">
            {topics.length === 0
              ? 'Load a document, then ask the sidekick to look up, change, or organize anything in it.'
              : `Ask about these ${topics.length} topic${topics.length === 1 ? '' : 's'}, or ask the sidekick to change something.`}
          </p>
        )}
      </div>
      <div className="sidekick-input">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder={selection ? 'Type “done” when finished…' : 'Ask me anything…'}
        />
        <button onClick={ask} disabled={asking || !question.trim()} title="Ask the AI sidekick">
          {asking ? 'Asking…' : 'Ask'}
        </button>
      </div>
    </div>
  )
}

export default Sidekick
