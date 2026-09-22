#!/bin/bash

# ---------------------------------------------------------------------------------------------------------------------
#  Script: bootstrap.sh
#  Description: Installs npm dependencies, runs tests, then starts both services
# ---------------------------------------------------------------------------------------------------------------------

set -e  # Exit on error

echo "🚀 Starting bootstrap process..."

# ---------------------------------------------------------------------------------------------------------------------
#  Install Backend Dependencies
# ---------------------------------------------------------------------------------------------------------------------

echo ""
echo "📦 Installing backend dependencies..."
cd backend
npm install
cd ..

# ---------------------------------------------------------------------------------------------------------------------
#  Install Frontend Dependencies
# ---------------------------------------------------------------------------------------------------------------------

echo ""
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# ---------------------------------------------------------------------------------------------------------------------
#  Run Backend Tests
# ---------------------------------------------------------------------------------------------------------------------

echo ""
echo "🧪 Running backend tests..."
cd backend
npm test
cd ..

# ---------------------------------------------------------------------------------------------------------------------
#  Run Frontend Tests
# ---------------------------------------------------------------------------------------------------------------------

echo ""
echo "🧪 Running frontend tests..."
cd frontend
npm test
cd ..

# ---------------------------------------------------------------------------------------------------------------------
#  Start Services
# ---------------------------------------------------------------------------------------------------------------------

echo ""
echo "✨ All tests passed! Starting services..."
echo ""

# Start backend in background
echo "🔧 Starting backend server..."
cd backend
npm run dev &
BACKEND_PID=$!
cd ..

# Start frontend in background
echo "🎨 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# ---------------------------------------------------------------------------------------------------------------------
#  Wait for processes
# ---------------------------------------------------------------------------------------------------------------------

echo ""
echo "✅ Services started!"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

