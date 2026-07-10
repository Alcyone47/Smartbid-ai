import { useMemo, useState } from "react"
import { Search } from "lucide-react"
import { useVendorSummaries } from "@/hooks/use-vendor-summaries"
import { StatusBadge } from "@/components/status-badge"
import { Input } from "@/components/ui/input"

function initials(name: string) {
  return name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

const LOGO_COLORS = ["#2563EB", "#7C3AED", "#0EA5E9", "#DC2626", "#059669", "#D97706"]

export function VendorsPage() {
  const { data: vendors, isLoading } = useVendorSummaries()
  const [search, setSearch] = useState("")

  const filtered = useMemo(
    () => (vendors ?? []).filter((v) => v.vendorName.toLowerCase().includes(search.toLowerCase())),
    [vendors, search],
  )

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-[22px] font-bold tracking-tight text-foreground">Vendors</h1>
        <p className="mt-1 text-[13.5px] text-muted-foreground">
          All vendors with uploaded datasheets across your projects
        </p>
      </div>

      <div className="mb-4 relative w-70">
        <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search vendors…"
          className="pl-8.5"
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-background">
              <th className="px-5 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Vendor
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Documents
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Status
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Last Updated
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-5 py-6 text-center text-sm text-muted-foreground">
                  Loading…
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-6 text-center text-sm text-muted-foreground">
                  No vendors found.
                </td>
              </tr>
            ) : (
              filtered.map((v, i) => (
                <tr key={v.vendorName} className="border-t border-slate-100 hover:bg-background">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="flex h-7.5 w-7.5 items-center justify-center rounded-lg text-[11.5px] font-bold text-white"
                        style={{ background: LOGO_COLORS[i % LOGO_COLORS.length] }}
                      >
                        {initials(v.vendorName)}
                      </div>
                      <span className="text-[13.5px] font-semibold text-foreground">{v.vendorName}</span>
                    </div>
                  </td>
                  <td className="px-3 py-3 text-[13px] text-slate-700">{v.documentCount}</td>
                  <td className="px-3 py-3">
                    <StatusBadge status={v.status} />
                  </td>
                  <td className="px-3 py-3 text-[12.5px] text-slate-400">
                    {new Date(v.lastUpdated).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
