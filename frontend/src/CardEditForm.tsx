import { useState } from 'react'

interface Props {
  title: string
  summary: string
  onSave: (data: { title: string; summary: string }) => void
  onCancel: () => void
}

function CardEditForm({ title, summary, onSave, onCancel }: Props) {
  const [draftTitle, setDraftTitle] = useState(title)
  const [draftSummary, setDraftSummary] = useState(summary)

  return (
    <div className="notecard editing">
      <input className="notecard-input" value={draftTitle} onChange={(e) => setDraftTitle(e.target.value)} />
      <textarea
        className="notecard-textarea"
        value={draftSummary}
        onChange={(e) => setDraftSummary(e.target.value)}
      />
      <div className="notecard-actions">
        <button onClick={() => onSave({ title: draftTitle, summary: draftSummary })} title="Save changes">
          Save
        </button>
        <button onClick={onCancel} title="Discard changes">
          Cancel
        </button>
      </div>
    </div>
  )
}

export default CardEditForm
