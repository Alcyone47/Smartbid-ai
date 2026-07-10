export function AuthMarketingPanel() {
  return (
    <div className="relative hidden flex-1 items-center justify-center overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-blue-900 md:flex">
      <div
        className="absolute inset-0 opacity-50"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 30%, rgba(37,99,235,0.35), transparent 40%), radial-gradient(circle at 80% 70%, rgba(16,185,129,0.18), transparent 45%)",
        }}
      />
      <div className="relative max-w-[420px] p-10 text-white">
        <div className="flex flex-col gap-5">
          <div className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur">
            <div className="mb-2.5 flex items-center justify-between">
              <span className="text-[12.5px] font-semibold text-slate-400">Nexbridge Networks</span>
              <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-[11px] font-bold text-emerald-500">
                94% MATCH
              </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
              <div className="h-full w-[94%] rounded-full bg-emerald-500" />
            </div>
          </div>
          <h2 className="text-[28px] leading-[1.3] font-bold tracking-tight">
            Turn RFP evaluation
            <br />
            from weeks into hours.
          </h2>
          <p className="text-[14.5px] leading-relaxed text-slate-300">
            AI-extracted requirements, automated vendor matching, and audit-ready compliance matrices — built for
            enterprise bid teams.
          </p>
        </div>
      </div>
    </div>
  )
}
