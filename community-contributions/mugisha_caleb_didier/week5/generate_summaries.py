"""Generate pre-computed summary documents from the knowledge base.

Run: uv run generate_summaries.py (from this directory)
Summaries are ingested alongside KB docs by ingest.py.
"""

import re
from pathlib import Path

WEEK5_DIR = Path(__file__).parent.parent.parent.parent / "week5"
KB_PATH = WEEK5_DIR / "knowledge-base"
SUMMARIES_PATH = Path(__file__).parent / "summaries"


def extract_employee_info(text, name):
    """Extract key facts from an employee markdown file."""
    info = {"name": name}

    summary_match = re.search(r"## Summary\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1)
        for field, key in [
            (r"\*\*Job Title[:\*]*\*?\*?\s*[:]*\s*(.+)", "title"),
            (r"\*\*Location[:\*]*\*?\*?\s*[:]*\s*(.+)", "location"),
            (r"\*\*Current Salary[:\*]*\*?\*?\s*[:]*\s*(.+)", "salary"),
        ]:
            match = re.search(field, summary)
            if match:
                info[key] = match.group(1).strip().rstrip("*").strip()

    career_match = re.search(
        r"## (?:Insurellm )?Career Progression\n(.*?)(?=\n##|\Z)", text, re.DOTALL
    )
    if career_match:
        career_text = career_match.group(1)
        # Find the most recent role (last bullet with date range including "Present")
        present_roles = re.findall(
            r"\*\*.*?Present.*?\*\*[:\s]*\*?\*?(.+?)(?=\n\s*-\s*\*\*|\n##|\Z)",
            career_text,
            re.DOTALL,
        )
        if present_roles:
            info["current_role_details"] = present_roles[-1].strip()

    achievements = []
    for pattern in [
        r"[^.]*(?:improved|increased|reduced|exceeded|achieved|generated|built|spearheaded|implemented|led|designed|developed)[^.]*(?:\d+%|\$[\d,.]+[MBK]?)[^.]*\.",
        r"[^.]*(?:award|Award|IIOTY|Year|Prize|recognized)[^.]*\.",
    ]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            achievement = match.group(0).strip()
            if achievement not in achievements and len(achievement) < 300:
                achievements.append(achievement)
    info["achievements"] = achievements

    return info


def parse_salary(salary_str):
    """Parse salary string to integer for sorting."""
    match = re.search(r"[\d,]+", salary_str)
    return int(match.group(0).replace(",", "")) if match else 0


def extract_contract_info(text, filename):
    """Extract key facts from a contract markdown file."""
    info = {"filename": filename}

    title_line = text.split("\n")[0]
    title_match = re.search(r"Contract with (.+?) for (.+)", title_line)
    if title_match:
        info["client"] = title_match.group(1).strip()
        raw_product = title_match.group(2).strip()
        known_products = {"Bizllm", "Carllm", "Claimllm", "Healthllm", "Homellm", "Lifellm", "Markellm", "Rellm"}
        info["product"] = raw_product
        for p in known_products:
            if raw_product.startswith(p):
                info["product"] = p
                break

    date_match = re.search(r"\*\*Contract Date:\*\*\s*(\w+ \d+,?\s*\d{4})", text)
    if date_match:
        info["date"] = date_match.group(1).strip()
    else:
        date_match = re.search(r"effective (?:as of|from)\s*(\w+ \d+,?\s*\d{4})", text, re.IGNORECASE)
        if date_match:
            info["date"] = date_match.group(1).strip()

    for pattern in [
        r"period of (\d+)\s*months",
        r"term of (\d+)\s*months",
        r"for (?:a )?(\d+)[- ]month",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info["duration_months"] = int(match.group(1))
            break

    subscription_match = re.search(
        r"(?:Subscription|Payment|pricing)[^.]*?\$([\d,]+)(?:\.\d+)?\s*(?:per month|/month)",
        text, re.IGNORECASE
    )
    if subscription_match:
        info["primary_monthly_cost"] = "$" + subscription_match.group(1)

    payment_section = re.search(r"(?:Payment|shall pay).*?(?=\n\d+\.\s*\*\*|\n---|\Z)", text, re.DOTALL | re.IGNORECASE)
    if payment_section:
        costs = re.findall(r"\$([\d,]+)(?:\.\d+)?\s*(?:per month|/month)", payment_section.group(0))
        if costs:
            info["monthly_costs"] = ["$" + c for c in costs]
            if "primary_monthly_cost" not in info:
                info["primary_monthly_cost"] = "$" + costs[0]
    elif not info.get("primary_monthly_cost"):
        cost_match = re.search(r"cost of \$([\d,]+)/month|at \$([\d,]+)/month|\$([\d,]+)\s*per month", text, re.IGNORECASE)
        if cost_match:
            val = cost_match.group(1) or cost_match.group(2) or cost_match.group(3)
            info["primary_monthly_cost"] = "$" + val
            info["monthly_costs"] = ["$" + val]

    total_match = re.search(r"totaling\s*\$([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    if total_match:
        info["total_value"] = "$" + total_match.group(1)
    elif "duration_months" in info and costs:
        try:
            monthly = int(costs[0].replace(",", ""))
            total = monthly * info["duration_months"]
            info["total_value"] = f"${total:,}"
            info["total_calculated"] = True
        except (ValueError, IndexError):
            pass

    tier_match = re.search(
        r"(Basic|Professional|Enterprise|Standard|Premium|Core|Essential|Starter|Business)\s*(?:Tier|Plan)",
        text,
        re.IGNORECASE,
    )
    if tier_match:
        info["tier"] = tier_match.group(1).strip() + " Tier"

    sig_section_match = re.search(r"\*\*Signatures?:?\*\*(.+)", text, re.DOTALL)
    if sig_section_match:
        sig_section = sig_section_match.group(1)
        # Pattern: **Name**\n**Title**: Role\n**Insurellm
        sig_match = re.search(
            r"\*\*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\*\*\s*\n\*\*Title\*\*:\s*(.+?)(?:\n|$)",
            sig_section
        )
        if sig_match:
            info["signatory_name"] = sig_match.group(1).strip()
            info["signatory_title"] = sig_match.group(2).strip()
        else:
            alt_match = re.search(
                r"\*\*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\(([^)]+)\)",
                sig_section
            )
            if alt_match:
                info["signatory_name"] = alt_match.group(1).strip()
                info["signatory_title"] = alt_match.group(2).strip()

    for pattern, key in [
        (r"([\d,]+)\s*(?:active )?(?:auto )?polic(?:y|ies)", "policies"),
        (r"([\d,]+)\s*(?:covered )?members", "members"),
        (r"(\d+)\s*(?:named )?user licens", "user_licenses"),
        (r"(\d+)\s*states", "states"),
        (r"([\d,]+)\s*claims", "claims"),
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info[key] = match.group(1)

    return info


def extract_product_pricing(text, name):
    """Extract pricing tiers from a product markdown file."""
    info = {"name": name}

    pricing_match = re.search(r"## Pricing\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if pricing_match:
            tiers = re.findall(
            r"\*\*(.+?)\*\*[:\s]*(?:Starting at\s*)?\$([\d,]+)/month",
            pricing_match.group(1),
        )
        info["tiers"] = [
            {"name": n.strip().rstrip(":"), "price": f"${p}/month"} for n, p in tiers
        ]

    return info


def generate_employee_directory(employees):
    """Generate a comprehensive employee directory."""
    sorted_emps = sorted(employees, key=lambda e: parse_salary(e.get("salary", "0")), reverse=True)
    lines = [
        "# Insurellm Complete Employee Directory",
        "",
        f"Insurellm has {len(employees)} employees as of 2025.",
        "",
        "## All Employees (sorted by salary, highest to lowest)",
        "",
    ]

    for emp in sorted_emps:
        salary = emp.get("salary", "N/A")
        lines.append(f"- **{emp['name']}**: {emp.get('title', 'N/A')}, {salary}, {emp.get('location', 'N/A')}")

    salaries = [(e["name"], e.get("title", ""), parse_salary(e.get("salary", "0")))
                for e in employees if e.get("salary")]
    under_80k = [(n, t, s) for n, t, s in salaries if s < 80000 and s > 0]
    under_100k = [(n, t, s) for n, t, s in salaries if s < 100000 and s > 0]

    lines.extend([
        "",
        "## Employees with Current Salary Under $80,000",
        "",
    ])
    if under_80k:
        for name, title, sal in sorted(under_80k, key=lambda x: x[2]):
            lines.append(f"- {name}: {title}, ${sal:,}")
        lines.append(f"\nTotal employees with salary under $80,000: {len(under_80k)}")
    else:
        lines.append("No employees currently have a salary under $80,000.")

    lines.extend([
        "",
        "## Employees with Current Salary Under $100,000",
        "",
    ])
    if under_100k:
        for name, title, sal in sorted(under_100k, key=lambda x: x[2]):
            lines.append(f"- {name}: {title}, ${sal:,}")
        lines.append(f"\nTotal employees with salary under $100,000: {len(under_100k)}")

    locations = {}
    for emp in sorted_emps:
        loc = emp.get("location", "Unknown")
        locations.setdefault(loc, []).append(emp)

    lines.extend(["", "## Employees by Location", ""])
    for loc in sorted(locations.keys()):
        emps = locations[loc]
        lines.append(f"### {loc} ({len(emps)} employees)")
        for emp in emps:
            lines.append(f"- {emp['name']}: {emp.get('title', 'N/A')}, {emp.get('salary', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def generate_employee_achievements(employees):
    """Generate summary of all employee achievements and performance metrics."""
    lines = [
        "# Insurellm Employee Achievements and Performance Metrics",
        "",
        "Key achievements, awards, and numerical performance data for all employees.",
        "",
    ]

    for emp in sorted(employees, key=lambda e: e["name"]):
        details = []
        if emp.get("achievements"):
            details.extend(emp["achievements"])
        if emp.get("current_role_details"):
            role_text = emp["current_role_details"]
            # Extract bullet points about what they do
            for bullet in re.findall(r"[*-]\s*(.+)", role_text):
                if any(kw in bullet.lower() for kw in ["product", "lead", "develop", "manage", "design", "build", "work"]):
                    details.append(bullet.strip())

        if details:
            lines.append(f"## {emp['name']} ({emp.get('title', 'N/A')})")
            for detail in details:
                # Clean up the detail text
                clean = detail.strip().lstrip("*- ").strip()
                if clean:
                    lines.append(f"- {clean}")
            lines.append("")

    return "\n".join(lines)


def generate_contract_portfolio(contracts):
    """Generate comprehensive contract portfolio summary with aggregated totals."""
    by_product = {}
    for c in contracts:
        product = c.get("product", "Unknown")
        by_product.setdefault(product, []).append(c)

    lines = [
        "# Insurellm Contract Portfolio - Complete Summary",
        "",
        f"Insurellm manages {len(contracts)} active contracts across {len(by_product)} product lines.",
        "",
        "## Contract Count by Product",
        "",
    ]

    for product in sorted(by_product.keys()):
        lines.append(f"- **{product}**: {len(by_product[product])} contracts")

    lines.append("")

    for product in sorted(by_product.keys()):
        product_contracts = by_product[product]
        lines.append(f"## {product} Contracts ({len(product_contracts)} total)")
        lines.append("")

        product_total = 0
        for c in product_contracts:
            lines.append(f"### {c.get('client', 'Unknown Client')}")
            if c.get("tier"):
                lines.append(f"- Tier: {c['tier']}")
            if c.get("primary_monthly_cost"):
                lines.append(f"- Monthly Cost: {c['primary_monthly_cost']}/month")
            if c.get("monthly_costs") and len(c["monthly_costs"]) > 1:
                lines.append(f"- All monthly rates: {', '.join(c['monthly_costs'])}")
            if c.get("total_value"):
                lines.append(f"- Total Contract Value: {c['total_value']}")
                # Parse total for aggregation
                total_str = c["total_value"].replace("$", "").replace(",", "")
                try:
                    product_total += int(float(total_str))
                except ValueError:
                    pass
            if c.get("duration_months"):
                years = c["duration_months"] / 12
                lines.append(f"- Duration: {c['duration_months']} months ({years:.0f} year{'s' if years != 1 else ''})")
            if c.get("date"):
                lines.append(f"- Effective Date: {c['date']}")
            if c.get("signatory_name"):
                lines.append(f"- Signed by: {c['signatory_name']} ({c.get('signatory_title', '')}) on behalf of Insurellm")
            if c.get("members"):
                lines.append(f"- Covered Members: {c['members']}")
            if c.get("policies"):
                lines.append(f"- Active Policies: {c['policies']}")
            if c.get("states"):
                lines.append(f"- States: {c['states']}")
            if c.get("user_licenses"):
                lines.append(f"- User Licenses: {c['user_licenses']}")
            if c.get("claims"):
                lines.append(f"- Projected Claims: {c['claims']}")
            lines.append("")

        if product_total > 0:
            lines.append(f"**Total {product} Contract Value: ${product_total:,}**")
            lines.append("")

    contracts_with_duration = [
        (c, c["duration_months"]) for c in contracts if c.get("duration_months")
    ]
    contracts_with_duration.sort(key=lambda x: -x[1])

    lines.extend(["## Contract Duration Comparison (Longest to Shortest)", ""])
    for c, dur in contracts_with_duration:
        years = dur / 12
        lines.append(
            f"- {c.get('client', 'Unknown')} ({c.get('product', '?')}): {dur} months ({years:.0f} year{'s' if years != 1 else ''})"
        )

    if contracts_with_duration:
        longest = contracts_with_duration[0]
        lines.extend([
            "",
            f"The longest contract duration is {longest[1]} months ({longest[1] / 12:.0f} years) "
            f"for the {longest[0].get('client', 'Unknown')} {longest[0].get('product', '')} contract.",
        ])

    return "\n".join(lines)


def generate_product_pricing(products):
    """Generate product pricing summary."""
    lines = [
        "# Insurellm Product Pricing - Complete Guide",
        "",
        f"Insurellm offers {len(products)} insurance software products.",
        "",
    ]

    for product in sorted(products, key=lambda x: x["name"]):
        lines.append(f"## {product['name']}")
        if product.get("tiers"):
            for tier in product["tiers"]:
                lines.append(f"- **{tier['name']}**: {tier['price']}")
        else:
            lines.append("- Contact sales for pricing.")
        lines.append("")

    return "\n".join(lines)


def main():
    SUMMARIES_PATH.mkdir(exist_ok=True)

    # Parse employees
    employees = []
    for f in sorted((KB_PATH / "employees").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        employees.append(extract_employee_info(text, f.stem))

    # Parse contracts
    contracts = []
    for f in sorted((KB_PATH / "contracts").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        contracts.append(extract_contract_info(text, f.stem))

    # Parse products
    products = []
    for f in sorted((KB_PATH / "products").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        products.append(extract_product_pricing(text, f.stem))

    # Generate and write summaries
    summaries = {
        "employee_directory.md": generate_employee_directory(employees),
        "employee_achievements.md": generate_employee_achievements(employees),
        "contract_portfolio.md": generate_contract_portfolio(contracts),
        "product_pricing.md": generate_product_pricing(products),
    }

    for filename, content in summaries.items():
        (SUMMARIES_PATH / filename).write_text(content, encoding="utf-8")

    print(f"Generated {len(summaries)} summary documents in {SUMMARIES_PATH}")
    print(f"  - employee_directory.md ({len(employees)} employees)")
    print(f"  - employee_achievements.md")
    print(f"  - contract_portfolio.md ({len(contracts)} contracts)")
    print(f"  - product_pricing.md ({len(products)} products)")


if __name__ == "__main__":
    main()
