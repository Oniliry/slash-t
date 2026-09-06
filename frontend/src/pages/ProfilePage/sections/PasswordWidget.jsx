import { useState } from 'react'

import { changePassword } from '../../../shared/api/profile.ts'

import './ProfileWidgets.css'

function PasswordWidget() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState(null)

  const canSave = currentPassword.length > 0 && newPassword.length >= 6 && !isSaving

  async function handleSave() {
    if (!canSave) return

    setIsSaving(true)
    setMessage(null)

    const response = await changePassword({
      current_password: currentPassword,
      new_password: newPassword,
    })

    setIsSaving(false)

    if (response.error) {
      setMessage({ type: 'error', text: response.message ?? 'Не удалось сменить пароль.' })
      return
    }

    setCurrentPassword('')
    setNewPassword('')
    setMessage({ type: 'success', text: 'Пароль успешно изменён.' })
  }

  return (
    <article className="profile-widget">
      <h2>Пароль</h2>
      <p className="profile-widget__hint">
        Для смены пароля подтвердите его текущим значением.
      </p>

      <div className="profile-widget__row">
        <div className="profile-widget__field">
          <label htmlFor="profile-current-password">Текущий пароль</label>
          <input
            id="profile-current-password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            type="password"
            autoComplete="current-password"
          />
        </div>
      </div>

      <div className="profile-widget__row" style={{ marginTop: 12 }}>
        <div className="profile-widget__field">
          <label htmlFor="profile-new-password">Новый пароль</label>
          <input
            id="profile-new-password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            type="password"
            autoComplete="new-password"
            minLength={6}
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

export default PasswordWidget
