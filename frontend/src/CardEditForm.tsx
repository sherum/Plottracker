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
      <input
        className="form-control form-control-sm"
        value={draftTitle}
        onChange={(e) => setDraftTitle(e.target.value)}
      />
      <textarea
        className="form-control form-control-sm notecard-textarea"
        value={draftSummary}
        onChange={(e) => setDraftSummary(e.target.value)}
      />
      <div className="notecard-actions">
        <button
          type="button"
          className="btn btn-sm btn-primary"
          onClick={() => onSave({ title: draftTitle, summary: draftSummary })}
          title="Save changes"
        >
          Save
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={onCancel} title="Discard changes">
          Cancel
        </button>
      </div>
    </div>
  )
}

export default CardEditForm
