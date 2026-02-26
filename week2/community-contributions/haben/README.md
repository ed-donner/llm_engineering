# ✈️ FlightAI Multimodal Assistant

> Transforming airline customer service through AI—where natural conversation meets intelligent booking.

## 📋 The Story Behind This Project

Customer service in the airline industry has always been a challenge. Travelers need quick answers, but traditional systems require navigating complex menus, waiting on hold, or filling out lengthy forms. What if customers could simply **talk** to an AI assistant that understands their needs, searches real-time flight data, and even shows them destinations visually?

That's exactly what **FlightAI Multimodal Assistant** does. Built during the **Andela LLM Engineering program**, this project demonstrates how AI can revolutionize customer interactions in the travel industry.

Instead of:
- ❌ Navigating complex booking systems
- ❌ Waiting for human agents
- ❌ Searching through multiple pages for flight information
- ❌ Reading long text responses

Customers can now:
- ✅ Ask questions naturally: *"What flights go to Paris?"*
- ✅ Book instantly: *"Book a flight to Tokyo for John Doe"*
- ✅ See destinations: *"Show me what London looks like"*
- ✅ Hear responses: *"Read me the flight information with audio"*

This isn't just a demo—it's a blueprint for the future of customer service in travel.

## What It Does

FlightAI helps travelers find and book flights through natural conversation:

- 🔍 **Intelligent Search** - Queries real-time PostgreSQL database for available flights
- 💳 **Instant Booking** - Books flights directly through the conversation
- 🖼️ **Visual Inspiration** - Generates beautiful destination images using DALL-E
- 🔊 **Audio Responses** - Converts flight information to speech for hands-free access
- 💬 **Natural Language** - Understands context and intent without rigid commands

## ✨ Features

### 🤖 AI-Powered Flight Management

- Natural language conversation interface
- Intelligent flight search and booking
- Real-time database integration with PostgreSQL
- Multi-criteria search (destination, price, time)
- Contextual understanding of user requests

### 🎨 Multimodal Capabilities

- **Text Responses**: Clear, concise flight information
- **Image Generation**: Beautiful destination visuals using DALL-E
- **Audio Narration**: Text-to-speech for hands-free access
- **Smart Tool Calling**: Automatically uses the right tools based on user intent

### 🔍 Advanced Search Features

- **Destination-based filtering**: Search by city name
- **Price information**: Real-time pricing from database
- **Flight details**: Departure/arrival times, flight numbers
- **Booking management**: Direct booking with confirmation

### 🛡️ Production-Ready Architecture

- Comprehensive error handling
- Database connection pooling
- Tool call validation
- Graceful degradation
- Environment-based configuration

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL database (running locally or remotely)
- OpenRouter API key (for GPT models)
- OpenAI API key (optional, for direct TTS/Image generation)

### Installation

