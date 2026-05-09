# ── Scanner Agent ─────────────────────────────────────────────────────────────

SCANNER_SYSTEM = """You are a freelance marketplace analyst.
From a list of gig postings, select the 5 most promising opportunities.
Respond in JSON with this exact format:
{"gigs": [{"description": "...", "posted_budget": 123.0, "url": "..."}]}
Only include gigs with a clearly stated numeric budget greater than zero.
Focus the description on the work required, not deal terms."""

SCANNER_USER_PREFIX = """Select the 5 best opportunities from this gig feed.
Each selected gig should have a detailed, clear description and an unambiguous budget.

Gigs:

"""

SCANNER_USER_SUFFIX = "\n\nRespond with exactly 5 gigs in the JSON format specified."

# ── Specialist Agent ───────────────────────────────────────────────────────────

SPECIALIST_SYSTEM = """You are a freelance rate estimation specialist.
Given a project description, estimate the fair market budget in USD.
Respond with a single number only — no $ sign, no explanation."""

# Few-shot examples: (description, fair_budget_str)
# These represent labelled training data for a lightweight specialist.
SPECIALIST_FEW_SHOTS = [
    ("Build a WordPress landing page with contact form and SEO optimisation", "350"),
    ("Develop a Python REST API with JWT authentication and PostgreSQL integration", "900"),
    ("Create 5 social media graphics for a brand launch campaign", "200"),
    ("Build a machine learning model for customer churn prediction with written report", "1500"),
    ("Write 10 SEO-optimised blog posts for a SaaS product, 500 words each", "450"),
    ("Set up a CI/CD pipeline on AWS with Docker containers and CloudWatch monitoring", "1100"),
    ("Design UI/UX in Figma for an iOS fitness tracker app across 15 screens", "800"),
    ("Build a React Native cross-platform app with push notifications and user auth", "2500"),
    ("Migrate a legacy PHP application to Laravel with tests and documentation", "2200"),
    ("Create a 60-second animated product explainer video with custom voiceover", "800"),
]

# ── Frontier Agent ─────────────────────────────────────────────────────────────

FRONTIER_SYSTEM = """You are an expert at estimating fair market rates for freelance projects.
You are given a project description and several similar historical projects with known budgets.
Estimate the fair market budget in USD. Reply with a single number only."""


def frontier_user(description: str, similars: list, budgets: list) -> str:
    context = "\n\n".join(
        f"Similar project:\n{s}\nFair budget: ${b:.0f}"
        for s, b in zip(similars, budgets)
    )
    return (
        f"Estimate the fair budget for this freelance project:\n\n{description}"
        f"\n\nFor context, here are similar projects:\n\n{context}"
    )
