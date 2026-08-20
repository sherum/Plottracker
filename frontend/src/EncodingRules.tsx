import { useState } from 'react'
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
  const [styleKind, setStyleKind] = useState('italic')
  const [blockLength, setBlockLength] = useState<'single' | 'multi'>('multi')
  const [position, setPosition] = useState<'chapter_start' | 'anywhere'>('chapter_start')
  const [label, setLabel] = useState('')
  const [description, setDescription] = useState('')

  async function addRule() {
    if (!label.trim()) return
    await fetch('/encoding-rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ style_kind: styleKind, block_length: blockLength, position, label, description }),
    })
    setLabel('')
    setDescription('')
    onRulesChanged()
  }

  async function deleteRule(id: number) {
    await fetch(`/encoding-rules/${id}`, { method: 'DELETE' })
    onRulesChanged()
  }

  return (
    <div className="notecards">
      <div className="card-grid">
        {rules.map((rule) => (
          <div className="card" key={rule.id}>
            <div className="card-header">
              <h4>{rule.label}</h4>
              <button
                className="edit-btn"
                onClick={() => deleteRule(rule.id)}
                aria-label="Delete rule"
                title="Delete this encoding rule"
              >
                Delete
              </button>
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
          <button onClick={addRule} disabled={!label.trim()} title="Add this encoding rule">
            Add Rule
          </button>
        </div>
      </div>
    </div>
  )
}

export default EncodingRules
