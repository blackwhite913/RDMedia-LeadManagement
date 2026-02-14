"""
CSV ingestion and processing logic
Handles Apollo CSV exports with flexible column mapping and deduplication
"""
import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from src.models import Lead, Import


# Column mapping: maps various possible CSV headers to our database fields
COLUMN_MAPPING = {
    # Email variations
    'email': 'email',
    'Email': 'email',
    'email_address': 'email',
    'Email Address': 'email',
    
    # First name variations
    'first_name': 'first_name',
    'First Name': 'first_name',
    'firstname': 'first_name',
    'FirstName': 'first_name',
    
    # Last name variations
    'last_name': 'last_name',
    'Last Name': 'last_name',
    'lastname': 'last_name',
    'LastName': 'last_name',
    
    # Company name variations
    'company_name': 'company_name',
    'Company Name': 'company_name',
    'company': 'company_name',
    'Company': 'company_name',
    'organization': 'company_name',
    'Organization': 'company_name',
    
    # Job title variations
    'job_title': 'job_title',
    'Job Title': 'job_title',
    'title': 'job_title',
    'Title': 'job_title',
    'position': 'job_title',
    'Position': 'job_title',
    
    # Company domain variations
    'company_domain': 'company_domain',
    'Company Domain': 'company_domain',
    'domain': 'company_domain',
    'Domain': 'company_domain',
    'website': 'company_domain',
    'Website': 'company_domain',
    
    # Country variations
    'country': 'country',
    'Country': 'country',
    'location': 'country',
    'Location': 'country',
    
    # City variations
    'city': 'city',
    'City': 'city',
    
    # Company Address (for parsing country if not provided)
    'company_address': 'company_address',
    'Company Address': 'company_address',

    # ICP ranking variations
    'ICP RANK': 'icp_score',
    'icp_rank': 'icp_score',
    'icp rank': 'icp_score',
    'icp_score': 'icp_score',
    'ICP_SCORE': 'icp_score',
    'Perplexity Ranked': 'icp_score',
    'perplexity_ranked': 'icp_score',
}

# Columns to explicitly exclude (Apollo tracking and metadata)
EXCLUDED_COLUMNS = [
    'mobile_phone', 'Mobile Phone', 'mobile', 'Mobile',
    'email_status', 'Email Status', 'emailstatus', 'EmailStatus',
    'email_open', 'Email Open', 'emailopen', 'EmailOpen',
    'qualify_contact', 'Qualify Contact', 'qualifycontact', 'QualifyContact',
    'Secondary Email', 'secondary_email', 'secondaryemail', 'SecondaryEmail',
    'Person Linkedin Url', 'person_linkedin_url', 'personlinkedinurl',
    'Company Linkedin Url', 'company_linkedin_url', 'companylinkedinurl',
    'Twitter Url', 'twitter_url', 'twitterurl',
    '# Employees', 'employees', 'num_employees', 'Employees',
    'Industry', 'industry',
    'Annual Revenue', 'annual_revenue', 'annualrevenue',
]


def normalize_column_name(col_name: str) -> str:
    """
    Normalize a CSV column name to our internal field name
    Returns None if column should be excluded
    """
    # Check if column should be excluded
    if col_name in EXCLUDED_COLUMNS:
        return None
    
    # Map to internal field name
    return COLUMN_MAPPING.get(col_name, None)


def clean_value(value) -> str:
    """
    Clean and normalize a cell value
    - Strip whitespace
    - Convert NaN/None to None
    - Convert to string
    """
    if pd.isna(value) or value is None:
        return None
    
    value_str = str(value).strip()
    return value_str if value_str else None


def normalize_email(email: str) -> str:
    """
    Normalize email for case-insensitive comparison
    """
    if not email:
        return None
    return email.lower().strip()


def extract_country_from_address(address: str) -> str:
    """
    Extract country from Apollo-style Company Address field
    Format: "street, city, state, country, zip"
    Returns the country part or None if not found
    """
    if not address or not isinstance(address, str):
        return None
    
    # Split by comma and get parts
    parts = [p.strip() for p in address.split(',')]
    
    # Apollo format typically has country as the second-to-last part
    # Example: "127 East 9th Street, Los Angeles, California, United States, 90015"
    # Parts: [street, city, state, COUNTRY, zip]
    if len(parts) >= 4:
        # Second to last part is usually the country
        country = parts[-2]
        # Clean up common variations
        if country and len(country) > 1:
            return country
    
    return None


