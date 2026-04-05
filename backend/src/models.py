"""
SQLAlchemy models for the lead management system
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Index, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from src.db import Base


def _parse_tags(value):
    """Parse qualification_tags JSON to list; return None if null or invalid."""
    if not value:
        return None
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return None


class Lead(Base):
    """
    Lead model representing a contact from Apollo or other sources
    
    Email is the unique identifier with case-insensitive handling
    Tracks first_seen_date (when lead was first imported) and
    last_seen_date (most recent import containing this lead)
    """
    __tablename__ = "leads"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Unique email identifier (case-insensitive)
    # We store emails in lowercase for consistency
    email = Column(String, unique=True, nullable=False, index=True)
    
    # Contact information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company_name = Column(String, nullable=True, index=True)
    job_title = Column(String, nullable=True)
    company_domain = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    icp_score = Column(Float, nullable=True)  # deprecated - no longer used
    qualification_tags = Column(String, nullable=True)  # deprecated - no longer used
    qualified_at = Column(DateTime, nullable=True)  # deprecated - no longer used
    qualification_reason = Column(String, nullable=True)  # deprecated - no longer used
    
    # Metadata
    source = Column(String, default="apollo", nullable=False)
    
    # Tracking dates
    first_seen_date = Column(DateTime, nullable=False)
    last_seen_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Export and cooldown tracking
    last_exported_at = Column(DateTime, nullable=True)
    export_count = Column(Integer, default=0, nullable=False)
    cooldown_until = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Lead(email='{self.email}', company='{self.company_name}')>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "company_domain": self.company_domain,
            "city": self.city,
            "country": self.country,
            "icp_score": self.icp_score,
            "qualification_tags": _parse_tags(self.qualification_tags),
            "qualified_at": self.qualified_at.isoformat() if self.qualified_at else None,
            "qualification_reason": self.qualification_reason,
            "source": self.source,
            "first_seen_date": self.first_seen_date.isoformat() if self.first_seen_date else None,
            "last_seen_date": self.last_seen_date.isoformat() if self.last_seen_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_exported_at": self.last_exported_at.isoformat() if self.last_exported_at else None,
            "export_count": self.export_count,
            "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None
        }


class Import(Base):
    """
    Import model tracking CSV upload history
    Provides full auditability of all lead imports
    """
    __tablename__ = "imports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String, nullable=False)
    source = Column(String, default="apollo", nullable=False)
    total_rows = Column(Integer, nullable=False)
    inserted_rows = Column(Integer, nullable=False)  # net new leads
    duplicate_rows = Column(Integer, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    imported_by = Column(String, default="system", nullable=False)  # for future user tracking
    
    def __repr__(self):
        return f"<Import(filename='{self.filename}', inserted={self.inserted_rows}, duplicates={self.duplicate_rows})>"


class Export(Base):
    """
    Export model tracking export batch operations
    Records percentage-based lead exports with filtering
    """
    __tablename__ = "exports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    export_batch_name = Column(String, nullable=False)
    percentage_used = Column(Float, nullable=False)  # e.g., 30.0, 40.0, 80.0
    total_leads_exported = Column(Integer, nullable=False)
    eligible_leads_count = Column(Integer, nullable=True)  # total eligible before selection
    exported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    filters_applied = Column(String, nullable=True)  # JSON string of filters
    seed_value = Column(Integer, nullable=True)  # for reproducibility
    
    def __repr__(self):
        return f"<Export(batch='{self.export_batch_name}', percentage={self.percentage_used}%, count={self.total_leads_exported})>"


class ExportLead(Base):
    """
    Junction table linking exports to leads (many-to-many)
    Tracks which leads were included in which exports
    """
    __tablename__ = "export_leads"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    export_id = Column(Integer, ForeignKey('exports.id'), nullable=False)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False)
    exported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ExportLead(export_id={self.export_id}, lead_id={self.lead_id})>"


# Create indexes for better query performance
Index('idx_email_lookup', Lead.email)
Index('idx_company_lookup', Lead.company_name)
Index('idx_last_seen', Lead.last_seen_date)
Index('idx_cooldown', Lead.cooldown_until)
Index('idx_export_eligibility', Lead.email, Lead.cooldown_until)
Index('idx_icp_score', Lead.icp_score)

# Index for export_leads junction table
Index('idx_export_lead', ExportLead.export_id, ExportLead.lead_id, unique=True)
