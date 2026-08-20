import { useState } from 'react'
import CardEditForm from './CardEditForm'
import Sidekick from './Sidekick'
import TopicCardGrid, { type Topic } from './TopicCardGrid'
import './Notecards.css'

const THEME_SEARCH_THRESHOLD = 6

interface Theme {
  id: number
  title: string
  summary: string
  excluded: boolean
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
  onToggleExcludeTopic: (id: number, excluded: boolean) => void
  onToggleExcludeTheme: (id: number, excluded: boolean) => void
  onUnassignTheme: (topicId: number) => void
  onSetAct: (id: number, act: 'opening' | 'conflict' | 'climax' | null) => void
}

function Notecards({
  themes,
  topics,
  selected,
  onSelect,
  onUpdateTopic,
  onUpdateTheme,
  onPromoteTheme,
  onToggleExcludeTopic,
  onToggleExcludeTheme,
  onUnassignTheme,
  onSetAct,
}: Props) {
  const [editingThemeId, setEditingThemeId] = useState<number | null>(null)
  const [themeSearch, setThemeSearch] = useState('')
  const unassignedTopics = topics.filter((t) => t.theme_id === null)

  if (selected !== null) {
    const isUnassigned = selected === UNASSIGNED
    const theme = isUnassigned ? null : themes.find((t) => t.id === selected)
    const shownTopics = isUnassigned ? unassignedTopics : topics.filter((t) => t.theme_id === selected)
    const activeTopics = shownTopics.filter((t) => !t.excluded)

    return (
      <div className="notecards">
        <button className="back" onClick={() => onSelect(null)} title="Back to the theme list">
          &larr; Themes
        </button>
        <h3>{isUnassigned ? 'Unassigned Topics' : theme?.title}</h3>
        {!isUnassigned && <p className="theme-summary">{theme?.summary}</p>}
        <TopicCardGrid
          topics={shownTopics}
          onUpdateTopic={onUpdateTopic}
          onToggleExcludeTopic={onToggleExcludeTopic}
          onRemoveTopic={isUnassigned ? undefined : onUnassignTheme}
          removeLabel="Remove from theme"
          onSetAct={onSetAct}
        />
        <Sidekick topics={activeTopics} />
      </div>
    )
  }

  const themeQuery = themeSearch.trim().toLowerCase()
  const shownThemes =
    themeQuery === ''
      ? themes
      : themes.filter(
          (t) => t.title.toLowerCase().includes(themeQuery) || t.summary.toLowerCase().includes(themeQuery)
        )

  return (
    <div className="notecards">
      {themes.length > THEME_SEARCH_THRESHOLD && (
        <input
          className="theme-search"
          value={themeSearch}
          onChange={(e) => setThemeSearch(e.target.value)}
          placeholder={`Search these ${themes.length} themes…`}
          aria-label="Search themes"
        />
      )}
      {themeQuery !== '' && shownThemes.length === 0 && <p className="hbar-hint">No themes match "{themeSearch}".</p>}
      <div className="card-grid">
        {shownThemes.map((theme) => {
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

          const activeTopicCount = topics.filter((t) => t.theme_id === theme.id && !t.excluded).length
          return (
            <div
              className={`card clickable${theme.excluded ? ' excluded' : ''}`}
              key={theme.id}
              onClick={() => onSelect(theme.id)}
            >
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
                    title="Edit this theme"
                  >
                    Edit
                  </button>
                  <button
                    className="edit-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      onToggleExcludeTheme(theme.id, !theme.excluded)
                    }}
                    aria-label={theme.excluded ? 'Include theme' : 'Exclude theme'}
                    title={theme.excluded ? 'Include this theme again' : 'Exclude this theme'}
                  >
                    {theme.excluded ? 'Include' : 'Exclude'}
                  </button>
                  <button
                    className="edit-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      onPromoteTheme(theme.id)
                    }}
                    aria-label="Promote theme to subplot"
                    title="Promote this theme to a subplot"
                  >
                    Promote
                  </button>
                </div>
              </div>
              <p>{theme.summary}</p>
              <div className="card-tags">
                {theme.excluded && <span className="tag">Excluded</span>}
                <span className="tag">{activeTopicCount} topics</span>
              </div>
            </div>
          )
        })}
        {unassignedTopics.length > 0 && (
          <div className="card clickable" onClick={() => onSelect(UNASSIGNED)}>
            <h4>Unassigned Topics</h4>
            <p>Topics not yet grouped into a theme.</p>
            <span className="tag">{unassignedTopics.filter((t) => !t.excluded).length} topics</span>
          </div>
        )}
      </div>
      {themes.length === 0 && unassignedTopics.length === 0 && (
        <p className="hbar-hint">No notecards yet. Load a document and analyze it to see topics and themes here.</p>
      )}
    </div>
  )
}

export default Notecards
