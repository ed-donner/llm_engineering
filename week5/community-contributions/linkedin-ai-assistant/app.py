import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import html2text
from collections import Counter, defaultdict, deque
import warnings
import time
import hashlib
import socket
import random
import zipfile
import tempfile
import shutil

warnings.filterwarnings('ignore')

import gradio as gr
import chromadb
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from openai import OpenAI
import torch

# ================================
# USAGE PROTECTION SYSTEM
# ================================

class UsageTracker:
    def __init__(self):
        self.hourly_limits = defaultdict(lambda: deque())
        self.daily_limits = defaultdict(int)
        self.total_requests = 0
        self.total_cost = 0.0
        
        # STRICTER LIMITS for cost control
        self.max_hourly = 5        # Reduced from 15
        self.max_daily = 20        # Reduced from 100  
        self.max_total = 200       # Reduced from 1000
        self.max_daily_cost = 3.0  # $3 daily limit
        
        # GPT-4o-mini pricing (approximate cost per request)
        self.cost_per_request = 0.01  # ~1 cent per request (conservative estimate)

    def can_make_request(self, user_id):
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Clean old hourly requests
        while self.hourly_limits[user_id] and self.hourly_limits[user_id][0] < hour_ago:
            self.hourly_limits[user_id].popleft()

        # Check limits
        if len(self.hourly_limits[user_id]) >= self.max_hourly:
            return False, f"⏰ Hourly limit reached ({self.max_hourly} requests/hour). Please try again in a few minutes."

        if self.daily_limits[user_id] >= self.max_daily:
            return False, f"📅 Daily limit reached ({self.max_daily} requests/day). Come back tomorrow!"

        if self.total_requests >= self.max_total:
            return False, "🚫 Service temporarily unavailable due to high usage. Please try again later."
        
        # Check estimated daily cost
        if self.total_cost >= self.max_daily_cost:
            return False, f"💰 Daily cost limit (${self.max_daily_cost}) reached. Service will reset tomorrow."

        return True, "OK"

    def record_request(self, user_id):
        now = datetime.now()
        self.hourly_limits[user_id].append(now)
        self.daily_limits[user_id] += 1
        self.total_requests += 1
        self.total_cost += self.cost_per_request  # Track estimated cost

    def get_usage_info(self):
        """Get current usage info for display"""
        return f"""
**📊 Current Usage:**
- Total requests today: {self.total_requests}/{self.max_total}
- Estimated cost today: ${self.total_cost:.2f}/${self.max_daily_cost}
- Service status: {'🟢 Active' if self.total_requests < self.max_total and self.total_cost < self.max_daily_cost else '🔴 Limited'}
"""

# Initialize tracker - ADD THIS LINE!
usage_tracker = UsageTracker()


def protected_function(func):
    def wrapper(*args, **kwargs):
        user_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        allowed, message = usage_tracker.can_make_request(user_id)
        
        if not allowed:
            return f"⚠️ {message}. Please try again later."
        
        usage_tracker.record_request(user_id)
        return func(*args, **kwargs)
    return wrapper

# ================================
# LINKEDIN DATA PROCESSOR
# ================================

