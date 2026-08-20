import { useState } from 'react'
import type { Topic } from './TopicCardGrid'
import './Sidekick.css'

interface Props {
  topics: Topic[]
}

function Sidekick({ topics }: Props) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [asking, setAsking] = useState(false)

  async function ask() {
    if (!question.trim()) return
    setAsking(true)
    setAnswer(null)
    const response = await fetch('/sidekick/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, topic_ids: topics.map((t) => t.id) }),
    })
    const data = await response.json()
    setAnswer(data.answer)
    setAsking(false)
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
        <button onClick={ask} disabled={asking || !question.trim()}>
          {asking ? 'Asking…' : 'Ask'}
        </button>
      </div>
      {answer && <p className="sidekick-answer">{answer}</p>}
    </div>
  )
}

export default Sidekick
