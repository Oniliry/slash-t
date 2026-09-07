import { useState } from 'react'

import { removeFamilyMember, updateFamilyMember } from '../../../shared/api/family.ts'
import { getMemberColor } from './memberColors.js'

import './FamilyWidgets.css'

const ROLE_LABELS = {
  adult: 'Взрослый',
  child: 'Ребёнок',
}

function formatMoney(value) {
  return `${new Intl.NumberFormat('ru-RU').format(value ?? 0)} ₽`
}

function formatShare(income_share) {
  if (income_share === null || income_share === undefined) return '0%'
  return `${Math.round(income_share * 100)}%`
}

function MemberEditPanel({ member, currentUserId, onChanged, onClose }) {
  const [name, setName] = useState(member.name)
  const [income, setIncome] = useState(member.monthly_income ?? '')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  const isSelf = member.id === currentUserId

  async function handleSave() {
    setIsSaving(true)
    setError('')

    const payload = { name: name.trim() }
    if (member.role === 'adult' && income !== '' && Number(income) > 0) {
      payload.monthly_income = Number(income)
    }

    const response = await updateFamilyMember(member.id, payload)
    setIsSaving(false)

    if (response.error) {
      setError(response.message ?? 'Не удалось сохранить изменения.')
      return
    }

    await onChanged()
    onClose()
  }

  async function handleRemove() {
    setIsSaving(true)
    setError('')

    const response = await removeFamilyMember(member.id)
    setIsSaving(false)

    if (response.error) {
      setError(response.message ?? 'Не удалось удалить участника.')
      return
    }

    await onChanged()
    onClose()
  }

  return (
    <div className="member-edit">
      <div className="member-edit__row">
        <div className="member-edit__field">
          <label>Имя</label>
          <input value={name} onChange={(event) => setName(event.target.value)} maxLength={100} />
        </div>
        {member.role === 'adult' && (
          <div className="member-edit__field">
            <label>Доход, ₽/мес</label>
            <input
              value={income}
              onChange={(event) => setIncome(event.target.value)}
              type="number"
              min="1"
            />
          </div>
        )}
      </div>
      {error && <p className="profile-widget__message profile-widget__message--error">{error}</p>}
      <div className="member-edit__actions">
        <button className="member-edit__save" type="button" onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Сохраняем...' : 'Сохранить'}
        </button>
        {!isSelf && (
          <button className="member-edit__remove" type="button" onClick={handleRemove} disabled={isSaving}>
            Удалить из семьи
          </button>
        )}
      </div>
    </div>
  )
}

function MemberList({ members, isAdmin, currentUserId, onChanged }) {
  const [expandedId, setExpandedId] = useState(null)

  let adultIndex = -1

  return (
    <article className="family-widget member-list">
      <h2>Участники</h2>
      {members.map((member) => {
        if (member.role === 'adult') adultIndex += 1
        const dotColor = member.role === 'adult' ? getMemberColor(adultIndex) : '#d8e0e6'
        const isExpanded = expandedId === member.id
        const isClickable = isAdmin

        return (
          <div key={member.id}>
            <div
              className={`member-row ${isClickable ? 'member-row--clickable' : ''}`}
              onClick={() => isClickable && setExpandedId(isExpanded ? null : member.id)}
            >
              <span className="member-row__dot" style={{ background: dotColor }} />
              <div className="member-row__info">
                <p className="member-row__name">
                  {member.name}
                  {member.is_admin && <span className="member-row__admin-badge">Админ</span>}
                </p>
                <p className="member-row__role">{ROLE_LABELS[member.role] ?? 'Роль не выбрана'}</p>
              </div>
              <div className="member-row__income">
                {formatMoney(member.monthly_income)}
                <span className="member-row__share">{formatShare(member.income_share)}</span>
              </div>
            </div>
            {isExpanded && (
              <MemberEditPanel
                member={member}
                currentUserId={currentUserId}
                onChanged={onChanged}
                onClose={() => setExpandedId(null)}
              />
            )}
          </div>
        )
      })}
    </article>
  )
}

export default MemberList
