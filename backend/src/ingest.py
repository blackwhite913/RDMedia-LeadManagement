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
from src.utils.location import extract_country


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


def normalize_company_domain(company_domain: str) -> str:
    """
    Normalize company domain for case-insensitive comparison.
    """
    if not company_domain:
        return None
    normalized = company_domain.lower().strip()
    return normalized or None


def is_missing_country(country_value) -> bool:
    """Return True when country is blank-like or N/A."""
    if country_value is None:
        return True
    if not isinstance(country_value, str):
        return False
    cleaned = country_value.strip()
    return cleaned == "" or cleaned.upper() == "N/A"


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
        csv_duplicates = 0
        cooldown_skipped = 0
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
                "csv_duplicates": 0,
                "db_matches": 0,
                "cooldown_skipped": 0,
                "error_rows": 0,
                "errors": ["CSV must contain an email column"]
            }

        # Pre-deduplicate rows inside the CSV by normalized email and domain.
        seen_emails = set()
        seen_domains = set()
        unique_rows = []

        for idx, row in df.iterrows():
            row_email = None
            row_domain = None

            for csv_col, internal_col in column_map.items():
                if internal_col == "email" and row_email is None:
                    row_email = clean_value(row[csv_col])
                elif internal_col == "company_domain" and row_domain is None:
                    row_domain = clean_value(row[csv_col])

            email_normalized = normalize_email(row_email)
            domain_normalized = normalize_company_domain(row_domain)

            # Keep rows with missing email so row-level validation can report errors consistently.
            if not email_normalized:
                unique_rows.append((idx, row))
                continue

            if email_normalized in seen_emails or (
                domain_normalized and domain_normalized in seen_domains
            ):
                csv_duplicates += 1
                continue

            seen_emails.add(email_normalized)
            if domain_normalized:
                seen_domains.add(domain_normalized)
            unique_rows.append((idx, row))
        
        # Process each row
        for idx, row in unique_rows:
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
                
                # Extract country from company_address when country is missing.
                if is_missing_country(lead_data.get('country')):
                    extracted_country = extract_country(lead_data.get('company_address'))
                    lead_data['country'] = extracted_country if extracted_country else None

                # Parse ICP score from ranking column (if present).
                if 'icp_score' in lead_data:
                    lead_data['icp_score'] = extract_icp_score(lead_data.get('icp_score'))
                
                # Normalize email for case-insensitive comparison
                email_normalized = normalize_email(email)
                if not email_normalized:
                    errors.append(f"Row {idx + 2}: Invalid email '{email}', skipping")
                    continue

                # Normalize company domain for case-insensitive deduplication.
                company_domain_normalized = normalize_company_domain(
                    lead_data.get('company_domain')
                )
                lead_data['company_domain'] = company_domain_normalized

                # Check if lead already exists by email OR company domain.
                if company_domain_normalized:
                    existing_lead = db.query(Lead).filter(
                        (Lead.email == email_normalized) |
                        (Lead.company_domain == company_domain_normalized)
                    ).first()
                else:
                    existing_lead = db.query(Lead).filter(
                        Lead.email == email_normalized
                    ).first()

                if existing_lead:
                    # Skip matched lead while cooldown is active.
                    if existing_lead.cooldown_until and existing_lead.cooldown_until > current_date:
                        cooldown_skipped += 1
                        continue

                    # Refresh last_seen_date when lead is outside cooldown.
                    existing_lead.last_seen_date = current_date

                    # Fill missing fields only; keep existing non-null values intact.
                    if not existing_lead.first_name and lead_data.get('first_name'):
                        existing_lead.first_name = lead_data.get('first_name')
                    if not existing_lead.last_name and lead_data.get('last_name'):
                        existing_lead.last_name = lead_data.get('last_name')
                    if not existing_lead.company_name and lead_data.get('company_name'):
                        existing_lead.company_name = lead_data.get('company_name')
                    if not existing_lead.job_title and lead_data.get('job_title'):
                        existing_lead.job_title = lead_data.get('job_title')
                    if not existing_lead.company_domain and company_domain_normalized:
                        existing_lead.company_domain = company_domain_normalized
                    if not existing_lead.city and lead_data.get('city'):
                        existing_lead.city = lead_data.get('city')
                    if is_missing_country(existing_lead.country) and lead_data.get('country'):
                        existing_lead.country = lead_data.get('country')
                    duplicates += 1
                else:
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

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()

        duplicate_rows_total = duplicates + csv_duplicates + cooldown_skipped
        
        # Create import record for audit trail
        import_record = Import(
            filename="uploaded_file.csv",  # Will be overridden by process_csv_bytes
            source=source,
            total_rows=total_rows,
            inserted_rows=new_leads,
            duplicate_rows=duplicate_rows_total,
            imported_at=current_date
        )
        db.add(import_record)
        db.commit()
        
        return {
            "success": True,
            "import_id": import_record.id,
            "total_rows": total_rows,
            "new_leads_inserted": new_leads,
            "duplicates_skipped": duplicate_rows_total,
            "csv_duplicates": csv_duplicates,
            "db_matches": duplicates,
            "cooldown_skipped": cooldown_skipped,
            "error_rows": len(errors),
            "errors": errors[:10]  # Limit to first 10 errors
        }
    
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "total_rows": 0,
            "new_leads_inserted": 0,
            "duplicates_skipped": 0,
            "csv_duplicates": 0,
            "db_matches": 0,
            "cooldown_skipped": 0,
            "error_rows": 0,
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
            "csv_duplicates": 0,
            "db_matches": 0,
            "cooldown_skipped": 0,
            "error_rows": 0,
            "errors": [f"Failed to process uploaded file: {str(e)}"]
        }
