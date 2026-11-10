"""
Summarize a website and its published blog articles using Ollama.
"""

from urllib.parse import urlparse

import requests
from openai import OpenAI

from scraper import fetch_page


OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL = "llama3.2"

# Limit the crawl so the program does not download the entire website.
MAX_ARTICLES = 5

# Replace this with your website's homepage.
WEBSITE_URL = "https://christopherburt.dev"


ollama = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama",
)



system_prompt = """
You are writing a consensual comedy roast of an AI professional's
website. Your subject explicitly wants sharp sarcasm, irony, puns,
and witty criticism.

Your default tone is a late-night comedy monologue, not a consultant's
report. Every paragraph must contain a punchline, sarcastic
observation, absurd comparison, or pun.

Target the website's copy, buzzwords, headlines, positioning, and
ideas. Do not attack protected characteristics or invent personal
facts.

Banned dry-review phrases include:

- "This is interesting"
- "This is insightful"
- "This is compelling"
- "This is valuable"
- "This is thought-provoking"
- "The author does a good job"
- "This article effectively explores"

If you use praise as a comedic setup, undercut it immediately in the
same sentence.

Stay accurate to the supplied source material, but commit fully to
the roast.

Respond in Markdown without wrapping it in a code block.
"""


def normalized_hostname(url):
    """
    Return a hostname without a leading 'www.'.

    For example:
    www.example.com becomes example.com.
    """
    hostname = urlparse(url).hostname or ""
    return hostname.removeprefix("www.")


def is_internal_link(link_url, website_url):
    """
    Return True when both URLs belong to the same website.
    """
    return normalized_hostname(link_url) == normalized_hostname(website_url)


def find_blog_page(homepage):
    """
    Inspect homepage links and find the most likely blog index.
    """
    blog_words = (
        "blog",
        "blogs",
        "articles",
        "writing",
        "insights",
        "posts",
    )

    candidates = []

    for link in homepage["links"]:
        if not is_internal_link(link["url"], homepage["url"]):
            continue

        searchable_text = (
            link["text"] + " " + link["url"]
        ).lower()

        if any(word in searchable_text for word in blog_words):
            candidates.append(link)

    if not candidates:
        return None

    # A short URL such as /blog is more likely to be the blog index
    # than a longer URL such as /blog/my-first-article.
    return min(
        candidates,
        key=lambda link: len(urlparse(link["url"]).path.split("/")),
    )


def find_article_links(blog_page, website_url):
    """
    Find likely article links on the blog index.
    """
    blog_path = urlparse(blog_page["url"]).path.rstrip("/")

    excluded_path_parts = (
        "/tag/",
        "/tags/",
        "/category/",
        "/categories/",
        "/author/",
        "/archive/",
        "/page/",
        "/feed",
        "/login",
    )

    excluded_file_types = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".pdf",
        ".zip",
    )

    article_links = []
    seen_urls = set()

    for link in blog_page["links"]:
        article_url = link["url"]
        article_path = urlparse(article_url).path.rstrip("/")
        link_text = link["text"].strip()

        if article_url in seen_urls:
            continue

        if not is_internal_link(article_url, website_url):
            continue

        if article_url.rstrip("/") == blog_page["url"].rstrip("/"):
            continue

        if any(part in article_path.lower() for part in excluded_path_parts):
            continue

        if article_path.lower().endswith(excluded_file_types):
            continue

        # Most websites store articles underneath the blog path:
        # /blog/article-title
        is_under_blog_path = (
            bool(blog_path)
            and article_path.startswith(blog_path + "/")
        )

        # Some platforms mark article cards with an <article> element.
        is_article_card = link["inside_article"]

        # Very short text such as "Home" or "Next" is unlikely to be
        # an article title.
        has_meaningful_title = len(link_text) >= 8

        if has_meaningful_title and (
            is_under_blog_path or is_article_card
        ):
            seen_urls.add(article_url)
            article_links.append(link)

    return article_links[:MAX_ARTICLES]


def collect_website_content(website_url):
    """
    Fetch the homepage, blog index, and individual articles.

    Return them separately so Ollama can analyze each part of the
    website independently.
    """
    print(f"Reading homepage: {website_url}")
    homepage = fetch_page(website_url)

    website = {
        "homepage": homepage,
        "blog_page": None,
        "articles": [],
    }

    blog_link = find_blog_page(homepage)

    if blog_link is None:
        print("No blog page was discovered on the homepage.")
        return website

    print(f'Blog page discovered: {blog_link["url"]}')
    blog_page = fetch_page(blog_link["url"])
    website["blog_page"] = blog_page

    article_links = find_article_links(
        blog_page=blog_page,
        website_url=homepage["url"],
    )

    print(f"Discovered {len(article_links)} article(s).")

    for article_number, link in enumerate(article_links, start=1):
        print(f'Reading article {article_number}: {link["url"]}')

        try:
            article = fetch_page(link["url"])
            website["articles"].append(article)

        except requests.RequestException as error:
            print(f'Could not read {link["url"]}: {error}')

    return website


