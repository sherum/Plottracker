import { useEffect, useRef, useState } from 'react'
import EncodingRules, { type EncodingRule } from './EncodingRules'
import IconButton from './IconButton'
import IngestForm from './IngestForm'
import Notecards, { type Selection } from './Notecards'
import PlotViewer from './PlotViewer'
import Subplots, { type Subplot } from './Subplots'
import { ToastProvider, useToast } from './ToastContext'
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
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  )
}

function AppContent() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [themes, setThemes] = useState<Theme[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [subplots, setSubplots] = useState<Subplot[]>([])
  const [encodingRules, setEncodingRules] = useState<EncodingRule[]>([])
  const [selectedTheme, setSelectedTheme] = useState<Selection>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState<Record<number, string>>({})
  const [classifying, setClassifying] = useState<Record<number, string>>({})
  const [loadedDocument, setLoadedDocument] = useState<Document | null>(null)
  const [documentsCollapsed, setDocumentsCollapsed] = useState(false)
  const notecardsRef = useRef<HTMLDivElement>(null)
  const { showError } = useToast()

  useEffect(() => {
    Promise.all([
      fetch('/documents').then((res) => res.json()),
      fetch('/themes').then((res) => res.json()),
      fetch('/topics').then((res) => res.json()),
      fetch('/subplots').then((res) => res.json()),
      fetch('/encoding-rules').then((res) => res.json()),
    ])
      .then(([documentsData, themesData, topicsData, subplotsData, encodingRulesData]) => {
        setDocuments(documentsData)
        setThemes(themesData.map(normalizeExcluded))
        setTopics(topicsData.map(normalizeExcluded))
        setSubplots(subplotsData)
        setEncodingRules(encodingRulesData)
      })
      .catch(() => setError('Could not reach the backend at http://localhost:8000'))
      .finally(() => setLoading(false))
  }, [])

  function navigateToTheme(themeId: number) {
    setSelectedTheme(themeId)
    notecardsRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  function refetchDocuments() {
    fetch('/documents')
      .then((res) => res.json())
      .then(setDocuments)
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
    try {
      const response = await fetch(`/topics/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error()
      const updated = normalizeExcluded(await response.json())
      setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
    } catch {
      showError('Could not save the topic. Please try again.')
    }
  }

  async function updateTheme(id: number, data: { title: string; summary: string }) {
    try {
      const response = await fetch(`/themes/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error()
      const updated = normalizeExcluded(await response.json())
      setThemes((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
    } catch {
      showError('Could not save the theme. Please try again.')
    }
  }

  async function promoteTheme(themeId: number) {
    try {
      const response = await fetch(`/themes/${themeId}/promote`, { method: 'POST' })
      if (!response.ok) throw new Error()
      refetchSubplots()
    } catch {
      showError('Could not promote the theme to a subplot. Please try again.')
    }
  }

  async function toggleExcludeTopic(id: number, excluded: boolean) {
    try {
      const response = await fetch(`/topics/${id}/${excluded ? 'exclude' : 'include'}`, { method: 'POST' })
      if (!response.ok) throw new Error()
      const updated = normalizeExcluded(await response.json())
      setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
    } catch {
      showError(`Could not ${excluded ? 'exclude' : 'include'} the topic. Please try again.`)
    }
  }

  async function toggleExcludeTheme(id: number, excluded: boolean) {
    try {
      const response = await fetch(`/themes/${id}/${excluded ? 'exclude' : 'include'}`, { method: 'POST' })
      if (!response.ok) throw new Error()
      const updated = normalizeExcluded(await response.json())
      setThemes((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
    } catch {
      showError(`Could not ${excluded ? 'exclude' : 'include'} the theme. Please try again.`)
    }
  }

  async function unassignTopicTheme(id: number) {
    try {
      const response = await fetch(`/topics/${id}/unassign-theme`, { method: 'POST' })
      if (!response.ok) throw new Error()
      const updated = normalizeExcluded(await response.json())
      setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
    } catch {
      showError('Could not remove the topic from its theme. Please try again.')
    }
  }

  async function reanalyzeDocument(id: number) {
    setAnalyzing((prev) => ({ ...prev, [id]: 'Analyzing…' }))
    try {
      const response = await fetch(`/documents/${id}/analyze`, { method: 'POST' })
      if (!response.ok) throw new Error()
      const result = await response.json()
      setAnalyzing((prev) => ({
        ...prev,
        [id]: `Done: ${result.topics_created} topics, ${result.themes_created} themes created`,
      }))
      refetchTopicsAndThemes()
    } catch {
      setAnalyzing((prev) => ({ ...prev, [id]: '' }))
      showError('Could not analyze this document. Please try again.')
    }
  }

  function refetchEncodingRules() {
    fetch('/encoding-rules')
      .then((res) => res.json())
      .then(setEncodingRules)
  }

  async function classifyDocument(id: number) {
    setClassifying((prev) => ({ ...prev, [id]: 'Classifying…' }))
    try {
      const response = await fetch(`/documents/${id}/classify-encoding`, { method: 'POST' })
      if (!response.ok) throw new Error()
      const result = await response.json()
      setClassifying((prev) => ({ ...prev, [id]: `Tagged ${result.tagged} segments` }))
    } catch {
      setClassifying((prev) => ({ ...prev, [id]: '' }))
      showError('Could not classify encoding for this document. Please try again.')
    }
  }

  async function deleteDocument(id: number, filename: string) {
    if (!window.confirm(`Delete "${filename}" and all its segments, topics, and subplot memberships?`)) return
    try {
      const response = await fetch(`/documents/${id}`, { method: 'DELETE' })
      if (!response.ok) throw new Error()
      if (loadedDocument?.id === id) setLoadedDocument(null)
      refetchDocuments()
      refetchTopicsAndThemes()
      refetchSubplots()
    } catch {
      showError('Could not delete this document. Please try again.')
    }
  }

  function loadDocument(doc: Document) {
    setLoadedDocument(doc)
    setDocumentsCollapsed(true)
  }

  if (error) {
    return <p className="error">{error}</p>
  }

  if (loading) {
    return <p className="loading">Loading Genre Writer…</p>
  }

  const loadedTopics = loadedDocument ? topics.filter((t) => t.document_filename === loadedDocument.filename) : []
  const loadedThemeIds = new Set(loadedTopics.map((t) => t.theme_id).filter((id): id is number => id !== null))
  const loadedThemes = loadedDocument ? themes.filter((t) => loadedThemeIds.has(t.id)) : []

  return (
    <main>
      <h1>{loadedDocument ? loadedDocument.filename : 'Genre Writer'}</h1>

      <div className="layout">
        <div className="col col-documents panel">
          <h2>Documents</h2>
          <IngestForm onIngested={refetchDocuments} />
          <details
            className="documents-accordion"
            open={!documentsCollapsed}
            onToggle={(e) => setDocumentsCollapsed(!(e.target as HTMLDetailsElement).open)}
          >
            <summary title="Show or hide the document list">Document list ({documents.length})</summary>
            {documents.length === 0 ? (
              <p>No documents ingested yet.</p>
            ) : (
              <ul className="documents-list">
                {documents.map((doc) => (
                  <li key={doc.id} className={loadedDocument?.id === doc.id ? 'loaded' : undefined}>
                    <span className="doc-filename">{doc.filename}</span> <span className="tag">{doc.role}</span>
                    <div className="doc-actions">
                      <IconButton icon="load" label="Load" onClick={() => loadDocument(doc)} />
                      <IconButton icon="reanalyze" label="Reanalyze" onClick={() => reanalyzeDocument(doc.id)} />
                      <IconButton icon="classify" label="Classify Encoding" onClick={() => classifyDocument(doc.id)} />
                      <IconButton icon="delete" label="Delete" onClick={() => deleteDocument(doc.id, doc.filename)} />
                    </div>
                    {analyzing[doc.id] && <span className="tag"> {analyzing[doc.id]}</span>}
                    {classifying[doc.id] && <span className="tag"> {classifying[doc.id]}</span>}
                  </li>
                ))}
              </ul>
            )}
          </details>
        </div>

        <div className="col col-center">
          <div className="col-center-inner">
            <section className="panel">
              <h2>Plot Viewer</h2>
              <PlotViewer
                topics={loadedTopics}
                themes={loadedThemes}
                onThemeClick={navigateToTheme}
                onUpdateTopic={updateTopic}
                onToggleExcludeTopic={toggleExcludeTopic}
              />
            </section>

            <section className="panel" ref={notecardsRef}>
              <h2>Notecards</h2>
              <Notecards
                themes={loadedThemes}
                topics={loadedTopics}
                selected={selectedTheme}
                onSelect={setSelectedTheme}
                onUpdateTopic={updateTopic}
                onUpdateTheme={updateTheme}
                onPromoteTheme={promoteTheme}
                onToggleExcludeTopic={toggleExcludeTopic}
                onToggleExcludeTheme={toggleExcludeTheme}
                onUnassignTheme={unassignTopicTheme}
              />
            </section>

            <section className="panel">
              <h2>Subplots</h2>
              <p className="hbar-hint">Subplots span all documents, not just the loaded one.</p>
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
          </div>
        </div>

        <div className="col col-encoding panel">
          <h2>Encoding Rules</h2>
          <EncodingRules rules={encodingRules} onRulesChanged={refetchEncodingRules} />
        </div>
      </div>
    </main>
  )
}

export default App
