# 🧭 GIT QUICK RULES (COURSE REPO)

## 🧠 CORE MODEL
- upstream/main → Ed’s repo (DO NOT TOUCH)
- origin/main → my GitHub fork
- main → local clean copy
- weekX-branch → my work

---

## 🚀 START OF DAY (SYNC MAIN)
1) git checkout main                
    # Switches your current branch to main. You need to be on main because you’re about to update it. Think of this as: “Go to the base branch.”

2) git fetch upstream               
    # Downloads the latest changes from the remote named upstream. upstream usually refers to the original repository you forked from. This does not change your files yet — it just updates remote tracking branches like upstream/main. 

3) git reset --hard upstream/main   
    # Forcefully makes your local main match upstream/main. Deletes any local commits on main that differ. Updates your working directory to exactly match upstream. This is a destructive operation (you lose local changes on main). After this step: Your local main = upstream’s latest main. It makes your local main exactly identical to upstream/main. It throws away any local commits or changes on main. Not common in teams because: People may have local commits on main . Destructive = risky

4) git push origin main --force 
    # Force-pushes your updated main to your fork (origin). origin is typically your own GitHub fork. --force overwrites the remote main branch to match your local one. After this step: Your fork’s main is now fully synced with upstream.

5) git checkout <your-branch> 
    # Switches to your working branch (feature branch). Replace your-branch with the actual branch name. This is where your work/changes live.

6) git rebase main
    # Reapplies your branch’s commits on top of the updated main. Makes your branch look like it was built on the latest code. Keeps history clean (linear instead of merge commits). You may need to resolve conflicts if files changed. After this step: Your branch is now based on the newest version of main.

---

## 🌿 START NEW WORK - # Create branch
git checkout -b suveerchaudhary/weekX-solution


---

## ✏️ DAILY WORK RULES
✔ Only edit:
weekX/community_contributions/<my-username>/

❌ Never edit:
weekX/*.ipynb (course files)

---

## 📦 SAVE WORK FLOW
1) git status
2) git add <file>   OR   git add weekX/community_contributions/<me>/
3) git commit -m "message"
4) git push -u origin weekX-solution 
    # Push early (optional, but good for backup) , Keep committing + pushing over time. Can (or don' t) open PR only when ready

---

## 🔄 IF UPSTREAM UPDATES
git checkout main
git fetch upstream
git reset --hard upstream/main
git push origin main --force
git checkout weekX-solution
git rebase main

---

## ⚠️ FIXES
Unstage:
git restore --staged <file>

Undo changes:
git restore <file>

Recover file from commit:
git restore --source=<commit> <file>

Ignore junk:
echo "mytest/" >> .gitignore

---

## 📦 PR CHECKLIST
✔ Only community_contributions/<my-username>
✔ No notebook outputs
✔ No course file edits
✔ git log shows only my commits

---

## 🧠 GOLDEN RULE
main = clean base  
branch = my workspace  
PR = merge request  
upstream = truth