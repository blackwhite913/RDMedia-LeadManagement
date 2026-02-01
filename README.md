# RD Media - Lead Management System

An internal lead management system for tracking outbound marketing leads from Apollo and other sources. Prevents duplicate outreach and tracks lead history.

## Features

- **CSV Import**: Upload Apollo exports and automatically process leads
- **Deduplication**: Email-based deduplication with case-insensitive matching
- **History Tracking**: Track when leads were first and last seen
- **Search & Filter**: Search leads by email or company name
- **Dashboard**: View statistics and system overview
- **Pagination**: Efficiently browse large datasets

## Project Structure

```
rdmedia/
├── backend/          # FastAPI backend (Python)
│   ├── data/         # SQLite database
│   ├── src/          # Source code
│   └── requirements.txt
├── frontend/         # React frontend (Vite + Tailwind)
│   ├── src/          # Source code
│   └── package.json
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
```

3. Activate virtual environment:
```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the server:
```bash
python -m src.main
```

The backend will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. **Start both servers** (backend and frontend)
2. **Open browser** to `http://localhost:5173`
3. **Upload CSV** via the Upload page
4. **View statistics** on the Dashboard
5. **Browse leads** on the Leads page

## CSV Format

The system accepts CSV files with the following columns (flexible naming):

### Required
- Email / email / Email Address

### Optional
- First Name / first_name
- Last Name / last_name
- Company Name / company_name / Company
- Job Title / job_title / Title
- Company Domain / company_domain / Website
- Country / country

### Excluded Columns
These columns are automatically removed during import:
- Mobile Phone
- Email Status
- Email Open
- Qualify Contact

## Deduplication Logic

1. **Email Normalization**: All emails are converted to lowercase
2. **Unique Check**: System checks if email already exists
3. **Update or Insert**:
   - **Existing lead**: Updates `last_seen_date` only
   - **New lead**: Inserts with `first_seen_date` = `last_seen_date` = today

This allows you to:
- Track when a lead was first discovered
- See when a lead was last seen in an export
- Prevent duplicate outreach
- Identify stale leads (large gap between first and last seen)

## Technology Stack

### Backend
- FastAPI - Modern Python web framework
- SQLAlchemy - SQL toolkit and ORM
- SQLite - Lightweight database
- Pandas - CSV processing
- Uvicorn - ASGI server

### Frontend
- React 18 - UI framework
- Vite - Build tool
- React Router - Navigation
- Tailwind CSS - Styling
- Axios - HTTP client

## API Endpoints

See `backend/README.md` for detailed API documentation.

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
python -m src.main  # Auto-reload enabled
```

### Frontend Development
```bash
cd frontend
npm run dev  # Hot reload enabled
```

## Production Build

### Frontend
```bash
cd frontend
npm run build
npm run preview
```

## Future Enhancements

- Export leads to CSV
- Filter by date range
- Bulk operations (delete/archive)
- Company-level deduplication
- Email validation
- Import from other sources (LinkedIn, etc.)
- Lead scoring and tagging
- User authentication

## License

Internal use only - RD Media

## Support

For issues or questions, contact the development team.
