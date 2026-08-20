import { useState } from 'react'
import CardEditForm from './CardEditForm'
import './Notecards.css'

export interface Topic {
  id: number
  theme_id: number | null
  act: 'opening' | 'conflict' | 'climax' | null
  title: string
  summary: string
  document_filename: string
  sequence_index: number
  excluded: boolean
}

interface Props {
  topics: Topic[]
  themeTitleById?: Record<number, string>
  onThemeClick?: (themeId: number) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onRemoveTopic?: (id: number) => void
  onToggleExcludeTopic: (id: number, excluded: boolean) => void
}

function TopicCardGrid({
  topics,
  themeTitleById,
  onThemeClick,
  onUpdateTopic,
  onRemoveTopic,
  onToggleExcludeTopic,
}: Props) {
  const [editingId, setEditingId] = useState<number | null>(null)

  return (
    <div className="card-grid">
      {topics.map((topic) => {
        if (editingId === topic.id) {
          return (
            <CardEditForm
              key={topic.id}
              title={topic.title}
              summary={topic.summary}
              onSave={(data) => {
                onUpdateTopic(topic.id, data)
                setEditingId(null)
              }}
              onCancel={() => setEditingId(null)}
            />
          )
        }

        const themeTitle = topic.theme_id !== null ? themeTitleById?.[topic.theme_id] : undefined
        return (
          <div className={`card${topic.excluded ? ' excluded' : ''}`} key={topic.id}>
            <div className="card-header">
              <h4>{topic.title}</h4>
              <div className="card-header-actions">
                <button className="edit-btn" onClick={() => setEditingId(topic.id)} aria-label="Edit topic">
                  Edit
                </button>
                <button
                  className="edit-btn"
                  onClick={() => onToggleExcludeTopic(topic.id, !topic.excluded)}
                  aria-label={topic.excluded ? 'Include topic' : 'Exclude topic'}
                >
                  {topic.excluded ? 'Include' : 'Exclude'}
                </button>
                {onRemoveTopic && (
                  <button
                    className="edit-btn"
                    onClick={() => onRemoveTopic(topic.id)}
                    aria-label="Remove topic from subplot"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
            <p>{topic.summary}</p>
            <div className="card-tags">
              {topic.excluded && <span className="tag">Excluded</span>}
              <span className="tag">{topic.document_filename}</span>
              {themeTitle && (
                <span
                  className={onThemeClick ? 'tag tag-link' : 'tag'}
                  onClick={onThemeClick ? () => onThemeClick(topic.theme_id!) : undefined}
                >
                  {themeTitle}
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default TopicCardGrid
