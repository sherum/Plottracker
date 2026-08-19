import { useEffect, useState } from 'react'
import './App.css'

interface Document {
  id: number
  role: string
  filename: string
  source_type: string
  ingested_at: string
}

interface Theme {
  id: number
  title: string
  summary: string
}

function App() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [themes, setThemes] = useState<Theme[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/documents').then((res) => res.json()),
      fetch('/themes').then((res) => res.json()),
    ])
      .then(([documentsData, themesData]) => {
        setDocuments(documentsData)
        setThemes(themesData)
      })
      .catch(() => setError('Could not reach the backend at http://localhost:8000'))
  }, [])

  if (error) {
    return <p className="error">{error}</p>
  }

  return (
    <main>
      <h1>Genre Writer</h1>

      <section>
        <h2>Documents</h2>
        {documents.length === 0 ? (
          <p>No documents ingested yet.</p>
        ) : (
          <ul>
            {documents.map((doc) => (
              <li key={doc.id}>
                {doc.filename} <span className="tag">{doc.role}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Themes</h2>
        {themes.length === 0 ? (
          <p>No themes extracted yet.</p>
        ) : (
          <ul>
            {themes.map((theme) => (
              <li key={theme.id}>
                <strong>{theme.title}</strong>: {theme.summary}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}

export default App
