import { useEffect, useRef, useState } from 'react'

import './AddPurchase.css'

function getCameraError(error) {
  if (window.isSecureContext === false) {
    return 'Камера работает только через HTTPS или на localhost.'
  }
  if (error?.name === 'NotAllowedError' || error?.name === 'PermissionDeniedError') {
    return 'Разрешите доступ к камере в браузере и нажмите «Повторить».'
  }
  if (error?.name === 'NotFoundError') {
    return 'Камера не найдена на устройстве.'
  }
  if (error?.name === 'NotReadableError') {
    return 'Камера занята другим приложением.'
  }
  return 'Не удалось включить камеру. Нажмите «Повторить».'
}

function ReceiptScannerModal({ onDecoded, onManualEntry }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const animationFrameRef = useRef(null)
  const detectorRef = useRef(null)
  const isMountedRef = useRef(true)
  const isDecodedRef = useRef(false)

  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')

  function stopCamera() {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    if (videoRef.current) {
      videoRef.current.pause()
      videoRef.current.srcObject = null
    }
  }

  function finish(decodedText) {
    if (isDecodedRef.current) return
    isDecodedRef.current = true
    stopCamera()
    onDecoded(decodedText)
  }

  function scanFrame() {
    const video = videoRef.current
    const detector = detectorRef.current
    if (!video || !detector || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
      animationFrameRef.current = requestAnimationFrame(scanFrame)
      return
    }

    detector
      .detect(video)
      .then((barcodes) => {
        const value = barcodes.find((barcode) => barcode.rawValue)?.rawValue
        if (value) {
          finish(value)
          return
        }
        if (isMountedRef.current) {
          animationFrameRef.current = requestAnimationFrame(scanFrame)
        }
      })
      .catch(() => {
        if (isMountedRef.current) {
          animationFrameRef.current = requestAnimationFrame(scanFrame)
        }
      })
  }

  async function startCamera() {
    stopCamera()
    isDecodedRef.current = false
    setStatus('loading')
    setError('')

    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Этот браузер не поддерживает доступ к камере.')
      setStatus('error')
      return
    }
    if (!('BarcodeDetector' in window)) {
      setError('Браузер не поддерживает распознавание QR-кодов. Откройте Chrome на телефоне.')
      setStatus('error')
      return
    }

    try {
      detectorRef.current = new window.BarcodeDetector({ formats: ['qr_code'] })
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 1280 },
        },
      })

      if (!isMountedRef.current) {
        stream.getTracks().forEach((track) => track.stop())
        return
      }

      streamRef.current = stream
      videoRef.current.srcObject = stream
      await videoRef.current.play()
      setStatus('scanning')
      animationFrameRef.current = requestAnimationFrame(scanFrame)
    } catch (cameraError) {
      setError(getCameraError(cameraError))
      setStatus('error')
    }
  }

  useEffect(() => {
    isMountedRef.current = true
    startCamera()

    return () => {
      isMountedRef.current = false
      stopCamera()
    }
    // Сканер запускается один раз при открытии модального окна.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleManualEntry() {
    stopCamera()
    onManualEntry()
  }

  return (
    <div className="receipt-scanner">
      <video
        ref={videoRef}
        className="receipt-scanner__video"
        autoPlay
        muted
        playsInline
      />

      <div className="receipt-scanner__overlay">
        <div className="receipt-scanner__frame" />
        <p className="receipt-scanner__hint">Наведите камеру на QR-код чека</p>
      </div>

      {status === 'loading' && (
        <div className="receipt-scanner__status">Включаем камеру...</div>
      )}

      {status === 'error' && (
        <div className="receipt-scanner__status receipt-scanner__status--error">
          <p className="receipt-scanner__status-text">{error}</p>
          <button className="receipt-scanner__retry" type="button" onClick={startCamera}>
            Повторить
          </button>
        </div>
      )}

      <button className="receipt-scanner__manual" type="button" onClick={handleManualEntry}>
        Ввести вручную
      </button>
    </div>
  )
}

export default ReceiptScannerModal
