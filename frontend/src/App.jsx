import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Export from './pages/Export'
import AdvancedExport from './pages/AdvancedExport'
import Leads from './pages/Leads'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/export" element={<Export />} />
            <Route path="/export/advanced" element={<AdvancedExport />} />
            <Route path="/leads" element={<Leads />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
