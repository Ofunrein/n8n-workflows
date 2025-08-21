from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from mangum import Mangum
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
import hashlib

app = FastAPI()

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the handler for Vercel
handler = Mangum(app)

# Lightweight workflow database for Vercel
class VercelWorkflowDB:
    """Lightweight workflow database using pre-built JSON data for Vercel serverless environment."""
    
    def __init__(self):
        self.data = self._load_data()
    
    def _load_data(self):
        """Load pre-built workflow data from JSON file."""
        try:
            data_file = 'vercel_workflows.json'
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Warning: {data_file} not found, using empty data")
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
    try:
        # Get real stats for display
        stats = db.get_stats()
        total_workflows = stats.get('total', 0)
        active_workflows = stats.get('active', 0)  
        total_nodes = stats.get('total_nodes', 0)
        unique_integrations = stats.get('unique_integrations', 0)
    except:
        total_workflows = 0
        active_workflows = 0
        total_nodes = 0
        unique_integrations = 0
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>⚡ N8N Workflow Documentation</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .header h1 {{ color: #1e293b; font-size: 2.5rem; margin-bottom: 10px; }}
            .header p {{ color: #64748b; font-size: 1.1rem; }}
            .success {{ background: #10b981; color: white; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .stat-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
            .stat-number {{ font-size: 2rem; font-weight: bold; color: #3b82f6; }}
            .stat-label {{ color: #64748b; margin-top: 5px; }}
            .workflows-section {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 20px 0; }}
            .workflow-item {{ padding: 10px; border-bottom: 1px solid #e2e8f0; }}
            .workflow-item:last-child {{ border-bottom: none; }}
            .workflow-name {{ font-weight: bold; color: #1e293b; }}
            .workflow-desc {{ color: #64748b; font-size: 0.9rem; margin-top: 4px; }}
            .workflow-meta {{ color: #94a3b8; font-size: 0.8rem; margin-top: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ N8N Workflow Documentation</h1>
                <p>High-performance API for browsing and searching workflow documentation</p>
            </div>
            
            <div class="success">
                <h2>🎉 Successfully Deployed on Vercel!</h2>
                <p>Your n8n workflows API is now live and running in the cloud.</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_workflows:,}</div>
                    <div class="stat-label">Total Workflows</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{unique_integrations:,}</div>
                    <div class="stat-label">Unique Integrations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_nodes:,}</div>
                    <div class="stat-label">Total Nodes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{active_workflows:,}</div>
                    <div class="stat-label">Active Workflows</div>
                </div>
            </div>
            
            <div class="stat-card">
                <h3>🚀 API Endpoints</h3>
                <p><strong>Health Check:</strong> <code>/health</code></p>
                <p><strong>API Stats:</strong> <code>/api/stats</code></p>
                <p><strong>Search Workflows:</strong> <code>/api/workflows</code></p>
                <p><strong>Categories:</strong> <code>/api/categories</code></p>
            </div>
            
            <div class="workflows-section" id="workflows-section">
                <h3>📋 Latest Workflows</h3>
                <div id="workflows-list">Loading workflows...</div>
            </div>
        </div>
        
        <script>
            // Load and display latest workflows
            fetch('/api/workflows?per_page=10')
                .then(response => response.json())
                .then(data => {{
                    const workflowsList = document.getElementById('workflows-list');
                    if (data.workflows && data.workflows.length > 0) {{
                        workflowsList.innerHTML = data.workflows.map(workflow => `
                            <div class="workflow-item">
                                <div class="workflow-name">${{workflow.name}}</div>
                                <div class="workflow-desc">${{workflow.description}}</div>
                                <div class="workflow-meta">
                                    ${{workflow.trigger_type}} • ${{workflow.complexity}} complexity • ${{workflow.node_count}} nodes
                                    ${{workflow.integrations.length > 0 ? ' • ' + workflow.integrations.slice(0, 3).join(', ') : ''}}
                                </div>
                            </div>
                        `).join('');
                    }} else {{
                        workflowsList.innerHTML = '<p>No workflows found. The database may need indexing.</p>';
                    }}
                }})
                .catch(error => {{
                    console.error('Error loading workflows:', error);
                    document.getElementById('workflows-list').innerHTML = '<p>Error loading workflows. Check the console for details.</p>';
                }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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

@app.get("/api/categories")
async def get_categories():
    return {
        "categories": [
            "AI Agent Development",
            "Business Process Automation", 
            "Cloud Storage & File Management",
            "Communication & Messaging",
            "Creative Content & Video Automation",
            "Creative Design Automation",
            "CRM & Sales",
            "Data Processing & Analysis",
            "E-commerce & Retail",
            "Financial & Accounting",
            "Marketing & Advertising Automation",
            "Project Management",
            "Social Media Management",
            "Technical Infrastructure & DevOps",
            "Web Scraping & Data Extraction"
        ]
    }
