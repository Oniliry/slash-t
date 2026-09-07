import { request } from './base'
import type { APIResponse } from './types'

export interface ParsedReceiptItem {
  name: string;
  sum: number;
  category: string;
  personal: boolean;
}

export interface ParsedReceiptResponse {
  shop: string | null;
  items: ParsedReceiptItem[];
}

export function parseReceiptPhoto(
  imageBase64: string,
  mimeType: string,
): Promise<APIResponse<ParsedReceiptResponse>> {
  return request<ParsedReceiptResponse>('/receipts/parse-photo', {
    method: 'POST',
    body: JSON.stringify({ image_base64: imageBase64, mime_type: mimeType }),
  })
}
