from salary_predictor.jobs import Job
import re

MIN_CHARS = 100
MIN_SALARY = 15_000
MAX_SALARY = 500_000
MAX_TEXT = 3000


def simplify(text) -> str:
    """Return a simplified string without too much whitespace"""
    if text is None:
        return ""
    return (
        str(text)
        .replace("\n", " ")
        .replace("\r", "")
        .replace("\t", " ")
        .replace("  ", " ")
        .strip()[:MAX_TEXT]
    )


def scrub(title, company, location, description, skills, schedule_type) -> str:
    """Return a cleansed full string"""
    result = f"Job Title: {title}\n"
    if company:
        result += f"Company: {simplify(company)}\n"
    if location:
        result += f"Location: {simplify(location)}\n"
    if schedule_type:
        result += f"Type: {simplify(schedule_type)}\n"
    if skills:
        result += f"Skills: {simplify(skills)}\n"
    if description:
        result += f"Description: {simplify(description)}\n"
    return result.strip()[:MAX_TEXT]


def parse(row):
    """
    Try to create a Job from this datapoint.
    Return the Job if successful, or None if it shouldn't be included.
    """
    try:
        # Try yearly salary first
        salary = row.get("salary_year_avg")
        if salary is None or salary != salary:  # NaN check
            return None
        salary = float(salary)
    except (ValueError, TypeError):
        return None

    if not (MIN_SALARY <= salary <= MAX_SALARY):
        return None

    title = row.get("job_title") or row.get("job_title_short") or ""
    if not title:
        return None

    company = row.get("company_name") or ""
    location = row.get("job_location") or ""
    category = row.get("job_title_short") or "Other"
    skills = row.get("job_skills") or ""
    schedule_type = row.get("job_schedule_type") or ""
    work_from_home = bool(row.get("job_work_from_home", False))

    # Build description from available fields
    description = ""
    # The dataset doesn't have a long job description text field,
    # so we build the full text from available structured fields
    full = scrub(title, company, location, description, skills, schedule_type)

    if len(full) < MIN_CHARS:
        return None

    return Job(
        title=title,
        category=category,
        salary=salary,
        full=full,
        location=location,
        company=company,
        skills=skills,
        schedule_type=schedule_type,
        work_from_home=work_from_home,
    )
