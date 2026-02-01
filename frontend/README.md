# Frontend - RD Media Lead Management System

React frontend for the lead management system, built with Vite and Tailwind CSS.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run development server:
```bash
npm run dev
```

3. Open browser:
```
http://localhost:5173
```

## Project Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx    # Stats overview
│   │   ├── Upload.jsx       # CSV upload
│   │   └── Leads.jsx        # Lead list/search
│   ├── components/
│   │   ├── Navbar.jsx       # Navigation bar
│   │   ├── StatsCard.jsx    # Stat display card
│   │   └── LeadTable.jsx    # Lead table
│   ├── api/
│   │   └── client.js        # API wrapper
│   ├── App.jsx              # Main app with routes
│   ├── main.jsx             # Entry point
│   └── index.css            # Tailwind imports
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## Pages

### Dashboard (`/`)
- Displays system statistics
- Total leads, 7-day, 30-day counts
- Unique companies count
- Quick action buttons

### Upload (`/upload`)
- CSV file upload interface
- Drag-and-drop support
- Upload progress indicator
- Result summary with counts
- Error handling

### Leads (`/leads`)
- Paginated lead table
- Search by email or company
- Debounced search (500ms)
- Responsive pagination
- Sort by last seen date

## Components

### Navbar
Navigation bar with:
- Logo/title
- Links to Dashboard, Upload, Leads
- Active page highlighting

### StatsCard
Reusable statistic display:
```jsx
<StatsCard 
  title="Total Leads" 
  value={5420} 
  subtitle="All time"
/>
```

### LeadTable
Table component displaying:
- Email, Name, Company, Job Title, Country, Last Seen
- Hover effects
- Loading state
- Empty state
- Responsive design

## API Client

All API calls are handled through `src/api/client.js`:

```javascript
import api from './api/client'

// Upload CSV
const result = await api.uploadCSV(file)

// Get stats
const stats = await api.getStats()

// Get leads (paginated)
const leads = await api.getLeads(page, limit)

// Search leads
const results = await api.searchLeads(query, page, limit)
```

## Routing

Routes are defined in `App.jsx`:
- `/` - Dashboard
- `/upload` - Upload page
- `/leads` - Leads page

## Styling

The project uses Tailwind CSS for styling:
- Utility-first CSS framework
- Responsive design
- Consistent color scheme
- Hover states and transitions

### Color Scheme
- Primary: Blue (600-700)
- Success: Green (50-900)
- Warning: Yellow (50-900)
- Error: Red (50-900)
- Neutral: Gray (50-900)

## Features

### Search Functionality
- Debounced search (500ms delay)
- Real-time results
- Search by email or company
- Clear search button

### Pagination
- Previous/Next buttons
- Page numbers with ellipsis
- Configurable page size (default: 50)
- Total count display

### File Upload
- Drag-and-drop support
- File type validation (.csv only)
- File size display
- Upload progress
- Result summary

### Error Handling
- API error messages
- Network error detection
- User-friendly error display
- Retry mechanisms

## Development

### Run development server:
```bash
npm run dev
```

### Build for production:
```bash
npm run build
```

### Preview production build:
```bash
npm run preview
```

## Configuration

### API Base URL
Configured in `src/api/client.js`:
```javascript
const API_BASE = 'http://localhost:8000/api'
```

For production, update this to your backend URL.

### Vite Configuration
Port and host settings in `vite.config.js`:
```javascript
server: {
  port: 5173,
  host: true
}
```

## Dependencies

### Main Dependencies
- **react** - UI framework
- **react-dom** - React DOM renderer
- **react-router-dom** - Routing
- **axios** - HTTP client

### Dev Dependencies
- **vite** - Build tool
- **@vitejs/plugin-react** - React plugin for Vite
- **tailwindcss** - CSS framework
- **autoprefixer** - CSS post-processor
- **postcss** - CSS transformer

## Browser Support

Modern browsers supporting:
- ES6+
- CSS Grid
- Flexbox
- Fetch API

Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Lazy loading for routes (can be added)
- Debounced search (500ms)
- Pagination limits data load
- Optimized re-renders with React hooks

## Accessibility

- Semantic HTML
- Keyboard navigation
- ARIA labels (can be enhanced)
- Focus states
- Color contrast (WCAG AA)

## Troubleshooting

### Backend not connecting
Check that:
1. Backend is running on port 8000
2. CORS is properly configured
3. API_BASE URL is correct

### Build errors
Try:
```bash
rm -rf node_modules
npm install
npm run dev
```

### Styling not working
Ensure Tailwind is properly configured:
```bash
npm install -D tailwindcss postcss autoprefixer
```

## Future Enhancements

- Dark mode
- Export to CSV
- Advanced filters
- Bulk operations
- Lead details modal
- Column sorting
- Column visibility toggle
- Keyboard shortcuts
- Toast notifications
- Loading skeletons
