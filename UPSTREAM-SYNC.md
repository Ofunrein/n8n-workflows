# 🔄 Upstream Sync System

This document explains how to use the automated upstream sync system to keep your n8n-workflows repository updated with the latest changes from [Zie619/n8n-workflows](https://github.com/Zie619/n8n-workflows) while preserving your custom Vercel deployment setup.

## 🎯 Overview

Your repository automatically syncs with the upstream repository to get:
- ✅ **New workflows** - Latest automation templates
- ✅ **Documentation updates** - Improved guides and examples  
- ✅ **Bug fixes** - Stability improvements
- ✅ **Feature enhancements** - New functionality

While preserving your customizations:
- 🛡️ **Vercel configuration** - Your serverless deployment setup
- 🛡️ **Email templates** - Your RE HTML email templates  
- 🛡️ **GitHub Actions** - Your automated sync workflows
- 🛡️ **Custom scripts** - Your local development setup

## 🤖 Automated Sync (Recommended)

### GitHub Actions Workflow

Your repository runs an automated sync every 6 hours that:

1. **Checks for updates** from upstream repository
2. **Safely merges** new workflows and documentation
3. **Preserves your customizations** (Vercel config, templates, etc.)
4. **Rebuilds the database** when new workflows are added
5. **Triggers Vercel deployment** automatically
6. **Notifies you** of successful updates

### Monitoring Automated Sync

- **View sync status**: Go to Actions tab in your GitHub repository
- **Check deployment**: Monitor at https://vercel.com/dashboard
- **Manual trigger**: Click "Run workflow" in GitHub Actions if needed

## 🔧 Manual Sync

### Quick Manual Sync

Run the automated sync script:

```bash
./sync-upstream.sh
```

This script will:
- ✅ Safely check for upstream changes
- ✅ Show you what will be updated
- ✅ Ask for confirmation before proceeding
- ✅ Preserve all your customizations
- ✅ Rebuild database if workflows changed
- ✅ Optionally push to trigger Vercel deployment

### Advanced Manual Sync

For more control over the sync process:

```bash
# 1. Check for updates
git fetch upstream main
git log --oneline HEAD..upstream/main

# 2. Create backup branch
git checkout -b backup-$(date +%Y%m%d)
git checkout main

# 3. Merge upstream changes
git merge upstream/main

# 4. Resolve any conflicts (preserve your custom files)
git checkout HEAD -- .gitignore vercel.json api/ requirements.txt
git checkout HEAD -- "RE HTML email_templates copy/"

# 5. Rebuild database if needed
python run.py --reindex
python build_vercel_data.py

# 6. Commit and push
git add .
git commit -m "🔄 Manual sync: Update from upstream"
git push origin main
```

## 🛡️ Protected Files

These files are automatically protected during sync and will never be overwritten:

| File/Directory | Purpose |
|---|---|
| `.gitignore` | Excludes your email templates from Git |
| `vercel.json` | Vercel deployment configuration |
| `api/` | Your Vercel serverless function |
| `requirements.txt` | Your Python dependencies |
| `RE HTML email_templates copy/` | Your email templates |
| `.github/workflows/` | Your automated sync workflows |
| `sync-upstream.sh` | Your manual sync script |

## 📁 Always Updated

These files/directories are always synced from upstream:

| File/Directory | Purpose |
|---|---|
| `workflows/` | Latest n8n workflow templates |
| `Documentation/` | Updated guides and documentation |
| `README.md` | Main project documentation |
| `api_server.py` | Core API server (checked for conflicts) |
| `workflow_db.py` | Database management code |

## 🚀 Vercel Auto-Deployment

When the sync detects new workflows:

1. **Database rebuilds** automatically with new workflows
2. **Vercel data regenerates** for serverless deployment  
3. **GitHub push triggers** Vercel deployment
4. **Live site updates** with new searchable workflows

Your live search engine at `https://n8n-workflows-[your-id].vercel.app` stays current automatically!

## 🔍 Troubleshooting

### Sync Fails

```bash
# Reset to last known good state
git reset --hard HEAD~1

# Try manual sync with more control
./sync-upstream.sh
```

### Vercel Deployment Issues

```bash
# Rebuild data files
python build_vercel_data.py

# Redeploy to Vercel
git add vercel_workflows.json
git commit -m "🔧 Rebuild Vercel data"
git push origin main
```

### Database Issues

```bash
# Force rebuild database
python run.py --reindex --force

# Check database stats
python -c "from workflow_db import WorkflowDatabase; print(WorkflowDatabase('database/workflows.db').get_stats())"
```

### Merge Conflicts

```bash
# During conflicts, always preserve your custom files
git checkout HEAD -- .gitignore vercel.json api/ requirements.txt
git checkout HEAD -- "RE HTML email_templates copy/"

# Then continue the merge
git add .
git commit -m "🔄 Resolve merge conflicts"
```

## ⚙️ Configuration

Edit `.syncconfig` to customize sync behavior:

```bash
# Enable/disable automatic database rebuild
AUTO_REBUILD_DB=true

# Enable/disable automatic Vercel data rebuild  
AUTO_BUILD_VERCEL_DATA=true

# Add more protected files
PROTECTED_FILES+=("your-custom-file.txt")
```

## 📊 Sync Status

Check if your repository is up to date:

```bash
# Check for upstream changes
git fetch upstream main
git log --oneline HEAD..upstream/main

# If empty output = you're up to date
# If shows commits = updates available
```

## 🎉 Benefits

- **🔄 Always Current**: Get latest workflows within 6 hours
- **🛡️ Safe Updates**: Your customizations are never lost  
- **🚀 Auto-Deploy**: Live site updates automatically
- **📱 Zero Downtime**: Seamless updates without breaking your site
- **🔍 Enhanced Search**: New workflows immediately searchable
- **📈 Growing Collection**: Access to 2000+ (and growing) workflows

---

## 🆘 Need Help?

- **Manual sync**: Run `./sync-upstream.sh`
- **Force sync**: Use GitHub Actions "Run workflow" with force option
- **Reset everything**: `git reset --hard backup-[date]` (if you created backup)
- **Check sync logs**: View GitHub Actions tab in your repository

Your n8n-workflows repository will now stay automatically synchronized with the latest updates while maintaining your custom Vercel deployment! 🎉
