"""
FastAPI endpoints for lead management system
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from src.db import get_db
from src.models import Lead, Import, Export, ExportLead
from src.ingest import process_csv_bytes

# Create router
router = APIRouter(prefix="/api")


class BulkDeleteRequest(BaseModel):
    ids: List[int] = Field(default_factory=list)


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a CSV file of leads
    
    Accepts Apollo CSV exports and other formats
    Returns summary of import results
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Process CSV
        result = process_csv_bytes(
            file_content=content,
            filename=file.filename,
            db=db,
            source="apollo"
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Get statistics about leads in the database
    
    Returns:
    - total_leads: Total number of unique leads
    - leads_last_7_days: Leads added in last 7 days
    - leads_last_30_days: Leads added in last 30 days
    - unique_companies: Number of unique companies
    """
    # Calculate date thresholds
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    # Total leads
    total_leads = db.query(func.count(Lead.id)).scalar()
    
    # Leads added in last 7 days (by first_seen_date)
    leads_last_7_days = db.query(func.count(Lead.id)).filter(
        Lead.first_seen_date >= seven_days_ago
    ).scalar()
    
    # Leads added in last 30 days
    leads_last_30_days = db.query(func.count(Lead.id)).filter(
        Lead.first_seen_date >= thirty_days_ago
    ).scalar()
    
    # Unique companies (excluding None)
    unique_companies = db.query(func.count(func.distinct(Lead.company_name))).filter(
        Lead.company_name.isnot(None),
        Lead.company_name != ''
    ).scalar()
    
    # Leads in cooldown
    leads_in_cooldown = db.query(func.count(Lead.id)).filter(
        Lead.cooldown_until.isnot(None),
        Lead.cooldown_until > now
    ).scalar()
    
    # Total exports
    total_exports = db.query(func.count(Export.id)).scalar()
    
    return {
        "total_leads": total_leads or 0,
        "leads_last_7_days": leads_last_7_days or 0,
        "leads_last_30_days": leads_last_30_days or 0,
        "unique_companies": unique_companies or 0,
        "leads_in_cooldown": leads_in_cooldown or 0,
        "total_exports": total_exports or 0
    }


@router.get("/leads")
def get_leads(
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of leads
    
    Sorted by last_seen_date (most recent first)
    """
    # Calculate offset
    offset = (page - 1) * limit
    
    # Get total count
    total = db.query(func.count(Lead.id)).scalar()
    
    # Get leads with pagination
    leads = db.query(Lead).order_by(
        Lead.last_seen_date.desc()
    ).offset(offset).limit(limit).all()
    
    # Convert to dictionaries
    leads_data = [lead.to_dict() for lead in leads]
    
    return {
        "total": total or 0,
        "page": page,
        "limit": limit,
        "total_pages": ((total - 1) // limit + 1) if total > 0 else 0,
        "leads": leads_data
    }


@router.delete("/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Delete a single lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        db.query(ExportLead).filter(ExportLead.lead_id == lead_id).delete(
            synchronize_session=False
        )
        db.delete(lead)
        db.commit()
        return {"success": True, "deleted_id": lead_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting lead: {str(e)}")


@router.post("/leads/delete-bulk")
def delete_leads_bulk(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """Delete multiple leads by ID list."""
    if not payload.ids:
        return {"success": True, "deleted_count": 0}

    unique_ids = list(set(payload.ids))
    try:
        db.query(ExportLead).filter(ExportLead.lead_id.in_(unique_ids)).delete(
            synchronize_session=False
        )
        deleted_count = db.query(Lead).filter(Lead.id.in_(unique_ids)).delete(
            synchronize_session=False
        )
        db.commit()
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error bulk deleting leads: {str(e)}")


@router.get("/leads/search")
def search_leads(
    q: str = Query(..., min_length=1, description="Search query (email or company)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Search leads by email or company name
    
    Case-insensitive search
    Returns paginated results
    """
    # Calculate offset
    offset = (page - 1) * limit
    
    # Search query (case-insensitive)
    search_pattern = f"%{q.lower()}%"
    
    # Build query with OR condition (email or company name)
    query = db.query(Lead).filter(
        or_(
            func.lower(Lead.email).like(search_pattern),
            func.lower(Lead.company_name).like(search_pattern)
        )
    )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    leads = query.order_by(
        Lead.last_seen_date.desc()
    ).offset(offset).limit(limit).all()
    
    # Convert to dictionaries
    leads_data = [lead.to_dict() for lead in leads]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": ((total - 1) // limit + 1) if total > 0 else 0,
        "query": q,
        "leads": leads_data
    }


