# 🚀 Deployment Guide for Hugging Face Spaces

## Quick Start

Follow these steps to deploy your Python to C++ Code Optimizer on Hugging Face Spaces:

### Step 1: Create a New Space

1. Go to https://huggingface.co/new-space
2. Fill in the details:
   - **Owner**: Your username or organization
   - **Space name**: `python-cpp-optimizer` (or your preferred name)
   - **License**: MIT
   - **Select SDK**: Gradio
   - **Space hardware**: CPU Basic (free tier) or CPU Upgrade for faster performance
   - **Visibility**: Public or Private (your choice)

### Step 2: Upload Files

Upload these files to your Space:
- ✅ `app.py` - Main application file
- ✅ `requirements.txt` - Python dependencies
- ✅ `README.md` - Documentation (will be displayed on Space page)

You can upload via:
- **Web UI**: Drag and drop files in the "Files" tab
- **Git**: Clone the Space repo and push files

```bash
git clone https://huggingface.co/spaces/YOUR-USERNAME/YOUR-SPACE-NAME
cd YOUR-SPACE-NAME
cp app.py requirements.txt README.md .
git add .
git commit -m "Initial commit"
git push
```

### Step 3: Add API Keys as Secrets

**CRITICAL STEP** - Your app won't work without API keys!

1. Go to your Space's **Settings** tab
2. Scroll down to **Repository secrets**
3. Click **New secret** and add:

   **Secret 1:**
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key (get from https://platform.openai.com/api-keys)

   **Secret 2:**
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key (get from https://console.anthropic.com/)

4. Click **Save** for each secret

### Step 4: Wait for Build

- Your Space will automatically build (takes 1-2 minutes)
- Watch the build logs in the "Logs" tab
- Once complete, your app will be live!

### Step 5: Test Your App

1. Click on your Space URL
2. Test the conversion with the default Python code
3. Try running both Python and C++ versions
4. Verify the output and performance comparison

## 🛠️ Troubleshooting

### App shows "Error: API key not found"
- Make sure you added both secrets in Settings → Repository secrets
- Check that the secret names are exactly: `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`
- Try rebuilding the Space (Settings → Factory reboot)

### C++ compilation fails
- This is expected on some Hugging Face hardware
- The Space may need additional system packages
- You can disable C++ execution and just show the generated code

### App is slow
- Free tier CPU is limited
- Upgrade to CPU Upgrade or GPU for faster performance
- AI model calls may take 10-30 seconds (this is normal)

### Build fails
- Check the build logs for specific errors
- Verify `requirements.txt` has correct package versions
- Make sure `app.py` has no syntax errors

## 💡 Tips for Better Performance

1. **Upgrade Hardware**: Consider CPU Upgrade ($0.03/hour) for faster execution
2. **Model Selection**: Use GPT-4o-mini or Claude-Haiku for lower costs
3. **Caching**: Implement response caching for repeated queries
4. **Timeouts**: Default 30s timeout prevents runaway execution

## 🔒 Security Notes

- **Never expose API keys** in code or public files
- Always use Hugging Face Secrets for credentials
- The app executes arbitrary code - clearly warn users
- Consider disabling execution features for public Spaces
- Monitor usage to prevent abuse

## 📊 Monitoring

- Check **Analytics** tab for usage statistics
- Monitor **Logs** for errors and performance
- Review **Settings** → Usage for API cost tracking

## 🎨 Customization Ideas

1. **Branding**: Update colors and logo in `app.py`
2. **Examples**: Add more example Python programs
3. **Languages**: Support other languages (Rust, Go, etc.)
4. **Features**: Add code explanation, optimization suggestions
5. **UI**: Customize the Gradio interface theme

## 📝 Updating Your Space

When you want to update:

```bash
# Pull latest changes
git pull

# Make your changes to app.py or other files

# Commit and push
git add .
git commit -m "Update: description of changes"
git push
```

The Space will automatically rebuild with your changes.

## 🌟 Making Your Space Popular

1. **Good README**: Clear description with examples
2. **Demo Video**: Record a quick demo GIF
3. **Tags**: Add relevant tags (AI, code-generation, optimization)
4. **Share**: Post on Twitter, LinkedIn, Reddit
5. **Engage**: Respond to comments and issues

## 📞 Support

- **Hugging Face Docs**: https://huggingface.co/docs/hub/spaces
- **Gradio Docs**: https://www.gradio.app/docs/
- **Community Forum**: https://discuss.huggingface.co/

---

Good luck with your deployment! 🚀

