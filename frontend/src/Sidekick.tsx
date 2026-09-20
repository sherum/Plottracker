import { useEffect, useRef, useState } from 'react'
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
  addTargetSubplotId?: number | null
  addTargetIsNew?: boolean
  onFilteredTopics?: (topicIds: number[]) => void
  filteredSelectionActive?: boolean
  onFinishAdd?: () => Promise<{ count: number; title: string }>
  deleteTargetCount?: number
  onFinishDelete?: () => Promise<{ count: number }>
  storyId?: number | null
}

function Sidekick({
  topics,
  storyId,
  currentTopicId,
  currentThemeId,
  onActionsPerformed,
  onSubplotCreated,
  selection,
  onFinishSelection,
  addTargetSubplotId,
  addTargetIsNew,
  onFilteredTopics,
  filteredSelectionActive,
  onFinishAdd,
  deleteTargetCount = 0,
  onFinishDelete,
}: Props) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [asking, setAsking] = useState(false)
  const { showError } = useToast()
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const addingTopics = addTargetIsNew === true || (addTargetSubplotId ?? null) !== null

  // Adding topics starts by asking here, so take the cursor.
  useEffect(() => {
    if (addingTopics) inputRef.current?.focus()
  }, [addingTopics])

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

    if (filteredSelectionActive && onFinishAdd && /^move( them)?[.!]*$/i.test(trimmed)) {
      setAsking(true)
      setAnswer(null)
      try {
        const { count, title } = await onFinishAdd()
        setAnswer(count > 0 ? `Added ${count} topic${count === 1 ? '' : 's'} to "${title}".` : 'Nothing was added.')
        setQuestion('')
      } catch {
        showError('Could not move those topics. Please try again.')
      } finally {
        setAsking(false)
      }
      return
    }

    if (deleteTargetCount > 0 && onFinishDelete && /^delete( them)?[.!]*$/i.test(trimmed)) {
      setAsking(true)
      setAnswer(null)
      try {
        const { count } = await onFinishDelete()
        setAnswer(`Deleted ${count} subplot${count === 1 ? '' : 's'}.`)
        setQuestion('')
      } catch {
        showError('Could not delete those subplots. Please try again.')
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
          add_target_subplot_id: addTargetSubplotId ?? null,
          add_target_is_new: addTargetIsNew ?? false,
          story_id: storyId ?? null,
        }),
      })
      if (!response.ok) throw new Error()
      const data = await response.json()
      setAnswer(data.answer)
      setQuestion('')
      if (data.actions?.length > 0) onActionsPerformed?.()
      if (data.created_subplot_id != null) onSubplotCreated?.(data.created_subplot_id)
      if (data.filtered_topic_ids != null) onFilteredTopics?.(data.filtered_topic_ids)
    } catch {
      showError('The sidekick could not answer that. Please try again.')
    } finally {
      setAsking(false)
    }
  }

  const hint = selection
    ? `Selecting topics for “${selection.subplotTitle}” — ${selection.selectedTopicIds.size} selected. Toggle topics in the plot viewer, then type “done” below.`
    : filteredSelectionActive
      ? 'Select topics from the filtered list, then type “move them” below.'
      : addingTopics
        ? 'Say which topics to add, e.g. “unassigned topics” or “topics starting with Q”.'
        : deleteTargetCount > 0
        ? `${deleteTargetCount} subplot${deleteTargetCount === 1 ? '' : 's'} marked for deletion. Type “delete them” below, or click − again to unmark.`
        : topics.length === 0
          ? 'Load a document, then ask the sidekick to look up, change, or organize anything in it.'
          : `Ask about these ${topics.length} topic${topics.length === 1 ? '' : 's'}, or ask the sidekick to change something.`

  const placeholder = selection
    ? 'Type “done” when finished…'
    : filteredSelectionActive
      ? 'Type “move them” when ready…'
      : addingTopics
        ? 'Which topics? e.g. unassigned topics…'
        : deleteTargetCount > 0
        ? 'Type “delete them” to confirm…'
        : 'Ask me anything…'

  return (
    <div className="sidekick">
      <div className="sidekick-answer-area">
        {asking ? (
          <p className="hbar-hint">Working on it - this can take 15 to 20 seconds on a long story.</p>
        ) : answer ? (
          <p className="sidekick-answer">{answer}</p>
        ) : (
          <p className="hbar-hint">{hint}</p>
        )}
      </div>
      <div className="sidekick-input">
        <textarea
          ref={inputRef}
          className="form-control form-control-sm"
          value={question}
          rows={6}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder={placeholder}
        ></textarea>
      </div>
        <button
          type="button"
          className="btn btn-sm btn-primary"
          onClick={ask}
          disabled={asking || !question.trim()}
          title="Ask the AI sidekick"
        >
          {asking ? 'Asking…' : 'Ask'}
        </button>
      </div>
    // </div>
  )
}

export default Sidekick
