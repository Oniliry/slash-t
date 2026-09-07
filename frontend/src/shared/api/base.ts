import type { APIResponse } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Токен сессии хранится в sessionStorage, а не в cookie. sessionStorage
// изолирован для каждой вкладки браузера (в отличие от cookie, общей на весь
// домен) — благодаря этому вход в аккаунт в одной вкладке не переключает
// (и не сбрасывает) сессию в других открытых вкладках сайта.
const TOKEN_STORAGE_KEY = 'slash-t:access_token'

export function getStoredToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    // sessionStorage может быть недоступен (приватный режим, ограничения браузера) —
    // тогда просто работаем без сохранённого токена.
    return null
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) {
      sessionStorage.setItem(TOKEN_STORAGE_KEY, token)
    } else {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  } catch {
    // Ничего страшного — просто не сохранится между запросами в рамках вкладки.
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<APIResponse<T>> {
  try {
    const token = getStoredToken()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> | undefined),
    }
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    })

    const rawPayload = await response.json()
    const payload = rawPayload as APIResponse<T> & {
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
