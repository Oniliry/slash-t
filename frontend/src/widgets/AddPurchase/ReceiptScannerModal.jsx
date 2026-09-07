import { useEffect, useRef, useState } from "react";

import { loadScriptOnce } from "../../shared/lib/loadScript.js";

import "./AddPurchase.css";

// html5-qrcode — готовое, широко используемое решение для сканирования
// QR-кодов прямо в браузере (обёртка над getUserMedia). Грузим с CDN, чтобы
// не тащить лишнюю зависимость в сборку. Раньше здесь был битый адрес
// ("https://jsdelivr.net" без пути до самого файла), из-за чего скрипт
// физически не загружался — почтено настоящий адрес файла библиотеки.
const HTML5_QRCODE_SRC =
  "https://cdnjs.cloudflare.com/ajax/libs/html5-qrcode/2.3.8/html5-qrcode.min.js";
const READER_ELEMENT_ID = "receipt-qr-reader";

// Чистый, облегченный конфиг без ограничений, ломающих Safari
const SCAN_CONFIG = {
  fps: 10,
  qrbox: { width: 260, height: 260 },
  aspectRatio: 1,
};

// Готовое решение "из коробки": просим у браузера именно заднюю камеру
// через стандартный WebRTC-constraint facingMode. html5-qrcode умеет
// принимать такой объект напрямую в start() вместо конкретного deviceId —
// это ровно то, что задокументировано в самой библиотеке для выбора
// задней/фронтальной камеры, и надёжнее, чем угадывать камеру по названию
// устройства (на части телефонов и особенно до выдачи разрешения на
// камеру label может быть пустым или не содержать слов "back"/"rear").
const REAR_CAMERA_CONSTRAINT = { facingMode: { ideal: "environment" } };

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

// Резервный вариант на случай, если у устройства вообще нет задней камеры
// (например, ноутбук с одной фронтальной веб-камерой) и facingMode
// "environment" не смог подобрать поток — тогда просто перечисляем все
// камеры и стараемся угадать заднюю по названию, а если не вышло, берём
// последнюю в списке (на телефонах это почти всегда основная задняя).
function pickFallbackCameraIndex(cameras) {
  const backIndex = cameras.findIndex((camera) => /back|rear|environment|задн|основн/i.test(camera.label ?? ""));
  if (backIndex !== -1) return backIndex;

  if (cameras.length > 1) {
    return cameras.length - 1;
  }
  return 0;
}

function ReceiptScannerModal({ onDecoded, onManualEntry }) {
  const scannerRef = useRef(null);
  const camerasRef = useRef([]);
  const cameraIndexRef = useRef(-1);
  const isFinishingRef = useRef(false);
  const isMountedRef = useRef(true);

  const [status, setStatus] = useState("loading"); // 'loading' | 'scanning' | 'error'
  const [error, setError] = useState("");
  const [retryToken, setRetryToken] = useState(0);
  const [cameraCount, setCameraCount] = useState(0);

  async function stopScanner() {
    const scanner = scannerRef.current;
    scannerRef.current = null;
    if (!scanner) return;

    try {
      await scanner.stop();
    } catch {
      // Игнорируем
    }
    try {
      await scanner.clear();
    } catch {
      // Игнорируем
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
    // Обычный пропуск кадра без QR-кода
  }

  // Пытается запустить сканер сразу с задней камерой через constraint.
  // Если на устройстве такой камеры нет (или браузер не поддерживает
  // constraint в этом месте API), откатывается к перечислению камер.
  async function startWithRearCamera(scanner) {
    try {
      await scanner.start(REAR_CAMERA_CONSTRAINT, SCAN_CONFIG, handleDecoded, handleScanFailure);
      cameraIndexRef.current = -1;
      return;
    } catch {
      // Продолжаем ниже — пробуем через явный список камер.
    }

    const { Html5Qrcode } = window;
    const cameras = await Html5Qrcode.getCameras();
    if (!cameras || cameras.length === 0) {
      throw new Error("no-camera");
    }
    camerasRef.current = cameras;

    const index = pickFallbackCameraIndex(cameras);
    await scanner.start(cameras[index].id, SCAN_CONFIG, handleDecoded, handleScanFailure);
    cameraIndexRef.current = index;
  }

  useEffect(() => {
    isMountedRef.current = true;
    isFinishingRef.current = false;
    let timeoutId = null;

    async function init() {
      setStatus("loading");
      setError("");

      try {
        await loadScriptOnce(HTML5_QRCODE_SRC);
        if (!isMountedRef.current) return;

        // Даем React 300мс полностью смонтировать div в DOM перед тем, как html5-qrcode начнет его искать
        timeoutId = setTimeout(async () => {
          try {
            const element = document.getElementById(READER_ELEMENT_ID);
            if (!element) {
              throw new Error("DOM element not found yet");
            }

            const { Html5Qrcode } = window;
            const scanner = new Html5Qrcode(READER_ELEMENT_ID, { verbose: false });
            scannerRef.current = scanner;

            await startWithRearCamera(scanner);

            if (!isMountedRef.current) {
              stopScanner();
              return;
            }

            // Список камер нужен только для необязательной кнопки
            // переключения — на большинстве телефонов с одной задней
            // камерой она просто не отобразится.
            if (camerasRef.current.length === 0) {
              try {
                camerasRef.current = await Html5Qrcode.getCameras();
              } catch {
                camerasRef.current = [];
              }
            }
            if (isMountedRef.current) setCameraCount(camerasRef.current.length);

            setStatus("scanning");
          } catch (err) {
            if (!isMountedRef.current) return;
            setError(describeCameraError(err));
            setStatus("error");
          }
        }, 300);

      } catch (err) {
        if (!isMountedRef.current) return;
        setError(describeCameraError(err));
        setStatus("error");
      }
    }

    init();

    return () => {
      isMountedRef.current = false;
      if (timeoutId) clearTimeout(timeoutId);
      stopScanner();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retryToken]);

  async function handleSwitchCamera() {
    const cameras = camerasRef.current;
    const scanner = scannerRef.current;
    if (!scanner || cameras.length < 2) return;

    const nextIndex = (cameraIndexRef.current + 1) % cameras.length;

    try {
      await scanner.stop();
    } catch {
      // Игнорируем
    }

    try {
      await scanner.start(cameras[nextIndex].id, SCAN_CONFIG, handleDecoded, handleScanFailure);
      cameraIndexRef.current = nextIndex;
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

  return (
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
    </div>
  );
}

export default ReceiptScannerModal;
