import { request } from './base'
import type { APIResponse } from './types'
import type { User } from './auth'

export interface UpdateNameRequest {
  name: string;
}

export interface UpdateIncomeRequest {
  monthly_income: number;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export function updateName(data: UpdateNameRequest): Promise<APIResponse<User>> {
  return request<User>('/profile/name', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function updateIncome(data: UpdateIncomeRequest): Promise<APIResponse<User>> {
  return request<User>('/profile/income', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function changePassword(
  data: ChangePasswordRequest,
): Promise<APIResponse<null>> {
  return request<null>('/profile/password', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}
