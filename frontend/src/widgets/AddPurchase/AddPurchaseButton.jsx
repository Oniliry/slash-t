import { useState } from 'react'

import AddPurchaseModal from './AddPurchaseModal.jsx'

import './AddPurchase.css'

function AddPurchaseButton({ variant = 'navbar' }) {
  const [isOpen, setIsOpen] = useState(false)

  function handleCreated() {
    // Другие виджеты (например, долги на главной) слушают это событие,
    // чтобы обновиться сразу после добавления новой покупки.
    window.dispatchEvent(new CustomEvent('slash-t:expense-created'))
  }

  if (variant === 'tabbar') {
    return (
      <>
        <button
          className="tab-bar__add"
          type="button"
          onClick={() => setIsOpen(true)}
          aria-label="Добавить покупку"
        >
          <span className="tab-bar__add-icon">+</span>
        </button>
        {isOpen && (
          <AddPurchaseModal onClose={() => setIsOpen(false)} onCreated={handleCreated} />
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
        aria-label="Добавить покупку"
        title="Добавить покупку"
      >
        +
      </button>
      {isOpen && (
        <AddPurchaseModal onClose={() => setIsOpen(false)} onCreated={handleCreated} />
      )}
    </>
  )
}

export default AddPurchaseButton
