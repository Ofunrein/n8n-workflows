#!/usr/bin/env python3
"""
Vercel-compatible FastAPI Server for N8N Workflow Documentation
Simplified version without external dependencies for serverless deployment.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="N8N Workflow Documentation API",
    description="Fast API for browsing and searching workflow documentation",
    version="2.0.0"
)

# Add middleware for performance
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class WorkflowSummary(BaseModel):
    id: Optional[int] = None
    filename: str
    name: str
    active: bool
    description: str = ""
    trigger_type: str = "Manual"
    complexity: str = "low"
    node_count: int = 0
    integrations: List[str] = []
    tags: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SearchResponse(BaseModel):
    workflows: List[WorkflowSummary]
    total: int
    page: int
    per_page: int
    pages: int
    query: str
    filters: Dict[str, Any]

class StatsResponse(BaseModel):
    total: int
    active: int
    inactive: int
    triggers: Dict[str, int]
    complexity: Dict[str, int]
    total_nodes: int
    unique_integrations: int
    last_indexed: str

# Vercel-compatible database using vercel_workflows.json
class VercelWorkflowDB:
    """Lightweight workflow database using pre-built JSON data for Vercel serverless environment."""
    
    def __init__(self):
        self.data = self._load_data()
    
    def _load_data(self):
        """Load pre-built workflow data from JSON file."""
        try:
            # Try to load from the built data file
            data_file = Path(__file__).parent / 'vercel_workflows.json'
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print("vercel_workflows.json not found")
                return {'stats': {}, 'workflows': []}
        except Exception as e:
            print(f"Error loading workflow data: {e}")
            return {'stats': {}, 'workflows': []}
    
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
    static_dir = Path(__file__).parent.parent / "static" / "index.html"
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

@app.get("/api/workflows", response_model=SearchResponse)
async def search_workflows(
    q: str = Query("", description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    try:
        offset = (page - 1) * per_page
        workflows, total = db.search_workflows(query=q, limit=per_page, offset=offset)
        
        # Convert to Pydantic models
        workflow_summaries = []
        for workflow in workflows:
            try:
                workflow_summaries.append(WorkflowSummary(**workflow))
            except Exception as e:
                print(f"Error converting workflow {workflow.get('filename', 'unknown')}: {e}")
                continue
        
        pages = (total + per_page - 1) // per_page
        
        return SearchResponse(
            workflows=workflow_summaries,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            query=q,
            filters={}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching workflows: {str(e)}")

@app.get("/api/workflows/{filename}")
async def get_workflow_detail(filename: str):
    """Get detailed workflow information including raw JSON."""
    try:
        print(f"DEBUG: Requested workflow filename: {filename} - Vercel deployment test")
        
        # Get workflow metadata from database
        workflows, _ = db.search_workflows(f'filename:"{filename}"', limit=1)
        print(f"DEBUG: Database search returned {len(workflows)} workflows")
        
        if not workflows:
            print(f"DEBUG: Workflow {filename} not found in database")
            raise HTTPException(status_code=404, detail="Workflow not found in database")
        
        workflow_meta = workflows[0]
        
        # Try to load from vercel_workflows.json
        raw_json = None
        try:
            # Try local copy first (in api/ directory)
            vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
            if not vercel_data_path.exists():
                # Fallback to parent directory
                vercel_data_path = Path(__file__).parent.parent / "vercel_workflows.json"
            
            if vercel_data_path.exists():
                print(f"Loading from vercel_workflows.json: {vercel_data_path}")
                with open(vercel_data_path, 'r', encoding='utf-8') as f:
                    vercel_data = json.load(f)
                
                # Find the workflow in the vercel data
                for workflow in vercel_data.get('workflows', []):
                    if workflow.get('filename') == filename:
                        # Reconstruct the raw JSON from the metadata
                        raw_json = {
                            'id': workflow.get('workflow_id', ''),
                            'name': workflow.get('name', ''),
                            'active': workflow.get('active', False),
                            'nodes': [],  # We don't have the full node data in vercel_workflows.json
                            'connections': {},
                            'meta': {
                                'description': workflow.get('description', ''),
                                'tags': workflow.get('tags', [])
                            }
                        }
                        print(f"Found workflow in vercel_workflows.json: {filename}")
                        break
                
                if raw_json is None:
                    print(f"Workflow {filename} not found in vercel_workflows.json")
                    raise HTTPException(status_code=404, detail=f"Workflow '{filename}' not found in vercel data")
            else:
                print("vercel_workflows.json not found")
                raise HTTPException(status_code=404, detail="vercel_workflows.json not found")
        except Exception as e:
            print(f"Error loading from vercel_workflows.json: {e}")
            raise HTTPException(status_code=500, detail=f"Error loading workflow data: {str(e)}")
        
        if raw_json is None:
            raise HTTPException(status_code=404, detail=f"Workflow file '{filename}' not found")
        
        return {
            "metadata": workflow_meta,
            "raw_json": raw_json
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading workflow: {str(e)}")

@app.get("/api/workflows/{filename}/download")
async def download_workflow(filename: str):
    """Download workflow JSON file with proper n8n structure."""
    try:
        # Get workflow metadata from database
        workflows, _ = db.search_workflows(f'filename:"{filename}"', limit=1)
        
        if not workflows:
            raise HTTPException(status_code=404, detail="Workflow not found in database")
        
        workflow_meta = workflows[0]
        
        # Try to load from vercel_workflows.json
        raw_json = None
        try:
            vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
            if not vercel_data_path.exists():
                vercel_data_path = Path(__file__).parent.parent / "vercel_workflows.json"
            
            if vercel_data_path.exists():
                with open(vercel_data_path, 'r', encoding='utf-8') as f:
                    vercel_data = json.load(f)
                
                # Find the workflow in the vercel data
                for workflow in vercel_data.get('workflows', []):
                    if workflow.get('filename') == filename:
                        # Reconstruct the raw JSON from the metadata
                        raw_json = {
                            'id': workflow.get('workflow_id', ''),
                            'name': workflow.get('name', ''),
                            'active': workflow.get('active', False),
                            'nodes': [],
                            'connections': {},
                            'meta': {
                                'description': workflow.get('description', ''),
                                'tags': workflow.get('tags', [])
                            }
                        }
                        break
                
                if raw_json is None:
                    raise HTTPException(status_code=404, detail=f"Workflow '{filename}' not found in vercel data")
            else:
                raise HTTPException(status_code=404, detail="vercel_workflows.json not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading workflow data: {str(e)}")
        
        # Add missing top-level fields for n8n compatibility
        if raw_json:
            if not raw_json.get('id'):
                raw_json['id'] = workflow_meta.get('workflow_id', '')
            if not raw_json.get('name'):
                raw_json['name'] = workflow_meta.get('name', '')
        
        return JSONResponse(
            content=raw_json,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading workflow: {str(e)}")

@app.get("/api/debug-vercel")
async def debug_vercel():
    """Debug endpoint to check Vercel deployment."""
    try:
        # Check if vercel_workflows.json exists
        vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
        if vercel_data_path.exists():
            with open(vercel_data_path, 'r', encoding='utf-8') as f:
                vercel_data = json.load(f)
            return {
                "status": "success",
                "vercel_data_exists": True,
                "workflow_count": len(vercel_data.get('workflows', [])),
                "sample_workflow": vercel_data.get('workflows', [])[0] if vercel_data.get('workflows') else None
            }
        else:
            return {"status": "error", "vercel_data_exists": False}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/test-workflow/{filename:path}")
async def test_workflow_route(filename: str):
    """Test endpoint to debug workflow route parameter extraction."""
    return {
        "filename": filename,
        "filename_type": type(filename).__name__,
        "filename_length": len(filename),
        "message": "Route parameter extracted successfully"
    }

# Mount static files if they exist
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
