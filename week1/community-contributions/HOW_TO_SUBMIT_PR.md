# How to submit a community contribution (PR)

From the course: your PR should **only** change files under `community-contributions`. Full steps: **https://edwarddonner.com/pr**

## Quick steps

1. **Fork** the repo on GitHub (ed-donner/llm_engineering) → your account gets `your-username/llm_engineering`.

2. **Clone your fork** (if you don’t have it yet):
   ```bash
   git clone https://github.com/YOUR_USERNAME/llm_engineering.git
   cd llm_engineering
   ```

3. **Add upstream** (optional, to pull latest course updates):
   ```bash
   git remote add upstream https://github.com/ed-donner/llm_engineering.git
   git fetch upstream
   ```

4. **Create a branch** for your contribution:
   ```bash
   git checkout -b email-subject-line-suggester
   ```

5. **Add only your new/changed files under `community-contributions`.**  
   Example for the email subject suggester:
   - You might add: `week1/community-contributions/email_subject_line_suggester_openrouter.ipynb`
   - Do **not** include changes to `week1/day1.ipynb` or other course files in this PR.

6. **Point a remote at your fork and push** (replace `YOUR_GITHUB_USERNAME` with your GitHub username):
   ```bash
   git remote add myfork https://github.com/YOUR_GITHUB_USERNAME/llm_engineering.git
   git push myfork email-subject-line-suggester
   ```
   GitHub no longer accepts account passwords. When prompted:
   - **Username:** your GitHub username  
   - **Password:** use a **Personal Access Token (PAT)** from GitHub → Settings → Developer settings → Personal access tokens. Create a token with `repo` scope and paste it as the password.

7. **Open the PR on GitHub:**  
   Go to your fork on GitHub → you should see “Compare & pull request” for the branch you just pushed. Open a PR **into** `ed-donner/llm_engineering` (base: usually `main` or the branch the course specifies).

## Before submitting (from the course)

- [ ] PR only contains changes under **community-contributions** (unless agreed otherwise).
- [ ] Notebook outputs are **cleared** (or minimal and tidy).
- [ ] Under **2,000 lines** total and not too many files.
- [ ] No unnecessary test files, long READMEs, or `.env.example` unless needed.
