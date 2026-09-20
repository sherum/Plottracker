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
  story_id: number | null
  story_position: number | null
}

interface Story {
  id: number
  name: string
  names: string[]
  document_count: number
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

// Story names come from filenames, e.g. "space_mage"; linked stories list every name in order.
function prettyName(name: string): string {
  return name.replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function storyTitle(story: Story | null): string {
  if (!story) return 'Story'
  return (story.names.length > 0 ? story.names : [story.name]).map(prettyName).join(' + ')
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
  const [stories, setStories] = useState<Story[]>([])
  const [activeStoryId, setActiveStoryId] = useState<number | null>(null)
  const [linkFromId, setLinkFromId] = useState<number | null>(null)
  const [linkPair, setLinkPair] = useState<{ a: number; b: number } | null>(null)
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
  const [documentsExpanded, setDocumentsExpanded] = useState(true)
  const [filteredSelection, setFilteredSelection] = useState<{
    topicIds: number[]
    selectedTopicIds: Set<number>
  } | null>(null)
  const [searchTopicIds, setSearchTopicIds] = useState<number[] | null>(null)
  const [hoveredSearchTopicId, setHoveredSearchTopicId] = useState<number | null>(null)
  const { showError } = useToast()

  function handlePreviewTopic(topicId: number | null, mode: 'theme' | 'topic') {
    setPreviewTopicId(topicId)
    setPreviewMode(mode)
  }

  // Themes, topics and story order all belong to one story, so they are
  // always fetched for the story being viewed.
  const storyQuery = activeStoryId === null ? '' : `?story_id=${activeStoryId}`

  useEffect(() => {
    Promise.all([fetch('/documents').then((res) => res.json()), fetch('/stories').then((res) => res.json())])
      .then(([documentsData, storiesData]: [Document[], Story[]]) => {
        setDocuments(documentsData)
        setStories(storiesData)
        setActiveStoryId(storiesData[0]?.id ?? null)
        if (storiesData.length === 0) setLoading(false)
      })
      .catch(() => setError('Could not reach the backend at http://localhost:8000'))
  }, [])

  useEffect(() => {
    if (activeStoryId === null) return
    Promise.all([
      fetch(`/themes${storyQuery}`).then((res) => res.json()),
      fetch(`/topics${storyQuery}`).then((res) => res.json()),
      fetch(`/story/documents${storyQuery}`).then((res) => res.json()),
    ])
      .then(([themesData, topicsData, storyDocumentsData]) => {
        setThemes(themesData.map(normalizeTheme))
        setTopics(topicsData.map(normalizeExcluded))
        setStoryDocuments(storyDocumentsData)
      })
      .catch(() => setError('Could not reach the backend at http://localhost:8000'))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeStoryId])

  function refetchDocuments() {
    return Promise.all([
      fetch('/documents').then((res) => res.json()),
      fetch('/stories').then((res) => res.json()),
    ]).then(([documentsData, storiesData]: [Document[], Story[]]) => {
      setDocuments(documentsData)
      setStories(storiesData)
      return documentsData
    })
  }

  async function updateStoryOrder(documentIds: number[]) {
    try {
      const response = await fetch('/story/documents', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: documentIds, story_id: activeStoryId }),
      })
      if (!response.ok) throw new Error()
      setStoryDocuments(await response.json())
      refetchTopicsAndThemes()
    } catch {
      showError('Could not update the story order. Please try again.')
    }
  }

  function switchStory(storyId: number) {
    // Half-finished flows hold topics and subplots of the story being left.
    setAddTarget(null)
    setAddTargetTitle(null)
    setFilteredSelection(null)
    setSubplotSelection(null)
    setDeleteTargetIds(new Set())
    setSearchTopicIds(null)
    setLoadedDocument(null)
    setActiveStoryId(storyId)
  }

  // Linking is two clicks - the order button on a story, then the story that follows it -
  // and then a dialog confirms the order.
  function toggleLinkFrom(storyId: number) {
    setLinkFromId((prev) => (prev === storyId ? null : storyId))
  }

  function pickLinkTarget(storyId: number) {
    if (linkFromId === null || storyId === linkFromId) return
    setLinkPair({ a: linkFromId, b: storyId })
  }

  function cancelLink() {
    setLinkPair(null)
    setLinkFromId(null)
  }

  async function confirmLink(flip: boolean) {
    if (!linkPair) return
    const [first, second] = flip ? [linkPair.b, linkPair.a] : [linkPair.a, linkPair.b]
    try {
      const response = await fetch('/stories/link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ first_story_id: first, second_story_id: second }),
      })
      if (!response.ok) throw new Error()
      const { story_id: survivorId } = await response.json()
      cancelLink()
      await refetchDocuments()
      setLoadedDocument(null)
      setSubplotRefreshToken((n) => n + 1)
      if (survivorId !== activeStoryId) setActiveStoryId(survivorId)
      else refetchStoryDocuments().then(refetchTopicsAndThemes)
    } catch {
      showError('Could not link these stories. Please try again.')
    }
  }

  async function unlinkStory(story: Story) {
    const last = prettyName(story.names[story.names.length - 1])
    if (!window.confirm(`Detach "${last}" from ${storyTitle(story)}? Its topics and subplots split back out.`)) return
    try {
      const response = await fetch(`/stories/${story.id}/unlink`, { method: 'POST' })
      if (!response.ok) throw new Error()
      await refetchDocuments()
      setLoadedDocument(null)
      setSubplotRefreshToken((n) => n + 1)
      refetchStoryDocuments().then(refetchTopicsAndThemes)
    } catch {
      showError('Could not unlink this story. Please try again.')
    }
  }

  function refetchStoryDocuments() {
    return fetch(`/story/documents${storyQuery}`)
      .then((res) => res.json())
      .then(setStoryDocuments)
  }

  async function handleIngested() {
    const docs = await refetchDocuments()
    const newest = docs.reduce((a, b) => (b.id > a.id ? b : a))
    if (newest.story_id !== null && newest.story_id !== activeStoryId) switchStory(newest.story_id)
    else refetchStoryDocuments().then(refetchTopicsAndThemes)
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
    Promise.all([
      fetch(`/themes${storyQuery}`).then((res) => res.json()),
      fetch(`/topics${storyQuery}`).then((res) => res.json()),
    ]).then(
      ([themesData, topicsData]) => {
        setThemes(themesData.map(normalizeTheme))
        setTopics(topicsData.map(normalizeExcluded))
      }
    )
  }

  function refetchEncodingRules() {
    // Rules are shown scoped to whichever single document is loaded, so
    // enabling/disabling one is unambiguous. The whole-story view spans
    // several documents at once, so there's no single document to scope by.
    const url = loadedDocument ? `/encoding-rules?document_id=${loadedDocument.id}` : '/encoding-rules'
    fetch(url)
      .then((res) => res.json())
      .then(setEncodingRules)
  }

  useEffect(() => {
    refetchEncodingRules()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedDocument?.id])

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
    refetchTopicsAndThemes()
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
    if (addTarget) {
      setFilteredSelection({ topicIds, selectedTopicIds: new Set() })
    } else {
      setSearchTopicIds(topicIds)
    }
  }

  function clearSearchResults() {
    setSearchTopicIds(null)
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
          body: JSON.stringify({ title: name, summary: '', story_id: activeStoryId }),
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
    refetchTopicsAndThemes()
    setSubplotRefreshToken((n) => n + 1)
    return { count: topicIds.length, title }
  }

  async function finishDeleteFlow(): Promise<{ count: number }> {
    const ids = [...deleteTargetIds]
    if (ids.length === 0) return { count: 0 }
    await Promise.all(ids.map((id) => fetch(`/subplots/${id}`, { method: 'DELETE' })))
    setDeleteTargetIds(new Set())
    refetchTopicsAndThemes()
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
      setSubplotRefreshToken((n) => n + 1)
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

  async function toggleEncodingRule(ruleId: number, enabled: boolean) {
    if (!loadedDocument) return
    try {
      const response = await fetch(`/documents/${loadedDocument.id}/encoding-rules/${ruleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      })
      if (!response.ok) throw new Error()
      setEncodingRules((prev) => prev.map((r) => (r.id === ruleId ? { ...r, enabled } : r)))
    } catch {
      showError('Could not update this encoding rule. Please try again.')
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
      await refetchDocuments()
      if (updated.story_id !== activeStoryId) switchStory(updated.story_id)
      else refetchStoryDocuments().then(refetchTopicsAndThemes)
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

  function toggleDocumentsPanel() {
    setDocumentsExpanded((prev) => !prev)
  }

  // The active story is shown as a whole - the story-ordered union of all its
  // editions' topics - unless one document has been loaded to view on its own.
  const inStoryMode = !loadedDocument && storyDocuments.length > 0
  const activeStory = stories.find((s) => s.id === activeStoryId) ?? null
  const editionNames: Record<number, string> = Object.fromEntries(
    storyDocuments.flatMap((d) => (d.story_position === null ? [] : [[d.story_position, d.filename]]))
  )
  const visibleDocuments = documents.filter((d) => activeStoryId === null || d.story_id === activeStoryId)
  const storyFilenames = new Set(storyDocuments.map((d) => d.filename))

  const loadedTopics = loadedDocument
    ? topics.filter((t) => t.document_filename === loadedDocument.filename && !t.excluded)
    : []
  const storyTopics = topics.filter((t) => storyFilenames.has(t.document_filename) && !t.excluded)
  const effectiveTopics = inStoryMode ? storyTopics : loadedTopics

  const effectiveThemeIds = new Set(effectiveTopics.map((t) => t.theme_id).filter((id): id is number => id !== null))
  const effectiveThemes = themes.filter((t) => effectiveThemeIds.has(t.id))

  const mainThemeId = themes.find((t) => t.is_main)?.id ?? null

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
      <h1 className="my-4">
        {inStoryMode
          ? `${storyTitle(activeStory)} (${storyDocuments.length} documents)`
          : loadedDocument
            ? loadedDocument.filename
            : 'Genre Writer'}
      </h1>
      {stories.length > 0 && (
        <div className="story-switcher d-flex align-items-center gap-2 mb-3">
          <label htmlFor="story-select" className="mb-0">
            Story
          </label>
          <select
            id="story-select"
            className="form-select form-select-sm w-auto"
            value={activeStoryId ?? ''}
            onChange={(e) => switchStory(Number(e.target.value))}
          >
            {stories.map((story) => (
              <option key={story.id} value={story.id}>
                {storyTitle(story)} ({story.document_count})
              </option>
            ))}
          </select>
          {loadedDocument && (
            <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setLoadedDocument(null)}>
              View whole story
            </button>
          )}
        </div>
      )}

      <div className="row g-4">
        <div className="col-12 col-lg-2 order-2 order-lg-1 d-flex flex-column gap-4 documents-panel">
        <div className="card">
          <div className="card-header documents-card-header">
            <h2 className="h5 mb-0">Documents</h2>
            <span className="documents-panel-toggle">
              <IconButton
                icon="chevron"
                label={documentsExpanded ? 'Collapse documents' : 'Expand documents'}
                active={documentsExpanded}
                onClick={toggleDocumentsPanel}
              />
            </span>
          </div>
          <div className="card-body">
          <IngestForm onIngested={handleIngested} />
          {stories.length > 0 && (
            <div className="stories-list">
              <h3>Stories</h3>
              {linkFromId !== null && (
                <p className="stories-hint">
                  Click the story that follows {storyTitle(stories.find((s) => s.id === linkFromId) ?? null)}.
                </p>
              )}
              <ul>
                {stories.map((story) => {
                  const isSource = story.id === linkFromId
                  const isTarget = linkFromId !== null && !isSource
                  const classes = [
                    story.id === activeStoryId ? 'story-active' : '',
                    isSource ? 'story-link-source' : '',
                    isTarget ? 'story-link-target' : '',
                  ]
                  return (
                    <li key={story.id} className={classes.filter(Boolean).join(' ') || undefined}>
                      <button
                        type="button"
                        className="doc-filename"
                        onClick={() => (isTarget ? pickLinkTarget(story.id) : switchStory(story.id))}
                      >
                        {storyTitle(story)} <span className="tag">{story.document_count}</span>
                      </button>
                      <div className="doc-actions">
                        <IconButton
                          icon="link"
                          label={
                            isSource
                              ? 'Cancel linking'
                              : `Link ${storyTitle(story)} to the story that follows it`
                          }
                          active={isSource}
                          onClick={() => toggleLinkFrom(story.id)}
                        />
                        {story.names.length > 1 && (
                          <IconButton
                            icon="unlink"
                            label={`Detach the last story from ${storyTitle(story)}`}
                            onClick={() => unlinkStory(story)}
                          />
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
          {documents.length === 0 ? (
            <p>No documents ingested yet.</p>
          ) : (
            <ul className={`documents-list${documentsExpanded ? '' : ' collapsed'}`}>
              {visibleDocuments.map((doc) => {
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
                      <button type="button" className="doc-filename" onClick={() => loadDocument(doc)}>
                        {doc.filename}
                      </button>
                    )}
                    <div className="doc-actions">
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
              <p className="story-order-hint">
                The order these documents are read in. Files numbered like <em>name_1</em>, <em>name_2</em> sort
                automatically, and linked stories follow their link order.
                {storyDocuments.length > 1 &&
                  ' Use the arrows to move a document; adding or renaming a file in this story sets the order back to automatic.'}
              </p>
              <ol className="story-order-list">
                {storyDocuments.map((doc, index) => (
                  <li key={doc.id}>
                    <span className="tag">{index + 1}</span> <span className="doc-filename">{doc.filename}</span>
                    {storyDocuments.length > 1 && (
                      <div className="doc-actions">
                        <IconButton
                          icon="up"
                          label={`Move ${doc.filename} earlier in the story`}
                          disabled={index === 0}
                          onClick={() => moveStoryDocument(doc.id, -1)}
                        />
                        <IconButton
                          icon="down"
                          label={`Move ${doc.filename} later in the story`}
                          disabled={index === storyDocuments.length - 1}
                          onClick={() => moveStoryDocument(doc.id, 1)}
                        />
                      </div>
                    )}
                  </li>
                ))}
              </ol>
              {storyDocuments.length > 1 && (
                <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => updateStoryOrder([])}>
                  Reset to automatic order
                </button>
              )}
            </div>
          )}
          </div>
        </div>
        </div>

        <div className="d-none d-lg-block col-lg-1 order-lg-2" />

        <div className="col-12 col-lg-6 order-1 order-lg-3 d-flex flex-column gap-4">
            <div className="card">
              <div className="card-header">
                <h2 className="h5 mb-0">Plot Viewer</h2>
              </div>
              <div className="card-body">
              <div className="main-plot-row">
                <HbarVisual
                  buckets={buckets}
                  extraBucket={extraBucket}
                  onSegmentClick={jumpToAct}
                  onDropTopic={
                    mainThemeId === null
                      ? undefined
                      : (topicId, actKey) =>
                          moveTopic(topicId, mainThemeId, actKey === 'unassigned' ? null : (actKey as 'opening' | 'conflict' | 'climax'))
                  }
                  markerTopicId={hoveredSearchTopicId ?? currentTopicId}
                />
                <IconButton
                  icon="add"
                  label="Add topics to a new subplot"
                  active={addTarget?.type === 'new'}
                  onClick={toggleAddTargetNew}
                />
              </div>
              <SubplotBars
                documentId={loadedDocument?.id ?? null}
                storyId={activeStoryId}
                editionNames={editionNames}
                storyMode={inStoryMode}
                topicOrderIndex={topicOrderIndex}
                refreshToken={subplotRefreshToken}
                currentTopicId={hoveredSearchTopicId ?? currentTopicId}
                onNavigateTopic={setCurrentTopicId}
                addTargetSubplotId={addTarget?.type === 'subplot' ? addTarget.subplotId : null}
                deleteTargetIds={deleteTargetIds}
                onClickAdd={toggleAddTargetSubplot}
                onToggleDelete={toggleDeleteTarget}
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
                searchTopics={
                  searchTopicIds ? effectiveTopics.filter((t) => searchTopicIds.includes(t.id)) : null
                }
                onClearSearch={clearSearchResults}
                onHoverSearchTopic={setHoveredSearchTopicId}
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

        <div className="d-none d-lg-block col-lg-1 order-lg-4" />

        <div className="col-12 col-lg-2 order-3 order-lg-5 d-flex flex-column gap-4 sidebar-panel">
          <div className="card">
            <div className="card-header">
              <h2 className="h5 mb-0">Encoding Rules</h2>
            </div>
            <div className="card-body">
              <EncodingRules
                rules={encodingRules}
                onToggleRule={loadedDocument && !inStoryMode ? toggleEncodingRule : undefined}
              />
            </div>
          </div>
          <div>
            <h2 className="h5">Sidekick</h2>
            <Sidekick
              topics={effectiveTopics}
              storyId={activeStoryId}
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

      {linkPair && (
        <div className="link-dialog-backdrop">
          <div className="link-dialog card" role="dialog" aria-modal="true" aria-labelledby="link-dialog-title">
            <div className="card-body">
              <h2 id="link-dialog-title" className="h5">
                Link these stories?
              </h2>
              <p>
                Do you want to link <strong>{storyTitle(stories.find((s) => s.id === linkPair.a) ?? null)}</strong> and{' '}
                <strong>{storyTitle(stories.find((s) => s.id === linkPair.b) ?? null)}</strong> in this order?
              </p>
              <p className="link-dialog-order">
                {storyTitle(stories.find((s) => s.id === linkPair.a) ?? null)}
                <i className="bi bi-arrow-right" aria-hidden="true" />
                {storyTitle(stories.find((s) => s.id === linkPair.b) ?? null)}
              </p>
              <p className="link-dialog-note">They will share one Main plot and be read in this order.</p>
              <div className="link-dialog-actions">
                <button type="button" className="btn btn-primary" onClick={() => confirmLink(false)}>
                  Yes
                </button>
                <button type="button" className="btn btn-outline-primary" onClick={() => confirmLink(true)}>
                  Flip (second, then first)
                </button>
                <button type="button" className="btn btn-outline-secondary" onClick={cancelLink}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

export default App
