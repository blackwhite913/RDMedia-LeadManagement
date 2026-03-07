"""
AI qualification layer using Perplexity API.
Evaluates companies once per domain and updates all leads for that domain.
Fetch once, group in memory, commit per domain.
"""
import json
import logging
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models import Lead

logger = logging.getLogger(__name__)

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar-pro"
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_DELAY_SEC = 1
THROTTLE_DELAY_SEC = 0.2
PROGRESS_LOG_EVERY = 25
MAX_QUALIFICATION_ERRORS = 50
# Only qualify leads first seen within this many days (e.g. newly uploaded)
QUALIFY_NEW_LEADS_DAYS = 7

SYSTEM_PROMPT = """You are an expert at evaluating B2B outbound prospects. Respond only with valid JSON in the exact format specified."""

USER_PROMPT_TEMPLATE = """Evaluate if this company is a good outbound prospect.

Ideal prospects:

Founder-led consumer brands selling their own products directly to customers.

Examples:

• skincare
• beauty
• cosmetics
• fashion
• supplements
• wellness
• personal care

Bad prospects:

• manufacturers
• suppliers
• wholesalers
• agencies
• consultants
• laboratories
• B2B service companies

Company data:

Company Name: {company_name}
Website: {company_domain}
Job Title: {job_title}
Country: {country}

Return JSON:

{{
 "score": 0-100,
 "tags": ["industry","brand_type"],
 "reason": "short explanation"
}}
"""


def _get_api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not key:
        raise ValueError("PERPLEXITY_API_KEY is not set. Set it in the environment or in a .env file.")
    return key


def _domain_key(lead: Lead) -> Optional[str]:
    """
    Stable key for grouping: normalized domain, or normalized company_name if domain missing.
    Returns None if both are null/empty after normalizing (strip, lowercase).
    """
    domain = (lead.company_domain or "").strip().lower()
    name = (lead.company_name or "").strip().lower()
    if domain:
        return domain
    if name:
        return name
    return None


def _call_perplexity(
    company_name: str,
    company_domain: str,
    job_title: str,
    country: str,
) -> Dict[str, Any]:
    """
    Call Perplexity chat completions and return parsed JSON with score, tags, reason.
    Timeout 20s, up to 3 retries. Raises on missing API key or after retries;
    safe JSON parsing and clear non-200 handling.
    """
    api_key = _get_api_key()
    user_content = USER_PROMPT_TEMPLATE.format(
        company_name=company_name or "-",
        company_domain=company_domain or "-",
        job_title=job_title or "-",
        country=country or "-",
    )
    payload = {
        "model": MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                PERPLEXITY_URL,
                data=body_bytes,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8")
            print(f"[Perplexity] Status: {status}")
            print(f"[Perplexity] Response: {raw[:500]}")
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                raw = e.read().decode("utf-8", errors="replace")[:200]
            except Exception:
                raw = ""
            last_error = ValueError(
                f"Perplexity API returned {status}: {raw}"
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SEC)
                continue
            raise last_error
        except (urllib.error.URLError, OSError) as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SEC)
                continue
            raise
        if status < 200 or status >= 300:
            last_error = ValueError(
                f"Perplexity API returned {status}: {(raw or '')[:200]}"
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SEC)
                continue
            raise last_error
        try:
            data = json.loads(raw)
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError("Invalid JSON from Perplexity") from e
        choice = data.get("choices")
        if not choice or not isinstance(choice, list):
            raise ValueError("Unexpected Perplexity response: no choices")
        message = choice[0].get("message")
        if not message:
            raise ValueError("Unexpected Perplexity response: no message")
        content = message.get("content")
        if not content or not isinstance(content, str):
            raise ValueError("Unexpected Perplexity response: no content")
        content = content.strip()
        try:
            out = json.loads(content)
        except json.JSONDecodeError:
            # Extract JSON from markdown code block or first {...} in text
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    out = json.loads(content[start:end])
                except json.JSONDecodeError as e:
                    raise ValueError("Perplexity response content is not valid JSON") from e
            else:
                raise ValueError("Perplexity response content is not valid JSON")
        if "score" not in out or "tags" not in out or "reason" not in out:
            raise ValueError("Perplexity response missing score, tags, or reason")
        score = out["score"]
        if not isinstance(score, (int, float)):
            raise ValueError("score must be a number")
        score = max(0, min(100, float(score)))
        tags = out["tags"]
        if not isinstance(tags, list):
            tags = [str(tags)]
        else:
            tags = [str(t) for t in tags]
        reason = str(out.get("reason", ""))
        return {"score": score, "tags": tags, "reason": reason}
    raise last_error or ValueError("Request failed after retries")