def extract_icp_score(value) -> float:
    """
    Parse ICP score from CSV cell values.
    Supports:
    - numeric cells (e.g., 95)
    - string patterns (e.g., "ICP_SCORE: 95\\nFIT: HIGH")
    - blank/invalid values -> None
    """
    raw = clean_value(value)
    if raw is None:
        return None

    # Direct numeric value.
    try:
        return float(raw)
    except (TypeError, ValueError):
        pass

    # Parse structured text like "ICP_SCORE: 95".
    match = re.search(r'ICP_SCORE:\s*([0-9]+(?:\.[0-9]+)?)', raw, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Fallback: first number anywhere in the string.
    fallback = re.search(r'([0-9]+(?:\.[0-9]+)?)', raw)
    if fallback:
        return float(fallback.group(1))

    return None


def process_csv_file(
    file_path: str,
    db: Session,
    source: str = "apollo"
) -> Dict[str, any]:
    """
    Process a CSV file and import leads into database
    
    Args:
        file_path: Path to CSV file
        db: Database session
        source: Source identifier (default: "apollo")
    
    Returns:
        Dictionary with processing results:
        - success: bool
        - total_rows: int
        - new_leads_inserted: int
        - duplicates_skipped: int
        - errors: list of error messages
    """
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        total_rows = len(df)
        new_leads = 0
        duplicates = 0
        errors = []
        current_date = datetime.utcnow()
        
        # Map columns to internal field names
        column_map = {}
        for col in df.columns:
            mapped = normalize_column_name(col)
            if mapped:
                column_map[col] = mapped
        
        # Check if we have at least an email column
        if 'email' not in column_map.values():
            return {
                "success": False,
                "total_rows": total_rows,
                "new_leads_inserted": 0,
                "duplicates_skipped": 0,
                "errors": ["CSV must contain an email column"]
            }
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Extract and map fields
                lead_data = {}
                for csv_col, internal_col in column_map.items():
                    value = clean_value(row[csv_col])
                    lead_data[internal_col] = value
                
                # Email is required
                email = lead_data.get('email')
                if not email:
                    errors.append(f"Row {idx + 2}: Missing email, skipping")
                    continue
                
                # Extract country from company_address if country field is empty
                if not lead_data.get('country') and lead_data.get('company_address'):
                    extracted_country = extract_country_from_address(lead_data.get('company_address'))
                    if extracted_country:
                        lead_data['country'] = extracted_country

                # Parse ICP score from ranking column (if present).
                if 'icp_score' in lead_data:
                    lead_data['icp_score'] = extract_icp_score(lead_data.get('icp_score'))
                
                # Normalize email for case-insensitive comparison
                email_normalized = normalize_email(email)
                if not email_normalized:
                    errors.append(f"Row {idx + 2}: Invalid email '{email}', skipping")
                    continue
                
                # #region agent log
                import json
                with open('/Users/ayaansheikh/Desktop/RDMedia/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"initial","hypothesisId":"A,D","location":"ingest.py:172","message":"Before duplicate check","data":{"row":int(idx)+2,"email_raw":email,"email_normalized":email_normalized},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                
                # Check if lead already exists (case-insensitive)
                existing_lead = db.query(Lead).filter(
                    Lead.email == email_normalized
                ).first()
                
                # #region agent log
                with open('/Users/ayaansheikh/Desktop/RDMedia/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"initial","hypothesisId":"A,C","location":"ingest.py:183","message":"After duplicate check","data":{"email_normalized":email_normalized,"existing_found":existing_lead is not None,"existing_id":existing_lead.id if existing_lead else None},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                
                if existing_lead:
                    # Update last_seen_date for existing lead
                    existing_lead.last_seen_date = current_date
                    # Refresh score when present in new import.
                    if lead_data.get('icp_score') is not None:
                        existing_lead.icp_score = lead_data.get('icp_score')
                    duplicates += 1
                    # #region agent log
                    with open('/Users/ayaansheikh/Desktop/RDMedia/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"initial","hypothesisId":"A","location":"ingest.py:190","message":"Updating existing lead","data":{"email":email_normalized,"lead_id":existing_lead.id,"duplicates_count":duplicates},"timestamp":int(__import__('time').time()*1000)})+'\n')
                    # #endregion
                else:
                    # #region agent log
                    with open('/Users/ayaansheikh/Desktop/RDMedia/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"initial","hypothesisId":"B,E","location":"ingest.py:198","message":"Before creating new lead","data":{"email":email_normalized,"new_leads_count":new_leads,"total_in_db_before":db.query(Lead).count()},"timestamp":int(__import__('time').time()*1000)})+'\n')
                    # #endregion
                    # Create new lead
                    new_lead = Lead(
                        email=email_normalized,
                        first_name=lead_data.get('first_name'),
                        last_name=lead_data.get('last_name'),
                        company_name=lead_data.get('company_name'),
                        job_title=lead_data.get('job_title'),
                        company_domain=lead_data.get('company_domain'),
                        city=lead_data.get('city'),
                        country=lead_data.get('country'),
                        icp_score=lead_data.get('icp_score'),
                        source=source,
                        first_seen_date=current_date,
                        last_seen_date=current_date
                    )
                    db.add(new_lead)
                    db.flush()  # Flush immediately to detect duplicates within the same batch
                    new_leads += 1
                    # #region agent log
                    with open('/Users/ayaansheikh/Desktop/RDMedia/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"initial","hypothesisId":"B,D","location":"ingest.py:215","message":"After adding new lead","data":{"email":email_normalized,"new_lead_id":new_lead.id if hasattr(new_lead,'id') else None,"new_leads_count":new_leads},"timestamp":int(__import__('time').time()*1000)})+'\n')
                    # #endregion
                
            except Exception as e:
                # #region agent log
                import json
                with open('/Users/ayaansheikh/Desktop/RDMedia/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"initial","hypothesisId":"ALL","location":"ingest.py:223","message":"Exception during row processing","data":{"row":int(idx)+2,"error":str(e),"error_type":type(e).__name__},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                errors.append(f"Row {idx + 2}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        # Create import record for audit trail
        import_record = Import(
            filename="uploaded_file.csv",  # Will be overridden by process_csv_bytes
            source=source,
            total_rows=total_rows,
            inserted_rows=new_leads,
            duplicate_rows=duplicates,
            imported_at=current_date
        )
        db.add(import_record)
        db.commit()
        
        return {
            "success": True,
            "import_id": import_record.id,
            "total_rows": total_rows,
            "new_leads_inserted": new_leads,
            "duplicates_skipped": duplicates,
            "errors": errors[:10]  # Limit to first 10 errors
        }
    
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "total_rows": 0,
            "new_leads_inserted": 0,
            "duplicates_skipped": 0,
            "errors": [f"Failed to process CSV: {str(e)}"]
        }


def process_csv_bytes(
    file_content: bytes,
    filename: str,
    db: Session,
    source: str = "apollo"
) -> Dict[str, any]:
    """
    Process CSV from bytes (for file uploads)
    
    Args:
        file_content: CSV file content as bytes
        filename: Original filename
        db: Database session
        source: Source identifier
    
    Returns:
        Same as process_csv_file
    """
    import io
    import tempfile
    
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        
        # Process the file
        result = process_csv_file(tmp_path, db, source)
        
        # Update the import record with actual filename
        if result.get('success') and result.get('import_id'):
            import_record = db.query(Import).filter(Import.id == result['import_id']).first()
            if import_record:
                import_record.filename = filename
                db.commit()
        
        # Add filename to result
        result['filename'] = filename
        
        # Clean up temp file
        import os
        os.unlink(tmp_path)
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "total_rows": 0,
            "new_leads_inserted": 0,
            "duplicates_skipped": 0,
            "errors": [f"Failed to process uploaded file: {str(e)}"]
        }
