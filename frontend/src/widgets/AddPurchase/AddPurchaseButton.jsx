import { useState } from 'react'

import AddPurchaseModal from './AddPurchaseModal.jsx'
import ReceiptScanner from './ReceiptScanner.jsx'

import './AddPurchase.css'

// Брейкпоинт совпадает с CSS-брейкпоинтом таббара (MainLayout.css):
// на мобильном «+» открывает сканер чека, на десктопе — ручную форму.
const MOBILE_QUERY = '(max-width: 700px)'

function AddPurchaseButton({ variant = 'navbar' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isScannerOpen, setIsScannerOpen] = useState(false)

  function handleCreated() {
    // Другие виджеты (например, долги на главной) слушают это событие,
    // чтобы обновиться сразу после добавления новой покупки.
    window.dispatchEvent(new CustomEvent('slash-t:expense-created'))
  }

  function handleClick() {
    if (window.matchMedia(MOBILE_QUERY).matches) {
      setIsScannerOpen(true)
    } else {
      setIsOpen(true)
    }
  }

  const className =
    variant === 'tabbar' ? 'tab-bar__add' : 'navbar__add'

  return (
    <>
      <button
        className={className}
        type="button"
        onClick={handleClick}
        aria-label="Добавить покупку"
        title="Добавить покупку"
      >
        {variant === 'tabbar' ? <span className="tab-bar__add-icon">+</span> : '+'}
      </button>

      {isOpen && (
        <AddPurchaseModal onClose={() => setIsOpen(false)} onCreated={handleCreated} />
      )}

      {isScannerOpen && (
        <ReceiptScanner
          onClose={() => setIsScannerOpen(false)}
          onManual={() => {
            setIsScannerOpen(false)
            setIsOpen(true)
          }}
        />
      )}
    </>
  )
}

export default AddPurchaseButton
