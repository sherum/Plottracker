import { useState } from 'react'
import TopicCardGrid, { type Topic } from './TopicCardGrid'
import './Notecards.css'
import './PlotViewer.css'

const ACTS = [
  { key: 'opening', label: 'Opening' },
  { key: 'conflict', label: 'Conflict' },
  { key: 'climax', label: 'Climax' },
] as const

type ActKey = (typeof ACTS)[number]['key']

const MIN_SEGMENT_PERCENT = 10

interface Theme {
  id: number
  title: string
}

interface Props {
  topics: Topic[]
  themes: Theme[]
  onThemeClick: (themeId: number) => void
  onUpdateTopic: (id: number, data: { title: string; summary: string }) => void
}

function segmentWidths(counts: number[]): number[] {
  const total = counts.reduce((sum, c) => sum + c, 0)
  if (total === 0) return counts.map(() => 100 / counts.length)

  const raw = counts.map((c) => Math.max((c / total) * 100, c > 0 ? MIN_SEGMENT_PERCENT : 0))
  const rawTotal = raw.reduce((sum, w) => sum + w, 0)
  return raw.map((w) => (w / rawTotal) * 100)
}

function PlotViewer({ topics, themes, onThemeClick, onUpdateTopic }: Props) {
  const [selectedAct, setSelectedAct] = useState<ActKey | 'unassigned' | null>(null)
  const themeTitleById = Object.fromEntries(themes.map((t) => [t.id, t.title]))

  const actTopics = ACTS.map((act) => topics.filter((t) => t.act === act.key))
  const unassignedTopics = topics.filter((t) => t.act === null)
  const widths = segmentWidths(actTopics.map((t) => t.length))

  const shownTopics =
    selectedAct === null
      ? []
      : selectedAct === 'unassigned'
        ? unassignedTopics
        : actTopics[ACTS.findIndex((a) => a.key === selectedAct)]

  return (
    <div className="notecards">
      <div className="hbar">
        {ACTS.map((act, i) => (
          <div
            key={act.key}
            className={`hbar-segment${selectedAct === act.key ? ' active' : ''}`}
            style={{ width: `${widths[i]}%` }}
            onClick={() => setSelectedAct(act.key)}
          >
            <span className="hbar-label">{act.label}</span>
            <div className="hbar-tooltip">
              <strong>{act.label}</strong>
              <ul>
                {actTopics[i].slice(0, 5).map((t) => (
                  <li key={t.id}>{t.title}</li>
                ))}
              </ul>
              {actTopics[i].length === 0 && <span>No topics yet</span>}
              {actTopics[i].length > 5 && <span>+{actTopics[i].length - 5} more</span>}
            </div>
          </div>
        ))}
        {unassignedTopics.length > 0 && (
          <div
            className={`hbar-segment hbar-unassigned${selectedAct === 'unassigned' ? ' active' : ''}`}
            onClick={() => setSelectedAct('unassigned')}
          >
            <span className="hbar-label">?</span>
            <div className="hbar-tooltip">
              <strong>Unassigned</strong>
              <ul>
                {unassignedTopics.slice(0, 5).map((t) => (
                  <li key={t.id}>{t.title}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {selectedAct === null ? (
        <p className="hbar-hint">Click a section above to see its topics.</p>
      ) : (
        <TopicCardGrid
          topics={shownTopics}
          themeTitleById={themeTitleById}
          onThemeClick={onThemeClick}
          onUpdateTopic={onUpdateTopic}
        />
      )}
    </div>
  )
}

export default PlotViewer
