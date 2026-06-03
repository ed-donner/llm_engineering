import os
import re
import sys

# Check for required dependencies and provide helpful error messages
try:
    import requests
except ImportError:
    print("❌ Error: 'requests' module not found.")
    print("💡 Install with: pip install requests")
    print("   Or: pip install -r requirements.txt")
    sys.exit(1)

try:
    import tiktoken
except ImportError:
    print("❌ Error: 'tiktoken' module not found.")
    print("💡 Install with: pip install tiktoken")
    print("   Or: pip install -r requirements.txt")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: 'python-dotenv' module not found.")
    print("💡 Install with: pip install python-dotenv")
    print("   Or: pip install -r requirements.txt")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("❌ Error: 'openai' module not found.")
    print("💡 Install with: pip install openai")
    print("   Or: pip install -r requirements.txt")
    sys.exit(1)

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("❌ Error: 'youtube-transcript-api' module not found.")
    print("💡 Install with: pip install youtube-transcript-api")
    print("   Or: pip install -r requirements.txt")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Error: 'beautifulsoup4' module not found.")
    print("💡 Install with: pip install beautifulsoup4")
    print("   Or: pip install -r requirements.txt")
    sys.exit(1)

try:
    from IPython.display import Markdown, display
except ImportError:
    # IPython is optional for Jupyter notebooks
    print("⚠️  Warning: IPython not available (optional for Jupyter notebooks)")
    Markdown = None
    display = None

#headers and class for website to summarize
headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class YouTubeVideo:
    def __init__(self, url):
        self.url = url
        youtube_pattern = r'https://www\.youtube\.com/watch\?v=[a-zA-Z0-9_-]+'
        if re.match(youtube_pattern, url):
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            self.video_id = url.split("v=")[1]
            self.title = soup.title.string if soup.title else "No title found"
            self.transcript = YouTubeTranscriptApi().fetch(self.video_id)
        else:
            raise ValueError("Invalid YouTube URL")                

#get api key and openai client
def get_api_key():
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    return api_key

def get_openai_client():
    api_key = get_api_key()
    return OpenAI(api_key=api_key)

#count tokens
def count_tokens(text, model="gpt-4o-mini"):
    """Count tokens in text using tiktoken with fallback"""
    try:
        # Try model-specific encoding first
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except KeyError:
        # Fallback to cl100k_base encoding (used by most OpenAI models)
        # This ensures compatibility even if model-specific encoding isn't available
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        # Ultimate fallback - rough estimation
        print(f"Warning: Token counting failed ({e}), using rough estimation")
        return len(text.split()) * 1.3  # Rough word-to-token ratio


def get_optimal_chunk_size(model="gpt-4o-mini"):
    """Calculate optimal chunk size based on model's context window"""
    model_limits = {
        "gpt-4o-mini": 8192,
        "gpt-4o": 128000,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 4096,
        "gpt-4": 8192,
    }
    
    context_window = model_limits.get(model, 8192)  # Default to 8K
    
    # Reserve tokens for:
    # - System prompt: ~800 tokens
    # - User prompt overhead: ~300 tokens  
    # - Output: ~2000 tokens
    # - Safety buffer: ~500 tokens
    reserved_tokens = 800 + 300 + 2000 + 500
    
    optimal_chunk_size = context_window - reserved_tokens
    
    # Ensure minimum chunk size
    return max(optimal_chunk_size, 2000)

