import { API_URL, getStoredToken, request } from './base'
import type { APIResponse } from './types'

export interface StatementTx {
  tx_id: string
  date: string
  group: string
  counterparty: string
  amount: number
  is_regular: boolean
  is_active: boolean
  is_transfer: boolean
  transfer_label: string | null
  include_in_cushion: boolean
}

export interface TransferCandidate {
  counterparty: string
  amount: number
  occurrences: number
}

export interface StatementAnalysis {
  full_months: string[]
  excluded_months: string[]
  months_analyzed: number
  transactions: StatementTx[]
  transfer_candidates: TransferCandidate[]
}

export interface StatementGroup {
  name: string
  monthly_amount: number
  ops_count: number
  total_amount: number
  description: string
  operations: string[]
}

export interface StatementRecalcRequest {
  months_analyzed?: number | null
  full_months: string[]
  excluded_months: string[]
  transactions: StatementTx[]
}

export interface StatementRecalcResult {
  months_analyzed: number
  cushion_total: number
  groups: StatementGroup[]
  excluded_groups: StatementGroup[]
}

export interface FamilyCushionRatingItem {
  user_id: number
  user_name: string
  cushion_total: number
  months_analyzed: number | null
}

export async function uploadStatement(
  file: File,
): Promise<APIResponse<StatementAnalysis>> {
  // Отдельный fetch для multipart: Content-Type с boundary выставляет
  // браузер, поэтому общий request() (жёстко ставящий application/json)
  // для FormData не подходит.
  try {
    const headers: Record<string, string> = {}
    const token = getStoredToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const response = await fetch(
      `${API_URL}/financial-cushion/upload-statement`,
      {
        method: 'POST',
        headers,
        body: buildStatementFormData(file),
      },
    )

    const rawPayload = await response.json()
    const payload = rawPayload as APIResponse<StatementAnalysis> & {
      detail?: Array<{ msg?: string }>
    }

    if (!response.ok) {
      const validationMessage = payload.detail
        ?.map((item) => item.msg)
        .filter(Boolean)
        .join(' ')

      return {
        error: true,
        message:
          payload.message ?? validationMessage ?? 'Ошибка запроса к серверу.',
        data: null,
        type: payload.type ?? `http_${response.status}`,
      }
    }

    return payload
  } catch {
    return {
      error: true,
      message: 'Не удалось подключиться к серверу.',
      data: null,
      type: 'network_error',
    }
  }
}

export function recalculateStatement(
  payload: StatementRecalcRequest,
): Promise<APIResponse<StatementRecalcResult>> {
  return request<StatementRecalcResult>('/financial-cushion/recalculate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getLastAnalysis(): Promise<APIResponse<StatementAnalysis | null>> {
  return request<StatementAnalysis | null>('/financial-cushion/last', {
    method: 'GET',
  })
}

export function getFamilySummary(): Promise<APIResponse<FamilyCushionRatingItem[]>> {
  return request<FamilyCushionRatingItem[]>('/financial-cushion/family-summary', {
    method: 'GET',
  })
}

export function resetLastAnalysis(): Promise<APIResponse<null>> {
  return request<null>('/financial-cushion/last', {
    method: 'DELETE',
  })
}

function buildStatementFormData(file: File): FormData {
  const formData = new FormData()
  formData.append('file', file, file.name || 'statement.pdf')
  return formData
}
