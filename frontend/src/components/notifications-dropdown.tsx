import { Bell, CheckCheck } from "lucide-react"
import { Link } from "@tanstack/react-router"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadNotificationCount,
} from "@/hooks/use-notifications"
import { cn } from "@/lib/utils"
import type { Notification } from "@/types/api"

function relativeTime(isoDate: string) {
  const diffMs = Date.now() - new Date(isoDate).getTime()
  const minutes = Math.floor(diffMs / 60_000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function typeDotColor(type: string) {
  if (type === "extraction_failed") return "bg-red-500"
  if (type === "matching_completed") return "bg-emerald-500"
  return "bg-primary"
}

function NotificationRow({ notification, onRead }: { notification: Notification; onRead: (id: string) => void }) {
  const content = (
    <div
      onClick={() => {
        if (!notification.is_read) onRead(notification.id)
      }}
      className={cn(
        "flex cursor-pointer gap-2.5 px-3 py-2.5 hover:bg-background",
        !notification.is_read && "bg-primary/5",
      )}
    >
      <div className={cn("mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full", notification.is_read ? "bg-transparent" : typeDotColor(notification.type))} />
      <div className="min-w-0 flex-1">
        <div className="text-[12.5px] font-semibold text-foreground">{notification.title}</div>
        <div className="mt-0.5 line-clamp-2 text-[12px] text-muted-foreground">{notification.message}</div>
        <div className="mt-1 text-[10.5px] text-slate-400">{relativeTime(notification.created_at)}</div>
      </div>
    </div>
  )

  if (notification.project_id) {
    return (
      <Link to="/projects/$projectId" params={{ projectId: notification.project_id }}>
        {content}
      </Link>
    )
  }
  return content
}

export function NotificationsDropdown() {
  const { data: notifications = [] } = useNotifications()
  const { data: unread } = useUnreadNotificationCount()
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()
  const unreadCount = unread?.count ?? 0

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="relative flex h-8.5 w-8.5 cursor-pointer items-center justify-center rounded-lg hover:bg-slate-100">
          <Bell size={18} strokeWidth={2} className="text-slate-600" />
          {unreadCount > 0 ? (
            <div className="absolute top-1.5 right-2 h-1.75 w-1.75 rounded-full border-[1.5px] border-white bg-red-500" />
          ) : null}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-90 p-0">
        <div className="flex items-center justify-between px-3.5 py-2.5">
          <span className="text-[13px] font-semibold text-foreground">Notifications</span>
          {unreadCount > 0 ? (
            <button
              onClick={() => markAllRead.mutate()}
              className="flex items-center gap-1 text-[11.5px] font-medium text-primary hover:underline"
            >
              <CheckCheck size={12} />
              Mark all read
            </button>
          ) : null}
        </div>
        <div className="max-h-90 overflow-y-auto border-t border-border">
          {notifications.length === 0 ? (
            <p className="px-3.5 py-6 text-center text-[12.5px] text-muted-foreground">No notifications yet</p>
          ) : (
            notifications.map((n) => (
              <NotificationRow key={n.id} notification={n} onRead={(id) => markRead.mutate(id)} />
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
