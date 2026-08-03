import { useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { useOrgMe } from "@/hooks/use-org"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const NAV = [
  { id: "profile", label: "Profile" },
  { id: "organization", label: "Organization" },
  { id: "notifications", label: "Notifications" },
]

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}

export function SettingsPage() {
  const { session } = useAuth()
  const { data: org, isLoading } = useOrgMe()
  const [tab, setTab] = useState("profile")

  return (
    <div className="flex items-start gap-6">
      <div className="flex w-50 shrink-0 flex-col gap-0.5">
        {NAV.map((n) => (
          <button
            key={n.id}
            onClick={() => setTab(n.id)}
            className={cn(
              "rounded-lg px-3 py-2.25 text-left text-[13.5px] font-medium text-slate-700",
              tab === n.id && "bg-secondary font-semibold text-primary",
            )}
          >
            {n.label}
          </button>
        ))}
      </div>

      <div className="max-w-160 min-w-0 flex-1">
        {tab === "profile" ? (
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="mb-4.5 text-[15px] font-bold text-foreground">Profile</div>
            <div className="mb-5.5 flex items-center gap-3.5">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary text-lg font-bold text-primary">
                {session?.user.email?.slice(0, 2).toUpperCase() ?? "?"}
              </div>
              {org ? <Badge className="capitalize">{org.role}</Badge> : null}
            </div>
            <div className="mb-3.5">
              <Label className="mb-1.5">Email</Label>
              <Input value={session?.user.email ?? ""} disabled />
            </div>
            {org ? (
              <div className="mb-3.5">
                <Label className="mb-1.5">Member since</Label>
                <Input value={formatDate(org.member_since)} disabled />
              </div>
            ) : null}
            <p className="text-xs text-muted-foreground">
              {isLoading ? "Loading..." : "Profile editing isn't wired up yet — this view is read-only."}
            </p>
          </div>
        ) : null}
        {tab === "organization" ? (
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="mb-4.5 text-[15px] font-bold text-foreground">Organization</div>
            {org ? (
              <>
                <div className="mb-3.5">
                  <Label className="mb-1.5">Organization name</Label>
                  <Input value={org.org_name} disabled />
                </div>
                <div className="mb-3.5 flex gap-6">
                  <div>
                    <Label className="mb-1.5">Members</Label>
                    <Input value={org.member_count} disabled className="w-24" />
                  </div>
                  <div>
                    <Label className="mb-1.5">Created</Label>
                    <Input value={formatDate(org.org_created_at)} disabled className="w-36" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Renaming the organization and inviting members isn't wired up yet — this view is read-only.
                </p>
              </>
            ) : (
              <p className="text-xs text-muted-foreground">{isLoading ? "Loading..." : "No organization found."}</p>
            )}
          </div>
        ) : null}
        {tab === "notifications" ? (
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="mb-4.5 text-[15px] font-bold text-foreground">Notifications</div>
            <p className="text-xs text-muted-foreground">
              Document extraction and vendor matching updates appear in the bell menu in the top bar. Per-channel
              notification preferences (e.g. email digests) aren't wired up yet.
            </p>
          </div>
        ) : null}
        <Button disabled className="mt-4">
          Save changes
        </Button>
      </div>
    </div>
  )
}
