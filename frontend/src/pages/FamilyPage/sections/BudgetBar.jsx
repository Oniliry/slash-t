import { useEffect, useRef, useState } from 'react'

import { updateBudgetSplit } from '../../../shared/api/family.ts'
import { getMemberColor } from './memberColors.js'

import './FamilyWidgets.css'

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function BudgetBar({ members, isAdmin, onChanged }) {
  const containerRef = useRef(null)
  const [drag, setDrag] = useState(null)

  const adults = members.filter((member) => member.role === 'adult')
  const totalIncome = adults.reduce((sum, member) => sum + Number(member.monthly_income ?? 0), 0)

  // Считаем базовые (без учёта текущего перетаскивания) координаты сегментов в процентах.
  let cursor = 0
  const baseSegments = adults.map((member, index) => {
    const width = totalIncome > 0 ? (Number(member.monthly_income ?? 0) / totalIncome) * 100 : 0
    const segment = { member, index, start: cursor, width }
    cursor += width
    return segment
  })

  // Если сейчас идёт перетаскивание, подменяем ширину ровно двух соседних сегментов —
  // остальные сегменты остаются на своих местах, общий бюджет не меняется.
  const segments = baseSegments.map((segment) => {
    if (!drag || (segment.index !== drag.boundaryIndex && segment.index !== drag.boundaryIndex + 1)) {
      return segment
    }

    const isFirstOfPair = segment.index === drag.boundaryIndex
    const width = isFirstOfPair ? drag.pairWidth * drag.ratio : drag.pairWidth * (1 - drag.ratio)
    const start = isFirstOfPair ? drag.pairStart : drag.pairStart + drag.pairWidth * drag.ratio

    return { ...segment, start, width }
  })

  function handlePointerDown(boundaryIndex) {
    return (event) => {
      if (!isAdmin) return
      event.preventDefault()

      const a = baseSegments[boundaryIndex]
      const b = baseSegments[boundaryIndex + 1]
      const pairStart = a.start
      const pairWidth = a.width + b.width

      if (pairWidth <= 0) return

      setDrag({
        boundaryIndex,
        pairStart,
        pairWidth,
        ratio: a.width / pairWidth,
      })
    }
  }

  useEffect(() => {
    if (!drag) return

    function handleMove(event) {
      const rect = containerRef.current?.getBoundingClientRect()
      if (!rect) return

      const clientX = event.touches ? event.touches[0].clientX : event.clientX
      const xPercent = clamp(((clientX - rect.left) / rect.width) * 100, 0, 100)
      const ratio = clamp((xPercent - drag.pairStart) / drag.pairWidth, 0, 1)

      setDrag((current) => (current ? { ...current, ratio } : current))
    }

    async function handleUp() {
      const a = baseSegments[drag.boundaryIndex]
      const b = baseSegments[drag.boundaryIndex + 1]

      await updateBudgetSplit({
        member_a_id: a.member.id,
        member_b_id: b.member.id,
        member_a_ratio: drag.ratio,
      })

      setDrag(null)
      await onChanged()
    }

    window.addEventListener('pointermove', handleMove)
    window.addEventListener('pointerup', handleUp, { once: true })

    return () => {
      window.removeEventListener('pointermove', handleMove)
      window.removeEventListener('pointerup', handleUp)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drag])

  if (adults.length === 0 || totalIncome <= 0) {
    return (
      <p className="budget-widget__hint" style={{ margin: 0 }}>
        Как только взрослые участники укажут доход в профиле, здесь появится
        распределение общего бюджета.
      </p>
    )
  }

  return (
    <>
      <div className="budget-bar" ref={containerRef}>
        {segments.map((segment) => (
          <div
            key={segment.member.id}
            className="budget-bar__segment"
            style={{
              width: `${segment.width}%`,
              background: getMemberColor(segment.index),
            }}
          >
            {segment.width > 12 && `${Math.round(segment.width)}%`}
          </div>
        ))}
        {isAdmin &&
          segments.slice(0, -1).map((segment) => (
            <div
              key={`handle-${segment.member.id}`}
              className="budget-bar__handle"
              style={{ left: `${segment.start + segment.width}%` }}
              onPointerDown={handlePointerDown(segment.index)}
            />
          ))}
      </div>
      {isAdmin && (
        <p className="budget-widget__hint">
          Перетащите точку между участниками, чтобы изменить их доли — общий
          бюджет семьи останется прежним.
        </p>
      )}
    </>
  )
}

export default BudgetBar
