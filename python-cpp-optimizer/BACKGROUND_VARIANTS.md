# Background Variants

This project includes two versions of the app with different login backgrounds:

## 📁 Files

### `app.py` - CSS Gradient Background (Default)
- **Background**: Beautiful purple gradient (`#667eea` to `#764ba2`)
- **Pros**: 
  - No external files needed
  - Works instantly on any platform
  - Fast loading
  - No CORS issues
- **Best for**: Quick deployment, Hugging Face Spaces

### `app_with_image.py` - Custom Image Background
- **Background**: Uses `assets/3656064.jpg` (Python-to-C++ themed image from Freepik)
- **Pros**: 
  - More personalized/branded appearance
  - Visually striking
- **Cons**: 
  - Requires image file in `assets/` folder
  - Slightly slower initial load
  - Need to adjust path for Hugging Face
- **Best for**: Local deployment, custom branding

## 🚀 Usage

### Local Development

**Gradient version:**
```bash
APP_PASSWORD=demo123 python3 app.py
```

**Image version:**
```bash
# Make sure assets/3656064.jpg exists
APP_PASSWORD=demo123 python3 app_with_image.py
```

### Hugging Face Deployment

**Gradient version (app.py):**
1. Upload `app.py` as your main app
2. Add secrets: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `APP_PASSWORD`
3. Factory reboot - Done! ✅

**Image version (app_with_image.py):**
1. Create an `assets/` folder in your Space
2. Upload `assets/3656064.jpg`
3. Rename `app_with_image.py` to `app.py` OR modify the Space to use `app_with_image.py`
4. **Important**: Update CSS in the file:
   ```css
   /* Change this: */
   background: url('assets/3656064.jpg')
   
   /* To this: */
   background: url('/file=assets/3656064.jpg')
   ```
5. Add secrets and factory reboot

## 🎨 Customization

### Change Gradient Colors (app.py)
Edit lines 382-392 in CSS:
```css
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%)
```

### Change Background Image (app_with_image.py)
1. Replace `assets/3656064.jpg` with your image
2. Update filename in CSS (lines 383, 392)
3. Update Freepik credit if needed (line 515)

## 📸 Image Credit

Background image by [Freepik](https://www.freepik.com)

## 💡 Recommendation

**For most users**: Use `app.py` (gradient) - it's simpler and works everywhere out of the box.

**For branding**: Use `app_with_image.py` if you want a custom visual identity.



