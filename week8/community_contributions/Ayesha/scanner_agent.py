import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List


ARXIV_API = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=20"


@dataclass
class Paper:
    title: str
    summary: str
    url: str
    def describe(self):
        return f"""
Title: {self.title}

Summary: {self.summary}

URL: {self.url}
"""


def fetch_papers() -> List[Paper]:
    r = requests.get(ARXIV_API)

    root = ET.fromstring(r.text)

    papers = []

    for entry in root:

        if entry.tag.endswith("entry"):

            title = ""
            summary = ""
            link = ""

            for child in entry:

                if child.tag.endswith("title"):
                    title = child.text or ""

                elif child.tag.endswith("summary"):
                    summary = child.text or ""

                elif child.tag.endswith("id"):
                    link = child.text or ""

            papers.append(
                Paper(
                    title=title.strip(),
                    summary=summary.strip(),
                    url=link.strip(),
                )
            )

    # print("Fetched papers:", len(papers))
    # print("Entry tag:", entry.tag)

    return papers