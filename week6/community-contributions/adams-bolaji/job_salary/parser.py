"""Parse job datapoints from lukebarousse/data_jobs into Job objects."""

from typing import Any, Optional

from job_salary.items import Job

MIN_SALARY = 15_000  # USD yearly
MAX_SALARY = 500_000
MIN_CHARS = 50
MAX_TEXT_TOTAL = 4000


def _skills_to_text(skills: list[str] | None) -> str:
    """Convert job_skills list to a readable string."""
    if not skills:
        return ""
    if isinstance(skills, list):
        return ", ".join(str(s) for s in skills[:30])  # limit for size
    return str(skills)


def _simplify(text: Any) -> str:
    """Return a simplified string, limited length."""
    s = str(text).replace("\n", " ").replace("\r", "").replace("\t", "").strip()
    return s[:1500]


def build_full(datapoint: dict) -> str:
    """Build full job description text from datapoint fields."""
    parts = []

    title = datapoint.get("job_title") or datapoint.get("job_title_short") or ""
    if title:
        parts.append(f"Title: {_simplify(title)}")

    company = datapoint.get("company_name") or ""
    if company:
        parts.append(f"Company: {_simplify(company)}")

    location = datapoint.get("job_location") or datapoint.get("search_location") or ""
    if location:
        parts.append(f"Location: {_simplify(location)}")

    country = datapoint.get("job_country") or ""
    if country:
        parts.append(f"Country: {country}")

    schedule = datapoint.get("job_schedule_type") or ""
    if schedule:
        parts.append(f"Schedule: {schedule}")

    remote = datapoint.get("job_work_from_home")
    if remote is True:
        parts.append("Remote: Yes")
    elif remote is False:
        parts.append("Remote: No")

    skills = datapoint.get("job_skills")
    if skills:
        parts.append(f"Skills: {_skills_to_text(skills)}")

    job_type_skills = datapoint.get("job_type_skills")
    if isinstance(job_type_skills, dict):
        for k, v in job_type_skills.items():
            if v:
                v_str = v if isinstance(v, str) else ", ".join(str(x) for x in (v[:10] if isinstance(v, list) else v))
                parts.append(f"{k}: {v_str}")

    full = "\n".join(parts).strip()[:MAX_TEXT_TOTAL]
    return full


def parse(datapoint: dict) -> Optional[Job]:
    """
    Parse a datapoint from lukebarousse/data_jobs into a Job.
    Returns None if salary is missing or out of range.
    """
    salary_raw = datapoint.get("salary_year_avg")
    if salary_raw is None:
        # Fallback: hourly * 2080 for rough annual
        hour_avg = datapoint.get("salary_hour_avg")
        if hour_avg is not None and isinstance(hour_avg, (int, float)):
            salary_raw = float(hour_avg) * 2080
        else:
            return None

    try:
        salary = float(salary_raw)
    except (ValueError, TypeError):
        return None

    if not (MIN_SALARY <= salary <= MAX_SALARY):
        return None

    title = datapoint.get("job_title") or datapoint.get("job_title_short") or "Unknown"
    category = datapoint.get("job_title_short") or datapoint.get("job_title") or "Other"
    full = build_full(datapoint)

    if len(full) < MIN_CHARS:
        return None

    company = datapoint.get("company_name") or ""
    location = datapoint.get("job_location") or datapoint.get("search_location") or ""
    remote = datapoint.get("job_work_from_home")

    return Job(
        title=str(title)[:200],
        category=str(category)[:100],
        salary=salary,
        full=full,
        company=company or None,
        location=location or None,
        remote=remote,
    )
