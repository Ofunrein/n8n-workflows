#!/bin/bash

echo "🚀 Deploying to Vercel"
echo "======================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    echo "❌ This script must be run from the n8n-workflows directory"
    exit 1
fi

# Step 1: Commit any local changes
print_status "Checking for local changes..."
if [ -n "$(git status --porcelain)" ]; then
    print_status "Local changes detected. Committing them..."
    git add .
    git commit -m "Auto-commit before Vercel deployment"
    git push origin main
    print_success "Changes committed and pushed"
else
    print_status "No local changes to commit"
fi

# Step 2: Deploy to Vercel
print_status "Deploying to Vercel..."
print_status "This will trigger an automatic deployment on Vercel"

# Step 3: Show deployment info
echo ""
print_success "🎉 Deployment triggered!"
echo ""
echo "📋 Check your deployment at:"
echo "   https://vercel.com/ofunreins-projects/n8n-workflows"
echo ""
echo "🌐 Your live URL will be updated automatically"
echo ""
echo "📊 To monitor deployment progress, check the Vercel dashboard"
