import { request } from './base'

export interface NotificationItem {
  kind: 'personal' | 'family' | 'advice';
  text: string;
}

export function getNotifications(): Promise<{ error: boolean; message?: string; data: NotificationItem[] | null; type?: string }> {
  const refreshToken = Date.now()
  return request<NotificationItem[]>(`/notifications/me?refresh=${refreshToken}`, {
    method: 'GET',
    cache: 'no-store',
  })
}

export function getAiNotification(): Promise<{ error: boolean; message?: string; data: NotificationItem | null; type?: string }> {
  const refreshToken = Date.now()
  return request<NotificationItem>(`/notifications/me/advice?refresh=${refreshToken}`, {
    method: 'GET',
    cache: 'no-store',
  })
}
