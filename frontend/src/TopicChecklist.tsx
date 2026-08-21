import type { Topic } from './TopicCardGrid'
import './TopicChecklist.css'

interface Props {
  topics: Topic[]
  selectedTopicIds: Set<number>
  onToggle: (topicId: number) => void
  onPreviewTopic?: (topicId: number | null, mode: 'theme' | 'topic') => void
}

function TopicChecklist({ topics, selectedTopicIds, onToggle, onPreviewTopic }: Props) {
  if (topics.length === 0) {
    return <p className="hbar-hint">No topics matched. Ask the sidekick to filter again.</p>
  }

  return (
    <ul className="topic-checklist">
      {topics.map((topic) => {
        const selected = selectedTopicIds.has(topic.id)
        return (
          <li key={topic.id}>
            <button
              className={`topic-checklist-row${selected ? ' selected' : ''}`}
              onClick={() => onToggle(topic.id)}
              onMouseEnter={() => onPreviewTopic?.(topic.id, 'theme')}
              onMouseLeave={() => onPreviewTopic?.(null, 'theme')}
              role="checkbox"
              aria-checked={selected}
            >
              <span className={`select-checkbox${selected ? ' checked' : ''}`} />
              <span className="topic-checklist-title">{topic.title}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}

export default TopicChecklist
