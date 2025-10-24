# Email for Community Contribution

---

**Subject:** Week 6 Day 5 - Fix for OpenAI Fine-Tuning Moderation Failures

---

Hi there,

I'm submitting a fix for a critical issue in the Week 6 Day 5 fine-tuning notebook that causes jobs to fail during post-training moderation.

## Root Cause

I received this error from OpenAI:

> "Unfortunately, your fine-tuning job ftjob-pJwYT39SqD8inEtpIVrGWTw6 has failed."

After investigation, I discovered the training completed successfully (200/200 steps), but OpenAI's post-training safety evaluation (`refusals_v3`) rejected the model due to product descriptions containing weapon/tactical keywords (knife, blade, combat, tactical) that triggered the "hate/threatening" category.

## Solution

I've created a comprehensive fix that:

1. **Filters sensitive content** before training using two-stage filtering:
   - Keyword pre-filter (25+ sensitive terms)
   - OpenAI Moderation API verification

2. **Provides multiple usage options**:
   - Pre-cleaned JSONL files (190 train, 48 validation) - ready to use
   - Standalone `fix_moderation.py` script for custom filtering
   - Updated notebook with `check_moderation()` function

3. **Maintains quality**: 190 examples still exceeds OpenAI's 50-100 recommendation

## Results

- **Before:** 200 examples → ❌ Failed with refusals_v3 error
- **After:** 190 examples → ✅ Successfully completed
- **Deployed model:** `ft:gpt-4o-mini-2024-07-18:personal:pricer:CQUN1Nk6`

## Files Included

9 files (~392 KB total):
- Modified `day5.ipynb` notebook
- Filtering scripts (`fix_moderation.py`, `test_moderation.py`)
- Pre-cleaned training/validation data
- Comprehensive documentation
- `requirements.txt`

## Why This Matters

This fix will save future users:
- Time: 30-60 minutes of troubleshooting
- Money: $5-10 in wasted API costs per failed attempt
- Frustration: Clear error messages and prevention

The solution is production-ready, tested, and includes extensive documentation for educational value.

Thank you for maintaining this excellent course!

Best regards,
Bilal-jamal

---

**Contribution Details:**
- Type: Critical Bug Fix
- Testing: Verified with successful fine-tuning job
- Impact: Prevents moderation failures for all week6/day5 users
