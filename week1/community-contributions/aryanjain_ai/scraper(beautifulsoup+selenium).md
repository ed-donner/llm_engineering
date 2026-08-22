# Web Scraping for GenAI — Requests, BeautifulSoup, Selenium & Playwright

## 1. Why Web Scraping?

In a GenAI application, we may want to give an LLM information from a webpage.

For example:
```text
User
  ↓
URL
  ↓
Web Scraper
  ↓
Extract webpage text
  ↓
LLM
  ↓
Summary
```

**Example:**
```python
display_summary("https://example.com")
```

The scraper first needs to obtain the webpage content. There are different ways to do this.

## 2. The Three Main Approaches

We can broadly use:

1. `requests` + `BeautifulSoup`
2. `Selenium`
3. `Selenium` + `BeautifulSoup`

There is also:

4. `Playwright`

The important thing is that these tools solve different problems.

## 3. requests

`requests` is an HTTP client. It sends a request to a website and receives the server's response.

```python
import requests

response = requests.get("https://example.com")
print(response.text)
```

**The flow is:**
```text
Python
  ↓
requests.get()
  ↓
Website Server
  ↓
HTML response
  ↓
Python
```

> **Important**
> `requests` does not normally behave like a browser.
> It does **not**:
> - execute JavaScript like Chrome
> - click buttons
> - scroll the page
> - interact with forms
> - wait for dynamic content

## 4. BeautifulSoup

BeautifulSoup is an HTML parser. It takes HTML and makes it easier to search and extract information from it.

```python
from bs4 import BeautifulSoup

html = """
<html>
    <body>
        <h1>Hello</h1>
        <p>This is a paragraph.</p>
    </body>
</html>
"""

soup = BeautifulSoup(html, "html.parser")
print(soup.find("h1").text)
```

**Output:**
```text
Hello
```

BeautifulSoup can help with:
- `soup.find()`
- `soup.find_all()`
- `soup.select()`

And extracting:
- `element.text`
- `element.get_text()`
- `element["href"]`

## 5. Requests + BeautifulSoup

For a simple/static website, this is usually the best approach.

```text
Website
  ↓
requests
  ↓
HTML
  ↓
BeautifulSoup
  ↓
Extract content
```

**Example:**
```python
import requests
from bs4 import BeautifulSoup

url = "https://example.com"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

title = soup.find("h1")

if title:
    print(title.get_text(strip=True))
```

## 6. Why does this sometimes fail?

Suppose a website is heavily dependent on JavaScript.

You request:
```python
response = requests.get(url)
```

The server might initially return something like:
```html
<div id="root"></div>
<script src="app.js"></script>
```
The actual content is then created by JavaScript in the browser.

So:
```text
requests
  ↓
Initial HTML
  ↓
JavaScript hasn't executed
  ↓
Important content missing
```

But when you open the same website in Chrome:
```text
Chrome
  ↓
HTML
  ↓
JavaScript
  ↓
JavaScript executes
  ↓
Additional requests
  ↓
Content appears
```
This explains why a scraper may work on one website but fail on another.

## 7. Example: JavaScript-heavy website

A website might initially contain:
```html
<div id="app"></div>
```
Then JavaScript executes:
```javascript
document.getElementById("app").innerHTML = "<h1>OpenAI</h1>";
```
A normal HTTP request may only see:
```html
<div id="app"></div>
```
A browser sees:
```html
<div id="app">
    <h1>OpenAI</h1>
</div>
```
This is called **client-side rendering / dynamic rendering**.

## 8. Selenium

Selenium is a browser automation framework. Instead of simply requesting HTML, Selenium controls a browser.

```text
Python
  ↓
Selenium
  ↓
Chrome
  ↓
Website
  ↓
JavaScript executes
  ↓
Rendered webpage
```

**Example:**
```python
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://example.com")
print(driver.title)
driver.quit()
```

## 9. Selenium can get text by itself

You do NOT need BeautifulSoup if all you want is the visible text.

**Example:**
```python
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://example.com")

text = driver.find_element("tag name", "body").text
print(text)

driver.quit()
```

**The flow:**
```text
Website
  ↓
Selenium
  ↓
Browser renders page
  ↓
<body>
  ↓
Visible text
```
This is perfectly valid.

## 10. Selenium can do much more than extracting text

Selenium can interact with the webpage. For example:

- **Open webpage:** `driver.get(url)`
- **Get title:** `driver.title`
- **Find element:** `driver.find_element(...)`
- **Click:** `element.click()`
- **Type:** `element.send_keys("hello")`
- **Get text:** `element.text`
- **Get rendered HTML:** `driver.page_source`

