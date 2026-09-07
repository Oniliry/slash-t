import { useState } from 'react'

import AddPurchaseModal from './AddPurchaseModal.jsx'
import ReceiptPhotoScreen from './ReceiptPhotoScreen.jsx'
import ReceiptReviewScreen from './ReceiptReviewScreen.jsx'

import './AddPurchase.css'

function AddPurchaseButton({ variant = 'navbar' }) {
  // 'closed' | 'photo' | 'manual' | 'review' — одинаковый флоу и на ПК, и на телефоне.
  const [mode, setMode] = useState('closed')
  const [parsed, setParsed] = useState(null)

  function handleCreated() {
    window.dispatchEvent(new CustomEvent('slash-t:expense-created'))
  }

  function closeFlow() {
    setMode('closed')
    setParsed(null)
  }

  const buttonProps =
    variant === 'tabbar'
      ? { className: 'tab-bar__add', children: <span className="tab-bar__add-icon">+</span> }
      : { className: 'navbar__add', children: '+', title: 'Добавить покупку' }

  return (
    <>
      <button
        type="button"
        onClick={() => setMode('photo')}
        aria-label="Добавить покупку"
        {...buttonProps}
      />

      {mode === 'photo' && (
        <ReceiptPhotoScreen
          onClose={closeFlow}
          onManualEntry={() => setMode('manual')}
          onParsed={(data) => {
            setParsed(data)
            setMode('review')
          }}
        />
      )}

      {mode === 'manual' && (
        <AddPurchaseModal onClose={closeFlow} onCreated={handleCreated} />
      )}

      {mode === 'review' && parsed && (
        <ReceiptReviewScreen
          shop={parsed.shop}
          items={parsed.items}
          onClose={closeFlow}
          onCreated={handleCreated}
        />
      )}
    </>
  )
}

export default AddPurchaseButton
