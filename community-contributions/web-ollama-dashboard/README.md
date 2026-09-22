# 🤖 Ollama Dashboard

A modern web application for managing and interacting with Ollama language models. This fullstack application provides a user-friendly interface to install, manage, and chat with Ollama models.

## ✨ Features

- **Model Management**

  - View installed models with their sizes (displayed in GB)
  - Browse available models from Ollama library with size information
  - Install new models with real-time progress tracking
  - Delete installed models with confirmation modal
  - Filter models to show only chat-compatible ones

- **Chat Interface**

  - Interactive chat with selected models
  - Multiple system prompts support (each prompt must not be empty)
  - Real-time response display
  - Input validation (requires model selection, system prompts, and message)
  - Error handling and user feedback

- **Health Monitoring**
  - Automatic Ollama service availability check on startup
  - Visual status indicators (success/error alerts)
  - Error messages and troubleshooting hints

## 🏗️ Project Structure

```
.
├── backend/                    # Express.js + TypeScript Backend
│   ├── src/
│   │   ├── index.ts           # Main server entry point
│   │   └── routes/
│   │       ├── __tests__/     # Backend unit tests
│   │       │   ├── health.test.ts
│   │       │   └── hello.test.ts
│   │       ├── health.ts      # Backend health check
│   │       ├── hello.ts       # Hello endpoint
│   │       └── ollama/        # Ollama-related routes
│   │           ├── __tests__/ # Ollama route tests
│   │           │   ├── chat.test.ts
│   │           │   ├── health.test.ts
│   │           │   └── utils.test.ts
│   │           ├── index.ts   # Router configuration
│   │           ├── utils.ts   # Utility functions (supportsChat, handleOllamaError)
│   │           ├── health.ts  # Ollama health check
│   │           ├── installed.ts  # List installed models (chat-compatible only)
│   │           ├── available.ts  # List available models
│   │           ├── install.ts    # Install model endpoint (SSE streaming)
│   │           ├── delete.ts     # Delete model endpoint
│   │           └── chat.ts       # Chat endpoint
│   ├── jest.config.js         # Jest configuration
│   ├── tsconfig.json
│   ├── tsconfig.test.json     # TypeScript config for tests
│   └── package.json
│
├── frontend/                   # React + TypeScript Frontend (Vite)
│   ├── src/
│   │   ├── App.tsx            # Main application component
│   │   ├── main.tsx           # Application entry point
│   │   ├── components/        # React components
│   │   │   ├── Header/        # Application header
│   │   │   ├── ModelsSelect/  # Model selection and management
│   │   │   │   ├── ModelsPanel.tsx  # Model management drawer
│   │   │   │   └── hooks/     # Custom hooks
│   │   │   │       ├── useOllamaModels.ts
│   │   │   │       ├── useOllamaAvailableModels.ts
│   │   │   │       ├── useInstallModel.ts
│   │   │   │       └── useDeleteModel.ts
│   │   │   ├── TextInputsList/ # System prompts management
│   │   │   └── ChatInterface/ # Chat interface
│   │   │       └── hooks/     # Chat hooks
│   │   │           ├── __tests__/
│   │   │           │   └── useChat.test.ts
│   │   │           └── useChat.ts
│   │   └── hooks/             # Global hooks
│   │       ├── __tests__/
│   │       │   └── useOllamaHealth.test.ts
│   │       └── useOllamaHealth.ts
│   ├── jest.config.cjs        # Jest configuration (CommonJS)
│   ├── tsconfig.json
│   ├── tsconfig.test.json     # TypeScript config for tests
│   └── package.json
│
├── bootstrap.sh                # Setup, test, and start script
├── reset.sh                    # Clean dependencies script
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** (version 18 or higher)
- **npm** or **yarn**
- **Ollama** installed and running on your machine
  - Download from [ollama.com](https://ollama.com)
  - Make sure Ollama is running: `ollama serve`

### Installation & Run

The easiest way to get started is using the bootstrap script:

```bash
./bootstrap.sh
```

This script will:

1. Install all npm dependencies (backend and frontend)
2. Run backend unit tests
3. Run frontend unit tests
4. Start both services in development mode (only if all tests pass)

The application will be available at:

- **Frontend**: `http://localhost:5173` (or the port shown in terminal)
- **Backend**: `http://localhost:3001`

### Alternative: Manual Setup

If you prefer to set up manually:

```bash
# Install dependencies
cd backend && npm install && cd ..
cd frontend && npm install && cd ..

# Run tests (optional but recommended)
cd backend && npm test && cd ..
cd frontend && npm test && cd ..

# Start backend (in one terminal)
cd backend && npm run dev

# Start frontend (in another terminal)
cd frontend && npm run dev
```

## 📝 Available Scripts

### Project Root Scripts

- `./bootstrap.sh` - Install dependencies, run tests, and start both services
- `./reset.sh` - Remove all node_modules and package-lock.json files
- `npm run dev` - Start both backend and frontend (requires concurrently)
- `npm run dev:backend` - Start only the backend
- `npm run dev:frontend` - Start only the frontend
- `npm run install:all` - Install dependencies for all projects
- `npm run build` - Build both backend and frontend for production

### Backend Scripts (inside `/backend`)

- `npm run dev` - Start server in development mode with hot reload
- `npm run build` - Compile TypeScript to JavaScript
- `npm start` - Start server in production mode (after build)
- `npm run type-check` - Check types without compiling
- `npm test` - Run unit tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report

### Frontend Scripts (inside `/frontend`)

