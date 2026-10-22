"""
VoiceScribe AI - Intelligent Audio Analysis Tool
Transforms MP3 recordings into actionable insights with transcription, summarization, and Q&A capabilities.
"""

import gradio as gr
import torch
from transformers import pipeline
from typing import Optional, Tuple, List
import re
from dataclasses import dataclass
import librosa  # For audio loading without ffmpeg
import warnings

# Suppress all deprecation and future warnings
warnings.filterwarnings("ignore", message=".*forced_decoder_ids.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# LangChain imports for RAG
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline  # NEW: Both from langchain_huggingface
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# For summarization
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


@dataclass
class TranscriptionResult:
    """Store transcription results and metadata"""
    text: str
    summary: str = ""
    key_points: List[str] = None
    timestamps: dict = None


class VoiceScribeAI:
    """Main class for VoiceScribe AI functionality"""

    def __init__(self):
        """Initialize models and components"""
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.dtype = torch.float16 if self.device == 'cuda' else torch.float32

        # Initialize transcription pipeline
        print(f"Loading Whisper model on {self.device}...")
        self.transcription_pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-medium.en",
            device=0 if self.device == 'cuda' else -1,  # 0 for GPU, -1 for CPU
            return_timestamps=True
        )

        # Initialize summarization model
        print("Loading summarization model...")
        self.summarization_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
        self.summarization_model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
        if self.device == 'cuda':
            self.summarization_model = self.summarization_model.to(self.device)

        # Initialize embeddings for RAG
        print("Loading embeddings model for RAG...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Initialize QA model
        print("Loading QA model...")
        qa_model = "google/flan-t5-base"
        self.qa_pipeline = pipeline(
            "text2text-generation",
            model=qa_model,
            device=0 if self.device == 'cuda' else -1,
            max_length=512
        )
        self.llm = HuggingFacePipeline(pipeline=self.qa_pipeline)

        # Storage for current session
        self.current_transcription: Optional[TranscriptionResult] = None
        self.vector_store: Optional[FAISS] = None
        self.qa_chain: Optional[RetrievalQA] = None

        print("✅ All models loaded successfully!")

    def transcribe_audio(self, audio_file_path: str, progress=gr.Progress()) -> Tuple[str, str, str, str]:
        """
        Transcribe audio file and return results

        Args:
            audio_file_path: Path to the audio file
            progress: Gradio progress tracker

        Returns:
            Tuple of (transcription, summary, key_points, status_message)
        """
        if not audio_file_path:
            return "", "", "", "❌ Please upload an audio file first."

        try:
            progress(0, desc="Starting transcription...")

            # Load audio using librosa (no ffmpeg needed!)
            progress(0.1, desc="Loading audio file...")
            audio_array, sampling_rate = librosa.load(audio_file_path, sr=16000)

            # Transcribe audio
            progress(0.2, desc="Transcribing audio (this may take a few minutes)...")
            result = self.transcription_pipe({
                "array": audio_array,
                "sampling_rate": sampling_rate
            })
            transcription = result["text"]
            timestamps = result.get("chunks", [])

            # Store transcription
            self.current_transcription = TranscriptionResult(
                text=transcription,
                timestamps=timestamps
            )

            progress(0.5, desc="Generating summary...")
            summary = self.generate_summary(transcription)
            self.current_transcription.summary = summary

            progress(0.8, desc="Extracting key points...")
            key_points = self.extract_key_points(transcription)
            self.current_transcription.key_points = key_points
            key_points_text = "\n".join([f"• {point}" for point in key_points])

            # Set up RAG for Q&A
            progress(0.9, desc="Setting up Q&A system...")
            self.setup_rag(transcription)

            progress(1.0, desc="Complete!")

            status = f"✅ Transcription complete! ({len(transcription.split())} words)"
            return transcription, summary, key_points_text, status

        except Exception as e:
            error_msg = f"❌ Error during transcription: {str(e)}"
            print(error_msg)
            return "", "", "", error_msg

    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a concise summary of the text"""
        try:
            # Split text into chunks if too long
            max_input_length = 1024
            chunks = self._split_text(text, max_input_length)

            summaries = []
            for chunk in chunks:
                inputs = self.summarization_tokenizer(
                    chunk,
                    max_length=max_input_length,
                    truncation=True,
                    return_tensors="pt"
                )

                if self.device == 'cuda':
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}

                summary_ids = self.summarization_model.generate(
                    inputs["input_ids"],
                    max_length=max_length,
                    min_length=50,
                    num_beams=4,
                    length_penalty=2.0,
                    early_stopping=True
                )

                summary = self.summarization_tokenizer.decode(
                    summary_ids[0],
                    skip_special_tokens=True
                )
                summaries.append(summary)

            # Combine summaries if multiple chunks
            if len(summaries) > 1:
                combined = " ".join(summaries)
                # Generate final summary of summaries
                inputs = self.summarization_tokenizer(
                    combined,
                    max_length=max_input_length,
                    truncation=True,
                    return_tensors="pt"
                )

                if self.device == 'cuda':
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}

                summary_ids = self.summarization_model.generate(
                    inputs["input_ids"],
                    max_length=max_length,
                    min_length=50,
                    num_beams=4
                )

                return self.summarization_tokenizer.decode(
                    summary_ids[0],
                    skip_special_tokens=True
                )

            return summaries[0]

        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """Extract key points from the text"""
        try:
            # Use the QA model to extract key points
            prompt = f"""Extract {num_points} key points or main ideas from the following text.
            List them as numbered points.

            Text: {text[:2000]}

            Key points:"""

            result = self.qa_pipeline(
                prompt,
                max_length=300,
                num_return_sequences=1
            )

            points_text = result[0]['generated_text']

            # Parse the points
            points = []
            lines = points_text.split('\n')
            for line in lines:
                line = line.strip()
                # Remove numbering and clean up
                line = re.sub(r'^\d+[\.\)]\s*', '', line)
                if line and len(line) > 10:
                    points.append(line)

            # If parsing failed, create basic points from sentences
            if not points:
                sentences = text.split('.')
                points = [s.strip() + '.' for s in sentences[:num_points] if len(s.strip()) > 20]

            return points[:num_points]

        except Exception:
            # Fallback: extract first few sentences
            sentences = text.split('.')
            return [s.strip() + '.' for s in sentences[:num_points] if len(s.strip()) > 20]

    def setup_rag(self, text: str):
        """Set up RAG system for Q&A"""
        try:
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            chunks = text_splitter.split_text(text)

            # Create vector store
            self.vector_store = FAISS.from_texts(chunks, self.embeddings)

            # Create QA chain
            qa_prompt_template = """Use the following pieces of context to answer the question at the end.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.

            Context: {context}

            Question: {question}

            Answer:"""

            QA_PROMPT = PromptTemplate(
                template=qa_prompt_template,
                input_variables=["context", "question"]
            )

            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
                chain_type_kwargs={"prompt": QA_PROMPT}
            )

        except Exception as e:
            print(f"Error setting up RAG: {e}")
            self.qa_chain = None

    def answer_question(self, question: str) -> str:
        """Answer questions about the transcription using RAG"""
        if not self.current_transcription:
            return "⚠️ Please transcribe an audio file first before asking questions."

        if not question or question.strip() == "":
            return "⚠️ Please enter a question."

        if not self.qa_chain:
            return "⚠️ Q&A system not ready. Please try transcribing the audio again."

        try:
            result = self.qa_chain.invoke({"query": question})
            answer = result.get('result', 'No answer found.')
            return answer
        except Exception as e:
            return f"❌ Error answering question: {str(e)}"

    def search_transcript(self, keyword: str) -> str:
        """Search for keyword in transcript"""
        if not self.current_transcription:
            return "⚠️ Please transcribe an audio file first."

        if not keyword or keyword.strip() == "":
            return "⚠️ Please enter a keyword to search."

        try:
            text = self.current_transcription.text
            keyword = keyword.strip().lower()

            # Find all occurrences
            sentences = text.split('.')
            matches = []

            for sentence in sentences:
                if keyword in sentence.lower():
                    context = sentence.strip()
                    matches.append(f"[Match {len(matches) + 1}] ...{context}...")

            if matches:
                result = f"Found {len(matches)} occurrence(s) of '{keyword}':\n\n"
                result += "\n\n".join(matches)
                return result
            else:
                return f"No occurrences of '{keyword}' found in the transcript."

        except Exception as e:
            return f"❌ Error searching transcript: {str(e)}"

    def _split_text(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks of max_length words"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            current_chunk.append(word)
            current_length += 1

            if current_length >= max_length:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks


def create_gradio_interface():
    """Create and configure the Gradio interface"""

    # Initialize VoiceScribe AI
    vs_ai = VoiceScribeAI()

    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        font-family: 'Arial', sans-serif;
    }
    .header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    """

    # Create interface
    with gr.Blocks(css=custom_css, title="VoiceScribe AI") as demo:
        gr.Markdown("""
        # 🎤 VoiceScribe AI
        ### Intelligent Audio Analysis Tool
        Transform your audio recordings into actionable insights with AI-powered transcription, summarization, and Q&A.
        """, elem_classes="header")

        with gr.Tab("📝 Transcribe & Analyze"):
            gr.Markdown("""
            ### Upload your audio file to get started
            Supports MP3, WAV, M4A, and other common audio formats.
            """)

            with gr.Row():
                audio_input = gr.Audio(
                    label="Upload Audio File",
                    type="filepath",
                    format="wav"
                )

            transcribe_btn = gr.Button("🚀 Transcribe & Analyze", variant="primary", size="lg")
            status_output = gr.Textbox(label="Status", interactive=False)

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📄 Full Transcript")
                    transcript_output = gr.Textbox(
                        label="Transcription",
                        lines=10,
                        placeholder="Transcript will appear here...",
                        interactive=False
                    )

                with gr.Column():
                    gr.Markdown("### 📊 Summary")
                    summary_output = gr.Textbox(
                        label="Summary",
                        lines=5,
                        placeholder="Summary will appear here...",
                        interactive=False
                    )

                    gr.Markdown("### 🎯 Key Points")
                    keypoints_output = gr.Textbox(
                        label="Key Points",
                        lines=5,
                        placeholder="Key points will appear here...",
                        interactive=False
                    )

        # Combined Chat & Search Tab
        with gr.Tab("💬 Chat & Search"):
            gr.Markdown("""
            ### Interact with your transcription
            Ask questions or search for specific keywords in your transcript.
            """)

            with gr.Row():
                # Left Column - Chat with Audio (Q&A)
                with gr.Column():
                    gr.Markdown("### 💬 Chat with Audio (Q&A)")
                    gr.Markdown("Ask natural language questions about your transcription.")

                    question_input = gr.Textbox(
                        label="Ask a Question",
                        placeholder="e.g., What were the main topics discussed?",
                        lines=2
                    )
                    ask_btn = gr.Button("🤔 Get Answer", variant="primary")
                    answer_output = gr.Textbox(
                        label="Answer",
                        lines=6,
                        placeholder="Answer will appear here...",
                        interactive=False
                    )

                    gr.Markdown("""
                    **Example Questions:**
                    - What did they say about training data?
                    - What are the action items mentioned?
                    - What problems were discussed?
                    """)

                # Right Column - Search Transcript
                with gr.Column():
                    gr.Markdown("### 🔍 Search Transcript")
                    gr.Markdown("Find all occurrences of a keyword or phrase.")

                    search_input = gr.Textbox(
                        label="Enter Keyword",
                        placeholder="e.g., deadline, budget, meeting",
                        lines=2
                    )
                    search_btn = gr.Button("🔎 Search", variant="primary")
                    search_output = gr.Textbox(
                        label="Search Results",
                        lines=6,
                        placeholder="Search results will appear here...",
                        interactive=False
                    )

                    gr.Markdown("""
                    **Search Tips:**
                    - Use single keywords for best results
                    - Try different variations (e.g., "meet", "meeting")
                    - Search is case-insensitive
                    """)

        with gr.Tab("ℹ️ About"):
            gr.Markdown("""
            ## About VoiceScribe AI

            VoiceScribe AI is an intelligent audio analysis tool that transforms your audio recordings into actionable insights.

            ### 🔹 Key Features:

            - **🎤 Automatic Transcription**: Converts audio to text using OpenAI's Whisper model
            - **🧠 Smart Summarization**: Generates clear summaries using BART
            - **📌 Key Points Extraction**: Lists the main topics and action items
            - **🔍 Searchable Transcript**: Quickly find parts of the recording by keyword
            - **💬 Chat with Audio (Q&A Mode)**: Ask natural questions using RAG (Retrieval Augmented Generation)
            - **📂 Drag-and-Drop Uploads**: Simple, user-friendly interface
            - **⚡ Real-Time Progress**: Watch transcription progress as it happens

            ### 🛠️ Technology Stack:

            - **Transcription**: OpenAI Whisper (medium.en)
            - **Summarization**: Facebook BART-large-CNN
            - **Q&A**: Google FLAN-T5 with LangChain RAG
            - **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
            - **Vector Store**: FAISS
            - **UI**: Gradio

            ### 📝 Usage Tips:

            1. Upload your audio file in the "Transcribe & Analyze" tab
            2. ⏳ **Wait for transcription to complete (may take a few minutes on CPU)**
            3. View your transcript, summary, and key points
            4. Switch to "Chat with Audio" to ask questions
            5. Use "Search Transcript" to find specific keywords

            ### 🚀 Powered by Open Source Models
            """)

        # Connect functions
        transcribe_btn.click(
            fn=vs_ai.transcribe_audio,
            inputs=[audio_input],
            outputs=[transcript_output, summary_output, keypoints_output, status_output]
        )

        ask_btn.click(
            fn=vs_ai.answer_question,
            inputs=[question_input],
            outputs=[answer_output]
        )

        search_btn.click(
            fn=vs_ai.search_transcript,
            inputs=[search_input],
            outputs=[search_output]
        )

    return demo


if __name__ == "__main__":
    print("🚀 Starting VoiceScribe AI...")
    print("=" * 60)

    # Create and launch interface
    demo = create_gradio_interface()

    print("=" * 60)
    print("✅ VoiceScribe AI is ready!")
    print("🌐 Opening in browser...")

    demo.launch(
        share=True,  # Create public link
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,
        show_error=True
    )
