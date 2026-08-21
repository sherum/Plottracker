import { useRef, useState } from 'react'
import { useToast } from './ToastContext'
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
  const [files, setFiles] = useState<File[]>([])
  const [role, setRole] = useState<'draft_script' | 'story_note'>('draft_script')
  const [status, setStatus] = useState<'idle' | 'loading'>('idle')
  const [result, setResult] = useState<IngestResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { showError } = useToast()

  async function submit() {
    if (files.length === 0) return
    setStatus('loading')
    setResult(null)
    const combined: IngestResult = { ingested: [], skipped: [], failed: [] }

    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('role', role)
      try {
        const response = await fetch('/ingest/upload', { method: 'POST', body: formData })
        if (!response.ok) {
          const body = await response.json().catch(() => null)
          combined.failed.push({ filename: file.name, error: body?.detail ?? `HTTP ${response.status}` })
          continue
        }
        const data: IngestResult = await response.json()
        combined.ingested.push(...data.ingested)
        combined.skipped.push(...data.skipped)
        combined.failed.push(...data.failed)
      } catch {
        combined.failed.push({ filename: file.name, error: 'network error' })
      }
    }

    setStatus('idle')
    setResult(combined)
    setFiles([])
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (combined.ingested.length > 0) onIngested()
    if (combined.failed.length > 0) showError(`Could not ingest ${combined.failed.length} file(s). See details below.`)
  }

  return (
    <div className="ingest-form">
      <div className="ingest-form-row">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".txt,.md,.docx,.pdf"
          disabled={status === 'loading'}
          onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          title=""
        /> {/*<select value={role} onChange={(e) => setRole(e.target.value as 'draft_script' | 'story_note')}>*/}
        {/*  <option value="draft_script">draft_script</option>*/}
        {/*  <option value="story_note">story_note</option>*/}
        {/*</select>
       */}
        {files.length > 0 && (
          <button onClick={submit} disabled={status === 'loading'} title="Ingest the selected file(s)">
            {status === 'loading' ? 'Ingesting…' : `Ingest ${files.length} file${files.length === 1 ? '' : 's'}`}
          </button>
        )}
      </div>

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
