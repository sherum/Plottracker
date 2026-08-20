import { useState } from 'react'
import './Notecards.css'
import './IngestForm.css'

interface IngestResult {
  ingested: string[]
  skipped: string[]
  failed: { filename: string; error: string }[]
}

interface Props {
  onIngested: () => void
}

function IngestForm({ onIngested }: Props) {
  const [folderPath, setFolderPath] = useState('draft_scripts')
  const [role, setRole] = useState<'draft_script' | 'story_note'>('draft_script')
  const [status, setStatus] = useState<'idle' | 'loading'>('idle')
  const [result, setResult] = useState<IngestResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setStatus('loading')
    setError(null)
    setResult(null)
    const response = await fetch('/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath, role }),
    })
    setStatus('idle')
    if (!response.ok) {
      const body = await response.json().catch(() => null)
      setError(body?.detail ?? `Ingest failed (HTTP ${response.status})`)
      return
    }
    const data: IngestResult = await response.json()
    setResult(data)
    if (data.ingested.length > 0) onIngested()
  }

  return (
    <div className="ingest-form">
      <div className="ingest-form-row">
        <input
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          placeholder="Folder path (relative to project root, or absolute)"
        />
        <select value={role} onChange={(e) => setRole(e.target.value as 'draft_script' | 'story_note')}>
          <option value="draft_script">draft_script</option>
          <option value="story_note">story_note</option>
        </select>
        <button
          onClick={submit}
          disabled={status === 'loading' || !folderPath.trim()}
          title="Ingest documents from this folder"
        >
          {status === 'loading' ? 'Ingesting…' : 'Ingest'}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <p className="ingest-result">
          Ingested {result.ingested.length}
          {result.skipped.length > 0 && `, skipped ${result.skipped.length}`}
          {result.failed.length > 0 && `, failed ${result.failed.length}`}
          {result.failed.length > 0 && ': ' + result.failed.map((f) => `${f.filename} (${f.error})`).join('; ')}
        </p>
      )}
    </div>
  )
}

export default IngestForm
