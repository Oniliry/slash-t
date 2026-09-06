import { useState } from 'react'

import { useAuth } from '../../../app/providers/AuthProvider.jsx'
import { updateName } from '../../../shared/api/profile.ts'

import './ProfileWidgets.css'

function NameWidget() {
  const { user, refreshUser } = useAuth()

  const [name, setName] = useState(user?.name ?? '')
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState(null)

  const trimmedName = name.trim()
  const isUnchanged = trimmedName === (user?.name ?? '')
  const canSave = trimmedName.length > 0 && !isUnchanged && !isSaving

  async function handleSave() {
    if (!canSave) return

    setIsSaving(true)
    setMessage(null)

    const response = await updateName({ name: trimmedName })

    setIsSaving(false)

    if (response.error) {
      setMessage({ type: 'error', text: response.message ?? 'Не удалось сохранить имя.' })
      return
    }

    await refreshUser()
    setMessage({ type: 'success', text: 'Имя обновлено.' })
  }

  return (
    <article className="profile-widget">
      <h2>Имя</h2>
      <p className="profile-widget__hint">
        Это имя видят другие участники вашей семьи. Логин при этом не меняется.
      </p>
      <div className="profile-widget__row">
        <div className="profile-widget__field">
          <label htmlFor="profile-name">Имя</label>
          <input
            id="profile-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            type="text"
            maxLength={100}
          />
        </div>
        <button className="profile-widget__save" type="button" onClick={handleSave} disabled={!canSave}>
          {isSaving ? 'Сохраняем...' : 'Сохранить'}
        </button>
      </div>
      {message && (
        <p className={`profile-widget__message profile-widget__message--${message.type}`}>
          {message.text}
        </p>
      )}
    </article>
  )
}

export default NameWidget
