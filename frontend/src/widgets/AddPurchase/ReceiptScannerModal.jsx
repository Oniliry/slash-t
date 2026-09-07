import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { loadScriptOnce } from "../../shared/lib/loadScript.js";

import "./AddPurchase.css";

const HTML5_QRCODE_SRC = "https://cdn.jsdelivr.net/npm/html5-qrcode@2.3.8/html5-qrcode.min.js";
const READER_ELEMENT_ID = "receipt-qr-reader";

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

// Выбирает id камеры через Html5Qrcode.getCameras() (это же вызывает системный
// запрос разрешения). Используется только как запасной путь, если основной
// способ (facingMode: exact "environment", ниже) не сработал: активно избегаем
// камеры с подписью "фронтальная", а не просто берём последнюю в списке.
async function pickCameraId(Html5Qrcode) {
  const cameras = await Html5Qrcode.getCameras();
  if (!cameras || cameras.length === 0) {
    throw new Error("no-camera");
  }
  if (cameras.length === 1) {
    return cameras[0].id;
  }

  const back = cameras.find((camera) => /back|rear|environment|задн/i.test(camera.label ?? ""));
  if (back) return back.id;

  const isFront = (camera) => /front|user|selfie|передн/i.test(camera.label ?? "");
  const nonFront = cameras.filter((camera) => !isFront(camera));
  if (nonFront.length > 0) {
    return nonFront[nonFront.length - 1].id;
  }

  return cameras[cameras.length - 1].id;
}

// Полноэкранный сканер QR-кода чека для мобильной версии. Парсинг содержимого
// (строка вида "t=2026...&s=...") backend пока не поддерживает, поэтому мы
// только считываем сырой текст из QR-кода и отдаём его наружу — без запросов на сервер.
function ReceiptScannerModal({ onDecoded, onManualEntry }) {
  const scannerRef = useRef(null);
  const isFinishingRef = useRef(false);

  const [status, setStatus] = useState("loading"); // 'loading' | 'scanning' | 'error'
  const [error, setError] = useState("");
  const [retryToken, setRetryToken] = useState(0);

  useEffect(() => {
    let isCurrent = true;
    isFinishingRef.current = false;

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

    async function start() {
      setStatus("loading");
      setError("");

      try {
        await loadScriptOnce(HTML5_QRCODE_SRC);
        if (!isCurrent) return;

        const { Html5Qrcode } = window;
        const scanner = new Html5Qrcode(READER_ELEMENT_ID, { verbose: false });
        scannerRef.current = scanner;

        const scanConfig = {
          fps: 10,
          qrbox: { width: 260, height: 260 },
          aspectRatio: 1,
          // Просим повыше разрешение — так мелкий QR-код на чеке проще
          // поймать в фокус.
          videoConstraints: {
            width: { ideal: 1920 },
            height: { ideal: 1080 },
          },
        };
        const onSuccess = (decodedText) => {
          if (isFinishingRef.current) return;
          isFinishingRef.current = true;

          stopScanner().finally(() => {
            if (isCurrent) onDecoded(decodedText);
          });
        };
        const onFailure = () => {
          // Кадр без распознанного QR-кода — обычное дело во время наведения камеры.
        };

        try {
          // Основной путь: жёстко требуем заднюю камеру через facingMode.
          // "exact" не даёт браузеру самому выбрать фронталку, если она
          // почему-то стоит первой в списке устройств.
          await scanner.start(
            { facingMode: { exact: "environment" } },
            scanConfig,
            onSuccess,
            onFailure,
          );
        } catch {
          if (!isCurrent) return;
          // Устройство не поддержало exact-ограничение — ищем заднюю камеру
          // по списку устройств и подписи (id вместо facingMode).
          const cameraId = await pickCameraId(Html5Qrcode);
          if (!isCurrent) return;
          await scanner.start(cameraId, scanConfig, onSuccess, onFailure);
        }

        if (!isCurrent) {
          stopScanner();
          return;
        }

        setStatus("scanning");
      } catch (err) {
        if (!isCurrent) return;
        setError(describeCameraError(err));
        setStatus("error");
      }
    }

    start();

    return () => {
      isCurrent = false;
      stopScanner();
    };
  }, [onDecoded, retryToken]);

  async function handleManualEntry() {
    const scanner = scannerRef.current;
    scannerRef.current = null;
    if (scanner) {
      try {
        await scanner.stop();
      } catch {
        // Не критично — состояние всё равно сбрасывается ниже.
      }
      try {
        await scanner.clear();
      } catch {
        // Аналогично.
      }
    }
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
