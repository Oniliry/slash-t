import { useState } from 'react'

import './FamilyWidgets.css'

function InviteCodeWidget({ inviteCode }) {
  const [isCopied, setIsCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(inviteCode)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch {
      // Буфер обмена недоступен — код всё равно виден на экране.
    }
  }

  return (
    <article className="family-widget invite-widget" onClick={handleCopy} role="button" tabIndex={0}>
      <div>
        <p className="invite-widget__label">Код семьи</p>
        <p className="invite-widget__code">{inviteCode}</p>
      </div>
      <span className="invite-widget__copy">{isCopied ? 'Скопировано' : 'Скопировать'}</span>
    </article>
  )
}

export default InviteCodeWidget