1. **Navigate to the project directory**

   ```bash
   cd week2/community-contributions/haben
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**

   Run the database setup script to create tables and insert demo data:

   ```bash
   python setup_database.py
   ```

5. **Configure environment variables**

   Create a `.env` file in the project directory:

   ```env
   # OpenRouter (for GPT models)
   OPENROUTER_API_KEY=sk-or-your-key-here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   OPENROUTER_MODEL=openai/gpt-4o-mini

   # OpenAI (optional, for direct TTS/Image generation access)
   OPENAI_API_KEY=sk-your-openai-key-here

   # PostgreSQL Database
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=andela_ai_engineering_bootcamp
   DB_USER=postgres
   DB_PASSWORD=your-password-here
   ```

6. **Launch the application**

   ```bash
   jupyter notebook w2d5-multimodal-airline-assistant.ipynb
   ```

   Or run all cells sequentially in your Jupyter environment.

## 📊 Database Schema

### Tables

#### `flights`

Primary flight information including:

- Flight number and airline
- Origin and destination cities
- Departure and arrival times
- Pricing information
- Timestamps for tracking

#### `bookings`

Customer booking records:

- Flight references
- Passenger information
- Booking status
- Timestamps

#### `passengers`

Passenger profiles:

- Personal information
- Loyalty points
- Preferences (JSONB)

#### `airports`

Airport reference data:

- Airport codes (IATA)
- Location information
- Timezone data

#### `contributions`

Project contribution tracking:

- Contributor information
- Project details
- Contribution dates

## 🔧 Architecture

### Tool-Based Function Calling

```python
tools = [
    price_tool,      # Flight price lookup
    booking_tool,    # Flight booking
    image_tool,      # Destination image generation
    audio_tool       # Text-to-speech conversion
]
```

All functions are registered as tools that the AI can call dynamically based on user requests.

### Core Functions

#### `get_ticket_price(destination_city)`

Searches the database for available flights to a destination:

- Queries `flights` table
- Returns up to 5 matching flights
- Includes flight numbers, prices, and schedules
- Handles case-insensitive city matching

#### `book_flight(destination_city, passenger_name)`

Creates a booking record:

- Finds available flight
- Inserts booking into `bookings` table
- Returns confirmation with booking ID
- Handles transaction rollback on errors

#### `generate_destination_image(destination_city, description)`

Generates travel destination images:

- Uses DALL-E via OpenAI API
- Creates professional travel brochure-style images
- Returns image URLs for display

#### `generate_audio_response(text)`

Converts text to speech:

- Uses OpenAI TTS API
- Supports multiple voice options
- Saves audio files for playback
- Falls back gracefully if API unavailable

## 🎨 UI Components

### Main Interface

- **Chat History**: Message-based conversation display
- **Multimodal Responses**: Text, images, and audio in one interface
- **Clean Design**: Modern Gradio interface with professional styling
- **Real-time Interaction**: Instant responses with tool calling

### User Experience

- Natural language input
- Automatic tool selection
- Visual destination previews
- Audio narration option
- Clear error messages

## 📝 Usage Examples

### Example 1: Flight Search

```
User: "What flights are available to Paris?"
Assistant: [Searches database, returns flight list]
```

### Example 2: Booking

```
User: "Book a flight to Tokyo for Sarah Johnson"
Assistant: [Books flight, returns confirmation with booking ID]
```

### Example 3: Visual Request

```
User: "Show me what London looks like"
Assistant: [Generates destination image, displays in chat]
```

### Example 4: Audio Request

```
User: "Read me the flight information for Paris with audio"
Assistant: [Provides flight info + generates audio file]
```

## 🔐 Security & Best Practices

### Current Implementation

- ✅ Environment variable management for API keys
- ✅ SQL injection prevention (parameterized queries)
- ✅ Error handling and graceful degradation
- ✅ Input validation through tool schemas
- ✅ Database connection management

### Important Disclaimers

⚠️ **This is a demonstration application**

- Flight bookings are simulated for educational purposes
- Real-world implementation would require payment processing
- Additional security measures needed for production use
- Database should be properly secured in production

## 🛠️ Tech Stack

- **AI/ML**: OpenAI GPT-4o-mini (via OpenRouter), DALL-E, TTS API
- **Database**: PostgreSQL with normalized schema
- **UI Framework**: Gradio
- **Language**: Python 3.8+
- **Key Libraries**:
  - `openai` - OpenAI API client
  - `gradio` - Web interface
  - `python-dotenv` - Environment management
  - `psycopg2-binary` - PostgreSQL adapter

## 📈 What's Next

### Immediate Plans

- [ ] Add flight cancellation functionality
- [ ] Implement seat selection
- [ ] Add payment processing integration
- [ ] Connect to real airline APIs
- [ ] Add user authentication

### Future Enhancements

- [ ] Streaming responses for real-time interaction
- [ ] Multi-language support
- [ ] Voice input (speech-to-text)
- [ ] Calendar integration for trip planning
- [ ] Loyalty program integration
- [ ] Mobile app version

## 💡 Key Learnings

Through building this project, I learned:

1. **Multimodal AI is powerful** - Combining text, images, and audio creates richer user experiences
2. **Tool calling eliminates complexity** - The AI figures out which tools to use, reducing code complexity
3. **Database integration is seamless** - PostgreSQL + AI = natural language database interface
4. **Error handling is critical** - Graceful degradation keeps the experience smooth even when APIs fail
5. **User intent matters** - Understanding context makes interactions feel natural

## 🌍 The Bigger Picture

This pattern extends beyond airlines. The same approach works for:

- Hotel booking systems
- Restaurant reservations
- Event ticketing platforms
- Service appointment scheduling
- E-commerce product search
- Any domain where natural language beats forms

**AI doesn't replace good database design—it makes it accessible through conversation.**

---

## 🤝 Contributing

This project was created as part of the **Andela LLM Engineering Week 2 Exercise**.

Feedback and contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run all cells to test
5. Submit a pull request

## 🙏 Acknowledgments

- **Andela LLM Engineering Program** - Educational framework and guidance
- **OpenAI** - GPT-4o, DALL-E, and TTS APIs
- **OpenRouter** - API gateway for model access
- **Gradio** - Making beautiful UIs accessible
- **PostgreSQL** - Robust database foundation

---

<div align="center">

**For the future of travel:** This is proof that AI can transform how customers interact with airline services.

_Built with ❤️ during Week 2 of the Andela LLM Engineering Program_

**FlightAI Assistant**

</div>
