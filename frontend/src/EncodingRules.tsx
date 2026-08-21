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
}

function EncodingRules({ rules }: Props) {
  return (
    <div className="notecards">
      <div className="encoding-rules-list">
        {rules.map((rule) => (
          <div className="encoding-rule-pill" key={rule.id} title={rule.description || rule.label}>
            {rule.description || rule.label}
          </div>
        ))}
      </div>
      {rules.length === 0 && (
        <p className="hbar-hint">
          No encoding rules yet. Ask the Sidekick to add one, e.g. "multi-line italics at a chapter start is a dream
          sequence".
        </p>
      )}
    </div>
  )
}

export default EncodingRules
