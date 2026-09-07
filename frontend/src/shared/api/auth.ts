import { request } from './base'
import type { APIResponse } from './types'

export type UserRole = 'adult' | 'child'

export interface User {
  id: number;
  name: string;
  login: string;
  created_at: string;
  family_id: number | null;
  role: UserRole | null;
  monthly_income: number | null;
}

export interface AuthResult {
  user: User;
  access_token: string;
}

export interface RegisterUserRequest {
  name: string;
  login: string;
  password: string;
}

export interface LoginUserRequest {
  login: string;
  password: string;
}

export async function registerUser(
  data: RegisterUserRequest,
): Promise<APIResponse<AuthResult>> {
  const response = await request<AuthResult>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  })

  return response
}

export async function loginUser(
  data: LoginUserRequest,
): Promise<APIResponse<AuthResult>> {
  const response = await request<AuthResult>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })

  return response
}

export function getCurrentUser(): Promise<APIResponse<User>> {
  return request<User>('/auth/me', {
    method: 'POST',
  })
}

export async function logoutUser(): Promise<APIResponse<null>> {
  return request<null>('/auth/logout', {
    method: 'POST',
  })
}
