import { request, setStoredToken, getStoredToken } from './base'
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

  if (!response.error && response.data) {
    setStoredToken(response.data.access_token)
  }

  return response
}

export async function loginUser(
  data: LoginUserRequest,
): Promise<APIResponse<AuthResult>> {
  const response = await request<AuthResult>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })

  if (!response.error && response.data) {
    setStoredToken(response.data.access_token)
  }

  return response
}

export function getCurrentUser(): Promise<APIResponse<User>> {
  // Если в этой вкладке токена нет — сразу считаем пользователя
  // неавторизованным, не дожидаясь ответа сервера.
  if (!getStoredToken()) {
    return Promise.resolve({
      error: true,
      message: 'Пользователь не авторизован.',
      data: null,
      type: 'authentication_required',
    })
  }

  return request<User>('/auth/me', {
    method: 'POST',
  })
}

export async function logoutUser(): Promise<APIResponse<null>> {
  const response = await request<null>('/auth/logout', {
    method: 'POST',
  })

  // Токен этой вкладки удаляем в любом случае — даже если запрос не дошёл до сервера.
  setStoredToken(null)

  return response
}