This is why Selenium is much more than a scraper. It is primarily a **browser automation tool**.

## 11. Selenium vs BeautifulSoup

This distinction is extremely important.

| Feature | Selenium | BeautifulSoup |
| :--- | :--- | :--- |
| **Purpose** | Browser automation | HTML parsing |
| **Opens browser** | Yes | No |
| **Executes JavaScript** | Yes | No |
| **Can click buttons** | Yes | No |
| **Can scroll** | Yes | No |
| **Can fill forms** | Yes | No |
| **Waits for dynamic content** | Yes | No |
| **Extracts text** | Can extract visible text | Can extract text from HTML |
| **Gets HTML** | Gets rendered HTML | Parses provided HTML |
| **Performance** | Heavier/slower | Lightweight/faster |

> **Remember:**
> - **Selenium** = Make the webpage work/render
> - **BeautifulSoup** = Analyze the HTML

## 12. Why use Selenium + BeautifulSoup?

You can combine them when you need the strengths of both.

**The flow becomes:**
```text
                  Website
                     ↓
                  Selenium
                     ↓
             Browser renders
                     ↓
            JavaScript executes
                     ↓
             Rendered HTML
                     ↓
          driver.page_source
                     ↓
              BeautifulSoup
                     ↓
             Parse HTML
                     ↓
            Extract content
```

**Example:**
```python
from selenium import webdriver
from bs4 import BeautifulSoup

url = "https://example.com"
driver = webdriver.Chrome()
driver.get(url)

# Get the HTML after JavaScript has rendered the page
html = driver.page_source

# Parse that rendered HTML
soup = BeautifulSoup(html, "html.parser")

# Extract text
text = soup.get_text(" ", strip=True)
print(text)

driver.quit()
```

## 13. Why is using both useful?

Suppose the webpage contains:
```html
<div class="article">
    <h1>AI News</h1>
    <p>First paragraph...</p>
    <p>Second paragraph...</p>

    <div class="advertisement">
        Buy something!
    </div>

    <p>Third paragraph...</p>
</div>
```

Selenium can render the page. BeautifulSoup can then specifically extract:

```python
article = soup.find("div", class_="article")
paragraphs = article.find_all("p")

for p in paragraphs:
    print(p.get_text(strip=True))
```

**Output:**
```text
First paragraph...
Second paragraph...
Third paragraph...
```
You can avoid unwanted content such as advertisements.

## 14. Selenium Alone vs Selenium + BeautifulSoup

### Selenium alone
Use this when you mainly need:
- Visible text
- Buttons
- Forms
- Links
- Interactions

**Example:**
```python
text = driver.find_element("tag name", "body").text
```

### Selenium + BeautifulSoup
Use this when you need:
**Rendered page + Precise HTML extraction**

For example:
- Find article
- Find paragraphs
- Find links
- Find images
- Extract specific attributes
- Ignore unwanted sections

## 15. Combined Practical Scraper

Here is a useful version for your GenAI exercise.

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def scrape_with_selenium(url):
    options = Options()
    
    # Run Chrome without opening a visible window
    options.add_argument("--headless=new")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        
        # Get the rendered HTML
        html = driver.page_source
        
        # Parse rendered HTML
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract visible text
        text = soup.get_text(" ", strip=True)
        return text
    finally:
        driver.quit()

url = "https://example.com"
text = scrape_with_selenium(url)
print(text)
```

## 16. Better version: Extract the main article

Instead of taking the entire page:
```python
text = soup.get_text(" ", strip=True)
```
You can target a particular element. For example:
```python
article = soup.find("article")

if article:
    text = article.get_text(" ", strip=True)
else:
    text = soup.get_text(" ", strip=True)
```

This is better for an LLM because you don't want to send:
- Navigation
- Login
- Advertisement
- Footer
- Cookie notice
- Related articles

You want: **Actual article**

## 17. Why clean text before sending it to an LLM?

Suppose you send:
```text
Navigation
Home
Login
Advertisement
Article title
Article paragraph...
Footer
Cookie policy
```
to the LLM. That's unnecessary noise.

Instead:
```text
Webpage
  ↓
Scraping
  ↓
HTML
  ↓
Cleaning
  ↓
Useful text
  ↓
LLM
  ↓
Summary
```
This can reduce:
- Token usage
- Unnecessary context
- Processing time
- Irrelevant information

## 18. Playwright

Playwright is another browser automation framework.

Conceptually:
```text
Selenium
  ↓
