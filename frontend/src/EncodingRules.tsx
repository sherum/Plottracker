import './Notecards.css'
import './EncodingRules.css'

export interface EncodingRule {
  id: number
  style_kind: string
  block_length: 'single' | 'multi'
  position: 'chapter_start' | 'anywhere'
  label: string
  description: string
  enabled?: boolean
}

interface Props {
  rules: EncodingRule[]
  onToggleRule?: (id: number, enabled: boolean) => void
}

function EncodingRules({ rules, onToggleRule }: Props) {
  return (
    <div className="notecards">
      <div className="encoding-rules-list">
        {rules.map((rule) => {
          const enabled = rule.enabled ?? true
          return (
            <button
              type="button"
              className={`encoding-rule-pill${enabled ? '' : ' encoding-rule-disabled'}`}
              key={rule.id}
              disabled={!onToggleRule}
              onClick={onToggleRule ? () => onToggleRule(rule.id, !enabled) : undefined}
              title={
                onToggleRule
                  ? `${enabled ? 'Disable' : 'Enable'} "${rule.label}" for this document`
                  : 'Load a single document to enable or disable rules'
              }
              aria-pressed={onToggleRule ? enabled : undefined}
            >
              {onToggleRule && (
                <i className={`bi ${enabled ? 'bi-check-circle-fill' : 'bi-slash-circle'}`} aria-hidden="true" />
              )}
              <span>{rule.description || rule.label}</span>
            </button>
          )
        })}
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
