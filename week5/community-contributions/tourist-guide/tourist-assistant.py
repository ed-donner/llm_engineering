import os
import glob
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI


# Initialization

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")

# Get Google Places API Key - used for location search
google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
if google_api_key:
    print(f"Google Places API Key exists and begins {google_api_key[:8]}")
else:
    print("Google Places API Key not set. Location search will be disabled.")

MODEL = "gpt-4o-mini"
openai = OpenAI()

# Functions for RAG implementation
def read_pdf(file_path):
    """Read a PDF file and extract text content."""
    pdf_reader = PdfReader(file_path)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

def load_knowledge_base():
    """Load all PDFs from the knowledge-base directory and create a vector store."""
    # Create the knowledge-base directory if it doesn't exist
    os.makedirs("knowledge-base", exist_ok=True)
    
    # Get all PDF files in the knowledge-base directory
    pdf_files = glob.glob("knowledge-base/*.pdf")
    
    if not pdf_files:
        print("No PDF files found in the knowledge-base directory.")
        return None
    
    # Read and concatenate all PDF content
    all_content = ""
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file}")
        content = read_pdf(pdf_file)
        all_content += content + "\n\n"
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(all_content)
    
    # Create vector store
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(chunks, embeddings)
    
    print(f"Created vector store with {len(chunks)} chunks from {len(pdf_files)} PDF files")
    return vector_store

# Initialize vector store
vector_store = load_knowledge_base()
if vector_store:
    # Create retrieval chain
    llm = ChatOpenAI(model=MODEL)
    retrieval_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=False
    )
    print("RAG system initialized successfully")
else:
    print("RAG system not initialized. Please add PDF files to the knowledge-base directory.")
    retrieval_chain = None



#audio generation
    
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
def talker(message):
        response=openai.audio.speech.create(
            
            model="tts-1",
            voice="onyx",
            input=message
        )
        audio_stream=BytesIO(response.content)
        audio=AudioSegment.from_file(audio_stream, format="mp3")
        play(audio)

def search_attractions(location):
    """Search for tourist attractions in a specified location using Google Places API."""
    if not google_api_key:
        return {"error": "Google Places API Key not set. Location search disabled."}
    
    try:
        # First get the place_id for the location
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={google_api_key}"
        geocode_response = requests.get(geocode_url)
        geocode_data = geocode_response.json()
        
        if geocode_data["status"] != "OK" or len(geocode_data["results"]) == 0:
            return {"error": f"Location not found: {location}"}
        
        # Get coordinates
        location_data = geocode_data["results"][0]
        lat = location_data["geometry"]["location"]["lat"]
        lng = location_data["geometry"]["location"]["lng"]
        
        # Search for attractions
        places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": 5000,  # 5km radius
            "type": "tourist_attraction",
            "key": google_api_key
        }
        
        places_response = requests.get(places_url, params=params)
        places_data = places_response.json()
        
        # Format the results
        attractions = []
        if places_data["status"] == "OK" and "results" in places_data:
            for place in places_data["results"][:10]:  # Limit to top 10 results
                attractions.append({
                    "name": place["name"],
                    "rating": place.get("rating", "Not rated"),
                    "vicinity": place.get("vicinity", "No address available"),
                    "types": place.get("types", [])
                })
                
        return {
            "location": location_data["formatted_address"],
            "coordinates": {"lat": lat, "lng": lng},
            "attractions": attractions
        }
        
    except Exception as e:
        return {"error": f"Error searching for attractions: {str(e)}"}
        
def get_attraction_details(location, attraction_name):
    """Get more detailed information about a specific attraction."""
    if not google_api_key:
        return {"error": "Google Places API Key not set. Location search disabled."}
    
    try:
        # Search for the specific place
        place_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {
            "input": f"{attraction_name} in {location}",
            "inputtype": "textquery",
            "fields": "place_id,name,formatted_address,rating,user_ratings_total,types,opening_hours,photos",
            "key": google_api_key
        }
        
        place_response = requests.get(place_url, params=params)
        place_data = place_response.json()
        
        if place_data["status"] != "OK" or len(place_data["candidates"]) == 0:
            return {"error": f"Attraction not found: {attraction_name} in {location}"}
        
        place_id = place_data["candidates"][0]["place_id"]
        
        # Get detailed place information
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            "place_id": place_id,
            "fields": "name,formatted_address,rating,reviews,opening_hours,website,price_level,formatted_phone_number,photos",
            "key": google_api_key
        }
        
        details_response = requests.get(details_url, params=details_params)
        details_data = details_response.json()
        
        if details_data["status"] != "OK":
            return {"error": f"Could not get details for: {attraction_name}"}
        
        return details_data["result"]
        
    except Exception as e:
        return {"error": f"Error getting attraction details: {str(e)}"}

