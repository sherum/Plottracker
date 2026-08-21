import { useState } from 'react'
import CardEditForm from './CardEditForm'
import StatusIcon from './StatusIcon'
import type { Topic } from './TopicCardGrid'
import './PlotCarousel.css'

interface Theme {
  id: number
  title: string
  summary: string
  excluded: boolean
}

interface Props {
  topics: Topic[]
  themes: Theme[]
  currentTopicId: number | null
  onNavigateTopic: (topicId: number) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onUpdateTheme: (id: number, data: { title: string; summary: string }) => void
}

function wrap(index: number, length: number): number {
  if (length === 0) return 0
  return ((index % length) + length) % length
}

function PlotCarousel({ topics, themes, currentTopicId, onNavigateTopic, onUpdateTopic, onUpdateTheme }: Props) {
  const [view, setView] = useState<'topic' | 'theme'>('topic')
  const [themeIndex, setThemeIndex] = useState(0)
  const [editing, setEditing] = useState(false)

  const orderedTopics = [...topics].sort((a, b) => a.sequence_index - b.sequence_index)
  const themeTitleById = Object.fromEntries(themes.map((t) => [t.id, t.title]))
  const topicIndex = Math.max(
    0,
    orderedTopics.findIndex((t) => t.id === currentTopicId)
  )

  function jumpToTopic(topicId: number) {
    onNavigateTopic(topicId)
    setEditing(false)
    setView('topic')
  }

  if (orderedTopics.length === 0) {
    return (
      <div className="plot-carousel">
        <ViewToggle view={view} onChange={setView} />
        <p className="hbar-hint">Load a document and analyze it to browse its topics and themes here.</p>
      </div>
    )
  }

  return (
    <div className="plot-carousel">
      <ViewToggle view={view} onChange={setView} />

      {view === 'topic' ? (
        <TopicView
          orderedTopics={orderedTopics}
          topicIndex={topicIndex}
          onNavigate={(i) => {
            onNavigateTopic(orderedTopics[wrap(i, orderedTopics.length)].id)
            setEditing(false)
          }}
          editing={editing}
          onStartEdit={() => setEditing(true)}
          onCancelEdit={() => setEditing(false)}
          onSave={(data) => {
            onUpdateTopic(orderedTopics[topicIndex].id, data)
            setEditing(false)
          }}
          themeTitleById={themeTitleById}
        />
      ) : (
        <ThemeView
          themes={themes}
          themeIndex={wrap(themeIndex, themes.length)}
          onNavigate={(i) => {
            setThemeIndex(wrap(i, themes.length))
            setEditing(false)
          }}
          editing={editing}
          onStartEdit={() => setEditing(true)}
          onCancelEdit={() => setEditing(false)}
          onSave={(data) => {
            if (themes[wrap(themeIndex, themes.length)]) {
              onUpdateTheme(themes[wrap(themeIndex, themes.length)].id, data)
            }
            setEditing(false)
          }}
          topics={topics}
          onTopicIconClick={jumpToTopic}
        />
      )}
    </div>
  )
}

function ViewToggle({ view, onChange }: { view: 'topic' | 'theme'; onChange: (v: 'topic' | 'theme') => void }) {
  return (
    <div className="carousel-toggle">
      <button
        className={`carousel-toggle-btn carousel-toggle-topic${view === 'topic' ? ' active' : ''}`}
        onClick={() => onChange('topic')}
        aria-pressed={view === 'topic'}
      >
        Topic View
      </button>
      <button
        className={`carousel-toggle-btn carousel-toggle-theme${view === 'theme' ? ' active' : ''}`}
        onClick={() => onChange('theme')}
        aria-pressed={view === 'theme'}
      >
        Theme View
      </button>
    </div>
  )
}

interface TopicViewProps {
  orderedTopics: Topic[]
  topicIndex: number
  onNavigate: (index: number) => void
  editing: boolean
  onStartEdit: () => void
  onCancelEdit: () => void
  onSave: (data: { title: string; summary: string }) => void
  themeTitleById: Record<number, string>
}

