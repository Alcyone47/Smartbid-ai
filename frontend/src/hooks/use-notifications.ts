import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { notificationsApi } from "@/api/notifications"

export const notificationsKey = ["notifications"] as const
export const unreadCountKey = ["notifications", "unread-count"] as const

export function useNotifications() {
  return useQuery({
    queryKey: notificationsKey,
    queryFn: () => notificationsApi.list(),
    refetchInterval: 30_000,
  })
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: unreadCountKey,
    queryFn: () => notificationsApi.unreadCount(),
    refetchInterval: 30_000,
  })
}

function useInvalidateNotifications() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: notificationsKey })
    queryClient.invalidateQueries({ queryKey: unreadCountKey })
  }
}

export function useMarkNotificationRead() {
  const invalidate = useInvalidateNotifications()
  return useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: invalidate,
  })
}

export function useMarkAllNotificationsRead() {
  const invalidate = useInvalidateNotifications()
  return useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: invalidate,
  })
}
