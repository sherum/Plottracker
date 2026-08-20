import { useState } from 'react'
import CardEditForm from './CardEditForm'
import TopicCardGrid, { type Topic } from './TopicCardGrid'
import './Notecards.css'

interface Theme {
  id: number
  title: string
  summary: string
}

export const UNASSIGNED = 'unassigned'
export type Selection = number | typeof UNASSIGNED | null

interface Props {
  themes: Theme[]
  topics: Topic[]
  selected: Selection
  onSelect: (selection: Selection) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onUpdateTheme: (id: number, data: { title: string; summary: string }) => void
  onPromoteTheme: (themeId: number) => void
}

function Notecards({ themes, topics, selected, onSelect, onUpdateTopic, onUpdateTheme, onPromoteTheme }: Props) {
  const [editingThemeId, setEditingThemeId] = useState<number | null>(null)
  const unassignedTopics = topics.filter((t) => t.theme_id === null)

  if (selected !== null) {
    const isUnassigned = selected === UNASSIGNED
    const theme = isUnassigned ? null : themes.find((t) => t.id === selected)
    const shownTopics = isUnassigned ? unassignedTopics : topics.filter((t) => t.theme_id === selected)

    return (
      <div className="notecards">
        <button className="back" onClick={() => onSelect(null)}>
          &larr; Themes
        </button>
        <h3>{isUnassigned ? 'Unassigned Topics' : theme?.title}</h3>
        {!isUnassigned && <p className="theme-summary">{theme?.summary}</p>}
        <TopicCardGrid topics={shownTopics} onUpdateTopic={onUpdateTopic} />
      </div>
    )
  }

  return (
    <div className="notecards">
      <div className="card-grid">
        {themes.map((theme) => {
          if (editingThemeId === theme.id) {
            return (
              <CardEditForm
                key={theme.id}
                title={theme.title}
                summary={theme.summary}
                onSave={(data) => {
                  onUpdateTheme(theme.id, data)
                  setEditingThemeId(null)
                }}
                onCancel={() => setEditingThemeId(null)}
              />
            )
          }

          return (
            <div className="card clickable" key={theme.id} onClick={() => onSelect(theme.id)}>
              <div className="card-header">
                <h4>{theme.title}</h4>
                <div className="card-header-actions">
                  <button
                    className="edit-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      setEditingThemeId(theme.id)
                    }}
                    aria-label="Edit theme"
                  >
                    Edit
                  </button>
                  <button
                    className="edit-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      onPromoteTheme(theme.id)
                    }}
                    aria-label="Promote theme to subplot"
                  >
                    Promote
                  </button>
                </div>
              </div>
              <p>{theme.summary}</p>
              <span className="tag">{topics.filter((t) => t.theme_id === theme.id).length} topics</span>
            </div>
          )
        })}
        {unassignedTopics.length > 0 && (
          <div className="card clickable" onClick={() => onSelect(UNASSIGNED)}>
            <h4>Unassigned Topics</h4>
            <p>Topics not yet grouped into a theme.</p>
            <span className="tag">{unassignedTopics.length} topics</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default Notecards
