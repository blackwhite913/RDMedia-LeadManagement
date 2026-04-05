"""
Lead export system with percentage-based selection and cooldown logic
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.models import Lead, Export, ExportLead

# Configurable cooldown period in days
COOLDOWN_DAYS = 90


def get_eligible_leads(
    db: Session,
    include_countries: Optional[List[str]] = None,
    exclude_countries: Optional[List[str]] = None
) -> List[Lead]:
    """
    Get leads eligible for export (not in cooldown, has valid email)
    
    Args:
        db: Database session
        include_countries: Optional allowlist country filter (IN)
        exclude_countries: Optional blocklist country filter (NOT IN)
    
    Returns:
        List of eligible Lead objects
    """
    now = datetime.utcnow()
    
    # Base query: must have valid email and not be in cooldown.
    query = db.query(Lead).filter(
        Lead.email.isnot(None),
        Lead.email != '',
        or_(
            Lead.cooldown_until.is_(None),
            Lead.cooldown_until < now
        )
    )

    # Apply optional filters
    if include_countries:
        query = query.filter(Lead.country.in_(include_countries))
    if exclude_countries:
        query = query.filter(Lead.country.notin_(exclude_countries))

    query = query.order_by(Lead.created_at.desc())
    
    return query.all()


def create_export(
    db: Session,
    percentage: float,
    batch_name: str,
    seed: Optional[int] = None,
    filters: Optional[Dict] = None
) -> Dict:
    """
    Create a new export batch with percentage-based lead selection
    
    Args:
        db: Database session
        percentage: Percentage of eligible leads to export (0.1-100)
        batch_name: Name for this export batch
        seed: Optional random seed for reproducibility
        filters: Optional filters (country, etc.)
    
    Returns:
        Dict with export summary and CSV data
    """
    if not (0 < percentage <= 100):
        raise ValueError("Percentage must be between 0 and 100")
    
    # Get eligible leads
    include_countries = filters.get('include_countries') if filters else None
    exclude_countries = filters.get('exclude_countries') if filters else None
    eligible = get_eligible_leads(
        db,
        include_countries=include_countries,
        exclude_countries=exclude_countries
    )
    eligible_count = len(eligible)
    
    if eligible_count == 0:
        return {
            "success": False,
            "message": "No eligible leads available for export"
        }
    
    # Calculate how many to export
    export_count = int(eligible_count * (percentage / 100))
    
    if export_count == 0:
        return {
            "success": False,
            "message": f"Percentage too low: would export 0 leads (eligible: {eligible_count})"
        }
    
    selected_leads = eligible[:export_count]
    
    # Create export record
    export_record = Export(
        export_batch_name=batch_name,
        percentage_used=percentage,
        total_leads_exported=len(selected_leads),
        eligible_leads_count=eligible_count,
        exported_at=datetime.utcnow(),
        filters_applied=str(filters) if filters else None,
        seed_value=seed
    )
    db.add(export_record)
    db.flush()  # Get export_id before committing
    
    # Update leads and create junction records
    cooldown_date = datetime.utcnow() + timedelta(days=COOLDOWN_DAYS)
    
    for lead in selected_leads:
        # Update lead with export info and cooldown
        lead.last_exported_at = datetime.utcnow()
        lead.export_count += 1
        lead.cooldown_until = cooldown_date
        
        # Create junction record
        export_lead = ExportLead(
            export_id=export_record.id,
            lead_id=lead.id
        )
        db.add(export_lead)
    
    # Commit all changes
    db.commit()
    
    # Prepare CSV data for download
    csv_data = [
        {
            "email": lead.email,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "company_name": lead.company_name,
            "company_domain": lead.company_domain,
            "job_title": lead.job_title,
            "country": lead.country,
            "icp_score": lead.icp_score,
            "qualification_tags": lead.qualification_tags,
            "qualification_reason": lead.qualification_reason,
        }
        for lead in selected_leads
    ]
    
    return {
        "success": True,
        "export_id": export_record.id,
        "batch_name": batch_name,
        "eligible_count": eligible_count,
        "exported_count": len(selected_leads),
        "percentage_used": percentage,
        "cooldown_until": cooldown_date.isoformat(),
        "cooldown_days": COOLDOWN_DAYS,
        "leads": csv_data
    }