system_message = "You are a helpful assistant for tourists visiting a city."
system_message += "Help the user and give him or her good explanation about the cities or places."
system_message += "Talk about history, geography and current conditions."
system_message += "Start with a short explanation about three lines and when the user wants explain more."
system_message += "Use the retrieved information from knowledge base when available to give detailed and accurate information."
system_message += "When the user asks about attractions in a specific location, use the provided attractions data to give recommendations."

#gradio handles the history of user messages and the assistant responses

def extract_location(message):
    """Extract location information from a message using OpenAI."""
    try:
        prompt = [
            {"role": "system", "content": "Extract the location mentioned in the user's query. If no location is explicitly mentioned, return 'None'. Return only the location name without any explanation."},
            {"role": "user", "content": message}
        ]
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Using a smaller model for simple location extraction
            messages=prompt,
            temperature=0.1,
            max_tokens=50
        )
        
        location = response.choices[0].message.content.strip()
        return None if location.lower() in ['none', 'no location mentioned', 'no location', 'not specified'] else location
        
    except Exception as e:
        print(f"Error extracting location: {str(e)}")
        return None

def chat(history):
    # Extract just the content from the message history for RAG
    chat_history = []
    messages = [{"role": "system", "content": system_message}]
    
    for i in range(0, len(history), 2):
        if i+1 < len(history):
            user_msg = history[i]["content"]
            ai_msg = history[i+1]["content"] if i+1 < len(history) else ""
            chat_history.append((user_msg, ai_msg))
            messages.append({"role": "user", "content": user_msg})
            if ai_msg:
                messages.append({"role": "assistant", "content": ai_msg})
    
    # Get the latest user message
    latest_user_message = history[-1]["content"] if history and history[-1]["role"] == "user" else ""
    
    # First check if we have a preset current_location
    location = None
    if current_location and "attractions" in latest_user_message.lower():
        # User is asking about attractions and we have a set location
        location = current_location
        print(f"Using preset location: {location}")
    else:
        # Try to extract location from the message
        extracted_location = extract_location(latest_user_message)
        if extracted_location:
            location = extracted_location
            print(f"Extracted location from message: {location}")
    
    # If we have a location and the API key, search for attractions
    if location and google_api_key:
        # This is likely a location-based query about attractions
        print(f"Searching for attractions in: {location}")
        
        # Get attraction data
        attractions_data = search_attractions(location)
        
        # If there's an error or no attractions found
        if "error" in attractions_data or (
            "attractions" in attractions_data and len(attractions_data["attractions"]) == 0
        ):
            error_msg = attractions_data.get("error", f"No attractions found in {location}")
            print(f"Location search error: {error_msg}")
            
            # Continue with regular processing but include the error info
            updated_msg = f"I tried to find attractions in {location}, but {error_msg.lower()}. Let me provide general information instead.\n\n{latest_user_message}"
            messages.append({"role": "system", "content": updated_msg})
        else:
            # Add the attraction information to the context
            attraction_context = f"Information about {location}: {attractions_data['location']}\n\nTop attractions:"
            for i, attraction in enumerate(attractions_data["attractions"], 1):
                attraction_context += f"\n{i}. {attraction['name']} - Rating: {attraction['rating']} - {attraction['vicinity']}"
            
            # Suggest specific attraction details if the user mentioned one
            if "attractions" in attractions_data and attractions_data["attractions"]:
                for attraction in attractions_data["attractions"]:
                    attraction_name = attraction["name"].lower()
                    if attraction_name in latest_user_message.lower():
                        print(f"Getting details for specific attraction: {attraction['name']}")
                        attraction_details = get_attraction_details(location, attraction["name"])
                        if "error" not in attraction_details:
                            details_str = f"\n\nDetails for {attraction['name']}:\n"
                            details_str += f"Address: {attraction_details.get('formatted_address', 'Not available')}\n"
                            details_str += f"Rating: {attraction_details.get('rating', 'Not rated')} ({attraction_details.get('user_ratings_total', 0)} reviews)\n"
                            
                            if "reviews" in attraction_details and attraction_details["reviews"]:
                                details_str += f"Sample review: \"{attraction_details['reviews'][0]['text']}\"\n"
                                
                            if "opening_hours" in attraction_details and "weekday_text" in attraction_details["opening_hours"]:
                                details_str += "Opening hours:\n"
                                for hours in attraction_details["opening_hours"]["weekday_text"]:
                                    details_str += f"- {hours}\n"
                                    
                            if "website" in attraction_details:
                                details_str += f"Website: {attraction_details['website']}\n"
                                
                            attraction_context += details_str
            
            # Add this context to the messages
            messages.append({"role": "system", "content": f"Use this location information in your response: {attraction_context}"})
    
    # If there's a current location set, add it to the context even if not asking for attractions
    elif current_location and google_api_key and not location:
        # Add a note about the current location setting
        messages.append({
            "role": "system", 
            "content": f"The user has set their current location to {current_location}. " +
                      "Consider this when responding, especially for questions about 'here', 'local', or nearby attractions."
        })
    
    # Use RAG if available, otherwise use the standard OpenAI API
    if retrieval_chain and latest_user_message:
        try:
            rag_response = retrieval_chain.invoke({
                "question": latest_user_message,
                "chat_history": chat_history[:-1] if chat_history else []
            })
            reply = rag_response["answer"]
            print(reply)
        except Exception as e:
            print(f"Error using RAG: {str(e)}")
            # Fallback to standard API
            response = openai.chat.completions.create(model=MODEL, messages=messages)
            reply = response.choices[0].message.content
    else:
        # Standard OpenAI API
        response = openai.chat.completions.create(model=MODEL, messages=messages)
        reply = response.choices[0].message.content
    
    history += [{"role":"assistant", "content":reply}]
    talker(reply)
    
    return history

