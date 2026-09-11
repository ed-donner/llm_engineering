# Week 1 scraper timeout

Official `week1/scraper.py` calls `requests.get` with no timeout. Day 5 and `solution.py` import that helper, so a slow or dead URL hangs the notebook until you interrupt the kernel.

This folder is a drop-in copy of the official scraper with `timeout=10` on both fetches. Function names and return values are unchanged.

## How to use

From the project root, replace the official helper (keep a backup if you want to compare):

```bash
cp week1/community-contributions/saadamjad-scraper-timeout/scraper.py week1/scraper.py
```

Then run Day 5 or `week1/solution.py` as usual. Official `week1/scraper.py` is not modified in this contribution.

## What changed

`REQUEST_TIMEOUT = 10` passed to both `requests.get` calls. Nothing else.
