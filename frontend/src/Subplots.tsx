import { useEffect, useState } from 'react'
import ActHbar, { type HbarBucket } from './ActHbar'
import CardEditForm from './CardEditForm'
import { onActivateKey } from './keyboardActivate'
import { useToast } from './ToastContext'
import TopicCardGrid, { type Topic } from './TopicCardGrid'
import './Notecards.css'

export interface Subplot {
  id: number
  theme_id: number | null
  theme_title: string | null
  title: string
  summary: string
  topic_count: number
}

interface Theme {
  id: number
  title: string
}

interface Props {
  subplots: Subplot[]
  allTopics: Topic[]
  themes: Theme[]
  onThemeClick: (themeId: number) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onSubplotsChanged: () => void
  onToggleExcludeTopic: (id: number, excluded: boolean) => void
}

const SUBPLOT_ACT_LABELS = ['Opening', 'Conflict', 'Climax']

// A subplot has no LLM-assigned act, so its own three-act shape is derived
// from the chronological order its member topics already carry.
function bucketSubplotIntoActs(topics: Topic[]): HbarBucket[] {
  const active = topics.filter((t) => !t.excluded)
  const base = Math.floor(active.length / 3)
  const remainder = active.length % 3
  const sizes = [base + (remainder > 0 ? 1 : 0), base + (remainder > 1 ? 1 : 0), base]

  let index = 0
  return SUBPLOT_ACT_LABELS.map((label, i) => {
    const slice = active.slice(index, index + sizes[i])
    index += sizes[i]
    return { key: `act-${i}`, label, topics: slice, activeTopics: slice }
  })
}

function Subplots({
  subplots,
  allTopics,
  themes,
  onThemeClick,
  onUpdateTopic,
  onSubplotsChanged,
  onToggleExcludeTopic,
}: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [subplotTopics, setSubplotTopics] = useState<Topic[]>([])
  const [addTopicId, setAddTopicId] = useState('')
  const [creating, setCreating] = useState(false)
  const themeTitleById = Object.fromEntries(themes.map((t) => [t.id, t.title]))
  const { showError } = useToast()

  useEffect(() => {
    if (selectedId === null) return
    fetch(`/subplots/${selectedId}/topics`)
      .then((res) => res.json())
      .then((data: Topic[]) => setSubplotTopics(data.map((t) => ({ ...t, excluded: Boolean(t.excluded) }))))
      .catch(() => showError('Could not load this subplot. Please try again.'))
  }, [selectedId, subplots, showError])

  async function createSubplot(data: { title: string; summary: string }) {
    try {
      const response = await fetch('/subplots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error()
      setCreating(false)
      onSubplotsChanged()
    } catch {
      showError('Could not create the subplot. Please try again.')
    }
  }

  if (selectedId !== null) {
    const subplot = subplots.find((s) => s.id === selectedId)
    const availableTopics = allTopics.filter((t) => !subplotTopics.some((st) => st.id === t.id))

    async function addTopic() {
      if (!addTopicId) return
      try {
        const response = await fetch(`/subplots/${selectedId}/topics`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_id: Number(addTopicId) }),
        })
        if (!response.ok) throw new Error()
        setAddTopicId('')
        onSubplotsChanged()
      } catch {
        showError('Could not add this topic to the subplot. Please try again.')
      }
    }

    async function removeTopic(topicId: number) {
      if (!window.confirm('Remove this topic from the subplot?')) return
      try {
        const response = await fetch(`/subplots/${selectedId}/topics/${topicId}`, { method: 'DELETE' })
        if (!response.ok) throw new Error()
        onSubplotsChanged()
      } catch {
        showError('Could not remove this topic from the subplot. Please try again.')
      }
    }

    return (
      <div className="notecards">
        <button className="back" onClick={() => setSelectedId(null)} title="Back to the subplot list">
          &larr; Subplots
        </button>
        <h3>{subplot?.title}</h3>
        <p className="theme-summary">{subplot?.summary}</p>

        <h4>Structure</h4>
        <ActHbar
          buckets={bucketSubplotIntoActs(subplotTopics)}
          themeTitleById={themeTitleById}
          onThemeClick={onThemeClick}
          onUpdateTopic={onUpdateTopic}
          onToggleExcludeTopic={onToggleExcludeTopic}
          size="small"
        />

        <h4>All Topics</h4>
        <div className="subplot-add">
          <select value={addTopicId} onChange={(e) => setAddTopicId(e.target.value)}>
            <option value="">Add a topic&hellip;</option>
            {availableTopics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.document_filename}: {t.title}
              </option>
            ))}
          </select>
          <button onClick={addTopic} disabled={!addTopicId} title="Add the selected topic to this subplot">
            Add
          </button>
        </div>

        <TopicCardGrid
          topics={subplotTopics}
          themeTitleById={themeTitleById}
          onThemeClick={onThemeClick}
          onUpdateTopic={onUpdateTopic}
          onRemoveTopic={removeTopic}
          removeLabel="Remove from subplot"
          onToggleExcludeTopic={onToggleExcludeTopic}
        />
      </div>
    )
  }

  return (
    <div className="notecards">
      {creating ? (
        <CardEditForm title="" summary="" onSave={createSubplot} onCancel={() => setCreating(false)} />
      ) : (
        <button className="back" onClick={() => setCreating(true)} title="Create a new subplot">
          + New Subplot
        </button>
      )}

      <div className="card-grid">
        {subplots.map((subplot) => (
          <div
            className="card clickable"
            key={subplot.id}
            onClick={() => setSelectedId(subplot.id)}
            role="button"
            tabIndex={0}
            aria-label={`Open subplot ${subplot.title}`}
            onKeyDown={onActivateKey(() => setSelectedId(subplot.id))}
          >
            <h4>{subplot.title}</h4>
            <p>{subplot.summary}</p>
            <div className="card-tags">
              <span className="tag">{subplot.topic_count} topics</span>
              {subplot.theme_title && <span className="tag">from {subplot.theme_title}</span>}
            </div>
          </div>
        ))}
      </div>
      {subplots.length === 0 && <p className="hbar-hint">No subplots yet. Promote a theme or create one above.</p>}
    </div>
  )
}

export default Subplots
