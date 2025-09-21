# YouTube Video Summarizer

A Python tool that automatically fetches YouTube video transcripts and generates comprehensive summaries using OpenAI's GPT-4o-mini model. Features intelligent chunking for large videos and high-quality summarization.

## Features

- 🎬 **YouTube Integration**: Automatically fetches video transcripts
- 🤖 **AI-Powered Summaries**: Uses GPT-4o-mini for high-quality summaries
- 📊 **Smart Chunking**: Handles large videos by splitting into manageable chunks
- 🔄 **Automatic Stitching**: Combines chunk summaries into cohesive final summaries
- 💰 **Cost-Effective**: Optimized for GPT-4o-mini's token limits
- 🛡️ **Error Handling**: Robust error handling with helpful messages

## Installation

### Prerequisites
- Python 3.8 or higher

### Option 1: Using the installation script (Recommended)
```bash
# Run the automated installation script
python install.py

# The script will let you choose between UV and pip
# Then run the script with your chosen method
```

### Option 2: Using UV
```bash
# Install UV if not already installed
pip install uv

# Install dependencies and create virtual environment
uv sync

# Run the script
uv run python youtube_video_summarizer.py
```

### Option 3: Using pip
```bash
# Install dependencies
pip install -r requirements.txt

# Run the script
python youtube_video_summarizer.py
```

### Optional Dependencies

#### With UV:
```bash
# For Jupyter notebook support
uv sync --extra jupyter

# For development dependencies (testing, linting, etc.)
uv sync --extra dev
```

#### With pip:
```bash
# For Jupyter notebook support
pip install ipython jupyter

# For development dependencies
pip install pytest black flake8 mypy
```

## Setup

1. **Get an OpenAI API Key**:
   - Visit [OpenAI API](https://platform.openai.com/api-keys)
   - Create a new API key

2. **Create a .env file**:
   ```bash
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

3. **Update the video URL** in `youtube_video_summarizer.py`:
   ```python
   video_url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
   ```

## Usage

### Basic Usage
```python
from youtube_video_summarizer import YouTubeVideo, summarize_video

# Create video object
video = YouTubeVideo("https://www.youtube.com/watch?v=VIDEO_ID")

# Generate summary
summary = summarize_video(video)
print(summary)
```

### Advanced Usage with Custom Settings
```python
# Custom chunking settings
summary = summarize_video(
    video, 
    use_chunking=True, 
    max_chunk_tokens=4000
)
```

## How It Works

1. **Video Processing**: Fetches YouTube video metadata and transcript
2. **Token Analysis**: Counts tokens to determine if chunking is needed
3. **Smart Chunking**: Splits large transcripts into manageable pieces
4. **Individual Summaries**: Generates summaries for each chunk
5. **Intelligent Stitching**: Combines chunk summaries into final result

## Configuration

### Model Settings
- **Model**: GPT-4o-mini (cost-effective and high-quality)
- **Temperature**: 0.3 (focused, consistent output)
- **Max Tokens**: 2,000 (optimal for summaries)

### Chunking Settings
- **Max Chunk Size**: 4,000 tokens (auto-calculated per model)
- **Overlap**: 5% of chunk size (maintains context)
- **Auto-detection**: Automatically determines if chunking is needed

## Error Handling

The script includes comprehensive error handling:
- ✅ **Missing Dependencies**: Clear installation instructions
- ✅ **Invalid URLs**: YouTube URL validation
- ✅ **API Errors**: OpenAI API error handling
- ✅ **Network Issues**: Request timeout and retry logic

## Requirements

- **Python**: 3.8 or higher
- **OpenAI API Key**: Required for summarization
- **Internet Connection**: For YouTube and OpenAI API access

## Dependencies

### Core Dependencies
- `requests`: HTTP requests
- `tiktoken`: Token counting
- `python-dotenv`: Environment variable management
- `openai`: OpenAI API client
- `youtube-transcript-api`: YouTube transcript fetching
- `beautifulsoup4`: HTML parsing

### Optional Dependencies
- `ipython`: Jupyter notebook support
- `jupyter`: Jupyter notebook support

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: 
   - With UV: Run `uv sync` to install dependencies
   - With pip: Run `pip install -r requirements.txt`
2. **UV not found**: Install UV with `pip install uv` or run `python install.py`
3. **OpenAI API Error**: Check your API key in `.env` file
4. **YouTube Transcript Error**: Video may not have transcripts available
5. **Token Limit Error**: Video transcript is too long (rare with chunking)

### Getting Help

If you encounter issues:
1. Check the error messages (they include helpful installation instructions)
2. Ensure all dependencies are installed:
   - With UV: `uv sync`
   - With pip: `pip install -r requirements.txt`
3. Verify your OpenAI API key is correct
4. Check that the YouTube video has transcripts available
5. Try running with the appropriate command:
   - With UV: `uv run python youtube_video_summarizer.py`
   - With pip: `python youtube_video_summarizer.py`

## License

This project is part of the LLM Engineering course materials.

## Contributing

Feel free to submit issues and enhancement requests!
