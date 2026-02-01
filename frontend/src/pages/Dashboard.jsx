import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import StatsCard from '../components/StatsCard'
import api from '../api/client'

function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getStats()
      setStats(data)
    } catch (err) {
      console.error('Error fetching stats:', err)
      setError('Failed to load statistics. Please check if the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">
          Overview of your lead management system
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">Loading statistics...</p>
        </div>
      )}

      {/* Stats Grid */}
      {!loading && stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <StatsCard
              title="Total Leads"
              value={stats.total_leads}
              subtitle="All time"
            />
            <StatsCard
              title="Last 7 Days"
              value={stats.leads_last_7_days}
              subtitle="Newly added leads"
            />
            <StatsCard
              title="Last 30 Days"
              value={stats.leads_last_30_days}
              subtitle="Newly added leads"
            />
            <StatsCard
              title="Unique Companies"
              value={stats.unique_companies}
              subtitle="Organizations"
            />
            <StatsCard
              title="Leads in Cooldown"
              value={stats.leads_in_cooldown}
              subtitle="90-day lockout"
            />
            <StatsCard
              title="Total Exports"
              value={stats.total_exports}
              subtitle="All time"
            />
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Quick Actions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link
                to="/upload"
                className="flex items-center justify-between p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors group"
              >
                <div>
                  <h3 className="font-medium text-gray-900 group-hover:text-blue-900">
                    Upload CSV
                  </h3>
                  <p className="text-sm text-gray-600">
                    Import leads from Apollo export
                  </p>
                </div>
                <svg
                  className="w-6 h-6 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </Link>

              <Link
                to="/export"
                className="flex items-center justify-between p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors group"
              >
                <div>
                  <h3 className="font-medium text-gray-900 group-hover:text-purple-900">
                    Export Leads
                  </h3>
                  <p className="text-sm text-gray-600">
                    Create percentage-based exports
                  </p>
                </div>
                <svg
                  className="w-6 h-6 text-purple-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
              </Link>

              <Link
                to="/leads"
                className="flex items-center justify-between p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors group"
              >
                <div>
                  <h3 className="font-medium text-gray-900 group-hover:text-green-900">
                    View Leads
                  </h3>
                  <p className="text-sm text-gray-600">
                    Browse and search all leads
                  </p>
                </div>
                <svg
                  className="w-6 h-6 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </Link>
            </div>
          </div>

          {/* Info Section */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-2">
              About This System
            </h3>
            <p className="text-sm text-blue-800">
              This lead management system helps you track all outbound leads
              contacted via Apollo. It prevents duplicate outreach by
              automatically deduplicating leads based on email addresses and
              tracking when leads were first and last seen.
            </p>
          </div>
        </>
      )}
    </div>
  )
}

export default Dashboard
