# Fix "Invalid username or token" when pushing to GitHub

Your Mac has an **old GitHub credential** stored in Keychain. Git keeps using it, so your new PAT is ignored.

## Step 1: Remove the stored GitHub credential

Run this in **Terminal** (it will ask for your Mac login password):

```bash
security delete-internet-password -s github.com
```

If it says "could not be found", try:

```bash
security delete-internet-password -s github.com -a 29275995
```

## Step 2: Make sure you have a valid Personal Access Token (PAT)

1. Open **https://github.com/settings/tokens**
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Note: **Expiration** (e.g. 90 days)
4. Check the **`repo`** scope (full control of private repositories)
5. Click **Generate token** and **copy the token** (starts with `ghp_` or similar)

## Step 3: Push again

From your repo folder:

```bash
cd /Users/mac/Documents/llm_engineering/llm_engineering
git push myfork email-subject-line-suggester
```

When prompted:

- **Username:** `idumachika`
- **Password:** paste your **PAT** (the token you copied)

Leave **Password** blank if it doesn’t prompt (then press Enter and it may ask again). Paste only the token, no spaces.

## Step 4: If it still fails

Use the token in the URL once (replace `YOUR_PAT_HERE` with your token). **Don’t share this URL or commit it.**

```bash
git push https://idumachika:YOUR_PAT_HERE@github.com/idumachika/llm_engineering.git email-subject-line-suggester
```

After a successful push, run Step 1 again to avoid storing the token in the URL in Keychain, or use **GitHub CLI**: `brew install gh && gh auth login`.
