import { useEffect, useRef, useState } from 'react'

import { scanReceipt } from '../../shared/api/receipts.ts'

import './ReceiptScanner.css'

// html5-qrcode подключается через CDN и загружается ЛЕНИВО — только
// при первом открытии сканера на мобильном. Десктоп библиотеку не грузит.
const SCANNER_CDN_URL = 'https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js'

let scannerScriptPromise = null

function loadHtml5Qrcode() {
  if (window.Html5Qrcode) {
    return Promise.resolve()
  }
  if (!scannerScriptPromise) {
    scannerScriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = SCANNER_CDN_URL
      script.async = true
      script.onload = resolve
      script.onerror = () => {
        scannerScriptPromise = null
        reject(new Error('Не удалось загрузить библиотеку сканера.'))
      }
      document.head.appendChild(script)
    })
  }
  return scannerScriptPromise
}

/**
 * Полноэкранный мобильный сканер QR-кодов чеков.
 *
 * @param {Function} onClose  Полностью закрыть сканер (крестик).
 * @param {Function} onManual Закрыть сканер и открыть ручную форму
 *                            («Ввести вручную» — существующая AddPurchaseModal).
 */
function ReceiptScanner({ onClose, onManual }) {
  const scannerRef = useRef(null)
  const isStoppingRef = useRef(false)

  const [status, setStatus] = useState('starting') // starting | scanning | error
  const [errorMessage, setErrorMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [resultRaw, setResultRaw] = useState(null)
  const [scanError, setScanError] = useState('')

  useEffect(() => {
    let cancelled = false
    const containerElementId = 'receipt-scanner-region'

    loadHtml5Qrcode()
      .then(() => {
        if (cancelled || !window.Html5Qrcode) {
          return
        }

        const scanner = new window.Html5Qrcode(containerElementId, {
          verbose: false,
        })
        scannerRef.current = scanner

        // Строго задняя (тыловая) камера + высокое разрешение,
        // чтобы текст чека и QR читались чётко.
        scanner
          .start(
            {
              facingMode: { exact: 'environment' },
              width: { ideal: 1920 },
              height: { ideal: 1080 },
            },
            { fps: 10, qrbox: { width: 250, height: 250 } },
            (decodedText) => handleDecoded(decodedText),
            () => {},
          )
          .then(() => {
            if (!cancelled) {
              setStatus('scanning')
            }
          })
          .catch((error) => {
            if (cancelled) {
              return
            }
            setStatus('error')
            setErrorMessage(
              error?.name === 'NotAllowedError'
                ? 'Нет доступа к камере. Разрешите доступ в настройках браузера.'
                : 'Не удалось запустить камеру. Проверьте разрешения.',
            )
          })
      })
      .catch((error) => {
        if (cancelled) {
          return
        }
        setStatus('error')
        setErrorMessage(error.message)
      })

    return () => {
      cancelled = true
      stopScanner()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function stopScanner() {
    const scanner = scannerRef.current
    if (!scanner || isStoppingRef.current) {
      return
    }
    isStoppingRef.current = true
    scanner
      .stop()
      .then(() => scanner.clear())
      .catch(() => {})
  }

  async function handleDecoded(decodedText) {
    if (isSending || resultRaw !== null) {
      return
    }

    // Кадр распознан — гасим камеру и отправляем raw QR на бэкенд.
    stopScanner()
    setIsSending(true)
    setScanError('')

    const response = await scanReceipt(decodedText)

    if (!response.error && response.data) {
      setResultRaw(response.data.raw)
    } else {
      setScanError(response.message ?? 'Не удалось проверить чек.')
    }

    setIsSending(false)
  }

  function handleCloseResult() {
    setResultRaw(null)
    setScanError('')
    onClose()
  }

  // ---- Экран результата: полноэкранный оверлей с сырым ответом API ----
  if (resultRaw !== null) {
    return (
      <div className="receipt-result" role="dialog" aria-modal="true" aria-label="Результат сканирования чека">
        <button
          className="receipt-result__close"
          type="button"
          onClick={handleCloseResult}
          aria-label="Закрыть результат"
        >
          ×
        </button>
        <h2 className="receipt-result__title">Результат сканирования</h2>
        <pre className="receipt-result__raw">{resultRaw}</pre>
      </div>
    )
  }

  return (
    <div className="receipt-scanner" role="dialog" aria-modal="true" aria-label="Сканирование QR-кода чека">
      <div className="receipt-scanner__camera" id="receipt-scanner-region" />

      {status === 'scanning' && (
        <>
          {/* Полупрозрачная маска с окном-видоискателем по центру */}
          <div className="receipt-scanner__mask" aria-hidden="true" />
          <div className="receipt-scanner__frame" aria-hidden="true">
            <span className="receipt-scanner__corner receipt-scanner__corner--tl" />
            <span className="receipt-scanner__corner receipt-scanner__corner--tr" />
            <span className="receipt-scanner__corner receipt-scanner__corner--bl" />
            <span className="receipt-scanner__corner receipt-scanner__corner--br" />
          </div>
          <p className="receipt-scanner__hint">Наведите камеру на QR-код чека</p>
        </>
      )}

      {(status === 'starting' || isSending) && (
        <div className="receipt-scanner__loader">
          <span className="receipt-scanner__spinner" aria-hidden="true" />
          <span>{isSending ? 'Проверяем чек...' : 'Запускаем камеру...'}</span>
        </div>
      )}

      {status === 'error' && (
        <div className="receipt-scanner__error">
          <p>{errorMessage}</p>
          <button className="receipt-scanner__secondary" type="button" onClick={onClose}>
            Закрыть
          </button>
        </div>
      )}

      {scanError && (
        <div className="receipt-scanner__error receipt-scanner__error--inline">
          <p>{scanError}</p>
          <button className="receipt-scanner__secondary" type="button" onClick={onClose}>
            Закрыть
          </button>
        </div>
      )}

      <button
        className="receipt-scanner__manual"
        type="button"
        onClick={onManual}
        disabled={isSending}
      >
        Ввести вручную
      </button>
    </div>
  )
}

export default ReceiptScanner
