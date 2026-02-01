# Backend - RD Media Lead Management System

FastAPI backend for the lead management system.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run server:
```bash
python -m src.main
```

Server runs at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

## Project Structure

```
backend/
├── data/
│   └── leads.db          # SQLite database (auto-created)
├── src/
│   ├── __init__.py       # Package init
│   ├── main.py           # FastAPI app entry point
│   ├── db.py             # Database connection & setup
│   ├── models.py         # SQLAlchemy models
│   ├── ingest.py         # CSV processing logic
│   └── api.py            # API endpoints
└── requirements.txt      # Python dependencies
```

## API Documentation

### POST /api/upload-csv

Upload and process a CSV file.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (CSV file)

**Response:**
```json
{
  "success": true,
  "total_rows": 500,
  "new_leads_inserted": 320,
  "duplicates_skipped": 180,
  "errors": []
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/upload-csv \
  -F "file=@leads.csv"
```

### GET /api/stats

Get system statistics.

**Response:**
```json
{
  "total_leads": 5420,
  "leads_last_7_days": 120,
  "leads_last_30_days": 450,
  "unique_companies": 890
}
```

**Example:**
```bash
curl http://localhost:8000/api/stats
```

### GET /api/leads

Get paginated list of leads.

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `limit` (int, default: 50, max: 100) - Items per page

**Response:**
```json
{
  "total": 5420,
  "page": 1,
  "limit": 50,
  "total_pages": 109,
  "leads": [
    {
      "id": 1,
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company_name": "Acme Corp",
      "job_title": "CEO",
      "company_domain": "acme.com",
      "country": "USA",
      "source": "apollo",
      "first_seen_date": "2026-01-15T10:30:00",
      "last_seen_date": "2026-01-28T14:20:00",
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/api/leads?page=1&limit=50"
```

### GET /api/leads/search

Search leads by email or company name.

**Query Parameters:**
- `q` (string, required) - Search query
- `page` (int, default: 1) - Page number
- `limit` (int, default: 50) - Items per page

**Response:**
```json
{
  "total": 15,
  "page": 1,
  "limit": 50,
  "total_pages": 1,
  "query": "example.com",
  "leads": [
    {
      "id": 1,
      "email": "contact@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "company_name": "Example Inc",
      "job_title": "CTO",
      "company_domain": "example.com",
      "country": "USA",
      "source": "apollo",
      "first_seen_date": "2026-01-20T09:15:00",
      "last_seen_date": "2026-01-30T11:45:00",
      "created_at": "2026-01-20T09:15:00"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/api/leads/search?q=example.com"
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-01T12:00:00"
}
```

## Database Schema

### Table: leads

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| email | TEXT | Unique email (case-insensitive) |
| first_name | TEXT | First name (nullable) |
| last_name | TEXT | Last name (nullable) |
| company_name | TEXT | Company name (nullable, indexed) |
| job_title | TEXT | Job title (nullable) |
| company_domain | TEXT | Company website (nullable) |
| country | TEXT | Country (nullable) |
| source | TEXT | Source (default: "apollo") |
| first_seen_date | DATETIME | When lead was first imported |
| last_seen_date | DATETIME | When lead was last seen |
| created_at | DATETIME | Record creation timestamp |

**Indexes:**
- `idx_email` - Email lookup
- `idx_company_name` - Company search
- `idx_last_seen_date` - Date sorting

## CSV Processing

### Column Mapping

The system automatically maps various CSV column names:

| CSV Column | Internal Field |
|------------|----------------|
| Email, email, Email Address | email |
| First Name, first_name | first_name |
| Last Name, last_name | last_name |
| Company Name, company, Company | company_name |
| Job Title, title, Title | job_title |
| Company Domain, domain, Website | company_domain |
| Country, country, Location | country |

### Excluded Columns

These columns are automatically filtered out:
- Mobile Phone / mobile_phone
- Email Status / email_status
- Email Open / email_open
- Qualify Contact / qualify_contact

### Deduplication

1. Email is normalized to lowercase
2. Database query checks for existing email (case-insensitive)
3. If exists: Update `last_seen_date`
4. If new: Insert with both `first_seen_date` and `last_seen_date` = now

## Development

### Run with auto-reload:
```bash
python -m src.main
```

### Access interactive API docs:
```
http://localhost:8000/docs
```

### Database location:
```
backend/data/leads.db
```

### Reset database:
Delete the `data/leads.db` file and restart the server.

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **sqlalchemy** - ORM
- **pandas** - CSV processing
- **python-multipart** - File upload support

## CORS Configuration

CORS is configured to allow requests from:
- http://localhost:5173 (Vite default)
- http://localhost:3000 (Alternative React port)
- http://127.0.0.1:5173
- http://127.0.0.1:3000

## Error Handling

All endpoints return appropriate HTTP status codes:
- 200 - Success
- 400 - Bad request (invalid file, missing parameters)
- 500 - Server error

Error responses include a `detail` field with error message.

## Performance Notes

- SQLite is suitable for 100k+ leads
- Pagination limits prevent memory issues
- Indexes optimize search and sorting
- For larger datasets, consider PostgreSQL

## Testing

You can test the API using the interactive docs at `/docs` or with curl:

```bash
# Upload CSV
curl -X POST http://localhost:8000/api/upload-csv \
  -F "file=@sample.csv"

# Get stats
curl http://localhost:8000/api/stats

# Get leads
curl http://localhost:8000/api/leads?page=1&limit=10

# Search leads
curl "http://localhost:8000/api/leads/search?q=acme"
```
