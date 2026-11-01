import os
import json
import pickle
import glob
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Set target directories relative to the workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TARGET_DIRS = ["week1", "week2", "week3", "week4", "week5", "week6", "week7", "week8", "guides"]
INDEX_FILE = Path(__file__).parent / "navigator_index.pkl"

def chunk_text(text, max_chars=1000, overlap=150):
    """Simple character-based chunking with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # If we are not at the end of the text, try to split at a newline or space
        if end < len(text):
            last_space = text.rfind('\n', start, end)
            if last_space == -1:
                last_space = text.rfind(' ', start, end)
            if last_space != -1 and last_space > start:
                end = last_space + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else end
    return chunks

def extract_from_notebook(file_path):
    """Extract code and markdown chunks from a Jupyter Notebook."""
    chunks = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        
        cells = nb.get("cells", [])
        for idx, cell in enumerate(cells):
            cell_type = cell.get("cell_type", "")
            source_lines = cell.get("source", [])
            
            # source can be a list of strings or a single string
            if isinstance(source_lines, list):
                source_text = "".join(source_lines)
            else:
                source_text = str(source_lines)
            
            if not source_text.strip():
                continue
            
            # Chunk the cell text if it's too long
            sub_chunks = chunk_text(source_text, max_chars=1000, overlap=100)
            for sub_idx, chunk in enumerate(sub_chunks):
                chunks.append({
                    "content": chunk,
                    "metadata": {
                        "file_path": str(file_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                        "file_type": "notebook",
                        "cell_index": idx,
                        "cell_type": cell_type,
                        "sub_index": sub_idx
                    }
                })
    except Exception as e:
        print(f"Warning: Failed to parse notebook {file_path}: {e}")
    return chunks

def extract_from_python_file(file_path):
    """Extract chunks from a Python file."""
    chunks = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.strip():
            return chunks
        
        # Split python file into functions and classes if possible, or simple chunks
        # Let's do simple line-based chunking of functions or blocks
        lines = content.splitlines()
        current_chunk = []
        current_len = 0
        line_start = 1
        
        for idx, line in enumerate(lines, 1):
            current_chunk.append(line)
            current_len += len(line) + 1
            # Chunk boundary when class/def starts or chunk is large enough
            if current_len >= 800 or (line.startswith(("def ", "class ", "if __name__")) and len(current_chunk) > 10):
                chunk_text_val = "\n".join(current_chunk)
                chunks.append({
                    "content": chunk_text_val,
                    "metadata": {
                        "file_path": str(file_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                        "file_type": "python",
                        "line_start": line_start,
                        "line_end": idx
                    }
                })
                # Keep some overlap by taking the last 2 lines
                current_chunk = current_chunk[-2:] if len(current_chunk) >= 2 else []
                current_len = sum(len(l) + 1 for l in current_chunk)
                line_start = idx - len(current_chunk) + 1
        
        # Add remainder
        if current_chunk:
            chunks.append({
                "content": "\n".join(current_chunk),
                "metadata": {
                    "file_path": str(file_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                    "file_type": "python",
                    "line_start": line_start,
                    "line_end": len(lines)
                }
            })
    except Exception as e:
        print(f"Warning: Failed to parse Python file {file_path}: {e}")
    return chunks

def extract_from_markdown(file_path):
    """Extract chunks from a Markdown file."""
    chunks = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.strip():
            return chunks
        
        # Split markdown by sections (headers) or simple character chunking
        sections = content.split("\n#")
        line_counter = 1
        
        for idx, section in enumerate(sections):
            prefix = "" if idx == 0 else "#"
            section_text = prefix + section
            if not section_text.strip():
                continue
            
            sub_chunks = chunk_text(section_text, max_chars=1000, overlap=100)
            for sub_idx, chunk in enumerate(sub_chunks):
                chunks.append({
                    "content": chunk,
                    "metadata": {
                        "file_path": str(file_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                        "file_type": "markdown",
                        "section_index": idx,
                        "sub_index": sub_idx
                    }
                })
    except Exception as e:
        print(f"Warning: Failed to parse Markdown file {file_path}: {e}")
    return chunks

def build_index():
    print(f"Scanning target directories in workspace root: {WORKSPACE_ROOT}")
    all_chunks = []
    
    for target in TARGET_DIRS:
        target_path = WORKSPACE_ROOT / target
        if not target_path.exists():
            print(f"Target directory {target_path} does not exist. Skipping.")
            continue
        
        # Find all .ipynb, .py, and .md files recursively
        for ext, handler in [("*.ipynb", extract_from_notebook), 
                             ("*.py", extract_from_python_file), 
                             ("*.md", extract_from_markdown)]:
            # Recursively find matching files
            files = glob.glob(str(target_path / "**" / ext), recursive=True)
            for file_path_str in files:
                file_path = Path(file_path_str)
                # Skip virtual env, hidden files, or community contributions
                if (
                    ".venv" in file_path.parts
                    or ".git" in file_path.parts
                    or "__pycache__" in file_path.parts
                    or "community-contributions" in file_path.parts
                    or "community_contributions" in file_path.parts
                ):
                    continue
                
                print(f"Processing: {file_path.relative_to(WORKSPACE_ROOT)}")
                file_chunks = handler(file_path)
                all_chunks.extend(file_chunks)
                
    if not all_chunks:
        print("No content chunks found to index!")
        return
        
    print(f"\nExtracted {len(all_chunks)} chunks from the codebase.")
    print("Loading embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Generating embeddings for all chunks (this may take a minute)...")
    texts = [chunk["content"] for chunk in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Bundle chunks and embeddings
    index_data = {
        "chunks": all_chunks,
        "embeddings": embeddings
    }
    
    # Save index to a pickle file
    print(f"Saving index to {INDEX_FILE}...")
    with open(INDEX_FILE, "wb") as f:
        pickle.dump(index_data, f)
        
    print("Indexing complete! Ready to navigate.")

if __name__ == "__main__":
    build_index()
