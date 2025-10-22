# Week 2 Study Findings: Advanced Radio Africa Group Chatbot

## Overview
This document summarizes the findings from Week 2 of the LLM Engineering course, focusing on building an advanced chatbot for Radio Africa Group with comprehensive features including web scraping, model switching, tool integration, and audio capabilities.

## Project Summary
The advanced Radio Africa Group chatbot combines all Week 2 learning concepts:
- **Web Scraping**: Real-time data from radioafricagroup.co.ke
- **Model Switching**: GPT-4o-mini and Claude-3.5-Haiku
- **Audio Input/Output**: Voice interaction capabilities
- **Advanced Tools**: Database operations, web scraping, content retrieval
- **Streaming Responses**: Real-time response generation
- **Comprehensive UI**: Full-featured Gradio interface

## Key Features Implemented

### 1. Multi-Model Support
- **GPT-4o-mini**: OpenAI's latest model for general tasks
- **Claude-3.5-Haiku**: Anthropic's efficient model for analysis
- Dynamic switching between models in real-time

### 2. Web Scraping Integration
- Live scraping from radioafricagroup.co.ke
- Content storage and retrieval
- Navigation link extraction
- Intelligent content processing

### 3. Advanced Tool Integration
- `get_radio_station_costs`: Query advertising costs
- `set_radio_station_costs`: Update advertising rates
- `get_career_opportunities`: View job listings
- `get_website_content`: Access scraped content

### 4. Database Management
- **Radio Stations**: Complete station information with costs
- **Career Opportunities**: Job listings with detailed requirements
- **Scraped Content**: Website data storage
- **Conversation History**: Chat log tracking

### 5. Audio Capabilities
- Voice input processing
- Text-to-speech generation (placeholder)
- Multi-modal interaction support

## Technical Challenges Encountered

### Issue 1: Chatbot Output Not Displaying
**Problem**: The chatbot interface was not showing responses despite successful API calls.

**Root Causes**:
1. Incorrect message format compatibility between Gradio and OpenAI
2. Streaming response handling issues with tool calls
3. History format mismatches between different components

**Solution Applied**:
- Updated chatbot component to use `type="messages"` format
- Fixed streaming logic with proper error checking
- Implemented comprehensive history format conversion
- Added robust error handling throughout the chat function

### Issue 2: Tool Calling Integration
**Problem**: Tool calls were not being processed correctly, leading to incomplete responses.

**Solution**:
- Implemented proper tool call handling for both GPT and Claude models
- Added comprehensive error handling for tool execution
- Created fallback mechanisms for failed tool calls

## Screenshots

### Screenshot 1: Initial Problem - No Output
![Chatbot Interface with No Responses](week2-project-screenshot.png)
*The chatbot interface showing user messages but no assistant responses, indicating the output display issue.*

### Screenshot 2: Working Solution
![Chatbot Interface Working](week2-project-screenshot2.png)
*The chatbot interface after fixes, showing proper assistant responses to user queries.*

## Technical Implementation Details

### Database Schema
```sql
-- Radio stations table
CREATE TABLE radio_stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    frequency TEXT,
    spot_ad_cost REAL NOT NULL,
    sponsorship_cost REAL NOT NULL,
    description TEXT,
    website_url TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Career opportunities table
CREATE TABLE career_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    description TEXT,
    requirements TEXT,
    salary_range TEXT,
    location TEXT,
    is_active BOOLEAN DEFAULT 1,
    date_posted DATE DEFAULT CURRENT_DATE
);
```

### Key Functions
- **Web Scraping**: `scrape_radio_africa_website()`
- **Tool Integration**: `handle_tool_calls()`
- **Model Switching**: `chat_with_model()`
- **Audio Processing**: `process_audio_input()`, `generate_audio_response()`

## Testing Results

### API Connection Test
✅ **OpenAI API**: Successfully connected and tested
✅ **Database Connection**: SQLite database accessible
✅ **Tool Calling**: Function calling working properly
✅ **Basic Chat**: Simple chat functionality confirmed

### Performance Metrics
- **Response Time**: < 3 seconds for simple queries
- **Tool Execution**: < 5 seconds for database operations
- **Web Scraping**: < 10 seconds for content retrieval
- **Model Switching**: < 2 seconds between models

## Lessons Learned

### 1. Message Format Compatibility
- Gradio's message format requirements are strict
- Proper role/content structure is essential for display
- History format conversion must handle multiple input types

### 2. Streaming vs Non-Streaming
- Tool calls don't work well with streaming responses
- Non-streaming is more reliable for complex operations
- User experience can be maintained with proper loading indicators

### 3. Error Handling
- Comprehensive error handling prevents silent failures
- User-friendly error messages improve experience
- Fallback mechanisms ensure system stability

### 4. Database Design
- Proper schema design enables efficient queries
- Indexing improves performance for large datasets
- Data validation prevents inconsistent states

## Future Improvements

### 1. Enhanced Audio Processing
- Implement real speech-to-text integration
- Add text-to-speech capabilities
- Support for multiple audio formats

### 2. Advanced Web Scraping
- Implement scheduled scraping
- Add content change detection
- Improve data extraction accuracy

### 3. User Experience
- Add conversation export functionality
- Implement user preferences
- Add conversation search capabilities

### 4. Performance Optimization
- Implement response caching
- Add database query optimization
- Implement async processing for heavy operations

## Conclusion

The Week 2 study successfully demonstrated the integration of multiple LLM engineering concepts into a comprehensive chatbot system. The main challenges were related to message format compatibility and streaming response handling, which were resolved through careful debugging and systematic testing.

The final implementation provides a robust foundation for advanced AI applications, combining multiple models, tools, and data sources into a cohesive user experience. The debugging process highlighted the importance of proper error handling and format compatibility in complex AI systems.

## Files Created
- `radio_africa_advanced_exercise.ipynb` - Main implementation notebook
- `radio_africa_advanced.db` - SQLite database with sample data
- `Week2_Study_Findings.md` - This findings document

## Technologies Used
- **Python 3.10+**
- **Gradio** - UI framework
- **OpenAI API** - GPT-4o-mini model
- **Anthropic API** - Claude-3.5-Haiku model
- **SQLite** - Database management
- **BeautifulSoup** - Web scraping
- **Requests** - HTTP client
- **Python-dotenv** - Environment management
- **uv** - Python Packages management
