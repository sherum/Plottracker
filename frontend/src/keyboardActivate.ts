import type { KeyboardEvent } from 'react'

// Lets a div/span standing in for a button (a clickable card, a tab-like
// segment) respond to Enter/Space the way a real <button> would natively.
export function onActivateKey(callback: () => void) {
  return (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      callback()
    }
  }
}
