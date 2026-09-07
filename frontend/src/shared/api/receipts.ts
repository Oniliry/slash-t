import { request } from './base'
import type { APIResponse } from './types'

/** Ответ бэкенда на сканирование QR чека: сырой ответ code-qr.ru внутри raw. */
export interface ReceiptScanResponse {
  hash: string
  status: string
  raw: string
}

/**
 * Отправляет raw-строку из QR-кода чека на бэкенд, который передаёт её
 * сервису code-qr.ru и возвращает хэш, статус проверки и сырой ответ.
 */
export function scanReceipt(qr: string): Promise<APIResponse<ReceiptScanResponse>> {
  return request<ReceiptScanResponse>('/receipts/scan', {
    method: 'POST',
    body: JSON.stringify({ qr }),
  })
}
