# About
 It categorizes websites based on its content of homepage.

# Prerequisites

- .env file with OPENAI_API_KEY in the root of the repo
- npm install
- npx playwright install chromium

# Run it

```sh
node index.js https://google.com // "Search Engine"

node index.js https://amazon.com // "eCommerce/Retail"
// ..etc
```