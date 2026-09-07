import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { getCushionState } from '../../../shared/api/cushion.ts'
import {
  getLastAnalysis,
  uploadStatement,
} from '../../../shared/api/financialCushion.ts'

import './CushionWidget.css'

// Лимиты должны совпадать с бэкендом (services/financial_cushion_service.py):
// некорректный файл отклоняем ещё до отправки, чтобы не тратить мобильный трафик.
const MAX_PDF_SIZE = 10 * 1024 * 1024

const moneyFormatter = new Intl.NumberFormat('ru-RU', {
  maximumFractionDigits: 0,
})

function DocumentIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="cushion-widget__icon">
      <path
        d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7l-5-5Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M14 2v5h5M9 13h6M9 17h4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  )
}

// Итог виджета считается по той же формуле, что и на бэкенде:
// [сумма активных трат] / [число полных месяцев].
function computeCushionTotal(analysis) {
  if (!analysis) {
    return 0
  }

  const activeSum = analysis.transactions
    .filter((tx) => tx.is_active)
    .reduce((sum, tx) => sum + tx.amount, 0)

  return activeSum / Math.max(analysis.months_analyzed, 1)
}

function CushionWidget() {
  const fileInputRef = useRef(null)

  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [monthlyExpenses, setMonthlyExpenses] = useState(0)
  const [goalTarget, setGoalTarget] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function load() {
      const [lastResponse, stateResponse] = await Promise.all([
        getLastAnalysis(),
        getCushionState(),
      ])

      if (cancelled) {
        return
      }

      if (!lastResponse.error && lastResponse.data) {
        setAnalysis(lastResponse.data)
      }

      if (!stateResponse.error && stateResponse.data) {
        setMonthlyExpenses(Number(stateResponse.data.monthly_expenses) || 0)
        setGoalTarget(
          stateResponse.data.goal
            ? Number(stateResponse.data.goal.target_amount) || 0
            : 0,
        )
      }

      setIsLoading(false)
    }

    load()

    return () => {
      cancelled = true
    }
  }, [])

  const cushionTotal = useMemo(() => computeCushionTotal(analysis), [analysis])

  const coveredMonths =
    monthlyExpenses > 0 ? Math.floor(cushionTotal / monthlyExpenses) : null

  const effectiveTarget = goalTarget || monthlyExpenses * 6
  const progressPercent =
    effectiveTarget > 0
      ? Math.min(Math.round((cushionTotal / effectiveTarget) * 100), 100)
      : 0

  const handleUploadClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''

    if (!file) {
      return
    }

    const isPdf =
      file.type === 'application/pdf' ||
      file.name.toLowerCase().endsWith('.pdf')

    if (!isPdf) {
      setError('Нужен файл в формате PDF.')
      return
    }

    if (file.size > MAX_PDF_SIZE) {
      setError('Файл больше 10 МБ — выберите выписку поменьше.')
      return
    }

    setIsUploading(true)
    setError('')

    const response = await uploadStatement(file)

    if (!response.error && response.data) {
      setAnalysis(response.data)
    } else {
      setError(response.message ?? 'Не удалось обработать выписку.')
    }

    setIsUploading(false)
  }, [])

  return (
    <article className="card cushion-widget">
      <div className="section-heading">
        <h2>ФинПодушка</h2>
      </div>

      {isLoading ? (
        <div className="cushion-widget__skeleton" aria-hidden="true">
          <span className="cushion-widget__skeleton-line cushion-widget__skeleton-line--wide" />
          <span className="cushion-widget__skeleton-line" />
        </div>
      ) : analysis ? (
        <Link
          to="/financial-cushion"
          className="cushion-widget__result"
          aria-label="Открыть подробный отчёт по финансовой подушке"
        >
          <div className="cushion-widget__metrics">
            <strong className="cushion-widget__value">
              {moneyFormatter.format(cushionTotal)} ₽
            </strong>
            <span className="cushion-widget__verdict">
              {coveredMonths !== null
                ? `Запас на ~${coveredMonths} мес. расходов`
                : 'Расчёт по выписке готов'}
            </span>
          </div>

          {effectiveTarget > 0 && (
            <div
              className="cushion-widget__bar"
              role="img"
              aria-label={`Накоплено ${progressPercent}% цели`}
            >
              <span
                className="cushion-widget__bar-fill"
                style={{ width: `${Math.max(progressPercent, 4)}%` }}
              />
            </div>
          )}

          <span className="cushion-widget__more">Подробнее</span>
        </Link>
      ) : (
        <div className="cushion-widget__upload">
          <span className="cushion-widget__upload-area">
            <DocumentIcon />
            <p className="cushion-widget__upload-text">
              Загрузите PDF-выписку банка — рассчитаем вашу финансовую подушку
            </p>
          </span>

          <button
            type="button"
            className="cushion-widget__upload-button"
            onClick={handleUploadClick}
            disabled={isUploading}
          >
            {isUploading ? (
              <>
                <span className="cushion-widget__spinner" aria-hidden="true" />
                Анализируем...
              </>
            ) : (
              'Выбрать выписку'
            )}
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf,.pdf"
            onChange={handleFileChange}
            hidden
          />

          <p className="cushion-widget__hint">PDF до 10 МБ</p>
          {error && <p className="cushion-widget__error">{error}</p>}
        </div>
      )}

      {isUploading && analysis && (
        <p className="cushion-widget__hint">Анализируем новую выписку...</p>
      )}
    </article>
  )
}

export default CushionWidget
