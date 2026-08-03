import { apiRequest } from "@/lib/api-client"
import type { Notification } from "@/types/api"

export const notificationsApi = {
  list: (limit = 20) => apiRequest<Notification[]>(`/api/v1/notifications?limit=${limit}`),
  unreadCount: () => apiRequest<{ count: number }>("/api/v1/notifications/unread-count"),
  markRead: (id: string) => apiRequest<Notification>(`/api/v1/notifications/${id}/read`, { method: "POST" }),
  markAllRead: () => apiRequest<{ marked: number }>("/api/v1/notifications/read-all", { method: "POST" }),
}
