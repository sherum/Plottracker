import { useEffect, useRef, useState } from 'react'
import Notecards, { type Selection } from './Notecards'
import PlotViewer from './PlotViewer'
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
}

function App() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [themes, setThemes] = useState<Theme[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [selectedTheme, setSelectedTheme] = useState<Selection>(null)
  const [error, setError] = useState<string | null>(null)
  const notecardsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    Promise.all([
      fetch('/documents').then((res) => res.json()),
      fetch('/themes').then((res) => res.json()),
      fetch('/topics').then((res) => res.json()),
    ])
      .then(([documentsData, themesData, topicsData]) => {
        setDocuments(documentsData)
        setThemes(themesData)
        setTopics(topicsData)
      })
      .catch(() => setError('Could not reach the backend at http://localhost:8000'))
  }, [])

  function navigateToTheme(themeId: number) {
    setSelectedTheme(themeId)
    notecardsRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  async function updateTopic(id: number, data: { title: string; summary: string }) {
    const response = await fetch(`/topics/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    const updated = await response.json()
    setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
  }

  async function updateTheme(id: number, data: { title: string; summary: string }) {
    const response = await fetch(`/themes/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    const updated = await response.json()
    setThemes((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
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
                {doc.filename} <span className="tag">{doc.role}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Plot Viewer</h2>
        <PlotViewer topics={topics} themes={themes} onThemeClick={navigateToTheme} onUpdateTopic={updateTopic} />
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
        />
      </section>
    </main>
  )
}

export default App
