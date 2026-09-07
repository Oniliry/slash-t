import { useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import { parseReceiptPhoto } from '../../shared/api/receipts.ts'

import './ReceiptScanner.css'

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '')
    reader.onerror = () => reject(new Error('Не удалось прочитать файл.'))
    reader.readAsDataURL(file)
  })
}

/**
 * Экран загрузки фото чека: сверху — выбор/съёмка фото, снизу — кнопка
 * перехода к ручному добавлению покупки.
 */
function ReceiptPhotoScreen({ onClose, onManualEntry, onParsed }) {
  const inputRef = useRef(null)
  const [preview, setPreview] = useState(null)
  const [status, setStatus] = useState('idle') // idle | sending | error
  const [error, setError] = useState('')

  async function processFile(file) {
    if (!file) return

    setPreview(URL.createObjectURL(file))
    setStatus('sending')
    setError('')

    try {
      const base64 = await fileToBase64(file)
      const response = await parseReceiptPhoto(base64, file.type || 'image/jpeg')

      if (response.error || !response.data) {
        setError(response.message ?? 'Не удалось распознать чек. Попробуйте ещё раз.')
        setStatus('error')
        return
      }

      onParsed(response.data)
    } catch {
      setError('Не удалось обработать фото. Попробуйте ещё раз.')
      setStatus('error')
    }
  }

  function handleFile(event) {
    processFile(event.target.files?.[0])
  }

  function handleDrop(event) {
    event.preventDefault()
    processFile(event.dataTransfer.files?.[0])
  }

  return createPortal(
    <div className="receipt-scanner receipt-scanner--photo" role="dialog" aria-modal="true">
      <button
        type="button"
        className="receipt-scanner__close"
        onClick={onClose}
        aria-label="Закрыть"
      >
        ×
      </button>

      <div
        className="receipt-photo__body"
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        {preview ? (
          <img className="receipt-photo__preview" src={preview} alt="Фото чека" />
        ) : (
          <div className="receipt-photo__placeholder">Перетащите файл</div>
        )}

        {status === 'sending' && <p className="receipt-scanner__hint">Распознаём чек...</p>}
        {status === 'error' && <p className="receipt-scanner__error">{error}</p>}

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="receipt-photo__input"
          onChange={handleFile}
        />
        <button
          type="button"
          className="receipt-photo__upload"
          onClick={() => inputRef.current?.click()}
          disabled={status === 'sending'}
        >
          {preview ? 'Загрузить другой чек' : 'Загрузить чек'}
        </button>
      </div>

      <button type="button" className="receipt-scanner__manual" onClick={onManualEntry}>
        Ввести вручную
      </button>
    </div>,
    document.body,
  )
}

export default ReceiptPhotoScreen
