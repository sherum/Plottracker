import { useState } from 'react'
import CardEditForm from './CardEditForm'
import StatusIcon from './StatusIcon'
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
  chapter_title?: string | null
  page_number?: number | null
}

const SEARCH_THRESHOLD = 6

interface Props {
  topics: Topic[]
  themeTitleById?: Record<number, string>
  onThemeClick?: (themeId: number) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onRemoveTopic?: (id: number) => void
  removeLabel?: string
  onToggleExcludeTopic: (id: number, excluded: boolean) => void
  onHoverTopic?: (id: number | null) => void
}

function TopicCardGrid({
  topics,
  themeTitleById,
  onThemeClick,
  onUpdateTopic,
  onRemoveTopic,
  removeLabel = 'Remove',
  onToggleExcludeTopic,
  onHoverTopic,
}: Props) {
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')

  const query = search.trim().toLowerCase()
  const shownTopics =
    query === ''
      ? topics
      : topics.filter(
          (t) => t.title.toLowerCase().includes(query) || t.summary.toLowerCase().includes(query)
        )

  return (
    <div>
      {topics.length > SEARCH_THRESHOLD && (
        <input
          className="topic-search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={`Search these ${topics.length} topics…`}
          aria-label="Search topics"
        />
      )}
      {query !== '' && shownTopics.length === 0 && <p className="hbar-hint">No topics match "{search}".</p>}
      <div className="card-grid">
      {shownTopics.map((topic) => {
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
        const actClass = topic.act ? ` card-act-${topic.act}` : ''
        return (
          <div
            className={`card${actClass}${topic.excluded ? ' excluded' : ''}`}
            key={topic.id}
            onMouseEnter={onHoverTopic ? () => onHoverTopic(topic.id) : undefined}
            onMouseLeave={onHoverTopic ? () => onHoverTopic(null) : undefined}
          >
            <div className="card-header">
              <h4>{topic.title}</h4>
              <div className="card-header-actions">
                <button
                  className="edit-btn"
                  onClick={() => setEditingId(topic.id)}
                  aria-label="Edit topic"
                  title="Edit this topic"
                >
                  Edit
                </button>
                <button
                  className="edit-btn"
                  onClick={() => onToggleExcludeTopic(topic.id, !topic.excluded)}
                  aria-label={topic.excluded ? 'Include topic' : 'Exclude topic'}
                  title={topic.excluded ? 'Include this topic again' : 'Exclude this topic'}
                >
                  {topic.excluded ? 'Include' : 'Exclude'}
                </button>
                {onRemoveTopic && (
                  <button
                    className="edit-btn"
                    onClick={() => onRemoveTopic(topic.id)}
                    aria-label={removeLabel}
                    title={removeLabel}
                  >
                    {removeLabel}
                  </button>
                )}
              </div>
            </div>
            <p>{topic.summary}</p>
            <div className="card-tags">
              {topic.excluded && <StatusIcon icon="excluded" label="Excluded" />}
              <span className="tag">{topic.document_filename}</span>
              {themeTitle && (
                <StatusIcon
                  icon="theme"
                  label={`Part of theme: ${themeTitle}`}
                  onClick={onThemeClick ? () => onThemeClick(topic.theme_id!) : undefined}
                >
                  {themeTitle}
                </StatusIcon>
              )}
            </div>
          </div>
        )
      })}
      </div>
    </div>
  )
}

export default TopicCardGrid
