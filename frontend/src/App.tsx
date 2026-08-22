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
  is_main: boolean
}

// SQLite stores booleans as 0/1 and the API returns them as raw JSON numbers.
function normalizeExcluded<T extends { excluded: unknown }>(row: T): T & { excluded: boolean } {
  return { ...row, excluded: Boolean(row.excluded) }
}

function normalizeTheme<T extends { excluded: unknown; is_main: unknown }>(
  row: T
): T & { excluded: boolean; is_main: boolean } {
  return { ...row, excluded: Boolean(row.excluded), is_main: Boolean(row.is_main) }
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
  const [storyDocuments, setStoryDocuments] = useState<Document[]>([])
  const [themes, setThemes] = useState<Theme[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [encodingRules, setEncodingRules] = useState<EncodingRule[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState<Record<number, string>>({})
  const [classifying, setClassifying] = useState<Record<number, string>>({})
  const [loadedDocument, setLoadedDocument] = useState<Document | null>(null)
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
  const [renamingDocId, setRenamingDocId] = useState<number | null>(null)
  const [renameValue, setRenameValue] = useState('')
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
      fetch('/story/documents').then((res) => res.json()),
    ])
      .then(([documentsData, themesData, topicsData, encodingRulesData, storyDocumentsData]) => {
        setDocuments(documentsData)
        setThemes(themesData.map(normalizeTheme))
        setTopics(topicsData.map(normalizeExcluded))
        setEncodingRules(encodingRulesData)
        setStoryDocuments(storyDocumentsData)
      })
      .catch(() => setError('Could not reach the backend at http://localhost:8000'))
      .finally(() => setLoading(false))
  }, [])

  function refetchDocuments() {
    fetch('/documents')
      .then((res) => res.json())
      .then(setDocuments)
  }

  async function updateStoryOrder(documentIds: number[]) {
    try {
      const response = await fetch('/story/documents', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: documentIds }),
      })
      if (!response.ok) throw new Error()
      setStoryDocuments(await response.json())
    } catch {
      showError('Could not update the story order. Please try again.')
    }
  }

  function addToStory(documentId: number) {
    if (storyDocuments.some((d) => d.id === documentId)) return
    updateStoryOrder([...storyDocuments.map((d) => d.id), documentId])
  }

  function removeFromStory(documentId: number) {
    updateStoryOrder(storyDocuments.filter((d) => d.id !== documentId).map((d) => d.id))
  }

  function moveStoryDocument(documentId: number, direction: -1 | 1) {
    const ids = storyDocuments.map((d) => d.id)
    const index = ids.indexOf(documentId)
    const target = index + direction
    if (target < 0 || target >= ids.length) return
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    updateStoryOrder(ids)
  }

  function refetchTopicsAndThemes() {
    Promise.all([fetch('/themes').then((res) => res.json()), fetch('/topics').then((res) => res.json())]).then(
      ([themesData, topicsData]) => {
        setThemes(themesData.map(normalizeTheme))
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

  async function setTopicAct(id: number, act: 'opening' | 'conflict' | 'climax' | null) {
    try {
      const response = await fetch(`/topics/${id}/set-act`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ act }),
      })
      if (!response.ok) throw new Error()
      const updated = normalizeExcluded(await response.json())
      setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
    } catch {
      showError('Could not move the topic. Please try again.')
    }
  }

  async function moveTopic(id: number, themeId: number, act: 'opening' | 'conflict' | 'climax' | null) {
    try {
      const response = await fetch(`/topics/${id}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme_id: themeId, act }),
      })
      if (!response.ok) throw new Error()
      const updated = normalizeExcluded(await response.json())
      setTopics((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
      setSubplotRefreshToken((n) => n + 1)
    } catch {
      showError('Could not move the topic. Please try again.')
    }
  }

  async function splitTopic(topicId: number, segmentId: number) {
    try {
      const response = await fetch(`/topics/${topicId}/split`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ split_segment_id: segmentId }),
      })
      if (!response.ok) throw new Error()
      refetchTopicsAndThemes()
      setSubplotRefreshToken((n) => n + 1)
    } catch {
      showError('Could not split the topic. Please try again.')
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
      const updated = normalizeTheme(await response.json())
      setThemes((prev) => prev.map((t) => (t.id === id ? { ...t, ...updated } : t)))
      // The subplot paired with this theme reads its title/summary live from
      // it - refresh the subplot bars so a rename shows up there too.
      setSubplotRefreshToken((n) => n + 1)
    } catch {
      showError('Could not save the theme. Please try again.')
    }
  }

  async function setMainTheme(id: number) {
    try {
      const response = await fetch(`/themes/${id}/set-main`, { method: 'POST' })
      if (!response.ok) throw new Error()
      refetchTopicsAndThemes()
      setSubplotRefreshToken((n) => n + 1)
    } catch {
      showError('Could not change the main theme. Please try again.')
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

  async function renameDocument(id: number, filename: string) {
    try {
      const response = await fetch(`/documents/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      })
      if (!response.ok) throw new Error()
      const updated = await response.json()
      setDocuments((prev) => prev.map((d) => (d.id === id ? { ...d, filename: updated.filename } : d)))
      setStoryDocuments((prev) => prev.map((d) => (d.id === id ? { ...d, filename: updated.filename } : d)))
      setLoadedDocument((prev) => (prev?.id === id ? { ...prev, filename: updated.filename } : prev))
      setRenamingDocId(null)
    } catch {
      showError('Could not rename this document. Please try again.')
    }
  }

  async function deleteDocument(id: number, filename: string) {
    if (!window.confirm(`Delete "${filename}" and all its segments, topics, and subplot memberships?`)) return
    try {
      const response = await fetch(`/documents/${id}`, { method: 'DELETE' })
      if (!response.ok) throw new Error()
      if (loadedDocument?.id === id) setLoadedDocument(null)
      setStoryDocuments((prev) => prev.filter((d) => d.id !== id))
      refetchDocuments()
      refetchTopicsAndThemes()
    } catch {
      showError('Could not delete this document. Please try again.')
    }
  }

  function loadDocument(doc: Document) {
    setLoadedDocument(doc)
  }

  // Once at least one document is linked into the story, the whole app
  // switches from viewing a single loaded document to viewing the full,
  // story-ordered union of every linked document's topics.
  const inStoryMode = storyDocuments.length > 0
  const storyFilenames = new Set(storyDocuments.map((d) => d.filename))

  const loadedTopics = loadedDocument
    ? topics.filter((t) => t.document_filename === loadedDocument.filename && !t.excluded)
    : []
  const storyTopics = topics.filter((t) => storyFilenames.has(t.document_filename) && !t.excluded)
  const effectiveTopics = inStoryMode ? storyTopics : loadedTopics

  const effectiveThemeIds = new Set(effectiveTopics.map((t) => t.theme_id).filter((id): id is number => id !== null))
  const effectiveThemes = themes.filter((t) => effectiveThemeIds.has(t.id))

  const mainThemeId = themes.find((t) => t.is_main)?.id ?? null
  const mainTheme =
    (inStoryMode || loadedDocument !== null) && mainThemeId !== null
      ? { id: mainThemeId, topics: topics.filter((t) => t.theme_id === mainThemeId) }
      : null

  const orderedEffectiveTopics = [...effectiveTopics].sort(
    (a, b) =>
      (a.document_story_position ?? 0) - (b.document_story_position ?? 0) || a.sequence_index - b.sequence_index
  )
  const topicOrderIndex = new Map(orderedEffectiveTopics.map((t, i) => [t.id, i]))

  // Keep the current topic pointer valid as the effective topic set changes.
  useEffect(() => {
    if (orderedEffectiveTopics.length === 0) {
      if (currentTopicId !== null) setCurrentTopicId(null)
      return
    }
    if (!orderedEffectiveTopics.some((t) => t.id === currentTopicId)) {
      setCurrentTopicId(orderedEffectiveTopics[0].id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedDocument, inStoryMode, orderedEffectiveTopics.length])

  // Keep the current theme pointer valid as the effective topic set changes.
  useEffect(() => {
    if (effectiveThemes.length === 0) {
      if (currentThemeId !== null) setCurrentThemeId(null)
      return
    }
    if (!effectiveThemes.some((t) => t.id === currentThemeId)) {
      setCurrentThemeId(effectiveThemes[0].id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedDocument, inStoryMode, effectiveThemes.length])

  const { buckets, extraBucket } = buildActBuckets(orderedEffectiveTopics)

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
    <main className="app-shell container-fluid">
      <h1 className="my-4">{inStoryMode ? `The Story (${storyDocuments.length} documents)` : loadedDocument ? loadedDocument.filename : 'Genre Writer'}</h1>

      <div className="row g-4">
        <div className="col-12 col-lg-2 order-2 order-lg-1 d-flex flex-column gap-4 documents-panel">
        <div className="card">
          <div className="card-header">
            <h2 className="h5 mb-0">Documents</h2>
          </div>
          <div className="card-body">
          <IngestForm onIngested={refetchDocuments} />
          {documents.length === 0 ? (
            <p>No documents ingested yet.</p>
          ) : (
            <ul className="documents-list">
              {documents.map((doc) => {
                const inStory = storyDocuments.some((d) => d.id === doc.id)
                const isRenaming = renamingDocId === doc.id
                return (
                  <li key={doc.id} className={loadedDocument?.id === doc.id ? 'loaded' : undefined}>
                    {isRenaming ? (
                      <div className="doc-rename-row">
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          value={renameValue}
                          autoFocus
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') renameDocument(doc.id, renameValue.trim())
                            if (e.key === 'Escape') setRenamingDocId(null)
                          }}
                        />
                        <button
                          type="button"
                          className="btn btn-sm btn-primary"
                          onClick={() => renameDocument(doc.id, renameValue.trim())}
                        >
                          Save
                        </button>
                        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setRenamingDocId(null)}>
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <>
                        <span className="doc-filename">{doc.filename}</span> <span className="tag">{doc.role}</span>
                      </>
                    )}
                    <div className="doc-actions">
                      <IconButton icon="load" label="Load" onClick={() => loadDocument(doc)} />
                      <IconButton
                        icon="rename"
                        label="Rename"
                        onClick={() => {
                          setRenamingDocId(doc.id)
                          setRenameValue(doc.filename)
                        }}
                      />
                      <IconButton icon="reanalyze" label="Reanalyze" onClick={() => reanalyzeDocument(doc.id)} />
                      <IconButton icon="classify" label="Classify Encoding" onClick={() => classifyDocument(doc.id)} />
                      <IconButton
                        icon="link"
                        label={inStory ? 'Remove from story order' : 'Add to story order'}
                        active={inStory}
                        onClick={() => (inStory ? removeFromStory(doc.id) : addToStory(doc.id))}
                      />
                      <IconButton icon="delete" label="Delete" onClick={() => deleteDocument(doc.id, doc.filename)} />
                    </div>
                    {analyzing[doc.id] && <span className="tag"> {analyzing[doc.id]}</span>}
                    {classifying[doc.id] && <span className="tag"> {classifying[doc.id]}</span>}
                  </li>
                )
              })}
            </ul>
          )}

          {storyDocuments.length > 0 && (
            <div className="story-order">
              <h3>Story Order</h3>
              <ol className="story-order-list">
                {storyDocuments.map((doc, index) => (
                  <li key={doc.id}>
                    <span className="tag">{index + 1}</span> <span className="doc-filename">{doc.filename}</span>
                    <div className="doc-actions">
                      <IconButton
                        icon="up"
                        label={`Move ${doc.filename} earlier in the story`}
                        onClick={() => moveStoryDocument(doc.id, -1)}
                      />
                      <IconButton
                        icon="down"
                        label={`Move ${doc.filename} later in the story`}
                        onClick={() => moveStoryDocument(doc.id, 1)}
                      />
                      <IconButton icon="remove" label={`Remove ${doc.filename} from the story`} onClick={() => removeFromStory(doc.id)} />
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}
          </div>
        </div>
        </div>

        <div className="col-12 col-lg-8 order-1 order-lg-2 d-flex flex-column gap-4">
            <div className="card">
              <div className="card-header">
                <h2 className="h5 mb-0">Plot Viewer</h2>
              </div>
              <div className="card-body">
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
                storyMode={inStoryMode}
                topicOrderIndex={topicOrderIndex}
                refreshToken={subplotRefreshToken}
                currentTopicId={currentTopicId}
                onNavigateTopic={setCurrentTopicId}
                addTargetSubplotId={addTarget?.type === 'subplot' ? addTarget.subplotId : null}
                deleteTargetIds={deleteTargetIds}
                onClickAdd={toggleAddTargetSubplot}
                onToggleDelete={toggleDeleteTarget}
                mainTheme={mainTheme}
                onDropTopic={moveTopic}
              />
              </div>
            </div>

            {addTarget && (
              <div className="card">
                <div className="card-body">
                <div className="selection-banner">
                  <span>
                    Adding topics to {addTarget.type === 'new' ? 'a new subplot' : `“${addTargetTitle ?? '…'}”`}.
                    {filteredSelection
                      ? ` ${filteredSelection.selectedTopicIds.size} of ${filteredSelection.topicIds.length} selected. Type “move them” in the sidekick when ready.`
                      : ' Ask the sidekick to filter topics, e.g. “unassigned topics” or “topics starting with Q”.'}
                  </span>
                  <button type="button" className="btn btn-sm btn-outline-secondary" onClick={cancelAdd}>
                    Cancel
                  </button>
                </div>
                {filteredSelection && (
                  <TopicChecklist
                    topics={effectiveTopics.filter((t) => filteredSelection.topicIds.includes(t.id))}
                    selectedTopicIds={filteredSelection.selectedTopicIds}
                    onToggle={toggleFilteredTopicSelection}
                    onPreviewTopic={handlePreviewTopic}
                  />
                )}
                </div>
              </div>
            )}

            <div className="card">
              <div className="card-body">
              <PlotCarousel
                topics={orderedEffectiveTopics}
                themes={effectiveThemes}
                currentTopicId={currentTopicId}
                currentThemeId={currentThemeId}
                onNavigateTopic={setCurrentTopicId}
                onNavigateTheme={setCurrentThemeId}
                onUpdateTopic={updateTopic}
                onUpdateTheme={updateTheme}
                onSetMainTheme={setMainTheme}
                onSetTopicAct={setTopicAct}
                onPreviewTopic={handlePreviewTopic}
                selection={subplotSelection}
                onToggleTopicSelection={toggleTopicSelection}
                onCancelSelection={cancelSubplotSelection}
              />
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h2 className="h5 mb-0">Preview</h2>
              </div>
              <div className="card-body">
              <SourcePreview
                topic={effectiveTopics.find((t) => t.id === previewTopicId) ?? null}
                mode={previewMode}
                onSplitTopic={splitTopic}
              />
              </div>
            </div>
        </div>

        <div className="col-12 col-lg-2 order-3 d-flex flex-column gap-4">
          <div className="card">
            <div className="card-header">
              <h2 className="h5 mb-0">Encoding Rules</h2>
            </div>
            <div className="card-body">
              <EncodingRules rules={encodingRules} />
            </div>
          </div>
          <div>
            <h2 className="h5">Sidekick</h2>
            <Sidekick
              topics={effectiveTopics}
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