Browser automation

Playwright
  ↓
Browser automation
```

Playwright can:
- Open websites
- Execute JavaScript
- Click, type, scroll
- Wait for elements
- Extract content
- Take screenshots

So the same general approach can be built with Playwright.

## 19. Selenium vs Playwright

| Feature | Selenium | Playwright |
| :--- | :--- | :--- |
| **Browser automation** | ✅ | ✅ |
| **JavaScript rendering** | ✅ | ✅ |
| **Clicking & Forms** | ✅ | ✅ |
| **Dynamic websites** | ✅ | ✅ |
| **Screenshots** | ✅ | ✅ |
| **Popularity** | Very mature | Very popular |
| **Learning Curve** | Good | Good |
| **Modern web automation** | Good | Excellent |

For your exercise, either is acceptable.

## 20. Why the tutorial mentions OpenAI

Your exercise says:
```python
display_summary("https://openai.com")
```
doesn't work.

The point isn't necessarily that OpenAI is impossible to scrape. The point is that the website is more dynamic/JavaScript-heavy than the simple pages the original scraper was designed for.

Therefore:
```text
requests + BeautifulSoup
  ↓
May not get the content you see in browser
```
While:
```text
Selenium / Playwright
  ↓
Real browser
  ↓
JavaScript executes
  ↓
Rendered content
```
can handle that type of page better.

## 21. Web Scraping for Your GenAI Project

Your overall project can look like:

```text
                         USER
                           │
                           ↓
                          URL
                           │
                           ↓
                     Web Scraper
                           │
             ┌─────────────┴─────────────┐
             ↓                           ↓
       Static website              JS-heavy website
             ↓                           ↓
        requests                  Selenium /
             ↓                    Playwright
        BeautifulSoup                   ↓
             │                    Rendered HTML
             │                           ↓
             │                    BeautifulSoup
             │                           ↓
             └─────────────┬─────────────┘
                           ↓
                      Clean Text
                           ↓
                          LLM
                           ↓
                        Summary
```

## 22. Where Tavily fits

This connects to what we discussed earlier about Tavily.

**Custom scraper:**
```text
Known URL
  ↓
Selenium / requests
  ↓
Page content
```
Good when: *"I already know which webpage I want."*

**Tavily:**
```text
Search query
  ↓
Tavily
  ↓
Web search
  ↓
Relevant results
  ↓
Content
```
Good when: *"Find relevant information on the web for me."*

So they aren't exactly replacements.

## 23. The most important concepts

### requests
Makes HTTP requests and receives server responses.
*(HTTP → HTML)*

### BeautifulSoup
Parses HTML and makes it easy to extract information.
*(HTML → structured extraction)*

### Selenium
Controls a real browser and can execute JavaScript through that browser.
*(Browser → render → interact → extract)*

### Playwright
Another modern browser automation framework.
*(Browser → render → interact → extract)*

## 24. Which one should you use?

Use the simplest tool that solves the problem.

**Case 1 — Static website**
```text
requests → BeautifulSoup
```

**Case 2 — Dynamic website, only need text**
```text
Selenium → body.text
```

**Case 3 — Dynamic website + precise extraction**
```text
Selenium → page_source → BeautifulSoup
```

**Case 4 — Dynamic website + complex interaction**
```text
Selenium / Playwright → click/scroll/login/wait → interact → extract
```

## 25. Final Mental Model

Remember this:

```text
                 WEB SCRAPING
                      │
          ┌───────────┴───────────┐
          ↓                       ↓
       STATIC                  DYNAMIC
          │                       │
          ↓                       ↓
     requests                 Browser
          │                 Selenium/
          ↓                 Playwright
   BeautifulSoup                 │
          │                       ↓
          │                 Rendered HTML
          │                       │
          │                       ↓
          │                 BeautifulSoup
          │                       │
          └──────────┬────────────┘
                     ↓
                Clean Text
                     ↓
                    LLM
                     ↓
                  Summary
```

### ⭐ The one thing to remember

**Selenium and BeautifulSoup are not competitors.**

**Selenium**
> *"Give me the webpage after the browser has rendered it."*

**BeautifulSoup**
> *"Now let me intelligently parse that HTML."*

And you don't have to use both.

If `driver.find_element("tag name", "body").text` gives you exactly the text you need, Selenium alone is enough.

If you need precise HTML extraction after JavaScript rendering, use:
**Selenium → page_source → BeautifulSoup**

That is the combination you should remember for your GenAI web-scraping exercise.
