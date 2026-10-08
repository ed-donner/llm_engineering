#!/bin/bash

# ---------------------------------------------------------------------------------------------------------------------
#  Script: reset.sh
#  Description: Removes all node_modules and package-lock.json files to reset the project
# ---------------------------------------------------------------------------------------------------------------------

set -e  # Exit on error

echo "🧹 Starting reset process..."
echo ""

# ---------------------------------------------------------------------------------------------------------------------
#  Remove Backend Dependencies
# ---------------------------------------------------------------------------------------------------------------------

if [ -d "backend/node_modules" ]; then
  echo "🗑️  Removing backend/node_modules..."
  rm -rf backend/node_modules
  echo "   ✅ Backend node_modules removed"
else
  echo "   ℹ️  Backend node_modules not found (already clean)"
fi

if [ -f "backend/package-lock.json" ]; then
  echo "🗑️  Removing backend/package-lock.json..."
  rm -f backend/package-lock.json
  echo "   ✅ Backend package-lock.json removed"
else
  echo "   ℹ️  Backend package-lock.json not found (already clean)"
fi

# ---------------------------------------------------------------------------------------------------------------------
#  Remove Frontend Dependencies
# ---------------------------------------------------------------------------------------------------------------------

if [ -d "frontend/node_modules" ]; then
  echo "🗑️  Removing frontend/node_modules..."
  rm -rf frontend/node_modules
  echo "   ✅ Frontend node_modules removed"
else
  echo "   ℹ️  Frontend node_modules not found (already clean)"
fi

if [ -f "frontend/package-lock.json" ]; then
  echo "🗑️  Removing frontend/package-lock.json..."
  rm -f frontend/package-lock.json
  echo "   ✅ Frontend package-lock.json removed"
else
  echo "   ℹ️  Frontend package-lock.json not found (already clean)"
fi

# ---------------------------------------------------------------------------------------------------------------------
#  Remove Root Dependencies (if any)
# ---------------------------------------------------------------------------------------------------------------------

if [ -d "node_modules" ]; then
  echo "🗑️  Removing root node_modules..."
  rm -rf node_modules
  echo "   ✅ Root node_modules removed"
else
  echo "   ℹ️  Root node_modules not found (already clean)"
fi

if [ -f "package-lock.json" ]; then
  echo "🗑️  Removing root package-lock.json..."
  rm -f package-lock.json
  echo "   ✅ Root package-lock.json removed"
else
  echo "   ℹ️  Root package-lock.json not found (already clean)"
fi

# ---------------------------------------------------------------------------------------------------------------------
#  Summary
# ---------------------------------------------------------------------------------------------------------------------

echo ""
echo "✨ Reset complete!"
echo ""
echo "To reinstall dependencies, run: ./bootstrap.sh"