def transcribe_audio(audio_path):
   
    try:
        # Check if audio_path is valid
        if audio_path is None:
            return "No audio detected. Please record again."
        
        # Open the audio file
        with open(audio_path, "rb") as audio_file:
             transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        return transcript.text
    
    except Exception as e:
        return f"Error during transcription: {str(e)}"




##################Interface with Gradio##############################

theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="indigo",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Poppins"), "ui-sans-serif", "system-ui", "sans-serif"]
)

# Load CSS from external file
with open('style.css', 'r') as f:
    css = f.read()

# Store the current location globally to use in queries
current_location = None

def refresh_knowledge_base():
    """Reload the knowledge base and update the retrieval chain."""
    global vector_store, retrieval_chain
    
    vector_store = load_knowledge_base()
    if vector_store:
        # Create retrieval chain
        llm = ChatOpenAI(model=MODEL)
        retrieval_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=False
        )
        return "Knowledge base refreshed successfully!"
    else:
        return "No PDF files found in the knowledge-base directory."
        
def set_location(location):
    """Set the current location for the assistant."""
    global current_location
    
    if not location or location.strip() == "":
        return "Please enter a valid location."
    
    # Verify the location exists using the Google Maps API
    if google_api_key:
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={google_api_key}"
        try:
            geocode_response = requests.get(geocode_url)
            geocode_data = geocode_response.json()
            
            if geocode_data["status"] != "OK" or len(geocode_data["results"]) == 0:
                return f"Location not found: {location}. Please enter a valid location."
                
            # Get the formatted location name
            current_location = geocode_data["results"][0]["formatted_address"]
            
            # Get preliminary attraction data for the location
            attractions_data = search_attractions(current_location)
            if "error" not in attractions_data and "attractions" in attractions_data:
                num_attractions = len(attractions_data["attractions"])
                return f"Location set to: {current_location}. Found {num_attractions} nearby attractions."
            else:
                return f"Location set to: {current_location}. No attractions data available."
                
        except Exception as e:
            current_location = location  # Fall back to user input
            return f"Location set to: {location}. Error verifying location: {str(e)}"
    else:
        current_location = location  # No API key, just use the user input
        return f"Location set to: {location}. (Google API not configured for verification)"

