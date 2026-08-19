import './Notecards.css'

export interface Topic {
  id: number
  theme_id: number | null
  act: 'opening' | 'conflict' | 'climax' | null
  title: string
  summary: string
  document_filename: string
  sequence_index: number
}

interface Props {
  topics: Topic[]
  themeTitleById?: Record<number, string>
  onThemeClick?: (themeId: number) => void
}

function TopicCardGrid({ topics, themeTitleById, onThemeClick }: Props) {
  return (
    <div className="card-grid">
      {topics.map((topic) => {
        const themeTitle = topic.theme_id !== null ? themeTitleById?.[topic.theme_id] : undefined
        return (
          <div className="card" key={topic.id}>
            <h4>{topic.title}</h4>
            <p>{topic.summary}</p>
            <div className="card-tags">
              <span className="tag">{topic.document_filename}</span>
              {themeTitle && (
                <span
                  className={onThemeClick ? 'tag tag-link' : 'tag'}
                  onClick={onThemeClick ? () => onThemeClick(topic.theme_id!) : undefined}
                >
                  {themeTitle}
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default TopicCardGrid
