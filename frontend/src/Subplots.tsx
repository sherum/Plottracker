import { useEffect, useState } from 'react'
import CardEditForm from './CardEditForm'
import Sidekick from './Sidekick'
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

interface Props {
  subplots: Subplot[]
  allTopics: Topic[]
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
  onSubplotsChanged: () => void
}

function Subplots({ subplots, allTopics, onUpdateTopic, onSubplotsChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [subplotTopics, setSubplotTopics] = useState<Topic[]>([])
  const [addTopicId, setAddTopicId] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    if (selectedId === null) return
    fetch(`/subplots/${selectedId}/topics`)
      .then((res) => res.json())
      .then(setSubplotTopics)
  }, [selectedId, subplots])

  async function createSubplot(data: { title: string; summary: string }) {
    await fetch('/subplots', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    setCreating(false)
    onSubplotsChanged()
  }

  if (selectedId !== null) {
    const subplot = subplots.find((s) => s.id === selectedId)
    const availableTopics = allTopics.filter((t) => !subplotTopics.some((st) => st.id === t.id))

    async function addTopic() {
      if (!addTopicId) return
      await fetch(`/subplots/${selectedId}/topics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic_id: Number(addTopicId) }),
      })
      setAddTopicId('')
      onSubplotsChanged()
    }

    async function removeTopic(topicId: number) {
      await fetch(`/subplots/${selectedId}/topics/${topicId}`, { method: 'DELETE' })
      onSubplotsChanged()
    }

    return (
      <div className="notecards">
        <button className="back" onClick={() => setSelectedId(null)}>
          &larr; Subplots
        </button>
        <h3>{subplot?.title}</h3>
        <p className="theme-summary">{subplot?.summary}</p>

        <div className="subplot-add">
          <select value={addTopicId} onChange={(e) => setAddTopicId(e.target.value)}>
            <option value="">Add a topic&hellip;</option>
            {availableTopics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.document_filename}: {t.title}
              </option>
            ))}
          </select>
          <button onClick={addTopic} disabled={!addTopicId}>
            Add
          </button>
        </div>

        <TopicCardGrid topics={subplotTopics} onUpdateTopic={onUpdateTopic} onRemoveTopic={removeTopic} />
        <Sidekick topics={subplotTopics} />
      </div>
    )
  }

  return (
    <div className="notecards">
      {creating ? (
        <CardEditForm title="" summary="" onSave={createSubplot} onCancel={() => setCreating(false)} />
      ) : (
        <button className="back" onClick={() => setCreating(true)}>
          + New Subplot
        </button>
      )}

      <div className="card-grid">
        {subplots.map((subplot) => (
          <div className="card clickable" key={subplot.id} onClick={() => setSelectedId(subplot.id)}>
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
