# 🏥 RoboCare AI Assistant

> Born from a real problem at MyWoosah Inc—now solving caregiver matching through AI.

## 📋 The Story Behind This Project

While working on a caregiver matching platform for **MyWoosah Inc** in the US, I faced a real challenge: how do you efficiently match families with the right caregivers when everyone has different needs?

Families would ask things like:

- _"I need someone for my mom on Monday mornings who speaks Spanish"_
- _"Can you find elder care in Boston under $30/hour with CPR certification?"_

Writing individual SQL queries for every combination of filters was exhausting and error-prone. I knew there had to be a better way.

That's when I discovered the **Andela LLM Engineering program**. I saw an opportunity to transform this problem into a solution using AI. Instead of rigid queries, what if families could just... talk? And the AI would understand, search, and recommend?

This project is my answer. It's not just an exercise—it's solving a real problem I encountered in the field.

## What It Does

RoboCare helps families find caregivers through natural conversation:

- 🔍 Searches the database intelligently
- 🎯 Finds the best matches
- 💬 Explains pros/cons in plain English
- 🔊 Speaks the results back to you

## ✨ Features

### 🤖 AI-Powered Matching

- Natural language conversation interface
- Intelligent requirement gathering
- Multi-criteria search optimization
- Personalized recommendations with pros/cons analysis

### 🔍 Advanced Search Capabilities

- **Location-based filtering**: City, state, and country
- **Service type matching**: Elder care, child care, companionship, dementia care, hospice support, and more
- **Availability scheduling**: Day and time-based matching
- **Budget optimization**: Maximum hourly rate filtering
- **Language preferences**: Multi-language support
- **Certification requirements**: CPR, CNA, BLS, and specialized certifications
- **Experience filtering**: Minimum years of experience

### 🎙️ Multi-Modal Interface

- Text-based chat interface
- Voice response generation (Text-to-Speech)
- Multiple voice options (coral, alloy, echo, fable, onyx, nova, shimmer)
- Clean, modern UI built with Gradio

### 🛡️ Defensive Architecture

- Comprehensive error handling
- Token overflow protection
- Tool call validation
- Graceful degradation

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key
- Virtual environment (recommended)

### Installation

1. **Clone the repository**

   ```bash
   cd week2
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

4. **Set up environment variables**

   Create a `.env` file in the project root:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run the application**

   ```bash
   jupyter notebook "week2 EXERCISE.ipynb"
   ```

   Or run all cells sequentially in your Jupyter environment.

## 📊 Database Schema

### Tables

#### `caregivers`

Primary caregiver information including:

- Personal details (name, gender)
- Experience level
- Hourly rate and currency
- Location (city, state, country, coordinates)
- Live-in availability

#### `caregiver_services`

Care types offered by each caregiver:

- Elder care
- Child care
- Companionship
- Post-op support
- Special needs
- Respite care
- Dementia care
- Hospice support

#### `availability`

Time slots when caregivers are available:

- Day of week (Mon-Sun)
- Start and end times (24-hour format)

#### `languages`

Languages spoken by caregivers

#### `certifications`

Professional certifications (CPR, CNA, BLS, etc.)

#### `traits`

Personality and professional traits

## 🔧 Architecture

### Tool Registry Pattern

```python
TOOL_REGISTRY = {
    "search_caregivers": search_caregivers,
    "get_caregiver_profile": get_caregiver_profile,
    # ... more tools
}
```

All database functions are registered and can be called by the AI dynamically.

### Search Functions

#### `search_caregivers()`

Multi-filter search with parameters:

- `city`, `state_province`, `country` - Location filters
- `care_type` - Type of care needed
- `min_experience` - Minimum years of experience
- `max_hourly_rate` - Budget constraint
- `live_in` - Live-in caregiver requirement
- `language` - Language preference
- `certification` - Required certification
- `day` - Day of week availability
- `time_between` - Time window availability
- `limit`, `offset` - Pagination

#### `get_caregiver_profile(caregiver_id)`

Returns complete profile including:

- Basic information
- Services offered
- Languages spoken
- Certifications
- Personality traits
- Availability schedule

## 🎨 UI Components

### Main Interface

- **Chat History**: Message-based conversation display
- **Voice Response**: Auto-playing audio output
- **Settings Sidebar**:
  - AI Model selector
  - Voice selection
  - Audio toggle
  - Clear conversation button

### User Experience

- Professional gradient header
- Collapsible instructions
- Helpful placeholder text
- Custom CSS styling
- Responsive layout

## 📝 Usage Examples

### Example 1: Basic Search

```python
results = search_caregivers(
    city="New York",
    care_type="elder care",
    max_hourly_rate=30.0,
    limit=5
)
```

### Example 2: Language Filter

```python
results = search_caregivers(
    care_type="child care",
    language="Spanish",
    limit=3
)
```

### Example 3: Availability Search

```python
results = search_caregivers(
    day="Mon",
    time_between=("09:00", "17:00"),
    city="Boston"
)
```

### Example 4: Get Full Profile

```python
profile = get_caregiver_profile(caregiver_id=1)
print(profile['services'])
print(profile['availability'])
```

## 🔐 Security & Best Practices

### Current Implementation

- ✅ Environment variable management for API keys
- ✅ SQL injection prevention (parameterized queries)
- ✅ Error handling and graceful degradation
- ✅ Input validation through tool schemas

### Important Disclaimers

⚠️ **This is a demonstration application**

- Credentials and background checks are NOT verified
- Families should independently verify all caregiver information
- Not intended for production use without additional security measures

## 🛠️ Tech Stack

- **AI/ML**: OpenAI GPT-4o-mini, Text-to-Speech API
- **Database**: SQLite with normalized schema
- **UI Framework**: Gradio
- **Language**: Python 3.8+
- **Key Libraries**:
  - `openai` - OpenAI API client
  - `gradio` - Web interface
  - `python-dotenv` - Environment management
  - `sqlite3` - Database operations

## 📈 What's Next

### Immediate Plans

- [ ] Add speech input (families could call and talk)
- [ ] Connect to actual MyWoosah database
- [ ] Background check API integration
- [ ] Deploy for real users

### Future Enhancements

- [ ] Streaming responses for real-time interaction
- [ ] Dynamic model switching
- [ ] User authentication and profiles
- [ ] Review and rating system
- [ ] Payment integration
- [ ] Calendar integration for scheduling

## 💡 Key Learnings

Through building this project, I learned:

1. **Prompt engineering is critical** - Small keyword mismatches = zero results. Mapping "Monday" → "Mon" matters.
2. **Function calling is powerful** - Eliminated the need for custom queries. The AI figures it out.
3. **Defensive programming saves headaches** - Things break. This code expects it and handles it elegantly.
4. **AI makes databases accessible** - Good database design + AI = natural language interface

## 🌍 The Bigger Picture

This isn't just about caregiving. The same pattern works for:

- Healthcare appointment booking
- Legal service matching
- Tutoring and education platforms
- Real estate agent matching
- Any matching problem where natural language beats forms

**AI doesn't replace good database design—it makes it accessible to everyone.**

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

- **MyWoosah Inc** - For the real-world problem that inspired this solution
- **Andela LLM Engineering Program** - Educational framework and guidance
- **OpenAI** - GPT-4o and TTS API
- **Gradio** - Making beautiful UIs accessible

---

<div align="center">
  
**For MyWoosah Inc and beyond:** This is proof that AI can transform how we connect people with the care they need.

_Built with ❤️ during Week 2 of the Andela LLM Engineering Program_

**RoboOffice Ltd**

</div>
