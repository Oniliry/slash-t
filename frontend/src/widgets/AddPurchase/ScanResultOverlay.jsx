import { createPortal } from "react-dom";

import "./AddPurchase.css";

// Показывает сырую расшифрованную строку из QR-кода чека (формат вида
// "t=2026...&s=..."). Запросов на бэкенд не делает — бэкенд для чеков ещё не готов.
function ScanResultOverlay({ text, onClose }) {
  return createPortal(
    <div className="scan-result">
      <button
        className="scan-result__close"
        type="button"
        onClick={onClose}
        aria-label="Закрыть"
      >
        ×
      </button>

      <div className="scan-result__body">
        <p className="scan-result__label">Данные из QR-кода чека</p>
        <pre className="scan-result__text">{text}</pre>
      </div>
    </div>,
    document.body,
  );
}

export default ScanResultOverlay;
