import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

function Qualify() {
  const [status, setStatus] = useState('loading') // loading | running | done | error
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [progress, setProgress] = useState(0)
  const startTimeRef = useRef(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    const run = async () => {
      try {
        const previewData = await api.qualifyPreview()
        if (cancelled) return
        setPreview(previewData)
        if (previewData.domains_count === 0) {
          setStatus('done')
          setResult({
            companies_evaluated: 0,
            leads_updated: 0,
            errors: [],
            message: 'No unscored leads from the last 7 days to qualify.',
          })
          return
        }
        setStatus('running')
        startTimeRef.current = Date.now()
        const data = await api.qualifyLeads()
        if (cancelled) return
        setProgress(100)
        setStatus('done')
        setResult(data)
      } catch (err) {
        if (cancelled) return
        setStatus('error')
        setError(err.response?.data?.detail || err.message || 'Qualification failed')
      }
    }

    run()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (status !== 'running' || !preview) return
    const estimatedMs = (preview.estimated_seconds || 300) * 1000
    intervalRef.current = setInterval(() => {
      const elapsedMs = Date.now() - startTimeRef.current
      setElapsed(Math.floor(elapsedMs / 1000))
      const p = Math.min(99, (elapsedMs / estimatedMs) * 100)
      setProgress(p)
    }, 1000)
    return () => clearInterval(intervalRef.current)
  }, [status, preview])

  const timeLeft = preview?.estimated_seconds
    ? Math.max(0, (preview.estimated_seconds - elapsed))
    : null
  const timeLeftStr =
    timeLeft !== null
      ? `${Math.floor(timeLeft / 60)}:${String(timeLeft % 60).padStart(2, '0')}`
      : '—'

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <Link to="/" className="text-blue-600 hover:text-blue-800 text-sm">
          ← Back to Dashboard
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Qualification</h1>
      <p className="text-gray-600 mb-8">
        Run Perplexity AI to score unscored leads from the last 7 days (one API call per company).
      </p>

      {status === 'loading' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-amber-500 mb-4" />
          <p className="text-gray-600">Checking how many leads to qualify…</p>
        </div>
      )}

      {status === 'running' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <p className="text-gray-700 mb-4">Qualifying leads… Do not close this page.</p>
          <div className="w-full bg-gray-200 rounded-full h-4 mb-2 overflow-hidden">
            <div
              className="h-full bg-amber-500 transition-all duration-1000 ease-linear rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between text-sm text-gray-500">
            <span>Progress: {Math.round(progress)}%</span>
            <span>Time left (est.): {timeLeftStr}</span>
            <span>Elapsed: {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}</span>
          </div>
          {preview && (
            <p className="mt-4 text-sm text-gray-500">
              Evaluating {preview.domains_count} companies ({preview.leads_count} leads). Estimated total: ~{Math.ceil(preview.estimated_seconds / 60)} min.
            </p>
          )}
        </div>
      )}

      {status === 'done' && result && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
            <div className="h-full bg-green-500 rounded-full" style={{ width: '100%' }} />
          </div>
          <p className="text-green-700 font-medium mb-4">Qualification complete</p>
          <ul className="space-y-2 text-gray-700">
            <li>Companies evaluated: <strong>{result.companies_evaluated}</strong></li>
            <li>Leads updated: <strong>{result.leads_updated}</strong></li>
            {result.errors?.length > 0 && (
              <li className="text-amber-700">API errors: {result.errors.length}</li>
            )}
          </ul>
          {result.message && <p className="mt-4 text-sm text-gray-500">{result.message}</p>}
          <Link
            to="/"
            className="inline-block mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Dashboard
          </Link>
        </div>
      )}

      {status === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-700 font-medium">Qualification failed</p>
          <p className="text-red-600 mt-2">{error}</p>
          <Link
            to="/"
            className="inline-block mt-4 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900"
          >
            Back to Dashboard
          </Link>
        </div>
      )}
    </div>
  )
}

export default Qualify
