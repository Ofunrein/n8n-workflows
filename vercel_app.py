from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>⚡ N8N Workflow Documentation</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { color: #1e293b; font-size: 2.5rem; margin-bottom: 10px; }
            .header p { color: #64748b; font-size: 1.1rem; }
            .success { background: #10b981; color: white; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
            .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }
            .stat-number { font-size: 2rem; font-weight: bold; color: #3b82f6; }
            .stat-label { color: #64748b; margin-top: 5px; }
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
                    <div class="stat-number">2,055</div>
                    <div class="stat-label">Total Workflows</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">365</div>
                    <div class="stat-label">Unique Integrations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">29,518</div>
                    <div class="stat-label">Total Nodes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">215</div>
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
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "n8n-workflows-api", "deployed": True}

@app.get("/api/stats")
async def get_stats():
    return {
        "total": 2055,
        "active": 215,
        "inactive": 1840,
        "triggers": {"Complex": 833, "Manual": 477, "Scheduled": 226, "Webhook": 519},
        "complexity": {"high": 716, "low": 565, "medium": 774},
        "total_nodes": 29518,
        "unique_integrations": 365,
        "last_indexed": "2025-08-20"
    }

@app.get("/api/workflows")
async def search_workflows():
    return {
        "workflows": [
            {
                "filename": "sample_workflow.json",
                "name": "Sample N8N Workflow",
                "active": True,
                "description": "This is a sample workflow for demonstration",
                "trigger_type": "Manual",
                "complexity": "medium",
                "node_count": 5,
                "integrations": ["HTTP", "Slack"]
            }
        ],
        "total": 1,
        "page": 1,
        "per_page": 20,
        "pages": 1,
        "query": "",
        "filters": {}
    }

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