class LinkedInDataProcessor:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.profile_data = {}
        self.processed_data = {}
        self.articles_content = []
        self.rag_documents = []

    def load_all_data(self):
        """Load all LinkedIn JSON and CSV files including HTML articles"""
        print("🔄 Loading LinkedIn data...")

        file_mappings = {
            'Profile.csv': 'basic_info',
            'Connections.csv': 'connections',
            'Experience.csv': 'experience',
            'Education.csv': 'education',
            'Skills.csv': 'skills',
            'Certifications.csv': 'certifications',
            'Articles.csv': 'articles_metadata',
            'Comments.csv': 'comments',
            'Shares.csv': 'shares',
            'Positions.csv': 'positions',
            'Languages.csv': 'languages',
            'Projects.csv': 'projects',
            'Publications.csv': 'publications',
            'Recommendations.csv': 'recommendations',
            'Endorsement_Given_Info.csv': 'endorsements_given',
            'Endorsement_Received_Info.csv': 'endorsements_received',
            'Courses.csv': 'courses',
            'Learning.csv': 'learning_paths',
            'Interests.csv': 'interests',
            'Company Follow.csv': 'companies_followed',
            'Reactions.csv': 'reactions',
            'Views.csv': 'views',
            'Saved_Items.csv': 'saved_items',
        }

        loaded_count = 0
        for file_name, data_type in file_mappings.items():
            file_path = self.data_path / file_name
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                    self.profile_data[data_type] = df
                    print(f"✅ Loaded {file_name}: {len(df)} records")
                    loaded_count += 1
                except Exception as e:
                    print(f"⚠️ Could not load {file_name}: {str(e)}")
            else:
                print(f"📁 {file_name} not found")

        self.load_html_articles()
        print(f"🎉 Successfully loaded {loaded_count} data files")
        return loaded_count > 0

    def load_html_articles(self):
        """Load and parse HTML articles"""
        print("\n📰 Loading HTML articles...")

        articles_paths = [
            self.data_path / "Articles" / "Articles",
            self.data_path / "Articles",
            self.data_path / "articles" / "articles",
            self.data_path / "articles",
        ]

        found_path = None
        for path in articles_paths:
            if path.exists():
                found_path = path
                break

        if not found_path:
            print("📁 Articles folder not found")
            return

        html_files = list(found_path.glob("*.html"))
        if not html_files:
            print("📄 No HTML files found")
            return

        print(f"📄 Found {len(html_files)} HTML articles")

        articles_data = []
        for html_file in html_files:
            try:
                article_data = self.parse_html_article(html_file)
                if article_data:
                    articles_data.append(article_data)
            except Exception as e:
                print(f"⚠️ Error parsing {html_file.name}: {str(e)}")

        self.articles_content = articles_data
        self.profile_data['articles_html'] = articles_data
        print(f"🎉 Successfully loaded {len(articles_data)} articles")

    def extract_linkedin_url_from_html(self, html_content, filename):
        """Extract LinkedIn URL from HTML article content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Look for canonical URL
            canonical = soup.find('link', {'rel': 'canonical'})
            if canonical and canonical.get('href'):
                url = canonical.get('href')
                if 'linkedin.com' in url:
                    return url

            # Look for meta property og:url
            og_url = soup.find('meta', {'property': 'og:url'})
            if og_url and og_url.get('content'):
                url = og_url.get('content')
                if 'linkedin.com' in url:
                    return url

            # Look for any LinkedIn URLs in the content
            linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/pulse/[^"\s<>]+'
            matches = re.findall(linkedin_pattern, html_content)
            if matches:
                return matches[0]

            # Fallback: construct URL from filename
            if filename:
                clean_name = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+-', '', filename)
                clean_name = clean_name.replace('.html', '')

                if len(clean_name) > 10 and '-' in clean_name:
                    return f"https://www.linkedin.com/pulse/{clean_name}/"

            return None

        except Exception as e:
            print(f"Error extracting LinkedIn URL: {e}")
            return None

    def parse_html_article(self, file_path):
        """Parse individual HTML article with LinkedIn URL extraction"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')

        # Extract title
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text().strip() if title_elem else self.extract_title_from_filename(file_path.name)

        # Extract LinkedIn URL
        linkedin_url = self.extract_linkedin_url_from_html(content, file_path.name)

        # Extract content
        content_selectors = ['article', '.article-content', '.post-content', 'main', '.content', 'body']
        article_content = None
        for selector in content_selectors:
            article_content = soup.select_one(selector)
            if article_content:
                break

        if not article_content:
            article_content = soup.find('body') or soup

        # Convert to plain text
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        plain_text = h.handle(str(article_content)).strip()

        # Extract metadata
        words = re.findall(r'\b\w+\b', plain_text.lower())

        return {
            'filename': file_path.name,
            'title': title,
            'content': str(article_content),
            'plain_text': plain_text,
            'date_published': self.extract_date_from_filename(file_path.name),
            'word_count': len(words),
            'topics': self.extract_topics(plain_text),
            'writing_style': self.analyze_writing_style(plain_text),
            'linkedin_url': linkedin_url
        }

    def extract_title_from_filename(self, filename):
        """Extract readable title from filename"""
        title = filename.replace('.html', '')
        title = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+-', '', title)
        title = title.replace('-', ' ').replace('_', ' ')
        return ' '.join(word.capitalize() for word in title.split())

    def extract_date_from_filename(self, filename):
        """Extract publication date from filename"""
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        return date_match.group(1) if date_match else ''

    def analyze_writing_style(self, text):
        """Analyze writing style indicators"""
        text_lower = text.lower()
        sentences = re.split(r'[.!?]+', text)
        words = re.findall(r'\b\w+\b', text_lower)

        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'question_count': text.count('?'),
            'first_person_usage': len(re.findall(r'\b(i|me|my|myself|we|us|our)\b', text_lower)),
            'technical_terms': sum(text_lower.count(term) for term in ['algorithm', 'framework', 'methodology', 'data', 'analysis', 'technology']),
        }

    def extract_topics(self, text, max_topics=10):
        """Extract main topics from text"""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'been', 'have', 'has', 'had'}
        word_freq = Counter(word for word in words if word not in stop_words and len(word) > 3)
        return [word for word, count in word_freq.most_common(max_topics)]

    def create_rag_documents(self):
        """Create documents for RAG system with LinkedIn URLs"""
        self.rag_documents = []

        # Process profile data
        for data_type, data_content in self.profile_data.items():
            if isinstance(data_content, pd.DataFrame) and not data_content.empty:
                self.process_dataframe_to_documents(data_content, data_type)
            elif isinstance(data_content, list) and data_content:
                self.process_list_to_documents(data_content, data_type)

        # Process articles with LinkedIn URLs
        if self.articles_content:
            for article in self.articles_content:
                if article['plain_text'].strip():
                    self.rag_documents.append({
                        'text': article['plain_text'],
                        'title': article['title'],
                        'source_type': 'article',
                        'date_published': article['date_published'],
                        'word_count': article['word_count'],
                        'topics': article['topics'],
                        'linkedin_url': article.get('linkedin_url', ''),
                        'filename': article['filename']
                    })

        print(f"📚 Created {len(self.rag_documents)} RAG documents with LinkedIn URLs")
        return self.rag_documents

    def process_dataframe_to_documents(self, df, data_type):
        """Convert DataFrame to RAG documents"""
        if data_type == 'experience':
            for _, row in df.iterrows():
                text = f"Experience: {row.get('Title', '')} at {row.get('Company', '')}\n"
                text += f"Duration: {row.get('Started On', '')} - {row.get('Finished On', 'Present')}\n"
                text += f"Description: {row.get('Description', '')}"

                self.rag_documents.append({
                    'text': text,
                    'title': f"{row.get('Title', '')} at {row.get('Company', '')}",
                    'source_type': 'experience',
                    'linkedin_url': ''
                })

        elif data_type == 'education':
            for _, row in df.iterrows():
                text = f"Education: {row.get('Degree', '')} in {row.get('Field Of Study', '')} from {row.get('School', '')}\n"
                text += f"Duration: {row.get('Start Date', '')} - {row.get('End Date', '')}"

                self.rag_documents.append({
                    'text': text,
                    'title': f"{row.get('Degree', '')} - {row.get('School', '')}",
                    'source_type': 'education',
                    'linkedin_url': ''
                })

        elif data_type == 'skills':
            if 'Skill' in df.columns:
                skills_text = "Professional Skills: " + ", ".join(df['Skill'].dropna().tolist())
                self.rag_documents.append({
                    'text': skills_text,
                    'title': 'Professional Skills',
                    'source_type': 'skills',
                    'linkedin_url': ''
                })

        elif data_type == 'certifications':
            if 'Name' in df.columns:
                certs_text = "Certifications: " + ", ".join(df['Name'].dropna().tolist())
                self.rag_documents.append({
                    'text': certs_text,
                    'title': 'Certifications',
                    'source_type': 'certifications',
                    'linkedin_url': ''
                })

        elif data_type == 'projects':
            for _, row in df.iterrows():
                text = f"Project: {row.get('Title', '')}\n"
                text += f"Description: {row.get('Description', '')}\n"
                text += f"URL: {row.get('Url', '')}"

                project_url = row.get('Url', '')
                linkedin_url = project_url if 'linkedin.com' in str(project_url) else ''

                self.rag_documents.append({
                    'text': text,
                    'title': row.get('Title', 'Project'),
                    'source_type': 'projects',
                    'linkedin_url': linkedin_url
                })

    def process_list_to_documents(self, data_list, data_type):
        """Convert list data to RAG documents"""
        if data_type == 'articles_html':
            return

    def get_profile_summary(self):
        """Get comprehensive profile summary"""
        summary = {
            'total_documents': len(self.rag_documents),
            'articles_count': len(self.articles_content),
            'data_types': list(self.profile_data.keys()),
            'skills_count': len(self.profile_data.get('skills', [])),
            'experience_count': len(self.profile_data.get('experience', [])),
            'education_count': len(self.profile_data.get('education', [])),
        }

        if self.articles_content:
            total_words = sum(article['word_count'] for article in self.articles_content)
            summary['total_article_words'] = total_words
            summary['avg_article_length'] = total_words // len(self.articles_content)

        return summary

