import { useState } from 'react'

import { renameFamily } from '../../../shared/api/family.ts'
import { EditIcon, LogoutIcon } from '../../../widgets/TabBar/icons.jsx'

import './FamilyWidgets.css'

function FamilyNameWidget({ family, isAdmin, onChanged, onLeave, isLeaving }) {
  const [isEditing, setIsEditing] = useState(false)
  const [name, setName] = useState(family.name)
  const [isSaving, setIsSaving] = useState(false)

  function handleStartEdit() {
    setName(family.name)
    setIsEditing(true)
  }

  async function handleSave() {
    const trimmed = name.trim()
    if (!trimmed || trimmed === family.name) {
      setIsEditing(false)
      return
    }

    setIsSaving(true)
    const response = await renameFamily({ name: trimmed })
    setIsSaving(false)

    if (!response.error) {
      await onChanged()
    }

    setIsEditing(false)
  }

  return (
    <article className="family-widget family-name">
      {isEditing ? (
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          onBlur={handleSave}
          onKeyDown={(event) => event.key === 'Enter' && handleSave()}
          autoFocus
          maxLength={150}
          disabled={isSaving}
        />
      ) : (
        <h1>{family.name}</h1>
      )}

      {!isEditing && (
        <div className="family-name__actions">
          {isAdmin && (
            <button
              type="button"
              className="family-name__action family-name__edit"
              onClick={handleStartEdit}
              aria-label="Изменить название семьи"
              title="Изменить название семьи"
            >
              <EditIcon />
            </button>
          )}
          <button
            type="button"
            className="family-name__action family-name__leave"
            onClick={onLeave}
            disabled={isLeaving}
            aria-label="Покинуть семью"
            title="Покинуть семью"
          >
            <LogoutIcon />
          </button>
        </div>
      )}
    </article>
  )
}

export default FamilyNameWidget