#chunk transcript
def chunk_transcript(transcript, max_tokens=4000, overlap_tokens=200, model="gpt-4o-mini"):
    """
    Split transcript into chunks that fit within token limits
    
    Args:
        transcript: List of transcript segments from YouTube
        max_tokens: Maximum tokens per chunk (auto-calculated if None)
        overlap_tokens: Number of tokens to overlap between chunks
        model: Model name for token limit calculation
    
    Returns:
        List of transcript chunks
    """
    # Auto-calculate max_tokens based on model if not provided
    if max_tokens is None:
        max_tokens = get_optimal_chunk_size(model)
    
    # Auto-calculate overlap as percentage of max_tokens
    if overlap_tokens is None:
        overlap_tokens = int(max_tokens * 0.05)  # 5% overlap
    # Convert transcript to text
    transcript_text = " ".join([segment.text for segment in transcript])
    
    # If transcript is small enough, return as single chunk
    if count_tokens(transcript_text) <= max_tokens:
        return [transcript_text]
    
    # Split into sentences for better chunking
    sentences = re.split(r'[.!?]+', transcript_text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if adding this sentence would exceed token limit
        test_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        if count_tokens(test_chunk) <= max_tokens:
            current_chunk = test_chunk
        else:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(current_chunk)
            
            # Start new chunk with overlap from previous chunk
            if chunks and overlap_tokens > 0:
                # Get last few words from previous chunk for overlap
                prev_words = current_chunk.split()[-overlap_tokens//4:]  # Rough word-to-token ratio
                current_chunk = " ".join(prev_words) + " " + sentence
            else:
                current_chunk = sentence
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

#generate system prompt
def generate_system_prompt():
    return f"""
    You are an expert YouTube video summarizer. Your job is to take the full transcript of a video and generate a structured, precise, and academically grounded summary.

    Your output must include:

    1. Title
    - Either reuse the video’s title (if it is clear, accurate, and concise)
    - Or generate a new, sharper, more descriptive title that best reflects the actual content covered.

    2. Topic & Area of Coverage
    - Provide a 1–2 line highlight of the main topic of the video and the specific area it best covers.
    - Format:
        - Domain (e.g., Finance, Health, Technology, Psychology, Fitness, Productivity, etc.)
        - Sub-area (e.g., investment strategies, portfolio design; training routine, best exercises; productivity systems, cognitive science insights, etc.)

    3. Summary of the Video
    - A structured, clear, and concise summary of the video.
    - Focus only on relevant, high-value content.
    - Skip fluff, tangents, product promotions, personal banter, or irrelevant side discussions.
    - Include key insights, frameworks, step-by-step methods, and actionable advice.
    - Where applicable, reference scientific studies, historical sources, or authoritative references (with author + year or journal if mentioned in the video, or inferred if the reference is well known).

    Style & Quality Rules:
    - Be extremely specific: avoid vague generalizations.
    - Use precise language and structured formatting (bullet points, numbered lists, sub-sections if needed).
    - Prioritize clarity and factual accuracy.
    - Write as though preparing an executive briefing or academic digest.
    - If the transcript includes non-relevant sections (jokes, ads, unrelated chit-chat), skip summarizing them entirely.
    """

#generate user prompt
def generate_user_prompt(website, transcript_chunk=None):
    if transcript_chunk:
        return f"""Here is a portion of a YouTube video transcript. Use the system instructions to generate a summary of this section.

    Video Title: {website.title}

    Transcript Section: {transcript_chunk}
    """
    else:
        return f"""Here is the transcript of a YouTube video. Use the system instructions to generate the output.

    Video Title: {website.title}

    Transcript: {website.transcript}
    """

#generate stitching prompt
def generate_stitching_prompt(chunk_summaries, video_title):
    """Generate prompt for stitching together chunk summaries"""
    return f"""You are an expert at combining multiple summaries into a cohesive, comprehensive summary.

    Video Title: {video_title}

    Below are summaries of different sections of this video. Combine them into a single, well-structured summary that:
    1. Maintains the original structure and quality standards
    2. Eliminates redundancy between sections
    3. Creates smooth transitions between topics
    4. Preserves all important information 
    5. Maintains the academic, professional tone
    6. Include examples and nuances where relevant
    7. Include the citations and references where applicable

    Section Summaries:
    {chr(10).join([f"Section {i+1}: {summary}" for i, summary in enumerate(chunk_summaries)])}

    Please provide a unified, comprehensive summary following the same format as the individual sections.
    Make sure the final summary is cohesive and logical.
    """

#summarize video
def summarize_video(website, use_chunking=True, max_chunk_tokens=4000):
    """Summarize a YouTube video using OpenAI API with optional chunking for large videos"""
    client = get_openai_client()
    
    # Check if we need chunking
    transcript_text = " ".join([segment.text for segment in website.transcript])
    total_tokens = count_tokens(transcript_text)
    
    print(f"Total transcript tokens: {total_tokens}")
    
    if total_tokens <= max_chunk_tokens and not use_chunking:
        # Single summary for small videos
        return summarize_single_chunk(website, client)
    else:
        # Chunked summary for large videos
        return summarize_with_chunking(website, client, max_chunk_tokens)

#summarize single chunk
def summarize_single_chunk(website, client):
    """Summarize a single chunk (small video)"""
    system_prompt = generate_system_prompt()
    user_prompt = generate_user_prompt(website)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"

#summarize with chunking
def summarize_with_chunking(website, client, max_chunk_tokens=4000):
    """Summarize a large video by chunking and stitching"""
    print("Video is large, using chunking strategy...")
    
    # Chunk the transcript
    chunks = chunk_transcript(website.transcript, max_chunk_tokens)
    print(f"Split into {len(chunks)} chunks")
    
    # Summarize each chunk
    chunk_summaries = []
    system_prompt = generate_system_prompt()
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        user_prompt = generate_user_prompt(website, chunk)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,  # Smaller for chunks
                temperature=0.3
            )
            
            chunk_summaries.append(response.choices[0].message.content)
            
        except Exception as e:
            chunk_summaries.append(f"Error in chunk {i+1}: {str(e)}")
    
    # Stitch the summaries together
    print("Stitching summaries together...")
    stitching_prompt = generate_stitching_prompt(chunk_summaries, website.title)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at combining multiple summaries into a cohesive, comprehensive summary."},
                {"role": "user", "content": stitching_prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error stitching summaries: {str(e)}"

#main function
def main():
    """Main function to demonstrate usage"""
    # Example usage - replace with actual YouTube URL
    video_url = "https://www.youtube.com/watch?v=Xan5JnecLNA"
    
    try:
        # Create YouTube video object
        print("Fetching video data...")
        video = YouTubeVideo(video_url)
        
        # Display video info
        print(f"Video Title: {video.title}")
        print(f"Video ID: {video.video_id}")
        
        # Count tokens in transcript
        transcript_text = " ".join([segment.text for segment in video.transcript])
        total_tokens = count_tokens(transcript_text)
        print(f"Total transcript tokens: {total_tokens}")
        
        # Generate summary (automatically uses chunking if needed)
        print("\nGenerating summary...")
        summary = summarize_video(video, use_chunking=True, max_chunk_tokens=4000)
        
        # Display results
        print("\n" + "="*50)
        print("FINAL SUMMARY")
        print("="*50)
        print(summary)
        
    except Exception as e:
        print(f"Error: {str(e)}")


def test_chunking():
    """Test function to demonstrate chunking with a sample transcript"""
    # Sample transcript for testing
    sample_transcript = [
        {"text": "This is a sample transcript segment 1. " * 100},  # ~1000 tokens
        {"text": "This is a sample transcript segment 2. " * 100},  # ~1000 tokens
        {"text": "This is a sample transcript segment 3. " * 100},  # ~1000 tokens
        {"text": "This is a sample transcript segment 4. " * 100},  # ~1000 tokens
        {"text": "This is a sample transcript segment 5. " * 100},  # ~1000 tokens
    ]
    
    print("Testing chunking functionality...")
    chunks = chunk_transcript(sample_transcript, max_tokens=2000, overlap_tokens=100)
    
    print(f"Original transcript: {count_tokens(' '.join([s['text'] for s in sample_transcript]))} tokens")
    print(f"Number of chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {count_tokens(chunk)} tokens")


if __name__ == "__main__":
    # Uncomment the line below to test chunking
    # test_chunking()
    
    # Run main function
    main()
