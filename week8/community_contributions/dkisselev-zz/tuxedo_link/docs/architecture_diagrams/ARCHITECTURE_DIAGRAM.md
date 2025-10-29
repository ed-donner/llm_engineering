# 🏗️ Tuxedo Link - Architecture Diagrams

**Date**: October 27, 2024  
**Tool**: [Eraser.io](https://www.eraser.io/)

---

## System Architecture

This diagram can be rendered on [Eraser.io](https://www.eraser.io/) or any compatible Mermaid format diagraming tool

### High-Level Architecture

```eraser
// Tuxedo Link - High-Level System Architecture

// External APIs
openai [icon: openai, color: green]
petfinder [icon: api, color: blue]
rescuegroups [icon: api, color: blue]
sendgrid [icon: email, color: red]

// Frontend Layer
gradio [icon: browser, color: purple] {
  search_tab
  alerts_tab
  about_tab
}

// Application Layer
framework [icon: server, color: orange] {
  TuxedoLinkFramework
}

// Agent Layer
agents [icon: users, color: cyan] {
  PlanningAgent
  ProfileAgent
  PetfinderAgent
  RescueGroupsAgent
  DeduplicationAgent
  MatchingAgent
  EmailAgent
}

// Data Layer
databases [icon: database, color: gray] {
  SQLite
  ChromaDB
}

// Deployment
modal [icon: cloud, color: blue] {
  scheduled_jobs
  volume_storage
}

// Connections
gradio > framework: User requests
framework > agents: Orchestrate
agents > openai: Profile extraction
agents > petfinder: Search cats
agents > rescuegroups: Search cats
agents > sendgrid: Send notifications
agents > databases: Store/retrieve
framework > databases: Manage data
modal > framework: Scheduled searches
modal > databases: Persistent storage
```

---

## Detailed Component Architecture

```eraser
// Tuxedo Link - Detailed Component Architecture

// Users
user [icon: user, color: purple]

// Frontend - Gradio UI
ui_layer [color: #E8F5E9] {
  gradio_app [label: "Gradio Application"]
  search_interface [label: "Search Tab"]
  alerts_interface [label: "Alerts Tab"]
  about_interface [label: "About Tab"]
  
  gradio_app > search_interface
  gradio_app > alerts_interface
  gradio_app > about_interface
}

// Framework Layer
framework_layer [color: #FFF3E0] {
  tuxedo_framework [label: "TuxedoLinkFramework", icon: server]
  user_manager [label: "UserManager", icon: user]
  
  tuxedo_framework > user_manager
}

// Orchestration Layer
orchestration [color: #E3F2FD] {
  planning_agent [label: "PlanningAgent\n(Orchestrator)", icon: brain]
}

// Processing Agents
processing_agents [color: #F3E5F5] {
  profile_agent [label: "ProfileAgent\n(GPT-4)", icon: chat]
  matching_agent [label: "MatchingAgent\n(Hybrid Search)", icon: search]
  dedup_agent [label: "DeduplicationAgent\n(Fingerprint+CLIP)", icon: filter]
}

// External Integration Agents
external_agents [color: #E0F2F1] {
  petfinder_agent [label: "PetfinderAgent\n(OAuth)", icon: api]
  rescuegroups_agent [label: "RescueGroupsAgent\n(API Key)", icon: api]
  email_agent [label: "EmailAgent\n(SendGrid)", icon: email]
}

// Data Storage
storage_layer [color: #ECEFF1] {
  sqlite_db [label: "SQLite Database", icon: database]
  vector_db [label: "ChromaDB\n(Vector Store)", icon: database]
  
  db_tables [label: "Tables"] {
    users_table [label: "users"]
    alerts_table [label: "alerts"]
    cats_cache_table [label: "cats_cache"]
  }
  
  vector_collections [label: "Collections"] {
    cats_collection [label: "cats_embeddings"]
  }
  
  sqlite_db > db_tables
  vector_db > vector_collections
}

// External Services
external_services [color: #FFEBEE] {
  openai_api [label: "OpenAI API\n(GPT-4)", icon: openai]
  petfinder_api [label: "Petfinder API\n(OAuth 2.0)", icon: api]
  rescuegroups_api [label: "RescueGroups API\n(API Key)", icon: api]
  sendgrid_api [label: "SendGrid API\n(Email)", icon: email]
}

// Deployment Layer
deployment [color: #E8EAF6] {
  modal_service [label: "Modal (Serverless)", icon: cloud]
  
  modal_functions [label: "Functions"] {
    daily_job [label: "daily_search_job"]
    weekly_job [label: "weekly_search_job"]
    cleanup_job [label: "cleanup_job"]
  }
  
  modal_storage [label: "Storage"] {
    volume [label: "Modal Volume\n(/data)"]
  }
  
  modal_service > modal_functions
  modal_service > modal_storage
}

// User Flows
user > ui_layer: Interact
ui_layer > framework_layer: API calls
framework_layer > orchestration: Search request

// Orchestration Flow
orchestration > processing_agents: Extract profile
orchestration > external_agents: Fetch cats
orchestration > processing_agents: Deduplicate
orchestration > processing_agents: Match & rank
orchestration > storage_layer: Cache results

// Agent to External Services
processing_agents > external_services: Profile extraction
external_agents > external_services: API requests
external_agents > external_services: Send emails

// Agent to Storage
processing_agents > storage_layer: Store/retrieve
external_agents > storage_layer: Cache & embeddings
orchestration > storage_layer: Query & update

// Modal Integration
deployment > framework_layer: Scheduled tasks
deployment > storage_layer: Persistent data
```

---

## Data Flow Diagram

```eraser
// Tuxedo Link - Search Data Flow

user [icon: user]

// Step 1: User Input
user_input [label: "1. User Input\n'friendly playful cat\nin NYC'"]

// Step 2: Profile Extraction
profile_extraction [label: "2. Profile Agent\n(OpenAI GPT-4)", icon: chat, color: purple]
extracted_profile [label: "CatProfile\n- location: NYC\n- age: young\n- personality: friendly"]

// Step 3: API Fetching (Parallel)
api_fetch [label: "3. Fetch from APIs\n(Parallel)", icon: api, color: blue]
petfinder_results [label: "Petfinder\n50 cats"]
rescuegroups_results [label: "RescueGroups\n50 cats"]

// Step 4: Deduplication
dedup [label: "4. Deduplication\n(3-tier)", icon: filter, color: orange]
dedup_details [label: "- Fingerprint\n- Text similarity\n- Image similarity"]

// Step 5: Cache & Embed
cache [label: "5. Cache & Embed", icon: database, color: gray]
sqlite_cache [label: "SQLite\n(Cat data)"]
vector_store [label: "ChromaDB\n(Embeddings)"]

// Step 6: Hybrid Matching
matching [label: "6. Hybrid Search\n60% vector\n40% metadata", icon: search, color: green]

// Step 7: Results
results [label: "7. Ranked Results\nTop 20 matches"]

// Step 8: Display
display [label: "8. Display to User\nwith explanations", icon: browser, color: purple]

// Flow connections
user > user_input
user_input > profile_extraction
profile_extraction > extracted_profile
extracted_profile > api_fetch

api_fetch > petfinder_results
api_fetch > rescuegroups_results

petfinder_results > dedup
rescuegroups_results > dedup
dedup > dedup_details

dedup > cache
cache > sqlite_cache
cache > vector_store

sqlite_cache > matching
vector_store > matching

matching > results
results > display
display > user
```

---

## Agent Interaction Diagram

```eraser
// Tuxedo Link - Agent Interactions

// Planning Agent (Orchestrator)
planner [label: "PlanningAgent\n(Orchestrator)", icon: brain, color: orange]

// Worker Agents
profile [label: "ProfileAgent", icon: chat, color: purple]
petfinder [label: "PetfinderAgent", icon: api, color: blue]
rescue [label: "RescueGroupsAgent", icon: api, color: blue]
dedup [label: "DeduplicationAgent", icon: filter, color: cyan]
matching [label: "MatchingAgent", icon: search, color: green]
email [label: "EmailAgent", icon: email, color: red]

// Data Stores
db [label: "DatabaseManager", icon: database, color: gray]
vectordb [label: "VectorDBManager", icon: database, color: gray]

// External
openai [label: "OpenAI API", icon: openai, color: green]
apis [label: "External APIs", icon: api, color: blue]
sendgrid [label: "SendGrid", icon: email, color: red]

// Orchestration
planner > profile: 1. Extract preferences
profile > openai: API call
openai > profile: Structured output
profile > planner: CatProfile

planner > petfinder: 2. Search (parallel)
planner > rescue: 2. Search (parallel)
petfinder > apis: API request
rescue > apis: API request
apis > petfinder: Cat data
apis > rescue: Cat data
petfinder > planner: Cats list
rescue > planner: Cats list

planner > dedup: 3. Remove duplicates
dedup > db: Check cache
db > dedup: Cached embeddings
dedup > planner: Unique cats

planner > db: 4. Cache results
planner > vectordb: 5. Update embeddings

planner > matching: 6. Find matches
matching > vectordb: Vector search
matching > db: Metadata filter
vectordb > matching: Similar cats
db > matching: Filtered cats
matching > planner: Ranked matches

planner > email: 7. Send notifications (if alert)
email > sendgrid: API call
sendgrid > email: Delivery status
```

---

## Deployment Architecture

```eraser
// Tuxedo Link - Modal Deployment

// Local Development
local [label: "Local Development", icon: laptop, color: purple] {
  gradio_dev [label: "Gradio UI\n:7860"]
  dev_db [label: "SQLite DB\n./data/"]
  dev_vector [label: "ChromaDB\n./cat_vectorstore/"]
}

// Modal Cloud
modal [label: "Modal Cloud", icon: cloud, color: blue] {
  // Scheduled Functions
  scheduled [label: "Scheduled Functions"] {
    daily [label: "daily_search_job\nCron: 0 9 * * *"]
    weekly [label: "weekly_search_job\nCron: 0 9 * * 1"]
    cleanup [label: "cleanup_job\nCron: 0 2 * * 0"]
  }
  
  // On-Demand Functions
  ondemand [label: "On-Demand"] {
    manual_search [label: "run_scheduled_searches()"]
    manual_cleanup [label: "cleanup_old_data()"]
  }
  
  // Storage
  storage [label: "Modal Volume\n/data"] {
    vol_db [label: "tuxedo_link.db"]
    vol_vector [label: "cat_vectorstore/"]
  }
  
  // Secrets
  secrets [label: "Secrets"] {
    api_keys [label: "- OPENAI_API_KEY\n- PETFINDER_*\n- RESCUEGROUPS_*\n- SENDGRID_*"]
  }
}

// External Services
external [label: "External Services", icon: cloud, color: red] {
  openai [label: "OpenAI"]
  petfinder [label: "Petfinder"]
  rescue [label: "RescueGroups"]
  sendgrid [label: "SendGrid"]
}

// Connections
local > modal: Deploy
modal > storage: Persistent data
modal > secrets: Load keys
scheduled > storage: Read/Write
ondemand > storage: Read/Write
modal > external: API calls
```

---

## Database Schema

```eraser
// Tuxedo Link - Database Schema

// Users Table
users [icon: table, color: blue] {
  id [label: "id: INTEGER PK"]
  email [label: "email: TEXT UNIQUE"]
  password_hash [label: "password_hash: TEXT"]
  created_at [label: "created_at: DATETIME"]
  last_login [label: "last_login: DATETIME"]
}

// Alerts Table
alerts [icon: table, color: green] {
  aid [label: "id: INTEGER PK"]
  user_id [label: "user_id: INTEGER FK"]
  user_email [label: "user_email: TEXT"]
  profile_json [label: "profile_json: TEXT"]
  frequency [label: "frequency: TEXT"]
  last_sent [label: "last_sent: DATETIME"]
  active [label: "active: INTEGER"]
  created_at [label: "created_at: DATETIME"]
  last_match_ids [label: "last_match_ids: TEXT"]
}

// Cats Cache Table
cats_cache [icon: table, color: orange] {
  cid [label: "id: TEXT PK"]
  name [label: "name: TEXT"]
  breed [label: "breed: TEXT"]
  age [label: "age: TEXT"]
  gender [label: "gender: TEXT"]
  size [label: "size: TEXT"]
  organization_name [label: "organization_name: TEXT"]
  city [label: "city: TEXT"]
  state [label: "state: TEXT"]
  source [label: "source: TEXT"]
  url [label: "url: TEXT"]
  cat_json [label: "cat_json: TEXT"]
  fingerprint [label: "fingerprint: TEXT"]
  image_embedding [label: "image_embedding: BLOB"]
  is_duplicate [label: "is_duplicate: INTEGER"]
  duplicate_of [label: "duplicate_of: TEXT"]
  fetched_at [label: "fetched_at: DATETIME"]
  created_at [label: "created_at: DATETIME"]
}

// ChromaDB Collection
vector_collection [icon: database, color: purple] {
  cats_embeddings [label: "Collection: cats_embeddings"]
  embedding_dim [label: "Dimensions: 384"]
  model [label: "Model: all-MiniLM-L6-v2"]
  metadata [label: "Metadata: name, breed, age, etc."]
}

// Relationships
users > alerts: user_id
alerts > cats_cache: Search results
cats_cache > vector_collection: Embeddings
```

---
## Diagram Types Included

1. **System Architecture** - High-level overview of all components
2. **Detailed Component Architecture** - Deep dive into layers and connections
3. **Data Flow Diagram** - Step-by-step search process
4. **Agent Interaction Diagram** - How agents communicate
5. **Deployment Architecture** - Modal cloud deployment
6. **Database Schema** - Data model and relationships

---

## Architecture Highlights

### Layered Architecture
```
┌─────────────────────────────────────┐
│  Frontend Layer (Gradio UI)         │
├─────────────────────────────────────┤
│  Framework Layer (Orchestration)    │
├─────────────────────────────────────┤
│  Agent Layer (7 Specialized Agents) │
├─────────────────────────────────────┤
│  Data Layer (SQLite + ChromaDB)     │
├─────────────────────────────────────┤
│  External APIs (4 Services)         │
└─────────────────────────────────────┘
```

### Key Design Patterns

- **Agent Pattern**: Specialized agents for different tasks
- **Orchestrator Pattern**: Planning agent coordinates workflow
- **Repository Pattern**: DatabaseManager abstracts data access
- **Strategy Pattern**: Different search strategies (Petfinder, RescueGroups)
- **Decorator Pattern**: Rate limiting and timing decorators
- **Observer Pattern**: Scheduled jobs watch for new alerts

### Technology Stack

**Frontend**: Gradio  
**Backend**: Python 3.12  
**Framework**: Custom Agent-based  
**Databases**: SQLite, ChromaDB  
**AI/ML**: OpenAI GPT-4, CLIP, SentenceTransformers  
**Deployment**: Modal (Serverless)  
**APIs**: Petfinder, RescueGroups, SendGrid  