def format_page(page):
    """
    Convert one scraped page into text Ollama can understand.
    """
    return f"""
URL: {page["url"]}
Title: {page["title"]}

PAGE CONTENT:

{page["text"]}
"""


def ask_ollama(task, source_material):
    """
    Send one focused roasting task to Ollama.
    """
    user_prompt = f"""
{task}

SOURCE MATERIAL:

{source_material}
"""

    response = ollama.chat.completions.create(
        model=MODEL,
        temperature=1.0,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    return response.choices[0].message.content


def summarize(website_url):
    """
    Generate separate roasts for the homepage, Blog feature,
    and published articles.
    """
    website = collect_website_content(website_url)

    print("Generating the homepage roast...")

    homepage_task = """
Roast the main website homepage.

Discuss what the owner is presenting, including the positioning,
capabilities, AI terminology, professional pitch, digital twin,
and calls to action.

Requirements:

- Write three to five short paragraphs.
- Every paragraph must contain a joke, sarcastic observation,
  ridiculous comparison, or pun.
- Include at least two AI-related puns.
- Target the copy and marketing language, not the person.
- Do not discuss the blog yet.
- Do not call anything interesting, insightful, impressive,
  compelling, valuable, or thoughtful unless you immediately
  undercut that praise with a joke.
- Do not write like a business consultant.
"""

    homepage_roast = ask_ollama(
        task=homepage_task,
        source_material=format_page(website["homepage"]),
    )

    if website["blog_page"] is None:
        return f"""
# The Website Roast

{homepage_roast}

# The Blog Feature Roast

The crawler could not find a Blog page. Apparently even the crawler
decided it had consumed enough thought leadership for one day.
"""

    print("Generating the Blog feature roast...")

    blog_feature_task = """
Analyze and roast the Blog feature as a section of the website.

This task concerns the Blog page as a whole—not the complete contents
of the individual articles.

Discuss:

- How the Blog is introduced and positioned
- The subjects the author repeatedly writes about
- The article titles and their tone
- The apparent editorial personality
- How the Blog supports or contradicts the main website
- Whether the collection feels practical, grandiose, repetitive,
  trend-driven, or some glorious combination of all four

Requirements:

- Write three to five short paragraphs.
- Include at least three specific jokes based on the supplied text.
- Include at least two puns.
- Treat the Blog as a website feature, not merely as a list of posts.
- Do not lapse into respectful literary criticism.
- Avoid generic praise.
"""

    blog_feature_roast = ask_ollama(
        task=blog_feature_task,
        source_material=format_page(website["blog_page"]),
    )

    if not website["articles"]:
        article_roast = (
            "No individual articles were discovered. The Blog has "
            "successfully achieved retrieval-augmented invisibility."
        )
    else:
        print("Generating the individual article roasts...")

        article_sections = []

        for article_number, article in enumerate(
            website["articles"],
            start=1,
        ):
            # Limiting each excerpt keeps the local model focused.
            article_sections.append(
                f"""
ARTICLE {article_number}

URL: {article["url"]}
Title: {article["title"]}

CONTENT:

{article["text"][:2_500]}
"""
            )

        article_source_material = "\n\n---\n\n".join(article_sections)

        article_task = """
Roast every supplied blog article individually.

For each article, use this format:

## Exact article title

**What it says:** Give one accurate sentence explaining the article.

**The roast:** Give a specific, sarcastic critique containing at
least one joke and one pun.

**Source:** Include the exact supplied URL.

Requirements:

- Cover every supplied article.
- Make each roast specific to that article.
- Do not describe an article as interesting, insightful, compelling,
  valuable, thoughtful, timely, or important.
- Do not congratulate the author.
- Do not invent claims or quotations.
- Humor is mandatory, not optional.
- Finish with a short, sarcastic verdict about the author's overall
  relationship with artificial intelligence.
"""

        article_roast = ask_ollama(
            task=article_task,
            source_material=article_source_material,
        )

    return f"""
# The Website Roast

{homepage_roast}

# The Blog Feature Roast

{blog_feature_roast}

# The Individual Article Roasts

{article_roast}
"""


if __name__ == "__main__":
    result = summarize(WEBSITE_URL)

    print("\n")
    print("=" * 60)
    print("OLLAMA WEBSITE ROAST")
    print("=" * 60)
    print(result)
