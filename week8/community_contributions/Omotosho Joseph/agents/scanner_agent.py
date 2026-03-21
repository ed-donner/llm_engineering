from typing import Optional, List
from openai import OpenAI
from agents.job_listings import ScrapedJob, JobSelection
from agents.agent import Agent


class ScannerAgent(Agent):
    MODEL = "gpt-4o-mini"

    SYSTEM_PROMPT = """You identify and summarize the 5 most promising job listings from a list.
    Select listings that have the most detailed job description and the clearest salary information.
    Respond strictly in JSON. You should provide the salary as a number derived from the description.
    If a salary range is given, use the midpoint. Convert hourly rates to annual (multiply by 2080).
    If the salary isn't clear, do not include that listing.
    Most important is that you respond with the 5 listings that have the most detailed job description with salary.
    Focus on the role itself, not perks or benefits.
    """

    USER_PROMPT_PREFIX = """Respond with the most promising 5 job listings from this list,
    selecting those with the most detailed job description and a clear salary greater than 0.
    Summarize each job's description focusing on the role, responsibilities, and requirements.
    Remember to respond with a short paragraph in the description field for each listing.

    Job Listings:

    """

    USER_PROMPT_SUFFIX = "\n\nInclude exactly 5 listings, no more."

    name = "Scanner Agent"
    color = Agent.CYAN

    def __init__(self):
        self.log("Scanner Agent is initializing")
        self.openai = OpenAI()
        self.log("Scanner Agent is ready")

    def fetch_jobs(self, memory) -> List[ScrapedJob]:
        self.log("Scanner Agent is fetching job listings from RSS feeds")
        urls = [opp.listing.url for opp in memory]
        scraped = ScrapedJob.fetch()
        result = [s for s in scraped if s.url not in urls]
        self.log(f"Scanner Agent received {len(result)} new job listings")
        return result

    def make_user_prompt(self, scraped) -> str:
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += "\n\n".join([s.describe() for s in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def scan(self, memory: List[str] = []) -> Optional[JobSelection]:
        """
        Scrape RSS feeds and use structured outputs to parse job listings.
        """
        scraped = self.fetch_jobs(memory)
        if scraped:
            user_prompt = self.make_user_prompt(scraped)
            self.log("Scanner Agent is calling OpenAI using Structured Outputs")
            result = self.openai.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=JobSelection,
            )
            result = result.choices[0].message.parsed
            result.listings = [l for l in result.listings if l.salary > 0]
            self.log(
                f"Scanner Agent received {len(result.listings)} listings with salary>0"
            )
            return result
        return None

    def test_scan(self, memory: List[str] = []) -> Optional[JobSelection]:
        """Return test data for development without live RSS feeds."""
        results = {
            "listings": [
                {
                    "job_title": "Senior Data Scientist",
                    "company": "TechCorp Inc",
                    "salary": 185000,
                    "location": "San Francisco, CA",
                    "description": "Lead ML initiatives for recommendation systems. Requires 5+ years with Python, TensorFlow, and large-scale data. PhD preferred.",
                    "url": "https://example.com/job/senior-ds-techcorp",
                },
                {
                    "job_title": "Machine Learning Engineer",
                    "company": "AI Startup Labs",
                    "salary": 165000,
                    "location": "Remote",
                    "description": "Build and deploy production ML models for NLP. Strong background in transformers, PyTorch, and cloud infrastructure required.",
                    "url": "https://example.com/job/mle-aistartup",
                },
                {
                    "job_title": "Data Analyst",
                    "company": "FinanceHub",
                    "salary": 95000,
                    "location": "New York, NY",
                    "description": "Analyze financial datasets and create dashboards. Requires SQL, Python, and Tableau. 2+ years in financial services.",
                    "url": "https://example.com/job/da-financehub",
                },
                {
                    "job_title": "DevOps Engineer",
                    "company": "CloudScale Systems",
                    "salary": 155000,
                    "location": "Seattle, WA",
                    "description": "Manage CI/CD pipelines and Kubernetes clusters at scale. AWS certifications and 4+ years infrastructure experience required.",
                    "url": "https://example.com/job/devops-cloudscale",
                },
            ]
        }
        return JobSelection(**results)
