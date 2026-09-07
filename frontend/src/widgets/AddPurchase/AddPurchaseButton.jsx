import { useState } from 'react'

import AddPurchaseModal from './AddPurchaseModal.jsx'
import ReceiptScannerModal from './ReceiptScannerModal.jsx'
import ScanResultOverlay from './ScanResultOverlay.jsx'

import './AddPurchase.css'

function AddPurchaseButton({ variant = 'navbar' }) {
  // ПК: открыта ли форма ручного ввода (поведение не меняется).
  const [isOpen, setIsOpen] = useState(false)

  // Мобайл: 'idle' -> 'scanner' -> 'result' | 'manual'.
  const [mobileMode, setMobileMode] = useState('idle')
  const [scannedText, setScannedText] = useState('')

  function handleCreated() {
    // Другие виджеты (например, долги на главной) слушают это событие,
    // чтобы обновиться сразу после добавления новой покупки.
    window.dispatchEvent(new CustomEvent('slash-t:expense-created'))
  }

  function resetMobileFlow() {
    setScannedText('')
    setMobileMode('idle')
  }

  if (variant === 'tabbar') {
    return (
      <>
        <button
          className="tab-bar__add"
          type="button"
          onClick={() => setMobileMode('scanner')}
          aria-label="Добавить трату"
        >
          <span className="tab-bar__add-icon">+</span>
        </button>

        {mobileMode === 'scanner' && (
          <ReceiptScannerModal
            onDecoded={(text) => {
              setScannedText(text)
              setMobileMode('result')
            }}
            onManualEntry={() => setMobileMode('manual')}
          />
        )}

        {mobileMode === 'result' && (
          <ScanResultOverlay text={scannedText} onClose={resetMobileFlow} />
        )}

        {mobileMode === 'manual' && (
          <AddPurchaseModal onClose={resetMobileFlow} onCreated={handleCreated} />
        )}
      </>
    )
  }

  return (
    <>
      <button
        className="navbar__add"
        type="button"
        onClick={() => setIsOpen(true)}
        aria-label="Добавить трату"
        title="Добавить трату"
      >
        <span className="navbar__add-icon" aria-hidden="true">+</span>
        <span>Добавить трату</span>
      </button>
      {isOpen && (
        <AddPurchaseModal onClose={() => setIsOpen(false)} onCreated={handleCreated} />
      )}
    </>
  )
}

export default AddPurchaseButton
