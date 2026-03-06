import re
from src.job_item import JobItem

def extract_salary(text):

    if not text:
        return None

    numbers = re.findall(r"\d[\d,\.]*", text)

    if len(numbers) == 0:
        return None

    values = [float(n.replace(",", "")) for n in numbers]

    salary = sum(values) / len(values)

    text_lower = text.lower()

    if "hour" in text_lower:
        salary = salary * 2080

    if "month" in text_lower:
        salary = salary * 12

    return salary

def parse(row):

    salary = extract_salary(row.get("salary"))

    title = row.get("positionName")
    company = row.get("company")
    location = row.get("location")
    description = row.get("description")

    if not all([salary, title, company, location, description]):
        return None

    return JobItem(
        title=title,
        company=company,
        location=location,
        experience="Unknown",
        skills=description[:300],
        salary=salary,
        description=description
    )