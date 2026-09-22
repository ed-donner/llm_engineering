import modal
from modal import Volume, Image
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_chroma import Chroma
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from langchain_core.documents import Document
import json
import os
from datetime import datetime

app = modal.App("audiatur-assistant-service")
image = Image.debian_slim().apt_install("sqlite3").pip_install(
    "torch", "transformers", "bitsandbytes", "accelerate","langchain","langchain-core","langchain-community","langchain-chroma","chromadb","sentence-transformers","firebase-admin"
)

GPU = "T4"
BASE_MODEL = "meta-llama/Llama-3.2-3B"
CACHE_DIR = "/cache"
VECTOR_DB_DIR = "/vector_db"

# Change this to 1 if you want Modal to be always running, otherwise it will go cold after 2 mins
MIN_CONTAINERS = 1

hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)
vector_volume = Volume.from_name("vector-db", create_if_missing=True)

secrets = [modal.Secret.from_name("huggingface-secret"), modal.Secret.from_name("firebase_secret")]

today = datetime.utcnow().strftime("%A, %B %d, %Y")
SYSTEM_PROMPT_TEMPLATE = f"""
You are a knowledgeable, friendly assistant that helps users get information about a community.

You can:
- answer questions about events
- check if a user is registered for an event
- register users for events
- retrieve events a user registered for

Today's date is: {today} (UTC).

Use this date when answering questions about months, dates, upcoming events, or past events.

IMPORTANT TOOL RULES:

1. Tools require specific parameters.
2. NEVER call a tool if required parameters are missing.
3. If the user's email is missing, ask the user for their email first.
4. If an event ID is missing, find the event ID from the context before calling the tool.
5. Users may mention an event name instead of the event ID. If so, find the corresponding event ID from the context.
6. Only call tools when you have ALL required parameters.

If relevant, use the given context to answer any question.
If you don't know the answer, say so.

Context:
{{context}}
"""


@app.cls(
    image=image.env({"HF_HUB_CACHE": CACHE_DIR}),
    secrets=secrets,
    gpu=GPU,
    timeout=1800,
    min_containers=MIN_CONTAINERS,
    volumes={
        CACHE_DIR: hf_cache_volume,
        VECTOR_DB_DIR: vector_volume
    },
)
class AudiaturAssistantService:
    @modal.enter()
    def setup(self):

        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            device_map="auto",
            load_in_4bit=True
        )

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7
        )


        config = json.loads(os.environ["firebase_secret"])
        cred = credentials.Certificate(config)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully!")
        self.db = firestore.client()
        self.event_registrations_collection = self.db.collection('event_registration')
        self.projectsCollection = self.db.collection('projects')


        self.llm = HuggingFacePipeline(pipeline=pipe)

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cuda"}  # or "cpu"
        )

        documents = self.load_documents()

        self.vectorstore = self.get_or_create_vectorstore(documents=documents,embeddings=embeddings, persist_directory=VECTOR_DB_DIR)
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )

    def get_or_create_vectorstore(self,documents=None,embeddings=None, persist_directory="/vector_db"):
        
        if os.path.exists(persist_directory) and os.listdir(persist_directory):
            print("Loading existing vector DB...")
            return Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings
            )

        if documents is None:
            raise ValueError("No documents provided to build vectorstore")

        print("Creating new vector DB...")
        db = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        db.persist()
        return db


    def load_documents(self):
        query = self.projectsCollection.where(filter=FieldFilter("projectType", "in", ["COMMUNITY", "CONFERENCE"]))     
        projects = query.get()
        self.project_map = {p.id: p for p in projects}
        documents = [Document(page_content=self.create_content(project), metadata={'source': project.id}) for project in projects]
        return documents

    def create_content(self,project):
        data = project.to_dict()
        if data.get('projectType') == 'CONFERENCE':
            return f"""
            Event: {data.get('name')}
            eventId: {project.id}
            Short Description: {data.get('shortDescription')}
            Description: {data.get('description')}
            Venue: {data.get('venue')}
            Start Date: { data.get("startDate").isoformat() if data.get("startDate") else "" }
            End Date: { data.get("endDate").isoformat() if data.get("endDate") else "" }
            Event Type: { data.get('projectType') }
            Status: { data.get('status') }
            organizer hierarchy: {" > ".join(self.get_project_hierarchy(project))}   
            """
        else :
            return f"""
            Community: {data.get('name')}
            Description: {data.get('description')}
            Short Description: {data.get('shortDescription')}
            Community hierarchy: {" > ".join(self.get_project_hierarchy(project))}   
            """

    def get_project_hierarchy(self,project):
        chain = []
        parent_id = project.to_dict().get("parentProjectId")
        if not parent_id:
            return []
        current_doc = self.project_map.get(parent_id)
        if not current_doc:
            return []
        current =  current_doc.to_dict()
        while current:
            chain.append(current.get("name"))
            parent_id = current.get("parentProjectId")
            if not parent_id:
                break
            current_doc = self.project_map.get(parent_id)
            if not current_doc:
                break
            current = current_doc.to_dict()

        return list(reversed(chain))
    
    @modal.method()
    def answer_question(self, question: str, history):
        query = "Represent this sentence for searching relevant passages: " + question
        docs = self.retriever.invoke(query)
        context = "\n\n".join(doc.page_content for doc in docs)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
        prompt = f"{system_prompt}\n\nUser: {question}\nAssistant:"
        response = self.llm.invoke(prompt)
        return response.content