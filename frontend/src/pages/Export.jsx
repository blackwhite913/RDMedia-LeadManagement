import { useState, useEffect } from 'react'
import api from '../api/client'

function Export() {
  const [batchName, setBatchName] = useState('')
  const [percentage, setPercentage] = useState(30)
  const [country, setCountry] = useState('')
  const [preview, setPreview] = useState(null)
  const [exportResult, setExportResult] = useState(null)
  const [exportHistory, setExportHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [historyPage, setHistoryPage] = useState(1)
  const [historyTotal, setHistoryTotal] = useState(0)

  useEffect(() => {
    fetchExportHistory()
  }, [historyPage])

  const fetchExportHistory = async () => {
    try {
      const data = await api.getExports(historyPage, 10)
      setExportHistory(data.exports)
      setHistoryTotal(data.total)
    } catch (err) {
      console.error('Error fetching export history:', err)
    }
  }

  const handlePreview = async () => {
    try {
      setLoading(true)
      setError(null)
      const filters = country ? { country } : {}
      const data = await api.previewExport(percentage, filters)
      setPreview(data)
    } catch (err) {
      console.error('Error previewing export:', err)
      setError('Failed to preview export. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateExport = async () => {
    if (!batchName.trim()) {
      setError('Please enter a batch name')
      return
    }

    try {
      setLoading(true)
      setError(null)
      const filters = country ? { country } : {}
      const data = await api.createExport(percentage, batchName, filters)
      
      if (data.success) {
        setExportResult(data)
        setBatchName('')
        setPreview(null)
        fetchExportHistory()
      } else {
        setError(data.message || 'Export failed')
      }
    } catch (err) {
      console.error('Error creating export:', err)
      setError(err.response?.data?.detail || 'Failed to create export. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const downloadCSV = (leads, filename) => {
    const headers = ['email', 'first_name', 'last_name', 'company_name', 
                     'job_title', 'company_domain', 'city', 'country', 'icp_score']
    
    const csvContent = [
      headers.join(','),
      ...leads.map(lead => 
        headers.map(h => `"${lead[h] || ''}"`).join(',')
      )
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Export Leads</h1>
        <p className="text-gray-600">
          Create percentage-based exports with automatic 90-day cooldown
        </p>
      </div>

      {/* Export Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Create New Export
        </h2>

        <div className="space-y-4">
          {/* Batch Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Batch Name *
            </label>
            <input
              type="text"
              value={batchName}
              onChange={(e) => setBatchName(e.target.value)}
              placeholder="e.g., Q1 Outreach Campaign"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Percentage Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Percentage
            </label>
            <div className="flex gap-2 mb-2">
              {[20, 30, 40, 80].map((pct) => (
                <button
                  key={pct}
                  onClick={() => setPercentage(pct)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    percentage === pct
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {pct}%
                </button>
              ))}
            </div>
            <input
              type="number"
              value={percentage}
              onChange={(e) => setPercentage(Number(e.target.value))}
              min="0.1"
              max="100"
              step="0.1"
              className="w-32 px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          {/* Optional Country Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Country Filter (Optional)
            </label>
            <input
              type="text"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              placeholder="e.g., USA"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          {/* Preview Button */}
          <button
            onClick={handlePreview}
            disabled={loading}
            className="w-full py-3 px-4 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors disabled:bg-gray-300"
          >
            {loading ? 'Loading...' : 'Preview Export'}
          </button>
        </div>

        {/* Preview Results */}
        {preview && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-3">Preview Results</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-blue-900">
                  {preview.total_leads}
                </p>
                <p className="text-sm text-blue-700">Total Leads</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-900">
                  {preview.eligible_count}
                </p>
                <p className="text-sm text-green-700">Eligible</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-900">
                  {preview.would_export}
                </p>
                <p className="text-sm text-purple-700">Will Export</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-yellow-900">
                  {preview.in_cooldown}
                </p>
                <p className="text-sm text-yellow-700">In Cooldown</p>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Create Export Button */}
        {preview && preview.available_for_export && (
          <button
            onClick={handleCreateExport}
            disabled={loading || !batchName.trim()}
            className="mt-4 w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-300"
          >
            Create Export
          </button>
        )}
      </div>

      {/* Export Result */}
      {exportResult && exportResult.success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-green-900 text-lg">
                Export Created Successfully
              </h3>
              <p className="text-sm text-green-700">
                Batch: {exportResult.batch_name}
              </p>
            </div>
            <button
              onClick={() => downloadCSV(
                exportResult.leads,
                `${exportResult.batch_name.replace(/\s+/g, '_')}_${exportResult.export_id}.csv`
              )}
              className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
            >
              Download CSV
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-green-900">
                {exportResult.exported_count}
              </p>
              <p className="text-sm text-green-700">Leads Exported</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-900">
                {exportResult.percentage_used}%
              </p>
              <p className="text-sm text-green-700">Percentage Used</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-900">
                {exportResult.eligible_count}
              </p>
              <p className="text-sm text-green-700">Were Eligible</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-900">
                {exportResult.cooldown_days}
              </p>
              <p className="text-sm text-green-700">Days Cooldown</p>
            </div>
          </div>

          <button
            onClick={() => setExportResult(null)}
            className="mt-4 text-sm text-green-700 hover:text-green-900 underline"
          >
            Create Another Export
          </button>
        </div>
      )}

      {/* Export History */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Export History
        </h2>

        {exportHistory.length === 0 ? (
          <p className="text-center text-gray-500 py-8">No exports yet</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Batch Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Percentage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Exported
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Eligible
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {exportHistory.map((exp) => (
                    <tr key={exp.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {exp.batch_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {exp.percentage}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {exp.exported_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {exp.eligible_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(exp.exported_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {historyTotal > 10 && (
              <div className="mt-4 flex items-center justify-between">
                <button
                  onClick={() => setHistoryPage(Math.max(1, historyPage - 1))}
                  disabled={historyPage === 1}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600">
                  Page {historyPage} of {Math.ceil(historyTotal / 10)}
                </span>
                <button
                  onClick={() => setHistoryPage(historyPage + 1)}
                  disabled={historyPage >= Math.ceil(historyTotal / 10)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Info Section */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">How Exports Work</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li className="list-disc list-inside">
            Exports select a percentage of eligible leads randomly
          </li>
          <li className="list-disc list-inside">
            Exported leads enter a 90-day cooldown period
          </li>
          <li className="list-disc list-inside">
            Leads in cooldown are excluded from future exports
          </li>
          <li className="list-disc list-inside">
            All exports are logged for full auditability
          </li>
        </ul>
      </div>
    </div>
  )
}

export default Export
