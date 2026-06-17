import { useState } from 'react'
import { scoreTransaction, getAccount } from '../api/client'
import ScoreGauge from '../components/ScoreGauge'
import Breakdown from '../components/Breakdown'

const EMPTY = {
  account_id: 'AC00202',
  amount: '',
  location: '',
  merchant: '',
  current_balance: '',
  txns_today: 1,
  login_attempts: 1,
  hour: 16,
}

export default function Score() {
  const [form, setForm]       = useState(EMPTY)
  const [result, setResult]   = useState(null)
  const [baseline, setBaseline] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }))

  // optional: peek at the account baseline so the user knows what 'normal' is
  const loadBaseline = async () => {
    if (!form.account_id.trim()) return
    try {
      const b = await getAccount(form.account_id.trim())
      setBaseline(b)
      setError(null)
    } catch {
      setBaseline(null)
      setError(`No profile found for account ${form.account_id}`)
    }
  }

  const submit = async () => {
    setError(null); setResult(null); setLoading(true)
    try {
      const payload = {
        account_id:      form.account_id.trim(),
        amount:          parseFloat(form.amount),
        location:        form.location.trim(),
        merchant:        form.merchant.trim(),
        current_balance: parseFloat(form.current_balance),
        txns_today:      parseInt(form.txns_today) || 1,
        login_attempts:  parseInt(form.login_attempts) || 1,
        hour:            parseInt(form.hour),
      }
      const data = await scoreTransaction(payload)
      setResult(data)
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(detail || 'Could not score. Is the API running on port 8500?')
    } finally {
      setLoading(false)
    }
  }

  const field = (label, key, type = 'text', extra = {}) => (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <input
        type={type}
        value={form[key]}
        onChange={e => update(key, e.target.value)}
        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                   focus:outline-none focus:ring-2 focus:ring-gray-300 bg-white"
        {...extra}
      />
    </div>
  )

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-gray-800 mb-1">Score a Transaction</h1>
      <p className="text-gray-500 mb-8">
        Scores how unusual a transaction is versus the account's normal behaviour.
        The result is an anomaly score.
      </p>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="col-span-2 flex gap-2 items-end">
          <div className="flex-1">
            <label className="block text-xs text-gray-500 mb-1">Account ID</label>
            <input
              value={form.account_id}
              onChange={e => update('account_id', e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-gray-300 bg-white"
            />
          </div>
          <button
            onClick={loadBaseline}
            className="px-3 py-2 rounded-lg border border-gray-300 text-sm text-gray-600
                       hover:border-gray-500 transition-all"
          >
            View baseline
          </button>
        </div>

        {field('Amount', 'amount', 'number', { placeholder: 'e.g. 1947.84' })}
        {field('Current balance', 'current_balance', 'number', { placeholder: 'e.g. 3980.30' })}
        {field('Location', 'location', 'text', { placeholder: 'e.g. Reykjavik' })}
        {field('Merchant', 'merchant', 'text', { placeholder: 'e.g. M015' })}
        {field('Transactions today', 'txns_today', 'number', { min: 1 })}
        {field('Login attempts', 'login_attempts', 'number', { min: 1 })}
        {field('Hour (0-23)', 'hour', 'number', { min: 0, max: 23 })}
      </div>

      {/* baseline peek */}
      {baseline && (
        <div className="mb-4 text-xs bg-gray-50 border border-gray-200 rounded-xl p-4 text-gray-600">
          <p className="font-semibold text-gray-700 mb-2">
            Account baseline ({baseline.txn_count} txns
            {baseline.low_confidence ? ', low confidence' : ''})
          </p>
          <p>avg amount ${baseline.amt_mean} (std {baseline.amt_std}), max ${baseline.amt_max}</p>
          <p>avg balance ${baseline.avg_balance} · avg {baseline.avg_daily_txns} txns/day</p>
          <p>known locations: {baseline.known_locations.join(', ')}</p>
          <p>{baseline.n_known_merchants} known merchants · typical hours {baseline.typical_hours.join(', ')}</p>
        </div>
      )}

      <button
        onClick={submit}
        disabled={loading}
        className="w-full py-3 rounded-xl bg-gray-800 text-white font-medium
                   hover:bg-gray-700 disabled:opacity-40 transition-all mb-6"
      >
        {loading ? 'Scoring...' : 'Score Transaction'}
      </button>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {result && (
        <>
          <ScoreGauge result={result} />
          <Breakdown breakdown={result.breakdown} />
        </>
      )}
    </div>
  )
}
