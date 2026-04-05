"""Backfill missing country values for existing leads."""
from sqlalchemy import func, or_

from src.db import SessionLocal
from src.models import Lead
from src.utils.location import infer_country_from_city


def _is_missing_country(country_value) -> bool:
    if country_value is None:
        return True
    if not isinstance(country_value, str):
        return False
    cleaned = country_value.strip()
    return cleaned == "" or cleaned.upper() == "N/A"


def run_backfill() -> None:
    db = SessionLocal()
    try:
        leads = db.query(Lead).filter(
            or_(
                Lead.country.is_(None),
                func.trim(Lead.country) == "",
                func.lower(Lead.country) == "n/a",
            )
        ).all()

        updated = 0
        skipped = 0

        for lead in leads:
            inferred_country = infer_country_from_city(lead.city)
            if inferred_country:
                lead.country = inferred_country
                updated += 1
            else:
                skipped += 1

        db.commit()

        print(f"Scanned leads: {len(leads)}")
        print(f"Updated countries: {updated}")
        print(f"Skipped (no inference): {skipped}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_backfill()

