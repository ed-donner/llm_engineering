# Token Visualizer

Visualize how LLMs predict tokens with probabilities in real-time using OpenRouter's free models.

## Prerequisites

- Node.js 18+

## Setup

1. Install dependencies:
   ```bash
   cd backend && npm install
   cd ../frontend && npm install
   ```

2. Start the backend server (port 3001):
   ```bash
   cd backend
   npm run dev
   ```

3. Start the frontend (port 3000):
   ```bash
   cd frontend
   npm run dev
   ```

4. Open http://localhost:3000 in your browser

## Usage

1. Enter a prompt
2. Select a free model (Gemma, Llama, Mistral, Phi, Qwen)
3. Adjust max tokens
4. Click "Visualize Tokens"
5. Watch the token prediction graph build in real-time

## Features

- Real-time token streaming with probabilities (via SSE)
- Interactive graph visualization (drag, zoom, pan)
- Alternative token suggestions shown as branches
- Token breakdown table with all probabilities
- Uses OpenRouter's free models - no API key needed

## Tech Stack

- Frontend: Next.js 14, React Flow, Tailwind, Shadcn/ui
- Backend: Express.js, OpenAI SDK (via OpenRouter)
- Models: OpenRouter free models (Gemma, Llama, Mistral, Phi, Qwen)