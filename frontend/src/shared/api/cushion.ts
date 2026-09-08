import { request } from './base'
import type { APIResponse } from './types'

export type CushionOperationKind = 'topup' | 'withdraw'

export interface CushionOperation {
  id: number
  kind: CushionOperationKind
  amount: number
  comment: string | null
  user_name: string | null
  created_at: string
}

export interface CushionGoal {
  target_amount: number
  months: number
  progress_percent: number
}

export interface CushionState {
  balance: number
  monthly_expenses: number
  goal: CushionGoal | null
  operations: CushionOperation[]
}

export interface CushionOperationRequest {
  amount: number
  comment?: string | null
}

export interface SetCushionGoalRequest {
  target_amount: number
  months: number
}

export function getCushionState(): Promise<APIResponse<CushionState>> {
  return request<CushionState>('/cushion', {
    method: 'GET',
  })
}

export function topUpCushion(
  data: CushionOperationRequest,
): Promise<APIResponse<CushionState>> {
  return request<CushionState>('/cushion/top-up', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function withdrawCushion(
  data: CushionOperationRequest,
): Promise<APIResponse<CushionState>> {
  return request<CushionState>('/cushion/withdraw', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function setCushionGoal(
  data: SetCushionGoalRequest,
): Promise<APIResponse<CushionState>> {
  return request<CushionState>('/cushion/goal', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
