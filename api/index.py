#!/usr/bin/env python3
"""
Vercel entry point for n8n-workflows search engine.
This serves the same functionality as run.py but adapted for serverless deployment.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app but modify it for Vercel
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from mangum import Mangum

# Create FastAPI app
app = FastAPI(
    title="N8N Workflow Documentation API",
    description="Fast API for browsing and searching workflow documentation",
    version="2.0.0"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lightweight workflow database for Vercel
class VercelWorkflowDB:
    """Lightweight workflow database using pre-built JSON data for Vercel serverless environment."""
    
    def __init__(self):
        self.data = self._load_data()
    
    def _load_data(self):
        """Load pre-built workflow data from JSON file."""
        try:
            # Try to load from the built data file
            data_file = project_root / 'vercel_workflows.json'
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Fallback: build data on-the-fly (slower but works)
                print("Building workflow data on-the-fly...")
                return self._build_data()
        except Exception as e:
            print(f"Error loading workflow data: {e}")
            return {'stats': {}, 'workflows': []}
    
    def _build_data(self):
        """Build workflow data from source files."""
        from build_vercel_data import build_vercel_data_dict
        return build_vercel_data_dict()
    
    def get_stats(self):
        """Get workflow statistics."""
        return self.data.get('stats', {
            'total': 0,
            'active': 0,
            'inactive': 0,
            'triggers': {},
            'complexity': {},
            'total_nodes': 0,
            'unique_integrations': 0,
            'last_indexed': '2025-08-21'
        })
    
    def search_workflows(self, query='', limit=20, offset=0):
        """Search workflows from pre-built data."""
        workflows = self.data.get('workflows', [])
        
        # Filter by query if provided
        if query.strip():
            query_lower = query.lower()
            filtered_workflows = [
                w for w in workflows 
                if query_lower in w.get('name', '').lower() or 
                   query_lower in w.get('description', '').lower() or
                   any(query_lower in integration.lower() for integration in w.get('integrations', []))
            ]
        else:
            filtered_workflows = workflows
        
        total = len(filtered_workflows)
        
        # Apply pagination
        start = offset
        end = offset + limit
        paginated_workflows = filtered_workflows[start:end]
        
        return paginated_workflows, total

# Initialize database
db = VercelWorkflowDB()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main documentation page."""
    static_dir = project_root / "static" / "index.html"
    if static_dir.exists():
        return FileResponse(str(static_dir))
    
    # Fallback inline response
    stats = db.get_stats()
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html><head><title>N8N Workflow Documentation</title></head>
    <body>
        <h1>⚡ N8N Workflow Documentation</h1>
        <p>Total workflows: {stats.get('total', 0)}</p>
        <p>API endpoints:</p>
        <ul>
            <li><a href="/api/stats">/api/stats</a> - Database statistics</li>
            <li><a href="/api/workflows">/api/workflows</a> - Search workflows</li>
            <li><a href="/docs">/docs</a> - API documentation</li>
        </ul>
    </body></html>
    """)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "n8n-workflows-api", "deployed": True}

@app.get("/api/stats")
async def get_stats():
    try:
        return db.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.get("/api/workflows")
async def search_workflows(
    q: str = Query("", description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    try:
        offset = (page - 1) * per_page
        workflows, total = db.search_workflows(query=q, limit=per_page, offset=offset)
        
        pages = (total + per_page - 1) // per_page
        
        return {
            "workflows": workflows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
            "query": q,
            "filters": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching workflows: {str(e)}")

# Mount static files if they exist
static_dir = project_root / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Create the handler for Vercel
handler = Mangum(app)
