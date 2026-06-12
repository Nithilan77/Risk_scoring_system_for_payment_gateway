// Shows WHY the score is what it is: each feature's contribution and reason.
// This is the core of the engine's explainability — the number alone is not enough.

export default function Breakdown({ breakdown }) {
  if (!breakdown || breakdown.length === 0) return null

  const maxContribution = Math.max(...breakdown.map(b => b.contribution), 1)

  return (
    <div className="mt-4 bg-white border border-gray-200 rounded-2xl p-6">
      <p className="text-sm font-semibold text-gray-700 mb-1">Why this score</p>
      <p className="text-xs text-gray-400 mb-4">
        Each feature contributes (sub-score × weight). Sorted by contribution.
      </p>

      <div className="flex flex-col gap-3">
        {breakdown.map(b => {
          const active = b.contribution > 0
          return (
            <div key={b.feature} className="flex items-center gap-3">
              <span className="text-sm font-medium w-20 capitalize text-gray-700">
                {b.feature}
              </span>

              <div className="flex-1">
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${(b.contribution / maxContribution) * 100}%`,
                      background: active ? '#2E4057' : 'transparent'
                    }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">{b.reason}</p>
              </div>

              <div className="text-right w-24 shrink-0">
                <span className={`text-sm font-semibold ${active ? 'text-gray-800' : 'text-gray-300'}`}>
                  +{b.contribution.toFixed(1)}
                </span>
                <p className="text-xs text-gray-400">
                  {b.sub_score.toFixed(0)} × {b.weight}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
