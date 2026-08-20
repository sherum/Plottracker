import { useState } from 'react'
import { useToast } from './ToastContext'
import type { Topic } from './TopicCardGrid'
import './Sidekick.css'

interface Props {
  topics: Topic[]
}

function Sidekick({ topics }: Props) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [asking, setAsking] = useState(false)
  const { showError } = useToast()

  async function ask() {
    if (!question.trim()) return
    setAsking(true)
    setAnswer(null)
    try {
      const response = await fetch('/sidekick/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, topic_ids: topics.map((t) => t.id) }),
      })
      if (!response.ok) throw new Error()
      const data = await response.json()
      setAnswer(data.answer)
    } catch {
      showError('The sidekick could not answer that. Please try again.')
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="sidekick">
      <div className="sidekick-input">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder={`Ask about these ${topics.length} topic${topics.length === 1 ? '' : 's'}…`}
        />
        <button onClick={ask} disabled={asking || !question.trim()} title="Ask the AI sidekick">
          {asking ? 'Asking…' : 'Ask'}
        </button>
      </div>
      {answer && <p className="sidekick-answer">{answer}</p>}
    </div>
  )
}

export default Sidekick
