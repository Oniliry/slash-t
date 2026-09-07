// Подгружает внешний скрипт (например, html5-qrcode с CDN) один раз и кэширует
// промис — повторные вызовы с тем же src просто дожидаются того же скрипта.
const loadedScripts = new Map();

export function loadScriptOnce(src) {
  if (loadedScripts.has(src)) {
    return loadedScripts.get(src);
  }

  const promise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      if (existing.dataset.loaded === "true") {
        resolve();
        return;
      }
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () =>
        reject(new Error(`Не удалось загрузить скрипт: ${src}`)),
      );
      return;
    }

    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = () => {
      script.dataset.loaded = "true";
      resolve();
    };
    script.onerror = () => {
      reject(new Error(`Не удалось загрузить скрипт: ${src}`));
    };
    document.head.appendChild(script);
  });

  loadedScripts.set(src, promise);
  return promise;
}