def get_unscored_leads_grouped_by_domain(db: Session) -> Dict[str, List[Lead]]:
    """
    Fetch unscored leads first seen in the last QUALIFY_NEW_LEADS_DAYS (newly uploaded only).
    Then in Python: require non-empty job_title and valid domain_key. Group by domain_key.
    """
    cutoff = datetime.utcnow() - timedelta(days=QUALIFY_NEW_LEADS_DAYS)
    leads = (
        db.query(Lead)
        .filter(Lead.icp_score.is_(None))
        .filter(Lead.first_seen_date >= cutoff)
        .order_by(Lead.id.asc())
        .all()
    )
    by_domain: Dict[str, List[Lead]] = defaultdict(list)
    for lead in leads:
        key = _domain_key(lead)
        if key is None:
            continue
        if not (lead.job_title and lead.job_title.strip()):
            continue
        by_domain[key].append(lead)
    return dict(by_domain)


def get_qualify_preview(db: Session) -> Dict[str, Any]:
    """Return counts of domains and leads that would be qualified (for UI estimate)."""
    grouped = get_unscored_leads_grouped_by_domain(db)
    domains_count = len(grouped)
    leads_count = sum(len(v) for v in grouped.values())
    # Rough estimate: ~3 seconds per domain (API + throttle)
    estimated_seconds = max(60, domains_count * 3)
    return {
        "domains_count": domains_count,
        "leads_count": leads_count,
        "estimated_seconds": min(estimated_seconds, 30 * 60),
    }


def run_qualification(db: Session) -> Dict[str, Any]:
    """
    Run qualification on unscored leads: group by domain_key, call Perplexity
    once per domain, update leads per domain with per-domain commit/rollback.
    Returns summary with companies_evaluated, leads_updated, errors.
    """
    errors: List[Dict[str, str]] = []
    companies_evaluated = 0
    leads_updated = 0
    processed_count = 0

    grouped = get_unscored_leads_grouped_by_domain(db)
    if not grouped:
        logger.info("Qualification: no newly uploaded unscored leads with valid domain_key and job_title")
        return {
            "companies_evaluated": 0,
            "leads_updated": 0,
            "errors": [],
            "message": f"No unscored leads from the last {QUALIFY_NEW_LEADS_DAYS} days (newly uploaded) with company_domain or company_name and non-empty job_title found.",
        }

    now = datetime.utcnow()

    for domain_key, domain_leads in grouped.items():
        if not domain_leads:
            continue
        representative = domain_leads[0]
        company_name = representative.company_name or ""
        job_title = representative.job_title or ""
        country = representative.country or ""
        try:
            result = _call_perplexity(
                company_name=company_name,
                company_domain=domain_key,
                job_title=job_title,
                country=country,
            )
        except Exception as e:
            err_msg = str(e)
            logger.warning("Qualification failed for domain %s: %s", domain_key, err_msg)
            errors.append({"domain": domain_key, "error": err_msg})
            processed_count += 1
            if processed_count % PROGRESS_LOG_EVERY == 0:
                logger.info(
                    "Qualification progress: %d domains processed, %d evaluated, %d errors",
                    processed_count,
                    companies_evaluated,
                    len(errors),
                )
            if len(errors) >= MAX_QUALIFICATION_ERRORS:
                logger.error(
                    "Qualification aborted: reached %d consecutive errors. Last error: %s",
                    MAX_QUALIFICATION_ERRORS,
                    err_msg,
                )
                break
            continue

        try:
            score = result["score"]
            tags_json = json.dumps(result["tags"])
            reason = result["reason"] or ""
            for lead in domain_leads:
                lead.icp_score = score
                lead.qualification_tags = tags_json
                lead.qualified_at = now
                lead.qualification_reason = reason
            db.commit()
            companies_evaluated += 1
            leads_updated += len(domain_leads)
        except Exception as e:
            db.rollback()
            err_msg = str(e)
            logger.warning("DB update failed for domain %s: %s", domain_key, err_msg)
            errors.append({"domain": domain_key, "error": err_msg})

        processed_count += 1
        if processed_count % PROGRESS_LOG_EVERY == 0:
            logger.info(
                "Qualification progress: %d domains processed, %d evaluated, %d errors",
                processed_count,
                companies_evaluated,
                len(errors),
            )
        time.sleep(THROTTLE_DELAY_SEC)

    logger.info(
        "Qualification complete: companies_evaluated=%d leads_updated=%d api_errors=%d",
        companies_evaluated,
        leads_updated,
        len(errors),
    )
    return {
        "companies_evaluated": companies_evaluated,
        "leads_updated": leads_updated,
        "errors": errors,
    }


def test_perplexity_call() -> None:
    """Smoke-test: run a single Perplexity request and print the result."""
    api_key = _get_api_key()
    print(f"Perplexity key loaded: {api_key[:6]}...")
    result = _call_perplexity(
        company_name="Glossier",
        company_domain="glossier.com",
        job_title="Founder",
        country="United States",
    )
    print("Test result:", result)
