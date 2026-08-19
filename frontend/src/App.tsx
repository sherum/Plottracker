import { useEffect, useState } from 'react'
import Notecards from './Notecards'
import './App.css'

interface Document {
  id: number
  role: string
  filename: string
  source_type: string
  ingested_at: string
}

function App() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/documents')
      .then((res) => res.json())
      .then(setDocuments)
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
        <h2>Notecards</h2>
        <Notecards />
      </section>
    </main>
  )
}

export default App
