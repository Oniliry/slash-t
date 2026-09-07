import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { loadScriptOnce } from "../../shared/lib/loadScript.js";

import "./AddPurchase.css";

const HTML5_QRCODE_SRC = "https://jsdelivr.net";
const READER_ELEMENT_ID = "receipt-qr-reader";

// Упрощаем конфиг: убираем жесткие рамки разрешения ideal: 1920, 
// из-за которых Safari на iOS часто молча зависает или падает.
const SCAN_CONFIG = {
  fps: 15,
  qrbox: { width: 260, height: 260 },
  aspectRatio: 1
};

// Пытается понять, что именно пошло не так с камерой, и вернуть понятную
// пользователю причину — вместо одной общей фразы на все случаи.
function describeCameraError(err) {
  if (typeof window !== "undefined" && window.isSecureContext === false) {
    return "Камера доступна только по защищённому соединению (https). Откройте сайт по ссылке, начинающейся с https://.";
  }

  if (typeof navigator !== "undefined" && !navigator.mediaDevices) {
    return "Этот браузер не поддерживает доступ к камере на данной странице.";
  }

  const name = err?.name || "";
  const message = err?.message || String(err ?? "");

  if (name === "NotAllowedError" || name === "PermissionDeniedError") {
    return "Доступ к камере запрещён. Разрешите доступ к камере для этого сайта в настройках браузера (или телефона) и нажмите «Повторить».";
  }
  if (name === "NotFoundError" || name === "DevicesNotFoundError" || message === "no-camera") {
    return "На устройстве не нашлась камера.";
  }
  if (name === "NotReadableError" || name === "TrackStartError") {
    return "Камера занята другим приложением или вкладкой. Закройте его и нажмите «Повторить».";
  }
  if (name === "OverconstrainedError" || name === "ConstraintNotSatisfiedError") {
    return "Камера устройства не поддерживает нужный режим съёмки.";
  }
  if (name === "SecurityError") {
    return "Браузер заблокировал доступ к камере на этой странице по соображениям безопасности.";
  }

  return "Не удалось включить камеру. Проверьте разрешение на доступ к камере в браузере и нажмите «Повторить».";
}

// Надежный выбор индекса задней камеры.
function pickInitialCameraIndex(cameras) {
  // Ищем камеру, в названии которой есть признаки задней
  const backIndex = cameras.findIndex((camera) => /back|rear|environment|задн|основн/i.test(camera.label ?? ""));
  if (backIndex !== -1) return backIndex;

  // Если названий нет (браузер скрыл до старта), то на iOS/Android 
  // в 99% случаев первая камера в списке (индекс 0) — это фронталка, 
  // а ПОСЛЕДНЯЯ камера в списке — это основная задняя.
  if (cameras.length > 1) {
    return cameras.length - 1; 
  }

  return 0;
}

// Полноэкранный сканер QR-кода чека для мобильной версии.
function ReceiptScannerModal({ onDecoded, onManualEntry }) {
  const scannerRef = useRef(null);
  const camerasRef = useRef([]);
  const isFinishingRef = useRef(false);
  const isMountedRef = useRef(true);

  const [status, setStatus] = useState("loading"); // 'loading' | 'scanning' | 'error'
  const [error, setError] = useState("");
  const [retryToken, setRetryToken] = useState(0);
  const [cameraIndex, setCameraIndex] = useState(0);
  const [cameraCount, setCameraCount] = useState(0);

  async function stopScanner() {
    const scanner = scannerRef.current;
    scannerRef.current = null;
    if (!scanner) return;

    try {
      await scanner.stop();
    } catch {
      // Сканер мог быть уже остановлен или не успел стартовать — не ошибка.
    }
    try {
      await scanner.clear();
    } catch {
      // Аналогично — очищать нечего.
    }
  }

  function handleDecoded(decodedText) {
    if (isFinishingRef.current) return;
    isFinishingRef.current = true;

    stopScanner().finally(() => {
      if (isMountedRef.current) onDecoded(decodedText);
    });
  }

  function handleScanFailure() {
    // Кадр без распознанного QR-кода — обычное дело во время наведения камеры.
  }

  useEffect(() => {
    isMountedRef.current = true;
    isFinishingRef.current = false;

    async function init() {
      setStatus("loading");
      setError("");

      try {
        await loadScriptOnce(HTML5_QRCODE_SRC);
        if (!isMountedRef.current) return;

        const { Html5Qrcode } = window;
        const scanner = new Html5Qrcode(READER_ELEMENT_ID, { verbose: false });
        scannerRef.current = scanner;

        // Сначала запрашиваем список камер
        const cameras = await Html5Qrcode.getCameras();
        if (!cameras || cameras.length === 0) {
          throw new Error("no-camera");
        }
        camerasRef.current = cameras;
        if (!isMountedRef.current) return;
        setCameraCount(cameras.length);

        // Определяем индекс задней камеры по нашему умному алгоритму
        const initialIndex = pickInitialCameraIndex(cameras);
        setCameraIndex(initialIndex);

        // Запускаем по конкретному ID устройства (это самый стабильный вариант для iOS Safari)
        await scanner.start(
          cameras[initialIndex].id,
          SCAN_CONFIG,
          handleDecoded,
          handleScanFailure
        );

        if (!isMountedRef.current) {
          stopScanner();
          return;
        }

        setStatus("scanning");
      } catch (err) {
        console.error("Camera init error:", err);
        if (!isMountedRef.current) return;
        setError(describeCameraError(err));
        setStatus("error");
      }
    }

    init();

    return () => {
      isMountedRef.current = false;
      stopScanner();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retryToken]);

  async function handleSwitchCamera() {
    const cameras = camerasRef.current;
    const scanner = scannerRef.current;
    if (!scanner || cameras.length < 2) return;

    const nextIndex = (cameraIndex + 1) % cameras.length;

    try {
      await scanner.stop();
    } catch {
      // Не критично — всё равно пробуем запустить следующую камеру ниже.
    }

    try {
      await scanner.start(cameras[nextIndex].id, SCAN_CONFIG, handleDecoded, handleScanFailure);
      setCameraIndex(nextIndex);
      setStatus("scanning");
    } catch (err) {
      setError(describeCameraError(err));
      setStatus("error");
    }
  }

  async function handleManualEntry() {
    await stopScanner();
    onManualEntry();
  }

  function handleRetry() {
    setRetryToken((token) => token + 1);
  }

  return createPortal(
    <div className="receipt-scanner">
      <div id={READER_ELEMENT_ID} className="receipt-scanner__video" />

      <div className="receipt-scanner__overlay">
        <div className="receipt-scanner__frame" />
        <p className="receipt-scanner__hint">Наведите камеру на QR-код чека</p>
      </div>

      {status === "scanning" && cameraCount > 1 && (
        <button
          className="receipt-scanner__switch"
          type="button"
          onClick={handleSwitchCamera}
          aria-label="Сменить камеру"
        >
          ⟳ Сменить камеру
        </button>
      )}

      {status === "loading" && (
        <div className="receipt-scanner__status">Включаем камеру...</div>
      )}

      {status === "error" && (
        <div className="receipt-scanner__status receipt-scanner__status--error">
          <p className="receipt-scanner__status-text">{error}</p>
          <button className="receipt-scanner__retry" type="button" onClick={handleRetry}>
            Повторить
          </button>
        </div>
      )}

      <button
        className="receipt-scanner__manual"
        type="button"
        onClick={handleManualEntry}
      >
        Ввести вручную
      </button>
    </div>,
    document.body,
  );
}

export default ReceiptScannerModal;
