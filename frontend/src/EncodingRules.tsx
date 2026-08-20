import { useState } from 'react'
import { useToast } from './ToastContext'
import './Notecards.css'
import './EncodingRules.css'

export interface EncodingRule {
  id: number
  style_kind: string
  block_length: 'single' | 'multi'
  position: 'chapter_start' | 'anywhere'
  label: string
  description: string
}

interface Props {
  rules: EncodingRule[]
  onRulesChanged: () => void
}

function EncodingRules({ rules, onRulesChanged }: Props) {
  const [editingId, setEditingId] = useState<number | null>(null)
  const [styleKind, setStyleKind] = useState('italic')
  const [blockLength, setBlockLength] = useState<'single' | 'multi'>('multi')
  const [position, setPosition] = useState<'chapter_start' | 'anywhere'>('chapter_start')
  const [label, setLabel] = useState('')
  const [description, setDescription] = useState('')
  const { showError } = useToast()

  function resetForm() {
    setEditingId(null)
    setStyleKind('italic')
    setBlockLength('multi')
    setPosition('chapter_start')
    setLabel('')
    setDescription('')
  }

  function startEditing(rule: EncodingRule) {
    setEditingId(rule.id)
    setStyleKind(rule.style_kind)
    setBlockLength(rule.block_length)
    setPosition(rule.position)
    setLabel(rule.label)
    setDescription(rule.description)
  }

  async function saveRule() {
    if (!label.trim()) return
    const body = JSON.stringify({ style_kind: styleKind, block_length: blockLength, position, label, description })
    try {
      const response = await fetch(
        editingId === null ? '/encoding-rules' : `/encoding-rules/${editingId}`,
        {
          method: editingId === null ? 'POST' : 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body,
        }
      )
      if (!response.ok) throw new Error()
      resetForm()
      onRulesChanged()
    } catch {
      showError(`Could not ${editingId === null ? 'add' : 'save'} this encoding rule. Please try again.`)
    }
  }

  async function deleteRule(id: number, label: string) {
    if (!window.confirm(`Delete the "${label}" encoding rule?`)) return
    try {
      const response = await fetch(`/encoding-rules/${id}`, { method: 'DELETE' })
      if (!response.ok) throw new Error()
      if (editingId === id) resetForm()
      onRulesChanged()
    } catch {
      showError('Could not delete this encoding rule. Please try again.')
    }
  }

  return (
    <div className="notecards">
      <div className="card-grid">
        {rules.map((rule) => (
          <div className={`card${editingId === rule.id ? ' editing-source' : ''}`} key={rule.id}>
            <div className="card-header">
              <h4>{rule.label}</h4>
              <div className="card-header-actions">
                <button
                  className="edit-btn"
                  onClick={() => startEditing(rule)}
                  aria-label="Edit rule"
                  title="Edit this encoding rule"
                >
                  Edit
                </button>
                <button
                  className="edit-btn"
                  onClick={() => deleteRule(rule.id, rule.label)}
                  aria-label="Delete rule"
                  title="Delete this encoding rule"
                >
                  Delete
                </button>
              </div>
            </div>
            {rule.description && <p>{rule.description}</p>}
            <div className="card-tags">
              <span className="tag">{rule.style_kind}</span>
              <span className="tag">{rule.block_length === 'multi' ? 'multi-line' : 'single line'}</span>
              <span className="tag">{rule.position === 'chapter_start' ? 'at chapter start' : 'anywhere'}</span>
            </div>
          </div>
        ))}
      </div>
      {rules.length === 0 && <p className="hbar-hint">No encoding rules yet. Add one below.</p>}

      <div className="encoding-rule-form">
        <div className="encoding-rule-form-row">
          <input value={styleKind} onChange={(e) => setStyleKind(e.target.value)} placeholder="style (e.g. italic)" />
          <select value={blockLength} onChange={(e) => setBlockLength(e.target.value as 'single' | 'multi')}>
            <option value="single">single line</option>
            <option value="multi">multi-line</option>
          </select>
          <select value={position} onChange={(e) => setPosition(e.target.value as 'chapter_start' | 'anywhere')}>
            <option value="chapter_start">at chapter start</option>
            <option value="anywhere">anywhere</option>
          </select>
        </div>
        <div className="encoding-rule-form-row">
          <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="label (e.g. dream_sequence)" />
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="description (optional)"
          />
          <button
            onClick={saveRule}
            disabled={!label.trim()}
            title={editingId === null ? 'Add this encoding rule' : 'Save changes to this encoding rule'}
          >
            {editingId === null ? 'Add Rule' : 'Save Changes'}
          </button>
          {editingId !== null && (
            <button onClick={resetForm} title="Discard changes">
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default EncodingRules
