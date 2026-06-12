// Shows the final risk score as a clear number + decision band.
// Honest labelling: "Anomaly Score", never "fraud probability".

const DECISION_STYLE = {
  ALLOW:  { color: '#3B6D11', bg: '#f0fdf4', border: '#bbf7d0', label: 'Allow' },
  REVIEW: { color: '#B87D00', bg: '#fefce8', border: '#fef08a', label: 'Review' },
  BLOCK:  { color: '#A32D2D', bg: '#fef2f2', border: '#fecaca', label: 'Block' },
}

export default function ScoreGauge({ result }) {
  if (!result) return null
  const style = DECISION_STYLE[result.decision] || DECISION_STYLE.ALLOW
  const score = result.risk_score ?? 0

  return (
    <div className="rounded-2xl border p-6" style={{ background: style.bg, borderColor: style.border }}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs uppercase tracking-widest text-gray-400">Anomaly Score</span>
        <span className="text-xs text-gray-400">not a fraud probability</span>
      </div>

      <div className="flex items-end gap-4">
        <span className="text-5xl font-bold" style={{ color: style.color }}>
          {score.toFixed(1)}
        </span>
        <span className="text-sm text-gray-400 mb-2">/ 100</span>
        <span
          className="ml-auto mb-1 px-4 py-1.5 rounded-full text-sm font-semibold"
          style={{ background: style.color, color: 'white' }}
        >
          {style.label}
        </span>
      </div>

      {/* track */}
      <div className="mt-4 h-2 w-full bg-white rounded-full overflow-hidden border" style={{ borderColor: style.border }}>
        <div className="h-full rounded-full transition-all duration-500"
             style={{ width: `${score}%`, background: style.color }} />
      </div>

      {/* confidence note */}
      <div className="mt-4 flex items-center gap-2">
        {result.confidence === 'low' && (
          <span className="text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            low confidence
          </span>
        )}
        <span className="text-xs text-gray-500">{result.confidence_note}</span>
      </div>
    </div>
  )
}
