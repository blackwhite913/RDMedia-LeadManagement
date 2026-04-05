import { useState, useEffect, useCallback } from 'react'
import LeadTable from '../components/LeadTable'
import api from '../api/client'

function Leads() {
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [total, setTotal] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [deleteMode, setDeleteMode] = useState(null)
  const [targetLeadId, setTargetLeadId] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const limit = 50

  // Fetch leads
  const fetchLeads = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      let data
      if (searchQuery) {
        data = await api.searchLeads(searchQuery, page, limit)
      } else {
        data = await api.getLeads(page, limit)
      }
      
      setLeads(data.leads)
      setTotal(data.total)
      setTotalPages(data.total_pages)
      setSelectedIds(new Set())
    } catch (err) {
      console.error('Error fetching leads:', err)
      setError('Failed to load leads. Please check if the backend is running.')
    } finally {
      setLoading(false)
    }
  }, [page, searchQuery])

  useEffect(() => {
    fetchLeads()
  }, [fetchLeads])

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== searchQuery) {
        setSearchQuery(searchInput)
        setPage(1) // Reset to first page on new search
      }
    }, 500) // 500ms debounce

    return () => clearTimeout(timer)
  }, [searchInput, searchQuery])

  const handleSearchChange = (e) => {
    setSearchInput(e.target.value)
  }

  const handleClearSearch = () => {
    setSearchInput('')
    setSearchQuery('')
    setPage(1)
  }

  const handlePrevPage = () => {
    if (page > 1) {
      setPage(page - 1)
    }
  }

  const handleNextPage = () => {
    if (page < totalPages) {
      setPage(page + 1)
    }
  }

  const handlePageClick = (pageNum) => {
    setPage(pageNum)
  }

  const handleToggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleToggleSelectAll = (checked) => {
    if (checked) {
      setSelectedIds(new Set(leads.map((lead) => lead.id)))
    } else {
      setSelectedIds(new Set())
    }
  }

  const handleRequestSingleDelete = (id) => {
    setDeleteMode('single')
    setTargetLeadId(id)
    setConfirmOpen(true)
  }

  const handleRequestBulkDelete = () => {
    if (selectedIds.size === 0) return
    setDeleteMode('bulk')
    setTargetLeadId(null)
    setConfirmOpen(true)
  }

  const handleCloseConfirm = () => {
    if (deleting) return
    setConfirmOpen(false)
    setDeleteMode(null)
    setTargetLeadId(null)
  }

  const handleConfirmDelete = async () => {
    try {
      setDeleting(true)
      setError(null)

      if (deleteMode === 'single' && targetLeadId !== null) {
        await api.deleteLead(targetLeadId)
      } else if (deleteMode === 'bulk') {
        await api.deleteLeadsBulk(Array.from(selectedIds))
      }

      setConfirmOpen(false)
      setDeleteMode(null)
      setTargetLeadId(null)
      setSelectedIds(new Set())
      await fetchLeads()
    } catch (err) {
      console.error('Error deleting lead(s):', err)
      setError('Failed to delete selected lead(s). Please try again.')
    } finally {
      setDeleting(false)
    }
  }

  const allSelected = leads.length > 0 && leads.every((lead) => selectedIds.has(lead.id))

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pages = []
    const maxVisible = 5
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      if (page <= 3) {
        for (let i = 1; i <= 4; i++) {
          pages.push(i)
        }
        pages.push('...')
        pages.push(totalPages)
      } else if (page >= totalPages - 2) {
        pages.push(1)
        pages.push('...')
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i)
        }
      } else {
        pages.push(1)
        pages.push('...')
        for (let i = page - 1; i <= page + 1; i++) {
          pages.push(i)
        }
        pages.push('...')
        pages.push(totalPages)
      }
    }
    
    return pages
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Leads</h1>
        <p className="text-gray-600">
          Browse and search all leads in the system
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchInput}
              onChange={handleSearchChange}
              placeholder="Search by email or company name..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchInput && (
              <button
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <span className="font-medium">{total.toLocaleString()}</span>
            <span className="ml-1">
              {searchQuery ? 'result(s)' : 'total lead(s)'}
            </span>
          </div>
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600">
                {selectedIds.size} selected
              </span>
              <button
                onClick={handleRequestBulkDelete}
                className="px-3 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700"
              >
                Delete Selected
              </button>
            </div>
          )}
        </div>
        {searchQuery && (
          <div className="mt-2 text-sm text-gray-600">
            Searching for: <span className="font-medium">{searchQuery}</span>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Lead Table */}
      <LeadTable
        leads={leads}
        loading={loading}
        selectedIds={selectedIds}
        allSelected={allSelected}
        onToggleSelect={handleToggleSelect}
        onToggleSelectAll={handleToggleSelectAll}
        onDeleteSingle={handleRequestSingleDelete}
      />

      {/* Pagination */}
      {!loading && leads.length > 0 && totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between bg-white rounded-lg shadow-sm border border-gray-200 px-4 py-3">
          <div className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </div>
          
          <div className="flex items-center gap-2">
            {/* Previous Button */}
            <button
              onClick={handlePrevPage}
              disabled={page === 1}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                page === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Previous
            </button>

            {/* Page Numbers */}
            <div className="hidden sm:flex gap-1">
              {getPageNumbers().map((pageNum, idx) => (
                pageNum === '...' ? (
                  <span key={idx} className="px-3 py-2 text-gray-400">
                    ...
                  </span>
                ) : (
                  <button
                    key={idx}
                    onClick={() => handlePageClick(pageNum)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      pageNum === page
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              ))}
            </div>

            {/* Next Button */}
            <button
              onClick={handleNextPage}
              disabled={page === totalPages}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                page === totalPages
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && leads.length === 0 && searchQuery && (
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-yellow-800">
            No leads found matching "{searchQuery}"
          </p>
          <button
            onClick={handleClearSearch}
            className="mt-2 text-sm text-yellow-900 hover:underline font-medium"
          >
            Clear search
          </button>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Confirm Delete</h2>
            </div>
            <div className="px-6 py-4 text-sm text-gray-700">
              {deleteMode === 'single'
                ? 'Are you sure you want to delete this lead? This action cannot be undone.'
                : `Are you sure you want to delete ${selectedIds.size} lead(s)? This action cannot be undone.`}
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={handleCloseConfirm}
                disabled={deleting}
                className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleting}
                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-60"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Leads
