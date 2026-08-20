import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'
import './ToastContext.css'

interface ToastContextValue {
  showError: (message: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showError = useCallback((msg: string) => {
    setMessage(msg)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => setMessage(null), 6000)
  }, [])

  return (
    <ToastContext.Provider value={{ showError }}>
      {children}
      {message && (
        <div className="toast" role="alert">
          <span>{message}</span>
          <button className="toast-dismiss" onClick={() => setMessage(null)} title="Dismiss">
            &times;
          </button>
        </div>
      )}
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within a ToastProvider')
  return ctx
}