- `npm run dev` - Start Vite development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm test` - Run unit tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report

## 🔌 API Endpoints

### Health & Status

- `GET /api/health` - Backend health check
- `GET /api/ollama/health` - Check Ollama service availability

### Models

- `GET /api/ollama/models/installed` - List all installed models (chat-compatible only)
  - Returns: `{ success: boolean, count: number, models: Array<{name, size, modified_at}> }`
- `GET /api/ollama/models/available` - List available models from Ollama library (not installed)
  - Returns: `{ success: boolean, count: number, models: Array<{name, size, installed: false}> }`
- `POST /api/ollama/models/install` - Install a model (Server-Sent Events streaming response with progress)
  - Request: `{ modelName: string }`
  - Response: SSE stream with progress events
- `POST /api/ollama/models/delete` - Delete an installed model
  - Request: `{ modelName: string }`
  - Response: `{ success: boolean, message: string }`

### Chat

- `POST /api/ollama/chat` - Send messages to a model
  - Request body:
    ```json
    {
      "model": "model-name",
      "messages": [
        { "role": "system", "content": "system prompt 1" },
        { "role": "system", "content": "system prompt 2" },
        { "role": "user", "content": "user message" }
      ]
    }
    ```
  - Response: `{ success: boolean, response: string, model: string }`

## 🛠️ Technologies

### Backend

- **Express.js** - Web framework
- **TypeScript** - Type safety
- **Axios** - HTTP client for Ollama API
- **CORS** - Cross-origin resource sharing
- **dotenv** - Environment variables
- **Jest** - Testing framework
- **Supertest** - HTTP assertion library

### Frontend

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Ant Design** - UI component library
- **Axios** - HTTP client
- **React Hooks** - State management
- **Jest** - Testing framework
- **React Testing Library** - Component testing utilities

## 🔧 Configuration

### Environment Variables

The backend uses environment variables (optional, with defaults):

- `OLLAMA_URL` - Ollama API URL (default: `http://127.0.0.1:11434`)
- `OLLAMA_REGISTRY_URL` - Ollama registry URL (default: `https://ollama.com`)

Create a `.env` file in the `backend` directory to override:

```env
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_REGISTRY_URL=https://ollama.com
```

### Frontend Proxy

The frontend is configured to proxy API requests to the backend through Vite. Requests to `/api/*` are automatically redirected to `http://localhost:3001`.

## 📖 Usage Guide

### 1. Check Ollama Status

When you open the application, you'll see a status indicator at the top showing whether Ollama is available. The check happens automatically on page load.

### 2. Select a Model

- Click "Manage Models" button to open the models panel
- Browse installed models (shown with "In Use" tag if selected)
- Browse available models (with size in GB)
- Click on an installed model to select it, or click "Install" on an available model
- The selected model will be shown in the main interface

### 3. Configure System Prompts

- Add one or more system prompts in the "System Prompts" card
- Each prompt must not be empty (validation enforced)
- Click "Add System Prompt" to add more prompts
- Multiple prompts will be combined (joined with double newlines) when sending to the model
- Remove prompts using the "Remove" button (at least one prompt is required)

### 4. Chat with the Model

- Enter your message in the chat input field
- Click "Send" button or press Enter
- The model's response will appear in the response area below
- Loading indicators show while waiting for response
- Error messages are displayed if something goes wrong

## 🧪 Testing

The project includes comprehensive unit tests using Jest for both backend and frontend.

### Running Tests

**Backend:**

```bash
cd backend
npm test              # Run all tests
npm run test:watch    # Run tests in watch mode
npm run test:coverage # Generate coverage report
```

**Frontend:**

```bash
cd frontend
npm test              # Run all tests
npm run test:watch    # Run tests in watch mode
npm run test:coverage # Generate coverage report
```

### Test Coverage

**Backend Tests:**

- Route handlers (health, hello, ollama routes)
- Utility functions (supportsChat, handleOllamaError)
- Error handling scenarios
- Request validation

**Frontend Tests:**

- React hooks (useOllamaHealth, useChat)
- State management
- Error handling
- Loading states

### Test Files Location

- Backend: `backend/src/**/__tests__/*.test.ts`
- Frontend: `frontend/src/**/__tests__/*.test.ts`

## 🐛 Troubleshooting

### Ollama Not Available

If you see "Ollama Not Available":

1. Make sure Ollama is installed: `ollama --version`
2. Start Ollama service: `ollama serve`
3. Check if Ollama is running: `curl http://localhost:11434/api/tags`
4. Verify the `OLLAMA_URL` environment variable if using custom configuration

### Models Not Loading

- Verify Ollama is running and accessible
- Check browser console for errors
- Ensure you have at least one model installed: `ollama list`
- Note: Only chat-compatible models are shown

### Installation Issues

- Run `./reset.sh` to clean all dependencies
- Run `./bootstrap.sh` to reinstall and start (includes test execution)

### Tests Failing

- Make sure all dependencies are installed: `npm install` in both backend and frontend
- Check that Jest dependencies are properly installed
- Verify TypeScript configuration files are correct

## 📦 Main Dependencies

### Backend

- `express` - Web framework
- `axios` - HTTP client
- `cors` - CORS middleware
- `dotenv` - Environment variables
- `tsx` - TypeScript executor
- `jest` - Testing framework
- `supertest` - HTTP assertion library
- `ts-jest` - TypeScript preprocessor for Jest

### Frontend

- `react` & `react-dom` - React library
- `vite` - Build tool
- `antd` - UI component library
- `@ant-design/icons` - Icons
- `axios` - HTTP client
- `jest` - Testing framework
- `@testing-library/react` - React testing utilities
- `@testing-library/jest-dom` - DOM matchers for Jest
- `ts-jest` - TypeScript preprocessor for Jest

## 📄 License

ISC
