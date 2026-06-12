import { useState } from 'react'
import { getAccount } from '../api/client'

export default function Account() {
  const [id, setId]         = useState('AC00202')
  const [data, setData]     = useState(null)
  const [error, setError]   = useState(null)
  const [loading, setLoading] = useState(false)

  const lookup = async () => {
    setError(null); setData(null); setLoading(true)
    try {
      const d = await getAccount(id.trim())
      setData(d)
    } catch (err) {
      setError(err?.response?.data?.detail || `No profile for account ${id}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-gray-800 mb-1">Account Baseline</h1>
      <p className="text-gray-500 mb-8">
        View the behavioural baseline the engine scores transactions against.
        A score only means something relative to this normal.
      </p>

      <div className="flex gap-2 mb-6">
        <input
          value={id}
          onChange={e => setId(e.target.value)}
          placeholder="Account ID e.g. AC00202"
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm
                     focus:outline-none focus:ring-2 focus:ring-gray-300 bg-white"
        />
        <button
          onClick={lookup}
          disabled={loading}
          className="px-5 py-2 rounded-lg bg-gray-800 text-white text-sm font-medium
                     hover:bg-gray-700 disabled:opacity-40 transition-all"
        >
          {loading ? 'Loading...' : 'Look up'}
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          {error}
        </div>
      )}

      {data && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-800">{data.account_id}</h2>
            {data.low_confidence && (
              <span className="text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                low confidence — {data.txn_count} txns
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <Stat label="Transactions on record" value={data.txn_count} />
            <Stat label="Customer age" value={data.customer_age} />
            <Stat label="Avg amount" value={`$${data.amt_mean}`} />
            <Stat label="Amount std dev" value={`$${data.amt_std}`} />
            <Stat label="Max amount" value={`$${data.amt_max}`} />
            <Stat label="Avg balance" value={`$${data.avg_balance}`} />
            <Stat label="Avg txns / day" value={data.avg_daily_txns} />
            <Stat label="Known merchants" value={data.n_known_merchants} />
          </div>

          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-1">Known locations</p>
            <div className="flex flex-wrap gap-2">
              {data.known_locations.map(l => (
                <span key={l} className="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                  {l}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-1">Typical hours</p>
            <p className="text-sm text-gray-700">{data.typical_hours.join(', ')}</p>
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-base font-semibold text-gray-800">{value}</p>
    </div>
  )
}
