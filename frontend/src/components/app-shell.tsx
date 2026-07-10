import type { ReactNode } from "react"
import { Link, useNavigate, useRouterState } from "@tanstack/react-router"
import { LayoutDashboard, Briefcase, Building2, FileBarChart, Settings, Search, Bell, ChevronDown } from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Projects", icon: Briefcase },
  { to: "/vendors", label: "Vendors", icon: Building2 },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/settings", label: "Settings", icon: Settings },
]

function initialsFromEmail(email: string | undefined) {
  if (!email) return "?"
  return email.slice(0, 2).toUpperCase()
}

export function AppShell({ children }: { children: ReactNode }) {
  const { session, signOut } = useAuth()
  const navigate = useNavigate()
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  const handleSignOut = async () => {
    await signOut()
    navigate({ to: "/login" })
  }

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 flex h-screen w-[236px] shrink-0 flex-col border-r border-border bg-card">
        <div className="flex items-center gap-2.5 px-5 pt-5 pb-4.5">
          <div className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-lg bg-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" fill="#fff" />
            </svg>
          </div>
          <span className="text-[15.5px] font-bold tracking-tight text-foreground">SmartBid AI</span>
        </div>

        <nav className="mt-1.5 flex flex-col gap-0.5 px-3">
          {NAV_ITEMS.map((item) => {
            const isActive = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to)
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] font-medium text-slate-700 transition-colors",
                  isActive && "bg-secondary font-semibold text-primary",
                )}
              >
                <item.icon size={17} strokeWidth={2} color={isActive ? "#2563EB" : "#64748B"} />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="mt-auto flex items-center gap-2.5 border-t border-slate-100 px-5 py-3.5">
          <div className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-lg bg-secondary text-[12.5px] font-bold text-primary">
            {initialsFromEmail(session?.user.email)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-[13px] font-semibold text-foreground">
              {session?.user.user_metadata?.first_name
                ? `${session.user.user_metadata.first_name} ${session.user.user_metadata.last_name ?? ""}`
                : session?.user.email}
            </div>
            <button
              onClick={handleSignOut}
              className="text-[11.5px] text-muted-foreground hover:text-foreground"
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-[60px] shrink-0 items-center justify-between border-b border-border bg-card px-6">
          <div className="relative w-[340px]">
            <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground" />
            <input
              placeholder="Search projects, vendors, requirements…"
              className="w-full rounded-lg border border-border bg-background py-2 pr-3 pl-8.5 text-[13.5px] text-foreground focus:border-primary focus:bg-white focus:ring-3 focus:ring-primary/10 focus:outline-none"
            />
          </div>
          <div className="flex items-center gap-4">
            <div className="relative flex h-8.5 w-8.5 cursor-pointer items-center justify-center rounded-lg hover:bg-slate-100">
              <Bell size={18} strokeWidth={2} className="text-slate-600" />
              <div className="absolute top-1.5 right-2 h-1.75 w-1.75 rounded-full border-[1.5px] border-white bg-red-500" />
            </div>
            <div className="h-5.5 w-px bg-border" />
            <div className="flex cursor-pointer items-center gap-2 rounded-lg px-1.5 py-1 hover:bg-slate-100">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-secondary text-[11.5px] font-bold text-primary">
                {initialsFromEmail(session?.user.email)}
              </div>
              <ChevronDown size={13} strokeWidth={2.5} className="text-slate-500" />
            </div>
          </div>
        </header>

        <main className="min-w-0 flex-1 px-8 pt-7 pb-15">{children}</main>
      </div>
    </div>
  )
}