# ================================
# RAG SYSTEM
# ================================

class LinkedInRAGSystem:
    def __init__(self, chroma_db_path):
        self.chroma_db_path = chroma_db_path
        self.embedding_model = None
        self.cross_encoder_model = None
        self.cross_encoder_tokenizer = None
        self.chroma_client = None
        self.collection = None
        self.openai_client = None

    def initialize_models(self):
        """Initialize all required models"""
        print("🔄 Initializing RAG models...")

        # Initialize OpenAI client
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ OpenAI API key not found in environment variables")
                return False
            self.openai_client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            return False

        # Load embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            return False

        # Load cross-encoder for reranking
        try:
            cross_encoder_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
            self.cross_encoder_tokenizer = AutoTokenizer.from_pretrained(cross_encoder_name)
            self.cross_encoder_model = AutoModelForSequenceClassification.from_pretrained(cross_encoder_name)
            print("✅ Cross-encoder model loaded")
        except Exception as e:
            print(f"❌ Failed to load cross-encoder: {e}")
            return False

        # Initialize ChromaDB
        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_db_path)
            print("✅ ChromaDB initialized")
        except Exception as e:
            print(f"❌ Failed to initialize ChromaDB: {e}")
            return False

        return True

    def create_vector_store(self, documents):
        """Create vector store from documents with enhanced metadata"""
        print("🔄 Creating vector store with LinkedIn URLs...")

        # Delete existing collection if it exists
        try:
            self.chroma_client.delete_collection("linkedin_profile")
        except:
            pass

        # Create new collection
        self.collection = self.chroma_client.create_collection("linkedin_profile")

        # Generate embeddings
        texts = [doc['text'] for doc in documents]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        # Prepare data for ChromaDB with enhanced metadata
        ids = [f"doc_{i}" for i in range(len(documents))]
        metadatas = []

        for doc in documents:
            metadata = {}
            for k, v in doc.items():
                if k != 'text':
                    if k == 'linkedin_url' and v:
                        metadata[k] = str(v)
                    elif k == 'date_published' and v:
                        metadata[k] = str(v)
                    elif k == 'topics' and isinstance(v, list):
                        metadata[k] = ', '.join(v) if v else ''
                    elif v is not None:
                        metadata[k] = str(v)
                    else:
                        metadata[k] = ''
            metadatas.append(metadata)

        # Add to collection
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            end_idx = min(i + batch_size, len(texts))
            self.collection.add(
                embeddings=embeddings[i:end_idx].tolist(),
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )

        print(f"✅ Vector store created with {self.collection.count()} documents")
        return True

    def retrieve_and_rerank(self, query, initial_k=20, final_n=5):
        """Retrieve and rerank documents"""
        if not self.collection:
            return []

        try:
            # Initial retrieval
            query_embedding = self.embedding_model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=initial_k,
                include=['documents', 'metadatas']
            )

            if not results['documents'][0]:
                return []

            # Prepare for reranking
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]

            # Rerank with cross-encoder
            pairs = [[query, doc] for doc in documents]
            inputs = self.cross_encoder_tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors='pt',
                max_length=512
            )

            with torch.no_grad():
                scores = self.cross_encoder_model(**inputs).logits.squeeze()

            if scores.dim() == 0:
                scores = [scores.item()]
            else:
                scores = scores.tolist()

            # Sort by score
            scored_docs = list(zip(documents, metadatas, scores))
            scored_docs.sort(key=lambda x: x[2], reverse=True)

            # Return top documents
            return [{'text': doc, 'metadata': meta, 'score': score}
                    for doc, meta, score in scored_docs[:final_n]]

        except Exception as e:
            print(f"Error in retrieve_and_rerank: {e}")
            return []

    def generate_response(self, query, retrieved_docs):
        """Generate response using OpenAI"""
        if not retrieved_docs:
            return "I couldn't find relevant information to answer your question."

        context = "\n\n".join([doc['text'] for doc in retrieved_docs])

        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant representing a LinkedIn profile. Answer questions based ONLY on the provided context from the LinkedIn profile data and articles.

