#!/bin/bash

echo "🔄 Syncing with Zie619/n8n-workflows and deploying to Vercel"
echo "=============================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    print_error "This script must be run from the n8n-workflows directory"
    exit 1
fi

# Step 1: Fetch latest changes from upstream
print_status "Fetching latest changes from Zie619/n8n-workflows..."
git fetch upstream

if [ $? -ne 0 ]; then
    print_error "Failed to fetch from upstream"
    exit 1
fi

# Step 2: Check if there are new changes
UPSTREAM_COMMIT=$(git rev-parse upstream/main)
LOCAL_COMMIT=$(git rev-parse HEAD)

if [ "$UPSTREAM_COMMIT" = "$LOCAL_COMMIT" ]; then
    print_warning "No new changes from upstream. Your repo is already up to date."
else
    print_status "New changes detected! Updating your repository..."
    
    # Step 3: Merge upstream changes
    print_status "Merging upstream changes..."
    git merge upstream/main --no-edit
    
    if [ $? -ne 0 ]; then
        print_error "Merge conflict detected! Please resolve conflicts manually and then run:"
        echo "  git add . && git commit -m 'Resolve merge conflicts'"
        exit 1
    fi
    
    print_success "Successfully merged upstream changes"
fi

# Step 4: Push to your origin (GitHub)
print_status "Pushing changes to your GitHub repository..."
git push origin main

if [ $? -ne 0 ]; then
    print_error "Failed to push to origin"
    exit 1
fi

print_success "Successfully pushed to GitHub"

# Step 5: Deploy to Vercel
print_status "Deploying to Vercel..."
print_status "This will trigger an automatic deployment on Vercel"

# Step 6: Show deployment status
echo ""
print_success "🎉 Sync and deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check your Vercel dashboard for deployment status"
echo "2. Your live URL will be updated automatically"
echo "3. To check deployment: https://vercel.com/ofunreins-projects/n8n-workflows"
echo ""
echo "🔄 To sync again in the future, just run: ./sync_with_upstream.sh"
echo ""
echo "📚 Your repository is now synced with:"
echo "   - Origin (your repo): https://github.com/Ofunrein/n8n-workflows"
echo "   - Upstream (Zie619): https://github.com/Zie619/n8n-workflows"
echo "   - Vercel: https://vercel.com/ofunreins-projects/n8n-workflows"
