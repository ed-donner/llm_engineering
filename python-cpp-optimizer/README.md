# 🚀 Python to C++ Code Optimizer

An AI-powered web application that converts Python code to optimized C++ with real-time execution and performance comparison.

## ✨ Features

- **AI-Powered Conversion**: Uses GPT-4o or Claude-3.5-Sonnet for high-quality code generation
- **Real-Time Execution**: Test both Python and C++ code directly in the browser
- **Performance Comparison**: Compare execution times side-by-side
- **Modern UI**: Clean, responsive interface with syntax highlighting
- **Password Protected**: Secure deployment with authentication
- **Cloud Ready**: Deploy instantly to Hugging Face Spaces

## 🎯 Supported AI Models

- **GPT-4o** (OpenAI) - Premium, fastest, most accurate
- **Claude-3.5-Sonnet** (Anthropic) - Premium, excellent for code

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd python-cpp-optimizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   APP_PASSWORD=your_secure_password_here
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the app**
   - Open your browser to `http://127.0.0.1:7860`
   - Login with username: `user` and the password you set

### Deploy to Hugging Face Spaces

1. **Create a new Space**
   - Go to https://huggingface.co/new-space
   - Name: `python-cpp-optimizer`
   - SDK: **Gradio**
   - Visibility: **Public** or **Private**

2. **Upload files**
   - Upload `app.py`
   - Upload `requirements.txt`
   - Upload `.gitignore`
   - Upload `README.md`

3. **Add Secrets**
   
   In Space Settings → Repository secrets, add:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `APP_PASSWORD`: Your chosen password

4. **Factory Reboot**
   - Settings → Factory reboot
   - Wait 2-3 minutes for deployment

5. **Access your Space**
   - Login with username: `user` and your `APP_PASSWORD`

## 🔑 API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-...`)
4. Add to `.env` file or Hugging Face Secrets

### Anthropic API Key
1. Go to https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-...`)
4. Add to `.env` file or Hugging Face Secrets

## 💰 Cost

Both AI models use pay-per-use pricing:
- **GPT-4o**: ~$0.01 per conversion
- **Claude-3.5-Sonnet**: ~$0.01 per conversion

Very affordable for personal use and demos!

## ⚠️ Security Warning

This application executes arbitrary Python and C++ code. 

**Important security considerations:**
- Only run code from trusted sources
- Use strong passwords for deployment
- Monitor API usage and costs
- Never share your API keys
- Consider rate limiting for public deployments

## 🛠️ Requirements

- Python 3.8+
- g++ compiler (for C++ execution)
- OpenAI API key
- Anthropic API key

## 📁 Project Structure

```
python-cpp-optimizer/
├── app.py              # Main Gradio application
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
├── .env               # Local environment variables (create this)
└── README.md          # This file
```

## 🤝 Contributing

Feel free to open issues or submit pull requests!

## 📝 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🎓 Credits

Built with:
- [Gradio](https://gradio.app/) - Modern ML web interfaces
- [OpenAI GPT-4o](https://openai.com/) - AI code generation
- [Anthropic Claude](https://anthropic.com/) - AI code generation

## 💡 Tips

1. **Start with simple code** - Test with small Python snippets first
2. **Compare outputs** - Always verify C++ produces identical results
3. **Monitor API usage** - Check your API dashboards regularly
4. **Use strong passwords** - Especially for public deployments
5. **Backup your work** - Save generated C++ code locally

## 🐛 Troubleshooting

### "API Key not found" error
- Make sure `.env` file exists with correct API keys
- For Hugging Face: Check secrets are added and Space is rebooted

### C++ compilation fails
- Ensure g++ is installed: `g++ --version`
- Check C++ code for syntax errors
- Try simpler Python code first

### Password not working
- Check `APP_PASSWORD` is set correctly
- Try factory reboot on Hugging Face Spaces

### App won't start
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)
- Look for error messages in terminal

## 📧 Support

For issues or questions, please open an issue on GitHub.

---

**Happy Coding! 🎉**