@router.post("/export")
async def create_lead_export(
    percentage: float = Query(..., ge=0.1, le=100, description="Percentage of eligible leads to export"),
    batch_name: str = Query(..., min_length=1, description="Name for this export batch"),
    country: Optional[str] = Query(None, description="Optional country filter"),
    seed: Optional[int] = Query(None, description="Optional random seed for reproducibility"),
    db: Session = Depends(get_db)
):
    """
    Create a new export batch with percentage-based selection
    
    Returns export summary and CSV data for download
    """
    try:
        from src.export import create_export
        
        filters = {"country": country} if country else None
        
        result = create_export(
            db=db,
            percentage=percentage,
            batch_name=batch_name,
            seed=seed,
            filters=filters
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating export: {str(e)}")


@router.get("/export/preview")
def preview_export(
    percentage: float = Query(..., ge=0.1, le=100, description="Percentage to preview"),
    country: Optional[str] = Query(None, description="Optional country filter"),
    db: Session = Depends(get_db)
):
    """
    Preview how many leads would be exported without creating the export
    
    Shows eligible count, would-export count, and cooldown count
    """
    try:
        from src.export import get_eligible_leads
        
        # Get eligible leads
        eligible = get_eligible_leads(
            db,
            country=country
        )
        eligible_count = len(eligible)
        would_export = int(eligible_count * (percentage / 100))
        
        # Count leads in cooldown
        now = datetime.utcnow()
        in_cooldown = db.query(func.count(Lead.id)).filter(
            Lead.cooldown_until.isnot(None),
            Lead.cooldown_until > now
        ).scalar()
        
        # Total leads in system
        total_leads = db.query(func.count(Lead.id)).scalar()
        
        return {
            "eligible_count": eligible_count,
            "would_export": would_export,
            "percentage": percentage,
            "in_cooldown": in_cooldown or 0,
            "total_leads": total_leads or 0,
            "available_for_export": eligible_count > 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing export: {str(e)}")


@router.get("/exports")
def get_exports(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get export history with pagination
    """
    # Calculate offset
    offset = (page - 1) * limit
    
    # Get total count
    total = db.query(func.count(Export.id)).scalar()
    
    # Get exports with pagination
    exports = db.query(Export).order_by(
        Export.exported_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Convert to dictionaries
    exports_data = [
        {
            "id": exp.id,
            "batch_name": exp.export_batch_name,
            "percentage": exp.percentage_used,
            "exported_count": exp.total_leads_exported,
            "eligible_count": exp.eligible_leads_count,
            "exported_at": exp.exported_at.isoformat(),
            "filters_applied": exp.filters_applied
        }
        for exp in exports
    ]
    
    return {
        "total": total or 0,
        "page": page,
        "limit": limit,
        "total_pages": ((total - 1) // limit + 1) if total > 0 else 0,
        "exports": exports_data
    }


@router.get("/imports")
def get_imports(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get import history with pagination
    """
    # Calculate offset
    offset = (page - 1) * limit
    
    # Get total count
    total = db.query(func.count(Import.id)).scalar()
    
    # Get imports with pagination
    imports = db.query(Import).order_by(
        Import.imported_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Convert to dictionaries
    imports_data = [
        {
            "id": imp.id,
            "filename": imp.filename,
            "source": imp.source,
            "total_rows": imp.total_rows,
            "inserted": imp.inserted_rows,
            "duplicates": imp.duplicate_rows,
            "imported_at": imp.imported_at.isoformat()
        }
        for imp in imports
    ]
    
    return {
        "total": total or 0,
        "page": page,
        "limit": limit,
        "total_pages": ((total - 1) // limit + 1) if total > 0 else 0,
        "imports": imports_data
    }


@router.get("/health")
def health_check():
    """
    Simple health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
