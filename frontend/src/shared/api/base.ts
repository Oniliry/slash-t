import type { APIResponse } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<APIResponse<T>> {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> | undefined),
    }

    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      credentials: 'include',
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