function TopicView({
  orderedTopics,
  topicIndex,
  onNavigate,
  editing,
  onStartEdit,
  onCancelEdit,
  onSave,
  themeTitleById,
}: TopicViewProps) {
  const current = orderedTopics[topicIndex]
  const previous = orderedTopics[wrap(topicIndex - 1, orderedTopics.length)]
  const next = orderedTopics[wrap(topicIndex + 1, orderedTopics.length)]
  const single = orderedTopics.length === 1

  return (
    <>
      <div className="carousel-nav carousel-nav-topic">
        <button className="carousel-tile" onClick={() => onNavigate(topicIndex - 1)} disabled={single}>
          <span className="carousel-tile-label">Previous</span>
          <TileContent topic={previous} themeTitleById={themeTitleById} />
        </button>
        <div className="carousel-tile carousel-tile-current">
          <span className="carousel-tile-label">Current Topic</span>
          <TileContent topic={current} themeTitleById={themeTitleById} />
        </div>
        <button className="carousel-tile" onClick={() => onNavigate(topicIndex + 1)} disabled={single}>
          <span className="carousel-tile-label">Next</span>
          <TileContent topic={next} themeTitleById={themeTitleById} />
        </button>
      </div>

      <div className="carousel-editor carousel-editor-topic">
        {editing ? (
          <CardEditForm title={current.title} summary={current.summary} onSave={onSave} onCancel={onCancelEdit} />
        ) : (
          <>
            <div className="carousel-editor-header">
              <h3>{current.title}</h3>
              <button className="edit-btn" onClick={onStartEdit} title="Edit this topic">
                Edit
              </button>
            </div>
            <p>{current.summary}</p>
            <div className="card-tags">
              {current.excluded && <StatusIcon icon="excluded" label="Excluded" />}
              {current.theme_id !== null && themeTitleById[current.theme_id] && (
                <StatusIcon icon="theme" label={`Part of theme: ${themeTitleById[current.theme_id]}`}>
                  {themeTitleById[current.theme_id]}
                </StatusIcon>
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}

function TileContent({ topic, themeTitleById }: { topic: Topic; themeTitleById: Record<number, string> }) {
  if (!topic) return null
  const actClass = topic.act ? ` card-act-${topic.act}` : ''
  return (
    <span className={`carousel-tile-content${actClass}`}>
      <span className="carousel-tile-title">{topic.title}</span>
      <span className="carousel-tile-icons">
        {topic.excluded && <StatusIcon icon="excluded" label="Excluded" />}
        {topic.theme_id !== null && themeTitleById[topic.theme_id] && (
          <StatusIcon icon="theme" label={`Part of theme: ${themeTitleById[topic.theme_id]}`} />
        )}
      </span>
    </span>
  )
}

interface ThemeViewProps {
  themes: Theme[]
  themeIndex: number
  onNavigate: (index: number) => void
  editing: boolean
  onStartEdit: () => void
  onCancelEdit: () => void
  onSave: (data: { title: string; summary: string }) => void
  topics: Topic[]
  onTopicIconClick: (topicId: number) => void
}

function ThemeView({
  themes,
  themeIndex,
  onNavigate,
  editing,
  onStartEdit,
  onCancelEdit,
  onSave,
  topics,
  onTopicIconClick,
}: ThemeViewProps) {
  if (themes.length === 0) {
    return <p className="hbar-hint">No themes yet. Themes appear here once topics are grouped into them.</p>
  }

  const current = themes[themeIndex]
  const previous = themes[wrap(themeIndex - 1, themes.length)]
  const next = themes[wrap(themeIndex + 1, themes.length)]
  const single = themes.length === 1
  const themeTopics = topics.filter((t) => t.theme_id === current.id)

  return (
    <>
      <div className="carousel-nav carousel-nav-theme">
        <button className="carousel-tile carousel-tile-theme" onClick={() => onNavigate(themeIndex - 1)} disabled={single}>
          <span className="carousel-tile-label">Previous</span>
          <span className="carousel-tile-title">{previous.title}</span>
        </button>
        <div className="carousel-tile carousel-tile-theme carousel-tile-current">
          <span className="carousel-tile-label">Current Theme</span>
          <span className="carousel-tile-title">{current.title}</span>
        </div>
        <button className="carousel-tile carousel-tile-theme" onClick={() => onNavigate(themeIndex + 1)} disabled={single}>
          <span className="carousel-tile-label">Next</span>
          <span className="carousel-tile-title">{next.title}</span>
        </button>
      </div>

      <div className="carousel-theme-body">
        <div className="carousel-editor carousel-editor-theme">
          {editing ? (
            <CardEditForm title={current.title} summary={current.summary} onSave={onSave} onCancel={onCancelEdit} />
          ) : (
            <>
              <div className="carousel-editor-header">
                <h3>{current.title}</h3>
                <button className="edit-btn" onClick={onStartEdit} title="Edit this theme">
                  Edit
                </button>
              </div>
              <p>{current.summary}</p>
              {current.excluded && <StatusIcon icon="excluded" label="Excluded" />}
            </>
          )}
        </div>

        <div className="carousel-topic-icons">
          {themeTopics.length === 0 && <p className="hbar-hint">No topics in this theme yet.</p>}
          {themeTopics.map((topic) => {
            const actClass = topic.act ? ` card-act-${topic.act}` : ''
            return (
              <button
                key={topic.id}
                className={`carousel-topic-icon${actClass}`}
                onClick={() => onTopicIconClick(topic.id)}
                title={topic.title}
              >
                {topic.excluded && <StatusIcon icon="excluded" label="Excluded" />}
                <span className="carousel-topic-icon-title">{topic.title}</span>
              </button>
            )
          })}
        </div>
      </div>
    </>
  )
}

export default PlotCarousel
