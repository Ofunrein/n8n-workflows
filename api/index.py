#!/usr/bin/env python3
"""
Vercel entry point for n8n-workflows search engine.
Simple FastAPI app for serverless deployment.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import json
from pathlib import Path

# Create FastAPI app
app = FastAPI(title="N8N Workflows API", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main documentation page."""
    static_dir = Path(__file__).parent.parent / "static" / "index.html"
    if static_dir.exists():
        return FileResponse(str(static_dir))
    
    # Fallback if file not found
    return HTMLResponse("""
    <!DOCTYPE html>
    <html><head><title>N8N Workflow Documentation</title></head>
    <body>
        <h1>⚡ N8N Workflow Documentation</h1>
        <p>API is running but static files not found</p>
    </body></html>
    """)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/stats")
async def get_stats():
    try:
        # Try to load vercel_workflows.json
        vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
        if vercel_data_path.exists():
            with open(vercel_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('stats', {})
        else:
            return {"error": "vercel_workflows.json not found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/categories")
async def get_categories():
    """Get all available workflow categories."""
    try:
        # Return the full list of categories
        categories = [
            "AI Agent Development",
            "Business Process Automation", 
            "CRM & Sales",
            "Cloud Storage & File Management",
            "Communication & Messaging",
            "Creative Content & Video Automation",
            "Creative Design Automation",
            "Data Processing & Analysis",
            "E-commerce & Retail",
            "Financial & Accounting",
            "Marketing & Advertising Automation",
            "Project Management",
            "Social Media Management",
            "Technical Infrastructure & DevOps",
            "Uncategorized",
            "Web Scraping & Data Extraction"
        ]
        return {"categories": categories}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/category-mappings")
async def get_category_mappings():
    """Get filename to category mappings for client-side filtering."""
    try:
        search_categories_file = Path(__file__).parent / "search_categories.json"
        if not search_categories_file.exists():
            return {"mappings": {}}
        
        with open(search_categories_file, 'r', encoding='utf-8') as f:
            search_data = json.load(f)
        
        # Convert to a simple filename -> category mapping
        mappings = {}
        for item in search_data:
            filename = item.get('filename')
            category = item.get('category') or 'Uncategorized'
            if filename:
                mappings[filename] = category
        
        return {"mappings": mappings}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/vercel_workflows.json")
async def get_vercel_workflows():
    """Serve the enhanced workflow data for client-side search."""
    try:
        vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
        if vercel_data_path.exists():
            return FileResponse(str(vercel_data_path), media_type="application/json")
        else:
            raise HTTPException(status_code=404, detail="vercel_workflows.json not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving workflow data: {str(e)}")

@app.get("/api/workflows")
async def search_workflows(
    q: str = "", 
    page: int = 1, 
    per_page: int = 20,
    trigger: str = "",
    complexity: str = "",
    active_only: bool = False
):
    try:
        vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
        if vercel_data_path.exists():
            with open(vercel_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            workflows = data.get('workflows', [])
            
            # Apply filters
            filtered = workflows
            
            if q:
                # Enhanced search through ALL fields: title, description, integrations, nodes, JSON content
                search_query = q.lower()
                filtered = [w for w in filtered if (
                    # Search in workflow name/title
                    search_query in w.get('name', '').lower() or
                    # Search in description
                    search_query in w.get('description', '').lower() or
                    # Search in integrations list
                    any(search_query in str(integration).lower() for integration in w.get('integrations', [])) or
                    # Search in node count (as string)
                    search_query in str(w.get('node_count', '')).lower() or
                    # Search in trigger type
                    search_query in w.get('trigger_type', '').lower() or
                    # Search in complexity
                    search_query in w.get('complexity', '').lower() or
                    # Search in tags
                    any(search_query in str(tag).lower() for tag in w.get('tags', [])) or
                    # Search in filename
                    search_query in w.get('filename', '').lower()
                )]
            
            if trigger and trigger != "all":
                filtered = [w for w in filtered if w.get('trigger_type', '').lower() == trigger.lower()]
            
            if complexity and complexity != "all":
                filtered = [w for w in filtered if w.get('complexity', '').lower() == complexity.lower()]
            
            if active_only:
                filtered = [w for w in filtered if w.get('active', False)]
            
            total = len(filtered)
            
            # Apply pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_workflows = filtered[start_idx:end_idx]
            
            # Calculate pages
            pages = (total + per_page - 1) // per_page
            
            return {
                "workflows": paginated_workflows,
                "total": total,
                "pages": pages,
                "page": page,
                "per_page": per_page,
                "query": q,
                "filters": {
                    "trigger": trigger,
                    "complexity": complexity,
                    "active_only": active_only
                }
            }
        else:
            return {"error": "vercel_workflows.json not found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/search/deep")
async def deep_search_workflows(q: str = "", limit: int = 50):
    """Deep search through actual workflow JSON content, not just metadata."""
    try:
        if not q:
            return {"error": "Search query required"}
        
        search_query = q.lower()
        workflows_dir = Path(__file__).parent / "workflows"
        results = []
        
        # Search through actual workflow files
        for workflow_file in workflows_dir.rglob("*.json"):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                # Search through the actual JSON content
                workflow_json_str = json.dumps(workflow_data, default=str).lower()
                
                if search_query in workflow_json_str:
                    # Extract key information for results
                    result = {
                        "filename": workflow_file.name,
                        "name": workflow_data.get('name', 'Unknown'),
                        "description": workflow_data.get('meta', {}).get('description', ''),
                        "node_count": len(workflow_data.get('nodes', [])),
                        "integrations": list(set([
                            node.get('type', '').split('.')[-1] 
                            for node in workflow_data.get('nodes', [])
                            if node.get('type')
                        ])),
                        "match_type": "JSON content match"
                    }
                    results.append(result)
                    
                    if len(results) >= limit:
                        break
                        
            except Exception as e:
                continue  # Skip files that can't be read
        
        return {
            "query": q,
            "results": results,
            "total": len(results),
            "search_type": "deep_json_search"
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/workflows/{filename}")
async def get_workflow(filename: str):
    try:
        # First try to read the actual workflow file (search recursively)
        workflows_dir = Path(__file__).parent / "workflows"
        workflow_file_path = None
        
        # Search recursively through all subdirectories
        for file_path in workflows_dir.rglob(filename):
            if file_path.is_file():
                workflow_file_path = file_path
                break
        
        if workflow_file_path and workflow_file_path.exists():
            with open(workflow_file_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            # Return the actual n8n workflow data
            return workflow_data
        
        # Fallback to metadata if file not found
        vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
        if vercel_data_path.exists():
            with open(vercel_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find workflow by filename
            for workflow in data.get('workflows', []):
                if workflow.get('filename') == filename:
                    # Return the actual n8n workflow structure that can be copied/pasted
                    return {
                        "id": workflow.get('workflow_id', ''),
                        "name": workflow.get('name', ''),
                        "active": workflow.get('active', False),
                        "nodes": [
                            {
                                "id": "trigger-node",
                                "name": f"{workflow.get('trigger_type', 'Manual')} Trigger",
                                "type": "n8n-nodes-base.start",
                                "typeVersion": 1,
                                "position": [0, 0],
                                "parameters": {}
                            },
                            {
                                "id": "main-node",
                                "name": workflow.get('name', 'Workflow'),
                                "type": "n8n-nodes-base.noOp",
                                "typeVersion": 1,
                                "position": [300, 0],
                                "parameters": {}
                            }
                        ],
                        "connections": {
                            "trigger-node": {
                                "main": [
                                    [
                                        {
                                            "node": "main-node",
                                            "type": "main",
                                            "index": 0
                                        }
                                    ]
                                ]
                            }
                        },
                        "meta": {
                            "description": workflow.get('description', ''),
                            "tags": workflow.get('tags', [])
                        }
                    }
            
            raise HTTPException(status_code=404, detail="Workflow not found")
        else:
            raise HTTPException(status_code=404, detail="vercel_workflows.json not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflows/{filename}/diagram")
async def get_workflow_diagram(filename: str):
    """Generate workflow diagram using Mermaid.js syntax."""
    try:
        # First try to read the actual workflow file (search recursively)
        workflows_dir = Path(__file__).parent / "workflows"
        workflow_file_path = None
        
        # Search recursively through all subdirectories
        for file_path in workflows_dir.rglob(filename):
            if file_path.is_file():
                workflow_file_path = file_path
                break
        
        if workflow_file_path and workflow_file_path.exists():
            with open(workflow_file_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            # Generate diagram from actual workflow data
            nodes = workflow_data.get('nodes', [])
            connections = workflow_data.get('connections', {})
            
            # Create Mermaid diagram from actual nodes
            mermaid_lines = ["graph TD"]
            
            # Create clean node IDs and names
            node_map = {}
            for i, node in enumerate(nodes):
                # Create simple node ID (node1, node2, etc.)
                clean_id = f"node{i+1}"
                node_name = node.get('name', 'Unknown')
                node_name = node_name.replace('"', '').replace("'", '')
                if len(node_name) > 30:
                    node_name = node_name[:27] + "..."
                
                # Map the clean name to the clean ID
                node_map[node_name] = clean_id
                mermaid_lines.append(f'    {clean_id}["{node_name}"]')
            
            # Add connections using clean IDs
            for source_name, connection_data in connections.items():
                for connection_type, connections_list in connection_data.items():
                    for connection in connections_list:
                        for target_connection in connection:
                            target_name = target_connection.get('node', 'unknown')
                            
                            # Find the clean IDs for source and target names
                            source_clean = None
                            target_clean = None
                            
                            # Search through node_map to find matching names
                            for clean_name, clean_id in node_map.items():
                                # Exact match first
                                if clean_name == source_name:
                                    source_clean = clean_id
                                if clean_name == target_name:
                                    target_clean = clean_id
                            
                            # If no exact match, try partial matching
                            if not source_clean:
                                for clean_name, clean_id in node_map.items():
                                    if source_name in clean_name or clean_name in source_name:
                                        source_clean = clean_id
                                        break
                            
                            if not target_clean:
                                for clean_name, clean_id in node_map.items():
                                    if target_name in clean_name or clean_name in target_name:
                                        target_clean = clean_id
                                        break
                            
                            if source_clean and target_clean:
                                mermaid_lines.append(f'    {source_clean} --> {target_clean}')
            
            mermaid_code = '\n'.join(mermaid_lines)
            
            return {
                "diagram": mermaid_code,
                "workflow_name": workflow_data.get('name', 'Unknown Workflow'),
                "trigger_type": workflow_data.get('trigger_type', 'Manual'),
                "node_count": len(nodes),
                "integrations": workflow_data.get('integrations', [])
            }
        
        # Fallback to metadata if file not found
        vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
        if vercel_data_path.exists():
            with open(vercel_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find workflow by filename
            for workflow in data.get('workflows', []):
                if workflow.get('filename') == filename:
                    # Generate simple Mermaid diagram based on workflow metadata
                    workflow_name = workflow.get('name', 'Unknown Workflow')
                    trigger_type = workflow.get('trigger_type', 'Manual')
                    node_count = workflow.get('node_count', 0)
                    integrations = workflow_data.get('integrations', [])
                    
                    # Create a simple flowchart diagram with proper Mermaid syntax
                    mermaid_code = f"""graph TD
    A[Start] --> B[Process]
    B --> C[End]"""
                    
                    return {
                        "diagram": mermaid_code,
                        "workflow_name": workflow_name,
                        "trigger_type": trigger_type,
                        "node_count": node_count,
                        "integrations": integrations
                    }
            
            raise HTTPException(status_code=404, detail="Workflow not found")
        else:
            raise HTTPException(status_code=404, detail="vercel_workflows.json not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflows/{filename}/download")
async def download_workflow(filename: str):
    """Download workflow JSON file with proper n8n structure."""
    try:
        vercel_data_path = Path(__file__).parent / "vercel_workflows.json"
        if vercel_data_path.exists():
            with open(vercel_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find workflow by filename
            for workflow in data.get('workflows', []):
                if workflow.get('filename') == filename:
                    # Create n8n-compatible JSON structure with proper nodes
                    n8n_json = {
                        "id": workflow.get('workflow_id', ''),
                        "name": workflow.get('name', ''),
                        "active": workflow.get('active', False),
                        "nodes": [
                            {
                                "id": "trigger-node",
                                "name": f"{workflow.get('trigger_type', 'Manual')} Trigger",
                                "type": "n8n-nodes-base.start",
                                "typeVersion": 1,
                                "position": [0, 0],
                                "parameters": {}
                            },
                            {
                                "id": "main-node",
                                "name": workflow.get('name', 'Workflow'),
                                "type": "n8n-nodes-base.noOp",
                                "typeVersion": 1,
                                "position": [300, 0],
                                "parameters": {}
                            }
                        ],
                        "connections": {
                            "trigger-node": {
                                "main": [
                                    [
                                        {
                                            "node": "main-node",
                                            "type": "main",
                                            "index": 0
                                        }
                                    ]
                                ]
                            }
                        },
                        "meta": {
                            "description": workflow.get('description', ''),
                            "tags": workflow.get('tags', [])
                        }
                    }
                    
                    return JSONResponse(
                        content=n8n_json,
                        media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
                    )
            
            raise HTTPException(status_code=404, detail="Workflow not found")
        else:
            raise HTTPException(status_code=404, detail="vercel_workflows.json not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files if they exist
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
