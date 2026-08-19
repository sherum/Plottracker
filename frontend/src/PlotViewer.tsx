import { useState } from 'react'
import TopicCardGrid, { type Topic } from './TopicCardGrid'
import './Notecards.css'

const ACTS = [
  { key: 'opening', label: 'Opening' },
  { key: 'conflict', label: 'Conflict' },
  { key: 'climax', label: 'Climax' },
] as const

type ActKey = (typeof ACTS)[number]['key']

interface Theme {
  id: number
  title: string
}

interface Props {
  topics: Topic[]
  themes: Theme[]
  onThemeClick: (themeId: number) => void
}

function PlotViewer({ topics, themes, onThemeClick }: Props) {
  const [selectedAct, setSelectedAct] = useState<ActKey | 'unassigned' | null>(null)
  const themeTitleById = Object.fromEntries(themes.map((t) => [t.id, t.title]))
  const unassignedTopics = topics.filter((t) => t.act === null)

  if (selectedAct !== null) {
    const isUnassigned = selectedAct === 'unassigned'
    const shownTopics = isUnassigned ? unassignedTopics : topics.filter((t) => t.act === selectedAct)
    const label = isUnassigned ? 'Unassigned' : ACTS.find((a) => a.key === selectedAct)!.label

    return (
      <div className="notecards">
        <button className="back" onClick={() => setSelectedAct(null)}>
          &larr; Acts
        </button>
        <h3>{label}</h3>
        <TopicCardGrid topics={shownTopics} themeTitleById={themeTitleById} onThemeClick={onThemeClick} />
      </div>
    )
  }

  return (
    <div className="notecards">
      <div className="card-grid">
        {ACTS.map((act) => (
          <div className="card clickable" key={act.key} onClick={() => setSelectedAct(act.key)}>
            <h4>{act.label}</h4>
            <span className="tag">{topics.filter((t) => t.act === act.key).length} topics</span>
          </div>
        ))}
        {unassignedTopics.length > 0 && (
          <div className="card clickable" onClick={() => setSelectedAct('unassigned')}>
            <h4>Unassigned</h4>
            <span className="tag">{unassignedTopics.length} topics</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default PlotViewer
