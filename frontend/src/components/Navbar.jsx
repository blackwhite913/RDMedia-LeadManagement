import { Link, useLocation } from 'react-router-dom'

function Navbar() {
  const location = useLocation()

  const isActive = (path) => {
    return location.pathname === path
      ? 'text-blue-600 border-b-2 border-blue-600'
      : 'text-gray-600 hover:text-gray-900'
  }

  return (
    <nav className="bg-white shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link to="/" className="text-xl font-bold text-gray-900">
              RD Media
            </Link>
            <span className="ml-2 text-sm text-gray-500">Lead Management</span>
          </div>

          {/* Navigation Links */}
          <div className="flex space-x-8">
            <Link
              to="/"
              className={`px-3 py-2 text-sm font-medium transition-colors ${isActive(
                '/'
              )}`}
            >
              Dashboard
            </Link>
            <Link
              to="/qualify"
              className={`px-3 py-2 text-sm font-medium transition-colors ${isActive(
                '/qualify'
              )}`}
            >
              Qualify
            </Link>
            <Link
              to="/upload"
              className={`px-3 py-2 text-sm font-medium transition-colors ${isActive(
                '/upload'
              )}`}
            >
              Upload
            </Link>
            <Link
              to="/export"
              className={`px-3 py-2 text-sm font-medium transition-colors ${isActive(
                '/export'
              )}`}
            >
              Export
            </Link>
            <Link
              to="/leads"
              className={`px-3 py-2 text-sm font-medium transition-colors ${isActive(
                '/leads'
              )}`}
            >
              Leads
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