with gr.Blocks(theme=theme, css=css) as ui:
    with gr.Column(elem_classes="container"):
        gr.Markdown("# 🌍 Tourist Assistant", elem_classes="title")
        gr.Markdown("Ask about any city, landmark, or destination around the world", elem_classes="subtitle")
        
        with gr.Blocks() as demo:
            gr.Image("travel.jpg", show_label=False, height=150, container=False, interactive=False)
 
        
        with gr.Column(elem_classes="chatbot-container"):
            chatbot = gr.Chatbot(
                height=400, 
                type="messages",
                bubble_full_width=False,
                show_copy_button=True,
                elem_id="chatbox"
            )

        with gr.Row(elem_classes="mic-container"):
            audio_input = gr.Audio(
                type="filepath",
                label="🎤 Hold the record button and ask your question",
                sources=["microphone"],
                streaming=False,
                interactive=True,
                autoplay=False,
                show_download_button=False,
                show_share_button=False,
                elem_id="mic-button"
            )
        with gr.Row():
            entry = gr.Textbox(
                label="",
                placeholder="Or type your question here or use the microphone below...",
                container=False,
                lines=2,
                scale=10
            )
                 
        with gr.Row():
            with gr.Column(scale=3):
                location_input = gr.Textbox(
                    label="Set Current Location",
                    placeholder="e.g., Paris, France or London, UK",
                    interactive=True
                )
            with gr.Column(scale=1):
                location_btn = gr.Button("Set Location", variant="primary", size="sm")
            with gr.Column(scale=1):
                attractions_btn = gr.Button("Nearby Attractions", variant="secondary", size="sm")
        
        with gr.Row():
            with gr.Column(scale=1):
                refresh_btn = gr.Button("🔄 Refresh Knowledge Base", variant="primary", size="sm")
                refresh_status = gr.Textbox(label="Status", interactive=False)
        
          
        with gr.Column(scale=1, elem_classes="clear-button"):
                clear = gr.Button("Clear", variant="secondary", size="sm")
            
    def transcribe_and_submit(audio_path):
        transcription = transcribe_audio(audio_path)
        history = chatbot.value if chatbot.value else []
        history += [{"role":"user", "content":transcription}]
        return transcription, history, history, None
        
    audio_input.stop_recording(
        fn=transcribe_and_submit,
        inputs=[audio_input],
        outputs=[entry, chatbot, chatbot, audio_input]
    ).then(
        chat, inputs=chatbot, outputs=[chatbot]
    )

    def do_entry(message, history):
        history += [{"role":"user", "content":message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot]
    )
    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)
    refresh_btn.click(refresh_knowledge_base, inputs=None, outputs=refresh_status)
    
    # Add location status to show the result
    location_status = gr.Textbox(label="Location Status", interactive=False)
    
    # Connect the location button to set the location
    location_btn.click(
        set_location, 
        inputs=location_input, 
        outputs=location_status
    )
    
    # Add a separate function to clear the input field
    def clear_location_input():
        return ""
        
    location_btn.click(
        clear_location_input,
        inputs=None,
        outputs=location_input
    )
    
    # Add a function to handle asking about nearby attractions
    def ask_about_attractions(history):
        global current_location
        if not current_location:
            history += [{"role":"user", "content":"Tell me about attractions near me"}]
            history += [{"role":"assistant", "content":"You haven't set a location yet. Please use the 'Set Current Location' field above to set your location first."}]
            return history
        
        history += [{"role":"user", "content":f"What are some attractions to visit in {current_location}?"}]
        return chat(history)
    
    # Connect the attractions button to ask about attractions
    attractions_btn.click(ask_about_attractions, inputs=chatbot, outputs=chatbot)

ui.launch(inbrowser=True)