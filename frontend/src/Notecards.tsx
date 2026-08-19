import { useEffect, useState } from 'react'
import './Notecards.css'

interface Topic {
  id: number
  theme_id: number | null
  title: string
  summary: string
  document_filename: string
  sequence_index: number
}

interface Theme {
  id: number
  title: string
  summary: string
}

const UNASSIGNED = 'unassigned'

function Notecards() {
  const [themes, setThemes] = useState<Theme[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [selected, setSelected] = useState<number | typeof UNASSIGNED | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/themes').then((res) => res.json()),
      fetch('/topics').then((res) => res.json()),
    ]).then(([themesData, topicsData]) => {
      setThemes(themesData)
      setTopics(topicsData)
    })
  }, [])

  const unassignedTopics = topics.filter((t) => t.theme_id === null)

  if (selected !== null) {
    const isUnassigned = selected === UNASSIGNED
    const theme = isUnassigned ? null : themes.find((t) => t.id === selected)
    const shownTopics = isUnassigned ? unassignedTopics : topics.filter((t) => t.theme_id === selected)

    return (
      <div className="notecards">
        <button className="back" onClick={() => setSelected(null)}>
          &larr; Themes
        </button>
        <h3>{isUnassigned ? 'Unassigned Topics' : theme?.title}</h3>
        {!isUnassigned && <p className="theme-summary">{theme?.summary}</p>}
        <div className="card-grid">
          {shownTopics.map((topic) => (
            <div className="card" key={topic.id}>
              <h4>{topic.title}</h4>
              <p>{topic.summary}</p>
              <span className="tag">{topic.document_filename}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="notecards">
      <div className="card-grid">
        {themes.map((theme) => (
          <div className="card clickable" key={theme.id} onClick={() => setSelected(theme.id)}>
            <h4>{theme.title}</h4>
            <p>{theme.summary}</p>
            <span className="tag">{topics.filter((t) => t.theme_id === theme.id).length} topics</span>
          </div>
        ))}
        {unassignedTopics.length > 0 && (
          <div className="card clickable" onClick={() => setSelected(UNASSIGNED)}>
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
