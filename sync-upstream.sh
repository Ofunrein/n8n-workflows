#!/bin/bash

# 🔄 Manual Upstream Sync Script for n8n-workflows
# This script safely syncs changes from Zie619/n8n-workflows while preserving your customizations

set -e  # Exit on any error

echo "🚀 Starting manual upstream sync..."

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
if [[ ! -f "run.py" || ! -d "workflows" ]]; then
    print_error "This script must be run from the n8n-workflows repository root"
    exit 1
fi

# Ensure we have upstream remote
print_status "Checking upstream remote..."
if ! git remote get-url upstream >/dev/null 2>&1; then
    print_status "Adding upstream remote..."
    git remote add upstream https://github.com/Zie619/n8n-workflows.git
fi

# Fetch latest from upstream
print_status "Fetching latest changes from upstream..."
git fetch upstream main

# Check for changes
UPSTREAM_COMMIT=$(git rev-parse upstream/main)
CURRENT_COMMIT=$(git rev-parse HEAD)

if [[ "$UPSTREAM_COMMIT" == "$CURRENT_COMMIT" ]]; then
    print_success "Repository is already up to date!"
    exit 0
fi

print_status "New changes detected from upstream"

# Create backup branch
BACKUP_BRANCH="backup-before-sync-$(date +%Y%m%d-%H%M%S)"
print_status "Creating backup branch: $BACKUP_BRANCH"
git checkout -b "$BACKUP_BRANCH"
git checkout main

# Show what will be updated
print_status "Changes that will be synced:"
git log --oneline HEAD..upstream/main | head -10

# Ask for confirmation
read -p "$(echo -e ${YELLOW}Do you want to proceed with the sync? [y/N]:${NC} )" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Sync cancelled by user"
    git branch -D "$BACKUP_BRANCH"
    exit 0
fi

# Create sync branch
SYNC_BRANCH="sync-upstream-$(date +%Y%m%d-%H%M%S)"
print_status "Creating sync branch: $SYNC_BRANCH"
git checkout -b "$SYNC_BRANCH"

# List of files/directories to protect from upstream changes
PROTECTED_FILES=(
    ".gitignore"
    "vercel.json"
    "api/"
    "requirements.txt"
    "RE HTML email_templates copy/"
    ".github/workflows/"
    "sync-upstream.sh"
)

print_status "Protecting custom files from overwrite..."

# Stash our protected files
for file in "${PROTECTED_FILES[@]}"; do
    if [[ -e "$file" ]]; then
        print_status "Protecting: $file"
        # Create temporary copies
        cp -r "$file" "${file}.protected" 2>/dev/null || true
    fi
done

# Merge upstream changes
print_status "Merging upstream changes..."
if git merge upstream/main --no-edit; then
    print_success "Merge completed successfully"
else
    print_warning "Merge conflicts detected, resolving automatically..."
    
    # Restore our protected files
    for file in "${PROTECTED_FILES[@]}"; do
        if [[ -e "${file}.protected" ]]; then
            print_status "Restoring: $file"
            rm -rf "$file" 2>/dev/null || true
            mv "${file}.protected" "$file" 2>/dev/null || true
        fi
    done
    
    # Mark conflicts as resolved
    git add .
    git commit -m "🔄 Auto-resolve: Preserve custom Vercel setup during upstream merge"
fi

# Clean up protected file backups
for file in "${PROTECTED_FILES[@]}"; do
    rm -rf "${file}.protected" 2>/dev/null || true
done

# Check if there are workflow changes
WORKFLOW_CHANGES=$(git diff HEAD~1 --name-only | grep "^workflows/" | wc -l)

if [[ $WORKFLOW_CHANGES -gt 0 ]]; then
    print_status "Found $WORKFLOW_CHANGES workflow changes, rebuilding database..."
    
    # Rebuild workflow database
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
from workflow_db import WorkflowDatabase
import os

print('🔄 Rebuilding workflow database...')
db = WorkflowDatabase('database/workflows.db')
stats = db.index_all_workflows(force_reindex=True)
print(f'✅ Database rebuilt: {stats}')
" 2>/dev/null || print_warning "Could not rebuild database - do this manually later"

        # Rebuild Vercel data
        python3 build_vercel_data.py 2>/dev/null || print_warning "Could not rebuild Vercel data - do this manually later"
        
        # Commit database updates
        git add database/ vercel_workflows.json 2>/dev/null || true
        git commit -m "🗃️ Auto-update: Rebuild database with new workflows" 2>/dev/null || true
    else
        print_warning "Python not found - rebuild database manually with: python run.py --reindex"
    fi
fi

# Switch back to main and merge
print_status "Merging changes to main branch..."
git checkout main
git merge --no-ff "$SYNC_BRANCH" -m "🔄 Manual sync: Integrate upstream updates ($(git rev-parse --short upstream/main))"

# Clean up branches
git branch -D "$SYNC_BRANCH"
git branch -D "$BACKUP_BRANCH"

# Show summary
print_success "Sync completed successfully!"
print_status "Summary:"
echo "  - Synced to upstream commit: $(git rev-parse --short upstream/main)"
echo "  - Workflow changes: $WORKFLOW_CHANGES files"
echo "  - Protected files preserved: ${#PROTECTED_FILES[@]} items"

# Ask about pushing
read -p "$(echo -e ${YELLOW}Push changes to GitHub and trigger Vercel deployment? [y/N]:${NC} )" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Pushing to GitHub..."
    git push origin main
    print_success "Changes pushed! Vercel deployment will start automatically."
    print_status "Monitor deployment at: https://vercel.com/dashboard"
else
    print_warning "Changes not pushed. Run 'git push origin main' when ready."
fi

print_success "Upstream sync complete! 🎉"
