# Quick Setup Guide

Follow these steps to get the RD Media Lead Management System up and running.

## Prerequisites

Make sure you have installed:
- Python 3.8 or higher
- Node.js 16 or higher
- npm (comes with Node.js)

## Step 1: Backend Setup

Open a terminal and run:

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python -m src.main
```

You should see:
```
Starting RD Media Lead Management System...
Database initialized successfully
Server ready at http://localhost:8000
API docs available at http://localhost:8000/docs
```

Keep this terminal open. The backend is now running.

## Step 2: Frontend Setup

Open a NEW terminal window and run:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

You should see:
```
VITE v5.0.11  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

## Step 3: Open the Application

1. Open your browser
2. Go to: `http://localhost:5173`
3. You should see the RD Media Lead Management System dashboard

## Step 4: Test with Sample Data

1. Click on "Upload" in the navigation
2. Use the sample CSV file provided: `sample_leads.csv` (in the root directory)
3. Upload the file
4. You should see:
   - Total Rows: 10
   - New Leads: 10
   - Duplicates: 0

5. Go to "Dashboard" to see statistics
6. Go to "Leads" to view all imported leads

## Testing Deduplication

To test the deduplication feature:

1. Upload the same `sample_leads.csv` file again
2. You should see:
   - Total Rows: 10
   - New Leads: 0
   - Duplicates: 10

This proves that the system recognizes existing leads and updates their `last_seen_date`.

## Troubleshooting

### Backend won't start
- Make sure port 8000 is not in use
- Check that Python 3.8+ is installed: `python --version`
- Try: `python3 -m src.main` instead of `python -m src.main`

### Frontend won't start
- Make sure port 5173 is not in use
- Check that Node.js is installed: `node --version`
- Try deleting `node_modules` and running `npm install` again

### Frontend can't connect to backend
- Make sure backend is running on port 8000
- Check browser console for CORS errors
- Verify backend URL in `frontend/src/api/client.js`

### CSV upload fails
- Make sure the file is a valid CSV
- Check that it has at least an "Email" column
- Look at the backend terminal for error messages

## Next Steps

- Read the main README.md for more features
- Check backend/README.md for API documentation
- Check frontend/README.md for frontend details
- Try searching and pagination features
- Upload your own Apollo CSV exports

## Stopping the System

To stop the servers:
1. Press `Ctrl+C` in the backend terminal
2. Press `Ctrl+C` in the frontend terminal

## Starting Again

Just repeat Step 1 and Step 2. The database persists in `backend/data/leads.db`.

## Need Help?

- API Documentation: `http://localhost:8000/docs`
- Check the logs in both terminals
- Review the README files for more details