Guidelines:
- Be professional and personable
- Provide specific details when available
- If information isn't in the context, politely say so
- Use first person when appropriate (since you're representing the profile owner)
- Keep responses concise but informative
- Do not mention or reference the sources in your response - that will be handled separately"""
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}\n\nPlease answer based on the LinkedIn profile information provided:"
            }
        ]

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=400,
                temperature=0.3,
                top_p=0.9
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Sorry, I encountered an error generating a response: {str(e)}"

    def format_sources_with_links(self, retrieved_docs):
        """Format sources with clickable LinkedIn links"""
        if not retrieved_docs:
            return ""

        sources_html = "<br><br>**📚 Sources:**<br>"

        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc['metadata']
            source_type = metadata.get('source_type', 'Unknown')
            title = metadata.get('title', 'Untitled')
            linkedin_url = metadata.get('linkedin_url', '')
            date_published = metadata.get('date_published', '')

            # Create source entry
            if linkedin_url:
                # Clickable LinkedIn link
                source_entry = f"🔗 <a href='{linkedin_url}' target='_blank' style='color: #0077B5; text-decoration: none; font-weight: 500;'>{title}</a>"
                if date_published:
                    source_entry += f" <span style='color: #666; font-size: 0.9em;'>({date_published})</span>"
            else:
                # No link available
                source_entry = f"📄 **{title}**"
                if date_published:
                    source_entry += f" <span style='color: #666; font-size: 0.9em;'>({date_published})</span>"

            # Add source type badge
            type_color = {
                'article': '#0077B5',
                'experience': '#2D7D32',
                'education': '#7B1FA2',
                'skills': '#F57C00',
                'projects': '#D32F2F',
                'certifications': '#1976D2'
            }.get(source_type, '#666')

            source_type_badge = f"<span style='background: {type_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 8px;'>{source_type.title()}</span>"

            sources_html += f"{i}. {source_entry}{source_type_badge}<br>"

        return sources_html

    def chat(self, query):
        """Main chat function with enhanced source linking"""
        retrieved_docs = self.retrieve_and_rerank(query)
        response = self.generate_response(query, retrieved_docs)

        # Add formatted sources with links
        sources_info = self.format_sources_with_links(retrieved_docs)

        return response + sources_info

# ================================
# UTILITY FUNCTIONS
# ================================

def extract_uploaded_data(zip_file_path, extract_to):
    """Extract uploaded LinkedIn data zip file"""
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✅ Extracted data to {extract_to}")
        return True
    except Exception as e:
        print(f"❌ Failed to extract zip file: {e}")
        return False

def initialize_linkedin_chatbot(data_path):
    """Initialize the complete LinkedIn chatbot system with clickable sources"""
    print("🚀 Initializing LinkedIn Profile Chatbot with clickable sources...")

    # Step 1: Load and process data
    processor = LinkedInDataProcessor(data_path)
    if not processor.load_all_data():
        return None, "Failed to load LinkedIn data. Please check the uploaded data."

    # Step 2: Create RAG documents with LinkedIn URLs
    documents = processor.create_rag_documents()
    if not documents:
        return None, "No documents created from LinkedIn data."

    # Count articles with LinkedIn URLs
    articles_with_urls = sum(1 for doc in documents if doc.get('linkedin_url') and doc.get('source_type') == 'article')

    # Step 3: Initialize RAG system
    temp_db_path = tempfile.mkdtemp()
    rag_system = LinkedInRAGSystem(temp_db_path)
    if not rag_system.initialize_models():
        return None, "Failed to initialize RAG models."

    # Step 4: Create vector store
    if not rag_system.create_vector_store(documents):
        return None, "Failed to create vector store."

    # Step 5: Get profile summary
    summary = processor.get_profile_summary()

    # Create a clean status message
    summary_text = f"""
### ✅ **AI Assistant Ready with Clickable Sources!**

I have successfully analyzed the LinkedIn profile data including **{summary['total_documents']} documents** and **{summary['articles_count']} published articles** ({articles_with_urls} with direct LinkedIn links).

**💼 What I can help you discover:**
- 🎯 **Professional Journey** - Career progression and experience
- 🛠️ **Skills & Expertise** - Technical and professional capabilities
- 🎓 **Educational Background** - Academic achievements and learning
- 📝 **Published Content** - Articles with direct LinkedIn links
- 🚀 **Projects & Achievements** - Notable work and accomplishments
- 🌐 **Professional Network** - Industry connections and activities

**🔗 Enhanced Features:**
- **Clickable Sources** - Direct links to LinkedIn articles and content
- **Smart Source Attribution** - See exactly where information comes from
- **Professional Context** - Answers based on real LinkedIn profile data

**Ready to explore this professional profile!** Ask me anything you'd like to know.
"""

    return rag_system, summary_text

# ================================
# GRADIO INTERFACE
# ================================

# Global variables
current_rag_system = None
current_status = "Upload your LinkedIn data to get started!"

# Add this anywhere in your Gradio interface after the status_display
usage_info = gr.Markdown(value=usage_tracker.get_usage_info())

def process_upload(zip_file):
    """Process uploaded LinkedIn data"""
    global current_rag_system, current_status
    
    if zip_file is None:
        return "Please upload a LinkedIn data ZIP file first.", ""
    
    try:
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        
        # Extract the uploaded file
        if extract_uploaded_data(zip_file.name, temp_dir):
            # Initialize the RAG system
            rag_system, status_message = initialize_linkedin_chatbot(temp_dir)
            
            if rag_system:
                current_rag_system = rag_system
                current_status = status_message
                return status_message, "✅ **Ready to chat!** Ask me anything about the LinkedIn profile."
            else:
                return f"❌ Failed to initialize: {status_message}", ""
        else:
            return "❌ Failed to extract uploaded file.", ""
            
    except Exception as e:
        return f"❌ Error processing upload: {str(e)}", ""

@protected_function
def chat_with_profile(message, history):
    """Chat function with protection"""
    global current_rag_system
    
    if current_rag_system is None:
        bot_response = "❌ **Please upload your LinkedIn data first using the file upload above.**"
        history.append((message, bot_response))
        return history, ""
    
    if not message.strip():
        bot_response = "👋 Please enter a question about the LinkedIn profile!"
        history.append((message, bot_response))
        return history, ""
    
    try:
        bot_response = current_rag_system.chat(message)
        history.append((message, bot_response))
    except Exception as e:
        bot_response = f"❌ **Error**: {str(e)}"
        history.append((message, bot_response))
    
    return history, ""

# Premium CSS
premium_css = """
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Main container styling */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

/* Header styling */
.main-header {
    background: linear-gradient(135deg, #0077B5 0%, #00A0DC 50%, #40E0D0 100%);
    color: white;
    padding: 2rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,119,181,0.3);
    border: 1px solid rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
}

.main-header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.main-header p {
    font-size: 1.2rem;
    opacity: 0.95;
    font-weight: 400;
}

/* Status card styling */
.status-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    border: 1px solid rgba(0,119,181,0.1);
}

