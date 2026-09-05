import { request } from './base'
import type { APIResponse } from './types'

export interface User {
  id: number;
  name: string;
  login: string;
  created_at: string;
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

export function registerUser(
  data: RegisterUserRequest,
): Promise<APIResponse<User>> {
  return request<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function loginUser(
  data: LoginUserRequest,
): Promise<APIResponse<User>> {
  return request<User>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getCurrentUser(): Promise<APIResponse<User>> {
  return request<User>('/auth/me', {
    method: 'POST',
  })
}

export function logoutUser(): Promise<APIResponse<null>> {
  return request<null>('/auth/logout', {
    method: 'POST',
  })
}