import { useEffect, useState } from 'react'
import { buildActBuckets } from './actBuckets'
import EncodingRules, { type EncodingRule } from './EncodingRules'
import HbarVisual from './HbarVisual'
import IconButton from './IconButton'
import IngestForm from './IngestForm'
import PlotCarousel from './PlotCarousel'
import Sidekick from './Sidekick'
import SourcePreview from './SourcePreview'
import SubplotBars from './SubplotBars'
import { ToastProvider, useToast } from './ToastContext'
import TopicChecklist from './TopicChecklist'
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
  const [encodingRules, setEncodingRules] = useState<EncodingRule[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState<Record<number, string>>({})
  const [classifying, setClassifying] = useState<Record<number, string>>({})
  const [loadedDocument, setLoadedDocument] = useState<Document | null>(null)
  const [documentsCollapsed, setDocumentsCollapsed] = useState(false)
  const [currentTopicId, setCurrentTopicId] = useState<number | null>(null)
  const [currentThemeId, setCurrentThemeId] = useState<number | null>(null)
  const [previewTopicId, setPreviewTopicId] = useState<number | null>(null)
  const [previewMode, setPreviewMode] = useState<'theme' | 'topic'>('theme')
  const [subplotRefreshToken, setSubplotRefreshToken] = useState(0)
  const [subplotSelection, setSubplotSelection] = useState<{
    subplotId: number
    subplotTitle: string
    selectedTopicIds: Set<number>
  } | null>(null)
  const [addTarget, setAddTarget] = useState<{ type: 'subplot'; subplotId: number } | { type: 'new' } | null>(null)
  const [addTargetTitle, setAddTargetTitle] = useState<string | null>(null)
  const [deleteTargetIds, setDeleteTargetIds] = useState<Set<number>>(new Set())
  const [filteredSelection, setFilteredSelection] = useState<{
    topicIds: number[]
    selectedTopicIds: Set<number>
  } | null>(null)
  const { showError } = useToast()

  function handlePreviewTopic(topicId: number | null, mode: 'theme' | 'topic') {
    setPreviewTopicId(topicId)
    setPreviewMode(mode)
  }

  useEffect(() => {
    Promise.all([
      fetch('/documents').then((res) => res.json()),
      fetch('/themes').then((res) => res.json()),
      fetch('/topics').then((res) => res.json()),
      fetch('/encoding-rules').then((res) => res.json()),
    ])
      .then(([documentsData, themesData, topicsData, encodingRulesData]) => {
        setDocuments(documentsData)
        setThemes(themesData.map(normalizeExcluded))
        setTopics(topicsData.map(normalizeExcluded))
        setEncodingRules(encodingRulesData)
      })
      .catch(() => setError('Could not reach the backend at http://localhost:8000'))
      .finally(() => setLoading(false))
  }, [])

  function refetchDocuments() {
    fetch('/documents')
      .then((res) => res.json())
      .then(setDocuments)
  }

  function refetchTopicsAndThemes() {
    Promise.all([fetch('/themes').then((res) => res.json()), fetch('/topics').then((res) => res.json())]).then(
      ([themesData, topicsData]) => {
        setThemes(themesData.map(normalizeExcluded))
        setTopics(topicsData.map(normalizeExcluded))
      }
    )
  }

  function refetchEncodingRules() {
    fetch('/encoding-rules')
      .then((res) => res.json())
      .then(setEncodingRules)
  }

  function refetchAfterSidekickAction() {
    refetchTopicsAndThemes()
    refetchEncodingRules()
    setSubplotRefreshToken((n) => n + 1)
  }

  async function handleSubplotCreated(subplotId: number) {
    try {
      const response = await fetch(`/subplots/${subplotId}`)
      if (!response.ok) throw new Error()
      const subplot = await response.json()
      setSubplotSelection({ subplotId, subplotTitle: subplot.title, selectedTopicIds: new Set() })
    } catch {
      showError('Created the subplot, but could not load it for topic selection.')
    }
  }

  function toggleTopicSelection(topicId: number) {
    setSubplotSelection((prev) => {
      if (!prev) return prev
      const next = new Set(prev.selectedTopicIds)
      if (next.has(topicId)) next.delete(topicId)
      else next.add(topicId)
      return { ...prev, selectedTopicIds: next }
    })
  }

  async function finishSubplotSelection(): Promise<{ count: number; title: string }> {
    if (!subplotSelection) return { count: 0, title: '' }
    const { subplotId, subplotTitle, selectedTopicIds } = subplotSelection
    const topicIds = [...selectedTopicIds]
    await Promise.all(
      topicIds.map((topicId) =>
        fetch(`/subplots/${subplotId}/topics`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_id: topicId }),
        })
      )
    )
    setSubplotSelection(null)
    setSubplotRefreshToken((n) => n + 1)
    return { count: topicIds.length, title: subplotTitle }
  }

  function cancelSubplotSelection() {
    setSubplotSelection(null)
  }

  async function toggleAddTargetSubplot(subplotId: number) {
    if (addTarget?.type === 'subplot' && addTarget.subplotId === subplotId) {
      setAddTarget(null)
      setAddTargetTitle(null)
      setFilteredSelection(null)
      return
    }
    setAddTarget({ type: 'subplot', subplotId })
    setFilteredSelection(null)
    try {
      const response = await fetch(`/subplots/${subplotId}`)
      if (!response.ok) throw new Error()
      const subplot = await response.json()
      setAddTargetTitle(subplot.title)
    } catch {
      setAddTargetTitle(null)
    }
  }

  function toggleAddTargetNew() {
    if (addTarget?.type === 'new') {
      setAddTarget(null)
      setAddTargetTitle(null)
      setFilteredSelection(null)
      return
    }
    setAddTarget({ type: 'new' })
    setAddTargetTitle(null)
    setFilteredSelection(null)
  }

  function cancelAdd() {
    setAddTarget(null)
    setAddTargetTitle(null)
    setFilteredSelection(null)
  }

  function toggleDeleteTarget(subplotId: number) {
    setDeleteTargetIds((prev) => {
      const next = new Set(prev)
      if (next.has(subplotId)) next.delete(subplotId)
      else next.add(subplotId)
      return next
    })
  }

  function handleFilteredTopics(topicIds: number[]) {
    setFilteredSelection({ topicIds, selectedTopicIds: new Set() })
  }

  function toggleFilteredTopicSelection(topicId: number) {
    setFilteredSelection((prev) => {
      if (!prev) return prev
      const next = new Set(prev.selectedTopicIds)
      if (next.has(topicId)) next.delete(topicId)
      else next.add(topicId)
      return { ...prev, selectedTopicIds: next }
    })
  }

  async function finishAddFlow(): Promise<{ count: number; title: string }> {
    if (!addTarget || !filteredSelection) return { count: 0, title: '' }
    const topicIds = [...filteredSelection.selectedTopicIds]
    let subplotId: number
    let title: string

    if (addTarget.type === 'new') {
      const name = window.prompt('Name this new subplot:')
      if (!name) return { count: 0, title: '' }
      try {
        const response = await fetch('/subplots', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: name, summary: '' }),
        })
        if (!response.ok) throw new Error()
        const subplot = await response.json()
        subplotId = subplot.id
        title = subplot.title
      } catch {
        showError('Could not create the new subplot. Please try again.')
        return { count: 0, title: '' }
      }
    } else {
      subplotId = addTarget.subplotId
      title = addTargetTitle ?? 'the subplot'
    }

    await Promise.all(
      topicIds.map((topicId) =>
        fetch(`/subplots/${subplotId}/topics`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_id: topicId }),
        })
      )
    )
    setAddTarget(null)
    setAddTargetTitle(null)
    setFilteredSelection(null)
    setSubplotRefreshToken((n) => n + 1)
    return { count: topicIds.length, title }
  }

  async function finishDeleteFlow(): Promise<{ count: number }> {
    const ids = [...deleteTargetIds]
    if (ids.length === 0) return { count: 0 }
    await Promise.all(ids.map((id) => fetch(`/subplots/${id}`, { method: 'DELETE' })))
    setDeleteTargetIds(new Set())
    setSubplotRefreshToken((n) => n + 1)
    return { count: ids.length }
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
    } catch {
      showError('Could not delete this document. Please try again.')
    }
  }

  function loadDocument(doc: Document) {
    setLoadedDocument(doc)
    setDocumentsCollapsed(true)
  }

  const loadedTopics = loadedDocument
    ? topics.filter((t) => t.document_filename === loadedDocument.filename && !t.excluded)
    : []
  const loadedThemeIds = new Set(loadedTopics.map((t) => t.theme_id).filter((id): id is number => id !== null))
  const loadedThemes = loadedDocument ? themes.filter((t) => loadedThemeIds.has(t.id)) : []
  const orderedLoadedTopics = [...loadedTopics].sort((a, b) => a.sequence_index - b.sequence_index)

  // Keep the current topic pointer valid as the loaded document changes.
  useEffect(() => {
    if (orderedLoadedTopics.length === 0) {
      if (currentTopicId !== null) setCurrentTopicId(null)
      return
    }
    if (!orderedLoadedTopics.some((t) => t.id === currentTopicId)) {
      setCurrentTopicId(orderedLoadedTopics[0].id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedDocument, orderedLoadedTopics.length])

  // Keep the current theme pointer valid as the loaded document changes.
  useEffect(() => {
    if (loadedThemes.length === 0) {
      if (currentThemeId !== null) setCurrentThemeId(null)
      return
    }
    if (!loadedThemes.some((t) => t.id === currentThemeId)) {
      setCurrentThemeId(loadedThemes[0].id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedDocument, loadedThemes.length])

  const { buckets, extraBucket } = buildActBuckets(loadedTopics)

  function jumpToAct(actKey: string) {
    const bucket = buckets.find((b) => b.key === actKey) ?? (extraBucket.key === actKey ? extraBucket : null)
    const firstTopic = bucket?.topics[0]
    if (firstTopic) setCurrentTopicId(firstTopic.id)
  }

  if (error) {
    return <p className="error">{error}</p>
  }

  if (loading) {
    return <p className="loading">Loading Genre Writer…</p>
  }

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
              <div className="main-plot-row">
                <HbarVisual buckets={buckets} extraBucket={extraBucket} onSegmentClick={jumpToAct} markerTopicId={currentTopicId} />
                <IconButton
                  icon="add"
                  label="Add topics to a new subplot"
                  active={addTarget?.type === 'new'}
                  onClick={toggleAddTargetNew}
                />
              </div>
              <SubplotBars
                documentId={loadedDocument?.id ?? null}
                refreshToken={subplotRefreshToken}
                currentTopicId={currentTopicId}
                onNavigateTopic={setCurrentTopicId}
                addTargetSubplotId={addTarget?.type === 'subplot' ? addTarget.subplotId : null}
                deleteTargetIds={deleteTargetIds}
                onClickAdd={toggleAddTargetSubplot}
                onToggleDelete={toggleDeleteTarget}
              />
            </section>

            {addTarget && (
              <section className="panel">
                <div className="selection-banner">
                  <span>
                    Adding topics to {addTarget.type === 'new' ? 'a new subplot' : `“${addTargetTitle ?? '…'}”`}.
                    {filteredSelection
                      ? ` ${filteredSelection.selectedTopicIds.size} of ${filteredSelection.topicIds.length} selected. Type “move them” in the sidekick when ready.`
                      : ' Ask the sidekick to filter topics, e.g. “unassigned topics” or “topics starting with Q”.'}
                  </span>
                  <button className="selection-cancel" onClick={cancelAdd}>
                    Cancel
                  </button>
                </div>
                {filteredSelection && (
                  <TopicChecklist
                    topics={loadedTopics.filter((t) => filteredSelection.topicIds.includes(t.id))}
                    selectedTopicIds={filteredSelection.selectedTopicIds}
                    onToggle={toggleFilteredTopicSelection}
                    onPreviewTopic={handlePreviewTopic}
                  />
                )}
              </section>
            )}

            <section className="panel">
              <PlotCarousel
                topics={loadedTopics}
                themes={loadedThemes}
                currentTopicId={currentTopicId}
                currentThemeId={currentThemeId}
                onNavigateTopic={setCurrentTopicId}
                onNavigateTheme={setCurrentThemeId}
                onUpdateTopic={updateTopic}
                onUpdateTheme={updateTheme}
                onPreviewTopic={handlePreviewTopic}
                selection={subplotSelection}
                onToggleTopicSelection={toggleTopicSelection}
                onCancelSelection={cancelSubplotSelection}
              />
            </section>

            <section className="panel">
              <h2>Preview</h2>
              <SourcePreview
                topic={loadedTopics.find((t) => t.id === previewTopicId) ?? null}
                mode={previewMode}
              />
            </section>
          </div>
        </div>

        <div className="col col-encoding">
          <div className="panel">
            <h2>Encoding Rules</h2>
            <EncodingRules rules={encodingRules} />
          </div>
          <div className="panelp">
            <h2>Sidekick</h2>
            <Sidekick
              topics={loadedTopics.filter((t) => !t.excluded)}
              currentTopicId={currentTopicId}
              currentThemeId={currentThemeId}
              onActionsPerformed={refetchAfterSidekickAction}
              onSubplotCreated={handleSubplotCreated}
              selection={subplotSelection}
              onFinishSelection={finishSubplotSelection}
              addTargetSubplotId={addTarget?.type === 'subplot' ? addTarget.subplotId : null}
              addTargetIsNew={addTarget?.type === 'new'}
              onFilteredTopics={handleFilteredTopics}
              filteredSelectionActive={filteredSelection !== null}
              onFinishAdd={finishAddFlow}
              deleteTargetCount={deleteTargetIds.size}
              onFinishDelete={finishDeleteFlow}
            />
          </div>
        </div>
      </div>
    </main>
  )
}

export default App