/* Chat container */
.chat-container {
    background: white;
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    border: 1px solid rgba(0,119,181,0.1);
    max-width: 900px;
    margin: 0 auto;
}

/* Upload container */
.upload-container {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border: 2px dashed #0077B5;
}

/* Button styling */
.primary-btn {
    background: linear-gradient(135deg, #0077B5 0%, #00A0DC 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,119,181,0.3);
}

.primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,119,181,0.4);
}

/* Example buttons */
.example-btn {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    color: #0077B5;
    border: 1px solid #0077B5;
    border-radius: 25px;
    padding: 0.6rem 1.2rem;
    font-weight: 500;
    margin: 0.3rem;
    transition: all 0.3s ease;
    font-size: 0.9rem;
}

.example-btn:hover {
    background: linear-gradient(135deg, #0077B5 0%, #00A0DC 100%);
    color: white;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,119,181,0.3);
}

/* Input styling */
.input-text {
    border: 2px solid #e1e8ed;
    border-radius: 12px;
    padding: 1rem;
    font-size: 1rem;
    transition: all 0.3s ease;
    background: #f8fafc;
}

.input-text:focus {
    border-color: #0077B5;
    box-shadow: 0 0 0 3px rgba(0,119,181,0.1);
    background: white;
}

/* Chatbot styling */
.chatbot {
    border: none;
    border-radius: 16px;
    box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);
}

