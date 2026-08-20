import { useEffect, useRef, useState } from 'react'
import Notecards, { type Selection } from './Notecards'
import PlotViewer from './PlotViewer'
import Subplots, { type Subplot } from './Subplots'
import type { Topic } from './TopicCardGrid'
import './App.css'

interface Document {
  id: number
  role: string
  filename: string
  source_type: string
  ingested_at: string
}

interface Theme {
  id: number
  title: string
  summary: string
  excluded: boolean
}

// SQLite stores booleans as 0/1 and the API returns them as raw JSON numbers.
function normalizeExcluded<T extends { excluded: unknown }>(row: T): T & { excluded: boolean } {
  return { ...row, excluded: Boolean(row.excluded) }
}

function App() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [themes, setThemes] = useState<Theme[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [subplots, setSubplots] = useState<Subplot[]>([])
  const [selectedTheme, setSelectedTheme] = useState<Selection>(null)
  const [error, setError] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState<Record<number, string>>({})
  const notecardsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    Promise.all([
      fetch('/documents').then((res) => res.json()),
      fetch('/themes').then((res) => res.json()),
      fetch('/topics').then((res) => res.json()),
      fetch('/subplots').then((res) => res.json()),
    ])
      .then(([documentsData, themesData, topicsData, subplotsData]) => {
        setDocuments(documentsData)
        setThemes(themesData.map(normalizeExcluded))
        setTopics(topicsData.map(normalizeExcluded))
        setSubplots(subplotsData)
      })
      .catch(() => setError('Could not reach the backend at http://localhost:8000'))
  }, [])

  function navigateToTheme(themeId: number) {
    setSelectedTheme(themeId)
    notecardsRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  function refetchSubplots() {
    fetch('/subplots')
      .then((res) => res.json())
      .then(setSubplots)
  }

  function refetchTopicsAndThemes() {
    Promise.all([fetch('/themes').then((res) => res.json()), fetch('/topics').then((res) => res.json())]).then(
      ([themesData, topicsData]) => {
        setThemes(themesData.map(normalizeExcluded))
        setTopics(topicsData.map(normalizeExcluded))
      }
    )
  }

  async function updateTopic(id: number, data: { title: string; summary: string }) {
    const response = await fetch(`/topics/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    const updated = normalizeExcluded(await response.json())
    setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
  }

  async function updateTheme(id: number, data: { title: string; summary: string }) {
    const response = await fetch(`/themes/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    const updated = normalizeExcluded(await response.json())
    setThemes((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
  }

  async function promoteTheme(themeId: number) {
    await fetch(`/themes/${themeId}/promote`, { method: 'POST' })
    refetchSubplots()
  }

  async function toggleExcludeTopic(id: number, excluded: boolean) {
    const response = await fetch(`/topics/${id}/${excluded ? 'exclude' : 'include'}`, { method: 'POST' })
    const updated = normalizeExcluded(await response.json())
    setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
  }

  async function toggleExcludeTheme(id: number, excluded: boolean) {
    const response = await fetch(`/themes/${id}/${excluded ? 'exclude' : 'include'}`, { method: 'POST' })
    const updated = normalizeExcluded(await response.json())
    setThemes((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
  }

  async function reanalyzeDocument(id: number) {
    setAnalyzing((prev) => ({ ...prev, [id]: 'Analyzing…' }))
    const response = await fetch(`/documents/${id}/analyze`, { method: 'POST' })
    const result = await response.json()
    setAnalyzing((prev) => ({
      ...prev,
      [id]: `Done: ${result.topics_created} topics, ${result.themes_created} themes created`,
    }))
    refetchTopicsAndThemes()
  }

  if (error) {
    return <p className="error">{error}</p>
  }

  return (
    <main>
      <h1>Genre Writer</h1>

      <section>
        <h2>Documents</h2>
        {documents.length === 0 ? (
          <p>No documents ingested yet.</p>
        ) : (
          <ul>
            {documents.map((doc) => (
              <li key={doc.id}>
                {doc.filename} <span className="tag">{doc.role}</span>{' '}
                <button className="edit-btn" onClick={() => reanalyzeDocument(doc.id)}>
                  Reanalyze
                </button>
                {analyzing[doc.id] && <span className="tag"> {analyzing[doc.id]}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Plot Viewer</h2>
        <PlotViewer
          topics={topics}
          themes={themes}
          onThemeClick={navigateToTheme}
          onUpdateTopic={updateTopic}
          onToggleExcludeTopic={toggleExcludeTopic}
        />
      </section>

      <section ref={notecardsRef}>
        <h2>Notecards</h2>
        <Notecards
          themes={themes}
          topics={topics}
          selected={selectedTheme}
          onSelect={setSelectedTheme}
          onUpdateTopic={updateTopic}
          onUpdateTheme={updateTheme}
          onPromoteTheme={promoteTheme}
          onToggleExcludeTopic={toggleExcludeTopic}
          onToggleExcludeTheme={toggleExcludeTheme}
        />
      </section>

      <section>
        <h2>Subplots</h2>
        <Subplots
          subplots={subplots}
          allTopics={topics}
          themes={themes}
          onThemeClick={navigateToTheme}
          onUpdateTopic={updateTopic}
          onSubplotsChanged={refetchSubplots}
          onToggleExcludeTopic={toggleExcludeTopic}
        />
      </section>
    </main>
  )
}

export default App
