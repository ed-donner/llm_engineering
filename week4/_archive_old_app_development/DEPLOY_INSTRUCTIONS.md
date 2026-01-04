# 🚀 Deploy to Hugging Face Spaces - Complete Guide

## Quick Deploy Steps

### 1. Create Your Space
- Go to: https://huggingface.co/new-space
- SDK: **Gradio**
- Hardware: **CPU Basic** (free) or **CPU Upgrade** ($0.03/hour)

### 2. Upload These Files
```
app.py
requirements.txt
README.md
```

### 3. Add API Keys as Secrets
Go to Settings → Repository secrets:
- `OPENAI_API_KEY` = your OpenAI key
- `ANTHROPIC_API_KEY` = your Anthropic key

### 4. Done! 🎉
Your app will build automatically in ~2 minutes.

---

## Detailed Instructions

### Option A: Web Upload (Easiest)

#### Step 1: Get Your Files Ready
Your files are located at:
```
/Users/khirod/Documents/Udemy/Generative AI/Projects/llm_engineering/week4/
```

Files to upload:
- ✅ `app.py` - The main Gradio application
- ✅ `requirements.txt` - Python dependencies
- ✅ `README.md` - Documentation (will show on your Space page)

#### Step 2: Create Hugging Face Account
1. Visit https://huggingface.co/join
2. Sign up (free!)
3. Verify your email

#### Step 3: Create a New Space
1. Go to https://huggingface.co/new-space
2. Configure your Space:
   ```
   Owner: [your-username]
   Space name: python-cpp-optimizer
   License: MIT
   SDK: Gradio ← IMPORTANT!
   Hardware: CPU Basic (free)
   Visibility: Public
   ```
3. Click "Create Space"

#### Step 4: Upload Files
1. In your new Space, click "Files and versions" tab
2. Click "Add file" → "Upload files"
3. Drag and drop or select:
   - app.py
   - requirements.txt
   - README.md
4. Add commit message: "Initial commit"
5. Click "Commit changes to main"

#### Step 5: Add API Keys (CRITICAL!)
⚠️ **Your app won't work without these!**

1. Click "Settings" tab (top of page)
2. Scroll to "Repository secrets"
3. Click "New secret"

**Secret 1:**
```
Name: OPENAI_API_KEY
Value: sk-... (your actual key from https://platform.openai.com/api-keys)
```

**Secret 2:**
```
Name: ANTHROPIC_API_KEY
Value: sk-ant-... (your actual key from https://console.anthropic.com/)
```

#### Step 6: Monitor Build
1. Click "Logs" tab
2. Watch the build process
3. Wait for "Running on local URL: http://127.0.0.1:7860" message
4. Build takes ~1-2 minutes

#### Step 7: Test Your App
1. Click "App" tab
2. You should see your beautiful modern UI!
3. Try the example code
4. Test both GPT-4o and Claude-3.5-Sonnet

---

### Option B: Git Clone and Push

#### Step 1: Create Space on Hugging Face
Follow Steps 1-3 from Option A

#### Step 2: Clone Your Space Repository
```bash
# Install git-lfs if you haven't (needed for HF)
brew install git-lfs  # macOS
# or
sudo apt-get install git-lfs  # Linux

# Initialize git-lfs
git lfs install

# Clone your Space
git clone https://huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE-NAME
cd YOUR-SPACE-NAME
```

#### Step 3: Copy Your Files
```bash
# Copy files from your project
cp /Users/khirod/Documents/Udemy/Generative\ AI/Projects/llm_engineering/week4/app.py .
cp /Users/khirod/Documents/Udemy/Generative\ AI/Projects/llm_engineering/week4/requirements.txt .
cp /Users/khirod/Documents/Udemy/Generative\ AI/Projects/llm_engineering/week4/README.md .
```

#### Step 4: Commit and Push
```bash
git add app.py requirements.txt README.md
git commit -m "Initial commit: Python to C++ Code Optimizer"
git push
```

#### Step 5: Add API Keys
Go to your Space's Settings page and add the secrets (see Step 5 in Option A)

---