/* Accordion styling */
.accordion {
    background: linear-gradient(135deg, #f8fafc 0%, #e1e8ed 100%);
    border-radius: 12px;
    border: 1px solid #e1e8ed;
}
"""

# Create Gradio interface
with gr.Blocks(css=premium_css, title="LinkedIn Profile AI Assistant", theme=gr.themes.Soft()) as interface:

    # Main Header
    gr.HTML("""
        <div class="main-header">
            <h1>🤖 LinkedIn Profile AI Assistant</h1>
            <p>Intelligent insights with clickable sources to original LinkedIn content</p>
        </div>
    """)

    # Upload Section
    with gr.Column(elem_classes=["upload-container"]):
        gr.Markdown("### 📁 **Upload Your LinkedIn Data**")
        gr.Markdown("Upload your LinkedIn data export ZIP file to get started. [Learn how to export your LinkedIn data](https://www.linkedin.com/help/linkedin/answer/a1339364)")
        
        with gr.Row():
            upload_file = gr.File(
                label="LinkedIn Data ZIP File",
                file_types=[".zip"],
                type="filepath"
            )
            upload_btn = gr.Button(
                "🚀 Process Data",
                variant="primary",
                elem_classes=["primary-btn"]
            )

    # Status Display
    status_display = gr.Markdown(
        value="📁 **Upload your LinkedIn data ZIP file above to get started!**",
        elem_classes=["status-card"]
    )
    
    chat_status = gr.Markdown(
        value="",
        elem_classes=["status-card"]
    )

    # Main Chat Interface
    with gr.Column(elem_classes=["chat-container"]):

        # Chat Display
        chatbot = gr.Chatbot(
            label="💬 Professional Profile Assistant",
            height=550,
            show_copy_button=True,
            avatar_images=("👤", "🤖"),
            bubble_full_width=False,
            elem_classes=["chatbot"]
        )

        # Input Section
        with gr.Row():
            with gr.Column(scale=5):
                msg = gr.Textbox(
                    placeholder="Ask about experience, skills, education, articles, or any aspect of the professional profile...",
                    label="Your Question",
                    lines=2,
                    max_lines=4,
                    elem_classes=["input-text"]
                )
            with gr.Column(scale=1, min_width=100):
                submit_btn = gr.Button(
                    "Send 💬",
                    variant="primary",
                    size="lg",
                    elem_classes=["primary-btn"]
                )

        # Quick Action Buttons
        with gr.Row():
            clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary", size="sm")

    # Enhanced Examples Section
    with gr.Accordion("💡 Example Questions - Click to Try", open=False, elem_classes=["accordion"]) as examples_accordion:

        gr.Markdown("### 🎯 **Professional Experience & Career**")
        with gr.Row():
            exp_q1 = gr.Button("What is the professional background?", elem_classes=["example-btn"], size="sm")
            exp_q2 = gr.Button("Describe the career progression", elem_classes=["example-btn"], size="sm")
            exp_q3 = gr.Button("What are the key achievements?", elem_classes=["example-btn"], size="sm")

        gr.Markdown("### 🛠️ **Skills & Expertise**")
        with gr.Row():
            skill_q1 = gr.Button("What skills and expertise are highlighted?", elem_classes=["example-btn"], size="sm")
            skill_q2 = gr.Button("What technologies are mentioned?", elem_classes=["example-btn"], size="sm")
            skill_q3 = gr.Button("What are the main areas of expertise?", elem_classes=["example-btn"], size="sm")

        gr.Markdown("### 📚 **Education & Learning**")
        with gr.Row():
            edu_q1 = gr.Button("Tell me about the educational background", elem_classes=["example-btn"], size="sm")
            edu_q2 = gr.Button("What certifications are mentioned?", elem_classes=["example-btn"], size="sm")
            edu_q3 = gr.Button("What courses or learning paths are included?", elem_classes=["example-btn"], size="sm")

        gr.Markdown("### 📝 **Articles & Content**")
        with gr.Row():
            content_q1 = gr.Button("What articles have been published?", elem_classes=["example-btn"], size="sm")
            content_q2 = gr.Button("What topics are covered in the writing?", elem_classes=["example-btn"], size="sm")
            content_q3 = gr.Button("What is the writing style like?", elem_classes=["example-btn"], size="sm")

        # Connect example buttons to input
        example_questions = [
            (exp_q1, "What is the professional background and experience?"),
            (exp_q2, "Describe the career progression and professional journey"),
            (exp_q3, "What are the key achievements and accomplishments?"),
            (skill_q1, "What skills and expertise are highlighted in the profile?"),
            (skill_q2, "What technologies, tools, and platforms are mentioned?"),
            (skill_q3, "What are the main areas of expertise and specialization?"),
            (edu_q1, "Tell me about the educational background and qualifications"),
            (edu_q2, "What certifications and professional credentials are mentioned?"),
            (edu_q3, "What courses, training, or learning paths are included?"),
            (content_q1, "What articles and content have been published?"),
            (content_q2, "What topics and themes are covered in the published writing?"),
            (content_q3, "What is the writing style and approach in the articles?")
        ]

        for btn, question in example_questions:
            btn.click(lambda q=question: q, outputs=msg)

    # About Section
    with gr.Accordion("ℹ️ About This AI Assistant", open=False, elem_classes=["accordion"]):
        gr.Markdown("""
            ### 🚀 **Advanced AI-Powered Profile Analysis with Clickable Sources**

            This intelligent assistant uses cutting-edge **Retrieval-Augmented Generation (RAG)** technology to provide accurate, contextual answers about LinkedIn profiles with direct links to original content.

            **🔧 Technical Capabilities:**
            - **Vector Search**: Semantic similarity matching for relevant information retrieval
            - **Cross-Encoder Reranking**: Advanced relevance scoring for precision
            - **GPT-4 Generation**: Natural, human-like response generation
            - **Multi-Source Integration**: Combines structured data and article content
            - **Clickable Sources**: Direct links to original LinkedIn articles and content

            **📊 Data Sources Analyzed:**
            - Professional experience and job history
            - Educational background and certifications
            - Skills, endorsements, and expertise areas
            - Published articles and thought leadership content (with clickable links)
            - Projects, achievements, and recommendations
            - Professional network activities and engagement

            **🔒 Privacy & Security:**
            - Only uses uploaded LinkedIn profile data
            - No external data access or web browsing
            - Responses based solely on uploaded content
            - Secure processing with no data retention

            **⚡ Built with:**
            - Gradio for the interface
            - OpenAI GPT-4 for generation
            - ChromaDB for vector storage
            - Sentence Transformers for embeddings
            - Custom LinkedIn URL extraction
        """)

    # Event Handlers
    upload_btn.click(
        process_upload,
        inputs=[upload_file],
        outputs=[status_display, chat_status]
    )

    msg.submit(chat_with_profile, inputs=[msg, chatbot], outputs=[chatbot, msg])
    submit_btn.click(chat_with_profile, inputs=[msg, chatbot], outputs=[chatbot, msg])
    clear_btn.click(lambda: [], outputs=chatbot)

    # Add this to your existing event handlers
    submit_btn.click(
        lambda: usage_tracker.get_usage_info(), 
        outputs=usage_info,
        queue=False
    )

    # Footer
    gr.HTML("""
        <div style="text-align: center; margin-top: 2rem; padding: 1rem; color: #666; font-size: 0.9rem;">
            <p>🤖 <strong>LinkedIn Profile AI Assistant</strong> | Powered by Advanced RAG Technology with Clickable Sources</p>
            <p>Built with ❤️ using Gradio, OpenAI GPT-4, ChromaDB, and Custom LinkedIn URL extraction</p>
        </div>
    """)

# Launch the interface
# Launch the interface
if __name__ == "__main__":
    interface.launch()