## 📋 Checklist Before Publishing

- [ ] Files uploaded: app.py, requirements.txt, README.md
- [ ] OPENAI_API_KEY added as secret
- [ ] ANTHROPIC_API_KEY added as secret
- [ ] Build completed successfully (check Logs)
- [ ] App loads without errors (check App tab)
- [ ] Tested code conversion with sample
- [ ] Security warning is visible

---

## 🐛 Troubleshooting

### "Error: API key not found"
- Check that secrets are added in Settings → Repository secrets
- Names must be exact: `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`
- Try Factory Reboot: Settings → Factory reboot

### Build fails
- Check Logs tab for specific error
- Verify requirements.txt has correct package versions
- Make sure app.py has no syntax errors

### C++ compilation fails
- Expected on some HF hardware (no g++ installed)
- You can disable C++ execution for Hugging Face:
  - Comment out the execute_cpp function calls
  - Or add system package installation

### App is slow
- Free tier has limited CPU
- Upgrade to CPU Upgrade ($0.03/hour) for better performance
- Or use GPU for even faster execution

### "Space keeps rebuilding"
- This is normal on first deploy
- Each file change triggers a rebuild
- Wait for "Running" status

---

## 💰 Cost Considerations

### Hugging Face Costs:
- **CPU Basic**: FREE ✅
- **CPU Upgrade**: $0.03/hour (~$22/month if always on)
- **GPU T4**: $0.60/hour

### API Costs (when users use your app):
- **OpenAI GPT-4o**: ~$0.01 per code conversion
- **Anthropic Claude-3.5-Sonnet**: ~$0.006 per code conversion

**Recommendation**: 
- Start with free CPU Basic
- Set monthly budget limits on OpenAI/Anthropic
- Monitor usage in your API dashboards

---

## 🎨 After Publishing

### Share Your Space
Your Space will be live at:
```
https://huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE-NAME
```

Share on:
- Twitter/X with #HuggingFace #Gradio #AI
- LinkedIn
- Reddit r/MachineLearning
- Dev.to / Hashnode blog post

### Make it Popular
1. **Add a good description** in README.md
2. **Record a demo GIF** and add to README
3. **Add tags**: code-generation, optimization, cpp, python
4. **Engage with users** in the Community tab
5. **Pin to your HF profile**

### Monitor Your Space
- **Analytics** tab: See usage statistics
- **Logs** tab: Monitor for errors
- **Community** tab: Respond to users

---

## 🔄 Updating Your Space

When you want to make changes:

### Via Web:
1. Go to Files tab
2. Click on file to edit
3. Make changes
4. Commit changes
5. Wait for rebuild

### Via Git:
```bash
cd YOUR-SPACE-NAME
# Make your changes to app.py or other files
git add .
git commit -m "Update: description of changes"
git push
```

---

## 🔒 Security Best Practices

1. **Never commit API keys** - Always use HF Secrets
2. **Set rate limits** in your code to prevent abuse
3. **Monitor usage** to catch unusual activity
4. **Keep security warnings visible** in UI
5. **Consider making Space private** if you're concerned about abuse
6. **Set budget alerts** on OpenAI/Anthropic dashboards

---

## 📞 Getting Help

- **Hugging Face Docs**: https://huggingface.co/docs/hub/spaces
- **Gradio Docs**: https://www.gradio.app/docs/
- **Community Forum**: https://discuss.huggingface.co/
- **Discord**: https://discord.gg/hugging-face

---

## ✅ Success!

Once deployed, your Space will be:
- ✨ Publicly accessible (or private if you chose)
- 🌍 Available worldwide
- 📱 Mobile-friendly
- 🔄 Auto-updating when you push changes
- 📊 Tracked with analytics

**Congratulations on publishing your first Hugging Face Space!** 🎉

---

## 📝 Quick Command Reference

```bash
# Clone Space
git clone https://huggingface.co/spaces/USER/SPACE

# Add files
git add app.py requirements.txt README.md

# Commit
git commit -m "Your message"

# Push
git push

# Force rebuild (if needed)
# Go to Settings → Factory reboot
```

